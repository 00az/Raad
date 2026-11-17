"""Platform smoke checks for one deployed environment (team practice: run after every deploy).

Nothing is contacted unless --execute is given. Before any request, the outputs document must
describe exactly the expected environment and account (the same validation as the C4/C5 writer),
and the caller's AWS account must equal --expected-account. Output is check names and outcomes
only: never a token, password, code, email, profile or secret value. A check whose evidence is
missing or cannot be established from this client is reported pending, which fails the run.

Run from infrastructure/:
    uv run python ../scripts/platform_smoke.py --environment dev --expected-account <id> \
        --outputs outputs.json --fixture-secret-arn <arn> --execute
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infrastructure"))

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from raad_platform.configuration import (
    ENVIRONMENTS,
    ConfigurationError,
    PlatformConfiguration,
    build_configuration,
)

PASSED, FAILED, PENDING = "passed", "failed", "pending"
TIMEOUT = 10
SDK_CONFIG = Config(connect_timeout=2, read_timeout=5, retries={"total_max_attempts": 2})
TlsProbe = Callable[[str, ssl.TLSVersion], str]


class ScopeError(RuntimeError):
    """The environment, account or outputs do not match; nothing further is attempted."""


@dataclass(frozen=True)
class Result:
    name: str
    outcome: str
    detail: str = ""


def planned_checks(environment: str) -> list[str]:
    checks = [
        "anonymous-refused",
        "direct-origin-refused",
        "tls-minimum",
        "outputs-coherent",
        "fixture-sign-in",
    ]
    return checks + (["dev-stub-mapping"] if environment == "dev" else [])


class PlatformSmoke:
    def __init__(
        self,
        *,
        environment: str,
        account: str,
        outputs: Any,
        clients: Callable[[str], Any],
        http: Any,
        tls_probe: TlsProbe,
        fixture_secret_arn: str | None,
        new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self.environment, self.account = environment, account
        self.outputs, self.clients, self.http = outputs, clients, http
        self.tls_probe, self.fixture_secret_arn, self.new_id = tls_probe, fixture_secret_arn, new_id

    def run(self) -> list[Result]:
        try:
            config = build_configuration(
                self.outputs, environment=self.environment, account=self.account
            )
        except ConfigurationError as error:
            raise ScopeError(str(error)) from error
        caller = self.clients("sts").get_caller_identity().get("Account")
        if caller != self.account:
            raise ScopeError("the caller's AWS account is not the expected account")
        api = config.mobile["apiBaseUrl"]
        endpoint = self._edge_output("HttpApiEndpointOutput")
        checks: dict[str, Callable[[], Result]] = {
            "anonymous-refused": lambda: self._anonymous(api),
            "direct-origin-refused": lambda: self._direct_origin(endpoint),
            "tls-minimum": lambda: self._tls(api),
            "outputs-coherent": lambda: self._outputs(config),
            "fixture-sign-in": lambda: self._sign_in(config),
            "dev-stub-mapping": lambda: self._stub(api),
        }
        return [self._guarded(name, checks[name]) for name in planned_checks(self.environment)]

    def _edge_output(self, key: str) -> str:
        value: str = self.outputs[f"RaadPublicEdge-{self.environment}"][key]
        return value

    @staticmethod
    def _guarded(name: str, check: Callable[[], Result]) -> Result:
        try:
            return check()
        except (requests.RequestException, BotoCoreError, ClientError):
            return Result(name, FAILED, "dependency unavailable")
        except (KeyError, ValueError, TypeError):
            return Result(name, FAILED, "unexpected response shape")

    def _error_body(self, response: Any, code: str, correlation: str | None) -> bool:
        body = response.json()
        return (
            isinstance(body, dict)
            and set(body) == {"code", "message", "correlationId"}
            and body["code"] == code
            and (correlation is None or body["correlationId"] == correlation)
        )

    def _anonymous(self, api: str) -> Result:
        correlation = self.new_id()
        response = self.http.get(
            f"{api}/money/v1/wallet",
            headers={"X-Correlation-Id": correlation},
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        echoed = response.headers.get("x-correlation-id") == correlation
        if (
            response.status_code == 401
            and echoed
            and self._error_body(response, "AUTHENTICATION_REQUIRED", correlation)
        ):
            return Result("anonymous-refused", PASSED)
        return Result("anonymous-refused", FAILED, f"status {response.status_code}")

    def _direct_origin(self, endpoint: str) -> Result:
        response = self.http.get(
            f"{endpoint}/money/v1/wallet", timeout=TIMEOUT, allow_redirects=False
        )
        if response.status_code == 403 and self._error_body(response, "FORBIDDEN", None):
            return Result("direct-origin-refused", PASSED)
        return Result("direct-origin-refused", FAILED, f"status {response.status_code}")

    def _tls(self, api: str) -> Result:
        host = urlsplit(api).hostname or ""
        old = self.tls_probe(host, ssl.TLSVersion.TLSv1_1)
        current = self.tls_probe(host, ssl.TLSVersion.TLSv1_2)
        if current != "accepted":
            return Result("tls-minimum", FAILED, "TLS 1.2 handshake failed")
        if old == "accepted":
            return Result("tls-minimum", FAILED, "TLS 1.1 was accepted")
        if old == "refused-by-server":
            return Result("tls-minimum", PASSED)
        return Result("tls-minimum", PENDING, "TLS 1.1 refusal not observable from this client")

    def _outputs(self, config: PlatformConfiguration) -> Result:
        ssm = self.clients("ssm")
        prefix = f"/raad/{self.environment}"

        def parameter(name: str) -> str:
            value: str = ssm.get_parameter(Name=f"{prefix}/{name}")["Parameter"]["Value"]
            return value

        if json.loads(parameter("verifier")) != config.verifier:
            return Result("outputs-coherent", FAILED, "verifier differs from outputs")
        if parameter("public-api-url").rstrip("/") != config.mobile["apiBaseUrl"]:
            return Result("outputs-coherent", FAILED, "public URL differs from outputs")
        bus = self.outputs[f"RaadIdentity-{self.environment}"]["EventBusArnOutput"]
        if parameter("event-bus/arn") != bus or not parameter("alarm-topic/arn"):
            return Result("outputs-coherent", FAILED, "shared ARNs differ from outputs")
        return Result("outputs-coherent", PASSED)

    def _sign_in(self, config: PlatformConfiguration) -> Result:
        if not self.fixture_secret_arn:
            return Result("fixture-sign-in", FAILED, "no fixture secret supplied")
        fixture = json.loads(
            self.clients("secretsmanager").get_secret_value(SecretId=self.fixture_secret_arn)[
                "SecretString"
            ]
        )
        if not isinstance(fixture.get("email"), str) or not isinstance(
            fixture.get("password"), str
        ):
            return Result("fixture-sign-in", FAILED, "fixture secret has no usable user")
        identity = self.outputs[f"RaadIdentity-{self.environment}"]
        authentication = self.clients("cognito-idp").admin_initiate_auth(
            UserPoolId=identity["UserPoolIdOutput"],
            ClientId=identity["UserPoolClientIdOutput"],
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": fixture["email"], "PASSWORD": fixture["password"]},
        )
        token = (authentication.get("AuthenticationResult") or {}).get("AccessToken")
        if not token:
            return Result("fixture-sign-in", FAILED, "sign-in returned a challenge, not tokens")
        response = self.http.get(
            f"{config.mobile['apiBaseUrl']}/money/v1/wallet",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        del token
        if response.status_code == 200 or (
            response.status_code == 404 and self._error_body(response, "WALLET_NOT_FOUND", None)
        ):
            return Result("fixture-sign-in", PASSED)
        return Result("fixture-sign-in", FAILED, f"status {response.status_code}")

    def _stub(self, api: str) -> Result:
        response = self.http.get(f"{api}/stub/v1/ping", timeout=TIMEOUT, allow_redirects=False)
        if response.status_code == 200 and response.json() == {
            "service": "platform-stub",
            "environment": "dev",
            "status": "ok",
        }:
            return Result("dev-stub-mapping", PASSED)
        return Result("dev-stub-mapping", FAILED, f"status {response.status_code}")


def aws_client(name: str) -> Any:
    """A bounded boto3 client from the operator's own session (real runs only)."""
    factory: Callable[..., Any] = boto3.client
    return factory(name, config=SDK_CONFIG)


def classify_tls_error(error: ssl.SSLError) -> str:
    """Only an alert sent by the server proves refusal; a local limitation proves nothing."""
    reason = str(getattr(error, "reason", "") or "")
    return "refused-by-server" if reason.startswith(("TLSV1_ALERT", "SSLV3_ALERT")) else "unknown"


def probe_tls(host: str, version: ssl.TLSVersion) -> str:
    """Attempt one handshake pinned to `version`; report accepted, refused-by-server or unknown."""
    context = ssl.create_default_context()
    try:
        context.minimum_version = context.maximum_version = version
        if version < ssl.TLSVersion.TLSv1_2:
            context.set_ciphers("DEFAULT:@SECLEVEL=0")
    except (ValueError, ssl.SSLError):
        return "unknown"
    try:
        with (
            socket.create_connection((host, 443), timeout=5) as raw,
            context.wrap_socket(raw, server_hostname=host),
        ):
            return "accepted"
    except ssl.SSLError as error:
        return classify_tls_error(error)
    except OSError:
        return "unknown"


def main(argv: list[str] | None = None, clients: Callable[[str], Any] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--environment", required=True, choices=ENVIRONMENTS)
    parser.add_argument("--expected-account", required=True)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--fixture-secret-arn")
    parser.add_argument("--execute", action="store_true", help="contact the environment")
    args = parser.parse_args(argv)
    if not args.execute:
        print("Planned checks: " + ", ".join(planned_checks(args.environment)))
        print("Not executed: pass --execute to contact the environment.")
        return 2
    try:
        outputs = json.loads(args.outputs.read_text(encoding="utf-8"))
        smoke = PlatformSmoke(
            environment=args.environment,
            account=args.expected_account,
            outputs=outputs,
            clients=clients or aws_client,
            http=requests,
            tls_probe=probe_tls,
            fixture_secret_arn=args.fixture_secret_arn,
        )
        results = smoke.run()
    except ScopeError as error:
        print(f"Refused before any check: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, BotoCoreError, ClientError):
        print("Refused before any check: outputs or caller identity unavailable", file=sys.stderr)
        return 1
    for result in results:
        print(f"{result.name}: {result.outcome}" + (f" ({result.detail})" if result.detail else ""))
    return 0 if all(result.outcome == PASSED for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
