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
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config
from botocore.credentials import Credentials
from botocore.exceptions import BotoCoreError, ClientError
from jwt import PyJWKClient
from urllib3.util import Timeout

CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ALLOWED_METHODS = {"GET", "PUT", "POST"}
_request_start = 0.0
_request_path = "/money/v1"
_request_method = ""
_jwk_clients: dict[str, PyJWKClient] = {}
_origin_cache: tuple[str, str, float] | None = None
SDK_CONFIG = Config(connect_timeout=0.25, read_timeout=0.5, retries={"total_max_attempts": 1})


def _fault_delay(mode: str) -> None:
    """Dev proof only: invalid or production configuration never injects delay."""
    if os.environ.get("ENVIRONMENT") != "dev" or os.environ.get("U1_DEV_FAULT_MODE") != mode:
        return
    if not re.fullmatch(r"[a-f0-9]{32}", os.environ.get("U1_DEV_FAULT_RUN_ID", "")):
        return
    time.sleep(2.1)


# This executes once per fresh published execution environment, before handle's timer.
_fault_delay("init")


def entry(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Origin entry wrapper; delay is outside the diagnostic adapter handler."""
    rejected = _origin_rejection(event)
    if rejected is not None:
        return rejected
    probe = (event.get("headers") or {}).get("x-u1-probe-run", "")
    enabled = bool(probe) and probe == os.environ.get("U1_DEV_FAULT_RUN_ID")
    if enabled:
        _fault_delay("origin")
    result = handle(event, context)
    if enabled and os.environ.get("ENVIRONMENT") == "dev":
        result["headers"]["x-u1-adapter-ms"] = str(
            max(0, int((time.monotonic() - _request_start) * 1000))
        )
        result["headers"]["x-u1-adapter-version"] = os.environ.get(
            "AWS_LAMBDA_FUNCTION_VERSION", ""
        )
    return result


def _origin_secret() -> str:
    """Read only the origin secret; finite caching bounds coordinated rotation."""
    global _origin_cache
    arn = os.environ["ORIGIN_SECRET_ARN"]
    now = time.monotonic()
    if _origin_cache and _origin_cache[0] == arn and now < _origin_cache[2]:
        return _origin_cache[1]
    value = boto3.client("secretsmanager", config=SDK_CONFIG).get_secret_value(SecretId=arn)[
        "SecretString"
    ]
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9]{64}", value):
        raise ValueError("invalid origin configuration")
    _origin_cache = (arn, value, now + 60)
    return value


def _origin_rejection(event: dict[str, Any]) -> dict[str, Any] | None:
    """Reject bypass traffic before auth, forwarding, or public SLI publication."""
    headers = event.get("headers") or {}
    supplied = next((v for k, v in headers.items() if k.lower() == "x-raad-origin"), "")
    status, code, message = 403, "FORBIDDEN", "The request is not permitted."
    try:
        if not os.environ.get("ORIGIN_SECRET_ARN"):
            raise KeyError("origin configuration unavailable")
        if supplied and hmac.compare_digest(supplied.encode(), _origin_secret().encode()):
            return None
    except (KeyError, ValueError, BotoCoreError, ClientError):
        status, code, message = (
            503,
            "SERVICE_UNAVAILABLE",
            "The service is temporarily unavailable.",
        )
    correlation = _correlation(headers)
    # Do not log the header, secret, or event, nor count direct-origin traffic as public samples.
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "x-correlation-id": correlation,
            "cache-control": "no-store",
        },
        "body": json.dumps({"code": code, "message": message, "correlationId": correlation}),
    }


def _publish_metrics(status: int, elapsed_ms: int, path: str, method: str) -> None:
    values: dict[str, int | float] = {"EdgeRequests": 1, "RequestLatencyMs": elapsed_ms}
    units: dict[str, str] = {"EdgeRequests": "Count", "RequestLatencyMs": "Milliseconds"}
    if status >= 500:
        values["Edge5xx"] = 1
        units["Edge5xx"] = "Count"
    if path.endswith("/transfers") and method == "POST":
        values.update({"TransferResponses": 1, "AdapterTransferLatencyMs": elapsed_ms})
        units.update({"TransferResponses": "Count", "AdapterTransferLatencyMs": "Milliseconds"})
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
    print(
        json.dumps(
            {
                "_aws": {
                    "Timestamp": int(time.time() * 1000),
                    "CloudWatchMetrics": [
                        {
                            "Namespace": "Raad/Platform",
                            "Dimensions": [["Environment"]],
                            "Metrics": metrics,
                        }
                    ],
                },
                "Environment": os.environ.get("ENVIRONMENT", "unknown"),
                **values,
            }
        )
    )


def _response(status: int, code: str, message: str, correlation_id: str) -> dict[str, Any]:
    try:
        version, protected = _protected_correlation(correlation_id)
        print(
            json.dumps(
                {
                    "component": "platform-edge",
                    "result": code,
                    "correlationKeyVersion": version,
                    "correlationKey": protected,
                }
            )
        )
    except (KeyError, ValueError, BotoCoreError, ClientError):
        pass  # Money response never depends on best-effort telemetry.
    _publish_metrics(
        status,
        max(0, int((time.monotonic() - _request_start) * 1000)),
        _request_path,
        _request_method,
    )
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "x-correlation-id": correlation_id,
            "cache-control": "no-store",
        },
        "body": json.dumps({"code": code, "message": message, "correlationId": correlation_id}),
    }


def _correlation(headers: dict[str, str]) -> str:
    value = next((v for k, v in headers.items() if k.lower() == "x-correlation-id"), "")
    return value if CORRELATION_PATTERN.fullmatch(value) else __import__("uuid").uuid4().hex


def _profile() -> tuple[str, str]:
    pool_id = os.environ["USER_POOL_ID"]
    region = pool_id.split("_")[0]
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    parameter = boto3.client("ssm", config=SDK_CONFIG).get_parameter(
        Name=os.environ["SERVICE_URL_PARAMETER"]
    )
    return issuer, parameter["Parameter"]["Value"]


def _verify(token: str, issuer: str) -> None:
    jwks_uri = f"{issuer}/.well-known/jwks.json"
    client = _jwk_clients.get(issuer)
    if client is None:
        client = PyJWKClient(
            jwks_uri,
            cache_jwk_set=True,
            cache_keys=False,
            lifespan=21600,
            timeout=1,
            cooldown_duration=60,
        )
        _jwk_clients[issuer] = client
    key = client.get_signing_key_from_jwt(token).key
    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        issuer=issuer,
        options={"verify_aud": False, "require": ["sub", "exp", "iss", "token_use", "client_id"]},
    )
    if claims.get("token_use") != "access" or claims.get("client_id") != os.environ["CLIENT_ID"]:
        raise jwt.InvalidTokenError("wrong token profile")


def _protected_correlation(correlation_id: str) -> tuple[str, str]:
    secret = json.loads(
        boto3.client("secretsmanager", config=SDK_CONFIG).get_secret_value(
            SecretId=os.environ["CORRELATION_SECRET_ARN"]
        )["SecretString"]
    )
    version = str(secret.get("version", "1"))
    key = secret.get("key") or secret.get("material", "")
    if not key:
        raise ValueError("correlation key unavailable")
    return version, hmac.new(key.encode(), correlation_id.encode(), hashlib.sha256).hexdigest()


def handle(event: dict[str, Any], _context: object) -> dict[str, Any]:
    """Handle one HTTP API event; payloads and credentials are never logged."""
    global _request_start, _request_path, _request_method
    rejected = _origin_rejection(event)
    if rejected is not None:
        return rejected
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
            return _response(
                503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation
            )
        version, protected = _protected_correlation(correlation)
        path = event.get("rawPath", "/money/v1")
        if not path.startswith("/money/v1"):
            return _response(
                500, "INTERNAL_ERROR", "The request could not be completed.", correlation
            )
        query = event.get("rawQueryString", "")
        url = target.rstrip("/") + "/"
        body = event.get("body")
        if event.get("isBase64Encoded") and body:
            body = base64.b64decode(body).decode("utf-8")
        original_headers = {
            "authorization": auth,
            "x-correlation-id": correlation,
            "content-type": next(
                (v for k, v in headers.items() if k.lower() == "content-type"), "application/json"
            ),
        }
        for name in ("idempotency-key",):
            value = next((v for k, v in headers.items() if k.lower() == name), None)
            if value is not None:
                original_headers[name] = value
        envelope = {
            "version": 1,
            "request": {
                "method": method,
                "path": path,
                "query": query,
                "headers": original_headers,
                "body": body,
            },
        }
        forward_headers = {"Content-Type": "application/json"}
        credentials = boto3.Session().get_credentials()
        if credentials is None:
            return _response(
                503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation
            )
        frozen = credentials.get_frozen_credentials()
        if not frozen.access_key or not frozen.secret_key:
            return _response(
                503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation
            )
        region = boto3.session.Session().region_name or os.environ.get("AWS_REGION", "")
        payload = json.dumps(envelope)
        outer = AWSRequest(method="POST", url=url, data=payload, headers=forward_headers)
        SigV4Auth(
            Credentials(frozen.access_key, frozen.secret_key, frozen.token), "lambda", region
        ).add_auth(outer)
        remaining = 8.0 - (time.monotonic() - _request_start)
        if remaining <= 0.25:
            return _response(
                503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation
            )
        response = requests.request(
            "POST",
            url,
            headers=dict(outer.headers),
            data=payload,
            # Requests accepts urllib3 Timeout at runtime; its stubs omit this form.
            timeout=Timeout(total=remaining, connect=0.25, read=remaining - 0.25),  # type: ignore[arg-type]
            allow_redirects=False,
        )
        if response.status_code >= 400:
            upstream_error = json.loads(response.text)
            if (
                not isinstance(upstream_error, dict)
                or not {"code", "message", "correlationId"} <= set(upstream_error)
                or upstream_error["correlationId"] != correlation
            ):
                return _response(
                    503,
                    "SERVICE_UNAVAILABLE",
                    "The service is temporarily unavailable.",
                    correlation,
                )
        duration = int((time.monotonic() - _request_start) * 1000)
        # Structured allowlist only; caller-controlled correlation is always HMAC protected.
        print(
            json.dumps(
                {
                    "component": "platform-edge",
                    "operation": "money",
                    "result": "upstream",
                    "durationMs": duration,
                    "correlationKeyVersion": version,
                    "correlationKey": protected,
                }
            )
        )
        response_headers = {
            k.lower(): v
            for k, v in response.headers.items()
            if k.lower()
            in {"content-type", "idempotency-replayed", "retry-after", "x-u1-history-truncated"}
        }
        response_headers.update({"x-correlation-id": correlation, "cache-control": "no-store"})
        _publish_metrics(response.status_code, duration, path, method)
        return {
            "statusCode": response.status_code,
            "headers": response_headers,
            "body": response.text,
            "isBase64Encoded": False,
        }
    except (requests.Timeout, requests.ConnectionError):
        return _response(
            503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation
        )
    except jwt.PyJWKClientConnectionError:
        return _response(
            503, "TOKEN_VERIFIER_UNAVAILABLE", "Sign in is temporarily unavailable.", correlation
        )
    except (jwt.InvalidTokenError, jwt.PyJWKClientError):
        return _response(401, "AUTHENTICATION_REQUIRED", "Sign in to continue.", correlation)
    except (KeyError, ValueError, requests.RequestException, BotoCoreError, ClientError):
        return _response(
            503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.", correlation
        )
