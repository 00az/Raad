"""C5 edge adapter: validate correlation, verify token profile, and forward safely."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from typing import Any
from urllib.parse import urlsplit

import boto3
import jwt
import requests
from requests_aws4auth import AWS4Auth
from jwt import PyJWKClient

CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ALLOWED_METHODS = {"GET", "PUT", "POST"}
_request_start = 0.0
_request_path = "/money/v1"
_request_method = ""


def _publish_metrics(status: int, elapsed_ms: int, path: str, method: str) -> None:
    values: dict[str, int | float] = {"EdgeRequests": 1, "RequestLatencyMs": elapsed_ms}
    units: dict[str, str] = {"EdgeRequests": "Count", "RequestLatencyMs": "Milliseconds"}
    if status >= 500:
        values["Edge5xx"] = 1
        units["Edge5xx"] = "Count"
    if path.endswith("/transfers") and method == "POST":
        values.update({"TransferResponses": 1, "TransferLatencyMs": elapsed_ms})
        units.update({"TransferResponses": "Count", "TransferLatencyMs": "Milliseconds"})
        if elapsed_ms > 2_000:
            values["TransferOver2s"] = 1
            units["TransferOver2s"] = "Count"
        if status == 201:
            values["ValidTransferSuccesses"] = 1
            units["ValidTransferSuccesses"] = "Count"
        elif status in {409, 422}:
            values["BusinessTransferRefusals"] = 1
            units["BusinessTransferRefusals"] = "Count"
        elif status >= 500:
            values["TechnicalTransferFailures"] = 1
            units["TechnicalTransferFailures"] = "Count"
    metrics = [{"Name": name, "Unit": units[name]} for name in values]
    print(json.dumps({"_aws": {"Timestamp": int(time.time() * 1000), "CloudWatchMetrics": [{"Namespace": "Raad/Platform", "Dimensions": [["Environment"]], "Metrics": metrics}]}, "Environment": os.environ.get("ENVIRONMENT", "unknown"), **values}))


def _response(status: int, code: str, message: str, correlation_id: str) -> dict[str, Any]:
    _publish_metrics(status, max(0, int((time.monotonic() - _request_start) * 1000)), _request_path, _request_method)
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json", "x-correlation-id": correlation_id, "cache-control": "no-store"},
        "body": json.dumps({"error": {"code": code, "message": message, "correlationId": correlation_id}}),
    }


def _correlation(headers: dict[str, str]) -> str:
    value = next((v for k, v in headers.items() if k.lower() == "x-correlation-id"), "")
    return value if CORRELATION_PATTERN.fullmatch(value) else __import__("uuid").uuid4().hex


def _profile() -> tuple[str, str]:
    pool_id = os.environ["USER_POOL_ID"]
    region = pool_id.split("_")[0]
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    parameter = boto3.client("ssm").get_parameter(Name=os.environ["SERVICE_URL_PARAMETER"])
    return issuer, parameter["Parameter"]["Value"]


def _verify(token: str, issuer: str) -> None:
    jwks_uri = f"{issuer}/.well-known/jwks.json"
    key = PyJWKClient(jwks_uri, cache_jwk_set=True, lifespan=300).get_signing_key_from_jwt(token).key
    claims = jwt.decode(token, key, algorithms=["RS256"], issuer=issuer, options={"verify_aud": False, "require": ["exp", "iss", "token_use", "client_id"]})
    if claims.get("token_use") != "access" or claims.get("client_id") != os.environ["CLIENT_ID"]:
        raise jwt.InvalidTokenError("wrong token profile")


def _protected_correlation(correlation_id: str) -> tuple[str, str]:
    secret = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["CORRELATION_SECRET_ARN"])["SecretString"])
    version = str(secret.get("version", "1"))
    key = secret.get("key") or secret.get("material", "")
    if not key:
        raise ValueError("correlation key unavailable")
    return version, hmac.new(key.encode(), correlation_id.encode(), hashlib.sha256).hexdigest()


def handle(event: dict[str, Any], _context: object) -> dict[str, Any]:
    """Handle one HTTP API event; payloads and credentials are never logged."""
    global _request_start, _request_path, _request_method
    headers = event.get("headers") or {}
    _request_start = time.monotonic()
    _request_path = event.get("rawPath", "/money/v1")
    _request_method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
    correlation = _correlation(headers)
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
        if method not in ALLOWED_METHODS:
            return _response(400, "VALIDATION_ERROR", "The request is invalid.", correlation)
        auth = next((v for k, v in headers.items() if k.lower() == "authorization"), "")
        if not auth.startswith("Bearer "):
            return _response(401, "AUTHENTICATION_REQUIRED", "Sign in to continue.", correlation)
        issuer, target = _profile()
        _verify(auth[7:], issuer)
        parsed = urlsplit(target)
        if parsed.scheme != "https" or not parsed.netloc:
            return _response(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation)
        version, protected = _protected_correlation(correlation)
        path = event.get("rawPath", "/money/v1")
        if not path.startswith("/money/v1"):
            return _response(500, "INTERNAL_ERROR", "The request could not be completed.", correlation)
        query = event.get("rawQueryString", "")
        url = target.rstrip("/") + path + (f"?{query}" if query else "")
        body = event.get("body")
        if event.get("isBase64Encoded") and body:
            body = base64.b64decode(body)
        forward_headers = {"Authorization": auth, "X-Correlation-Id": correlation, "Content-Type": headers.get("content-type", "application/json")}
        credentials = boto3.Session().get_credentials()
        if credentials is None:
            return _response(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation)
        frozen = credentials.get_frozen_credentials()
        region = boto3.session.Session().region_name or os.environ.get("AWS_REGION", "")
        signed = AWS4Auth(frozen.access_key, frozen.secret_key, region, "lambda", session_token=frozen.token)
        response = requests.request(method, url, headers=forward_headers, data=body, auth=signed, timeout=(1.0, 7.0), allow_redirects=False)
        duration = int((time.monotonic() - _request_start) * 1000)
        # Structured allowlist only; caller-controlled correlation is always HMAC protected.
        print(json.dumps({"component": "platform-edge", "operation": "money", "result": "upstream", "durationMs": duration, "correlationKeyVersion": version, "correlationKey": protected}))
        response_headers = {k.lower(): v for k, v in response.headers.items() if k.lower() in {"content-type", "idempotency-replayed"}}
        response_headers.update({"x-correlation-id": correlation, "cache-control": "no-store"})
        _publish_metrics(response.status_code, duration, path, method)
        return {"statusCode": response.status_code, "headers": response_headers, "body": response.text, "isBase64Encoded": False}
    except (requests.Timeout, requests.ConnectionError):
        return _response(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation)
    except (KeyError, ValueError, jwt.PyJWTError, requests.RequestException):
        return _response(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation)
