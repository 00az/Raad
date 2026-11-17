"""Offline tests of the platform smoke tool: scope first, injected dependencies, no leaks."""

from __future__ import annotations

import importlib.util
import json
import ssl
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from conftest import REPOSITORY

from raad_platform import configuration

SPEC = importlib.util.spec_from_file_location(
    "platform_smoke", REPOSITORY / "scripts/platform_smoke.py"
)
assert SPEC and SPEC.loader
smoke = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = smoke  # dataclasses resolve their module
SPEC.loader.exec_module(smoke)

ACCOUNT = "111111111111"
POOL = "us-east-1_Synthetic1"
CLIENT = "syntheticclient1"
API = "https://dev.api.example.test"
ENDPOINT = "https://abc123defg.execute-api.us-east-1.amazonaws.com"
TOKEN = "eyJsynthetic.access.tokenvalue"
PASSWORD = "Synthetic-Password-1"
EMAIL = "smoke.fixture@example.test"
SECRET_ARN = "arn:aws:secretsmanager:us-east-1:111111111111:secret:raad/dev/smoke-fixture"


def outputs(environment: str = "dev") -> dict[str, Any]:
    verifier = configuration.verifier_config(environment, "us-east-1", POOL, CLIENT)
    return {
        f"RaadIdentity-{environment}": {
            "EnvironmentOutput": environment,
            "UserPoolIdOutput": POOL,
            "UserPoolClientIdOutput": CLIENT,
            "EventBusArnOutput": f"arn:aws:events:us-east-1:{ACCOUNT}:event-bus/raad-{environment}-identity-events",
        },
        f"RaadPublicEdge-{environment}": {
            "EnvironmentOutput": environment,
            "PublicApiUrlOutput": f"https://{environment}.api.example.test",
            "VerifierConfigOutput": json.dumps(verifier),
            "HttpApiEndpointOutput": ENDPOINT,
        },
    }


def response(status: int, body: Any, headers: dict[str, str] | None = None) -> Mock:
    return Mock(status_code=status, headers=headers or {}, json=Mock(return_value=body))


class Http:
    """Answers like a healthy deployed dev platform unless a route is overridden."""

    def __init__(self, **overrides: Any) -> None:
        self.overrides = overrides
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, headers: dict[str, str] | None = None, **_: Any) -> Mock:
        headers = headers or {}
        self.calls.append((url, headers))
        if url in self.overrides:
            return self.overrides[url]
        if url == f"{API}/money/v1/wallet" and "Authorization" not in headers:
            correlation = headers["X-Correlation-Id"]
            return response(
                401,
                {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Sign in.",
                    "correlationId": correlation,
                },
                {"x-correlation-id": correlation},
            )
        if url == f"{API}/money/v1/wallet":
            return response(404, {"code": "WALLET_NOT_FOUND", "message": "x", "correlationId": "c"})
        if url == f"{ENDPOINT}/money/v1/wallet":
            return response(403, {"code": "FORBIDDEN", "message": "x", "correlationId": "c"})
        if url == f"{API}/stub/v1/ping":
            return response(200, {"service": "platform-stub", "environment": "dev", "status": "ok"})
        raise AssertionError(f"unexpected request {url}")


def clients(account: str = ACCOUNT, verifier: dict | None = None) -> tuple[Any, dict[str, Mock]]:
    expected = verifier or configuration.verifier_config("dev", "us-east-1", POOL, CLIENT)
    values = {
        "/raad/dev/verifier": json.dumps(expected),
        "/raad/dev/public-api-url": API,
        "/raad/dev/event-bus/arn": outputs()["RaadIdentity-dev"]["EventBusArnOutput"],
        "/raad/dev/alarm-topic/arn": f"arn:aws:sns:us-east-1:{ACCOUNT}:raad-dev-alerts",
    }
    made = {
        "sts": Mock(get_caller_identity=Mock(return_value={"Account": account})),
        "ssm": Mock(get_parameter=lambda Name: {"Parameter": {"Value": values[Name]}}),
        "secretsmanager": Mock(
            get_secret_value=Mock(
                return_value={"SecretString": json.dumps({"email": EMAIL, "password": PASSWORD})}
            )
        ),
        "cognito-idp": Mock(
            admin_initiate_auth=Mock(return_value={"AuthenticationResult": {"AccessToken": TOKEN}})
        ),
    }
    return (lambda name: made[name]), made


def run(http: Http | None = None, factory: Any = None, **overrides: Any) -> list[Any]:
    settings: dict[str, Any] = {
        "environment": "dev",
        "account": ACCOUNT,
        "outputs": outputs(),
        "clients": factory or clients()[0],
        "http": http or Http(),
        "tls_probe": lambda host, version: (
            "accepted" if version == ssl.TLSVersion.TLSv1_2 else "refused-by-server"
        ),
        "fixture_secret_arn": SECRET_ARN,
        "new_id": lambda: "smoke-correlation-1",
    }
    settings.update(overrides)
    return smoke.PlatformSmoke(**settings).run()


def outcomes(results: list[Any]) -> dict[str, str]:
    return {result.name: result.outcome for result in results}


def test_healthy_dev_environment_passes_every_mandatory_check() -> None:
    http = Http()
    factory, made = clients()
    results = run(http, factory)
    assert outcomes(results) == {
        "anonymous-refused": "passed",
        "direct-origin-refused": "passed",
        "tls-minimum": "passed",
        "outputs-coherent": "passed",
        "fixture-sign-in": "passed",
        "dev-stub-mapping": "passed",
    }
    made["cognito-idp"].admin_initiate_auth.assert_called_once()
    assert made["cognito-idp"].admin_initiate_auth.call_args.kwargs["UserPoolId"] == POOL
    assert ("Authorization", f"Bearer {TOKEN}") in http.calls[-2][1].items()


def test_wrong_caller_account_is_refused_before_any_request() -> None:
    http = Http()
    factory, made = clients(account="222222222222")
    with pytest.raises(smoke.ScopeError, match="account"):
        run(http, factory)
    assert http.calls == []
    made["secretsmanager"].get_secret_value.assert_not_called()


@pytest.mark.parametrize("environment", ["stg", "prd"])
def test_outputs_of_another_environment_are_refused_before_any_aws_call(environment) -> None:
    factory = Mock(side_effect=AssertionError("must not contact AWS"))
    with pytest.raises(smoke.ScopeError):
        run(factory=factory, outputs=outputs(environment))


@pytest.mark.parametrize(
    "url,answer,check",
    [
        (f"{API}/money/v1/wallet", response(200, {}), "anonymous-refused"),
        (f"{ENDPOINT}/money/v1/wallet", response(200, {"ok": True}), "direct-origin-refused"),
        (f"{API}/stub/v1/ping", response(404, {}), "dev-stub-mapping"),
    ],
)
def test_a_wrong_answer_fails_its_check(url, answer, check) -> None:
    if check == "anonymous-refused":
        answer = response(
            401, {"code": "AUTHENTICATION_REQUIRED", "message": "x", "correlationId": "other"}
        )
    assert outcomes(run(Http(**{url: answer})))[check] == "failed"


@pytest.mark.parametrize(
    "old,current,outcome",
    [
        ("refused-by-server", "accepted", "passed"),
        ("accepted", "accepted", "failed"),
        ("unknown", "accepted", "pending"),
        ("refused-by-server", "unknown", "failed"),
    ],
)
def test_tls_minimum_needs_a_server_refusal_of_tls_1_1(old, current, outcome) -> None:
    def probe(_host: str, version: ssl.TLSVersion) -> str:
        return current if version == ssl.TLSVersion.TLSv1_2 else old

    assert outcomes(run(tls_probe=probe))["tls-minimum"] == outcome


def test_only_server_alerts_count_as_tls_refusal() -> None:
    alert = ssl.SSLError()
    alert.reason = "TLSV1_ALERT_PROTOCOL_VERSION"
    local = ssl.SSLError()
    local.reason = "NO_PROTOCOLS_AVAILABLE"
    assert smoke.classify_tls_error(alert) == "refused-by-server"
    assert smoke.classify_tls_error(local) == "unknown"


def test_outputs_must_match_the_published_parameters() -> None:
    other = configuration.verifier_config("dev", "us-east-1", POOL, "otherclient")
    factory, _ = clients(verifier=other)
    assert outcomes(run(factory=factory))["outputs-coherent"] == "failed"


def test_missing_fixture_or_a_challenge_fails_sign_in_instead_of_skipping() -> None:
    assert outcomes(run(fixture_secret_arn=None))["fixture-sign-in"] == "failed"
    factory, made = clients()
    made["cognito-idp"].admin_initiate_auth.return_value = {
        "ChallengeName": "NEW_PASSWORD_REQUIRED"
    }
    assert outcomes(run(factory=factory))["fixture-sign-in"] == "failed"


def test_stg_runs_no_stub_check() -> None:
    assert "dev-stub-mapping" not in smoke.planned_checks("stg")


def test_command_line_does_nothing_without_execute(tmp_path, capsys) -> None:
    source = tmp_path / "outputs.json"
    source.write_text(json.dumps(outputs()))
    factory = Mock(side_effect=AssertionError("must not contact AWS"))
    arguments = ["--environment", "dev", "--expected-account", ACCOUNT, "--outputs", str(source)]
    assert smoke.main(arguments, clients=factory) == 2
    assert "Not executed" in capsys.readouterr().out


def test_command_line_reports_names_and_outcomes_only(tmp_path, capsys, monkeypatch) -> None:
    source = tmp_path / "outputs.json"
    source.write_text(json.dumps(outputs()))
    monkeypatch.setattr(smoke, "requests", Mock(get=Http().get, RequestException=Exception))
    monkeypatch.setattr(
        smoke,
        "probe_tls",
        lambda host, version: "accepted" if version == ssl.TLSVersion.TLSv1_2 else "unknown",
    )
    factory, _ = clients()
    arguments = [
        "--environment",
        "dev",
        "--expected-account",
        ACCOUNT,
        "--outputs",
        str(source),
        "--fixture-secret-arn",
        SECRET_ARN,
        "--execute",
    ]
    assert smoke.main(arguments, clients=factory) == 1  # TLS 1.1 refusal is pending here
    printed = capsys.readouterr()
    text = printed.out + printed.err
    assert "tls-minimum: pending" in text and "fixture-sign-in: passed" in text
    for private in (TOKEN, PASSWORD, EMAIL, SECRET_ARN, POOL):
        assert private not in text
    wrong, _ = clients(account="222222222222")
    assert smoke.main(arguments, clients=wrong) == 1
    assert "Refused before any check" in capsys.readouterr().err


def test_dependency_failure_fails_the_check_without_detail_leakage() -> None:
    factory, made = clients()
    made["secretsmanager"].get_secret_value.side_effect = smoke.ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": SECRET_ARN}}, "GetSecretValue"
    )
    [result] = [r for r in run(factory=factory) if r.name == "fixture-sign-in"]
    assert (result.outcome, result.detail) == ("failed", "dependency unavailable")


def test_bounded_client_settings_for_real_runs(monkeypatch) -> None:
    factory = Mock(return_value="client")
    monkeypatch.setattr(smoke.boto3, "client", factory)
    assert smoke.aws_client("sts") == "client"
    assert factory.call_args.kwargs["config"].retries["total_max_attempts"] == 2
    assert Path(smoke.__file__).name == "platform_smoke.py"
