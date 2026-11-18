"""Offline tests of the C3 P1-P13 capability checklist: no fake pass, scoped, booleans only."""

from __future__ import annotations

import importlib.util
import json
import sys
from typing import Any
from unittest.mock import Mock

import pytest
from botocore import UNSIGNED
from botocore.exceptions import ClientError, EndpointConnectionError
from botocore.stub import ANY, Stubber
from conftest import REPOSITORY, load_contract

from raad_platform import configuration, stacks

SPEC = importlib.util.spec_from_file_location(
    "check_identity_capabilities", REPOSITORY / "scripts/check_identity_capabilities.py"
)
assert SPEC and SPEC.loader
capabilities = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = capabilities  # dataclasses resolve their module
SPEC.loader.exec_module(capabilities)

ACCOUNT = "111111111111"
POOL = "us-east-1_Synthetic1"
CLIENT = "syntheticclient1"


def outputs() -> dict[str, Any]:
    verifier = configuration.verifier_config("dev", "us-east-1", POOL, CLIENT)
    return {
        "RaadIdentity-dev": {
            "EnvironmentOutput": "dev",
            "UserPoolIdOutput": POOL,
            "UserPoolClientIdOutput": CLIENT,
            "EventBusArnOutput": f"arn:aws:events:us-east-1:{ACCOUNT}:event-bus/raad-dev-identity-events",
        },
        "RaadPublicEdge-dev": {
            "EnvironmentOutput": "dev",
            "PublicApiUrlOutput": "https://dev.api.example.test",
            "VerifierConfigOutput": json.dumps(verifier),
            "HttpApiEndpointOutput": "https://abc123defg.execute-api.us-east-1.amazonaws.com",
        },
    }


def evidence(checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"environment": "dev", "account": ACCOUNT, "checks": checks}


def all_true() -> dict[str, dict[str, bool]]:
    return {
        check: dict.fromkeys(fields, True)
        for check, fields in capabilities.REQUIRED_EVIDENCE.items()
    }


def provider(symbols: bool = False, account: str = ACCOUNT) -> Any:
    made = {
        "sts": Mock(get_caller_identity=Mock(return_value={"Account": account})),
        "cognito-idp": Mock(
            describe_user_pool=Mock(
                return_value={
                    "UserPool": {
                        "Policies": {
                            "PasswordPolicy": {
                                "MinimumLength": 8,
                                "RequireLowercase": True,
                                "RequireUppercase": True,
                                "RequireNumbers": True,
                                "RequireSymbols": symbols,
                            }
                        },
                        "SchemaAttributes": [
                            {"Name": "email", "Required": True},
                            {"Name": "name", "Required": True},
                            {"Name": "sub", "Required": False},
                        ],
                    }
                }
            ),
            describe_user_pool_client=Mock(
                return_value={
                    "UserPoolClient": {
                        "PreventUserExistenceErrors": "ENABLED",
                        "AccessTokenValidity": 60,
                        "RefreshTokenValidity": 43200,
                        "TokenValidityUnits": {"AccessToken": "minutes", "RefreshToken": "minutes"},
                    }
                }
            ),
        ),
        "wafv2": Mock(
            get_web_acl_for_resource=Mock(return_value={"WebACL": {"Name": "raad-dev-identity"}})
        ),
    }
    return (lambda name: made[name]), made


def jwks() -> Any:
    keys = {"keys": [{"kty": "RSA", "alg": "RS256", "kid": "k1"}]}
    return Mock(get=Mock(return_value=Mock(status_code=200, json=Mock(return_value=keys))))


def probe(**overrides: Any) -> dict[str, dict[str, bool]]:
    factory, _ = provider(**overrides)
    result: dict[str, dict[str, bool]] = capabilities.probe_settings(
        outputs(), environment="dev", account=ACCOUNT, clients=factory, http=jwks()
    )
    return result


def by_check(results: list[Any]) -> dict[str, Any]:
    return {result.check: result for result in results}


def test_checklist_is_exactly_the_canonical_c3_capability_checks() -> None:
    contract = load_contract("c3-sign-in-client-profile-v1.yaml")["capability_checks"]
    assert list(capabilities.REQUIRED_EVIDENCE) == [check["id"] for check in contract]
    assert all(capabilities.REQUIRED_EVIDENCE.values())


def test_nothing_recorded_means_every_check_is_pending_never_passed() -> None:
    results = capabilities.evaluate({})
    assert {result.outcome for result in results} == {"pending"}


def test_p7_needs_both_codes_and_the_generic_acknowledgement() -> None:
    partial = {"P7": {"secondCodeAccepted": True}}
    assert by_check(capabilities.evaluate(partial))["P7"].outcome == "pending"
    stale = {
        "P7": {
            "firstCodeRefusedAfterResend": False,
            "secondCodeAccepted": True,
            "resendAcknowledgementSameForUnknownAndConfirmed": True,
        }
    }
    result = by_check(capabilities.evaluate(stale))["P7"]
    assert (result.outcome, result.failed) == ("failed", ("firstCodeRefusedAfterResend",))
    complete = {"P7": dict.fromkeys(capabilities.REQUIRED_EVIDENCE["P7"], True)}
    assert by_check(capabilities.evaluate(complete))["P7"].outcome == "passed"


@pytest.mark.parametrize(
    "document",
    [
        evidence({"P7": {"firstCodeRefusedAfterResend": "123456"}}),
        evidence({"P1": {"accessToken": True}}),
        evidence({"P99": {}}),
        {"environment": "stg", "account": ACCOUNT, "checks": {}},
        {"environment": "dev", "account": "222222222222", "checks": {}},
        {**evidence({}), "notes": "free text"},
    ],
)
def test_evidence_accepts_only_known_boolean_fields_for_this_scope(document) -> None:
    with pytest.raises(capabilities.ScopeError):
        capabilities.load_evidence(document, environment="dev", account=ACCOUNT)


def test_settings_probes_record_only_what_settings_can_show() -> None:
    probed = probe()
    assert probed["P4"] == {"passwordPolicyMatchesA4": True}
    assert probed["P9"] == {"accessTokenSixtyMinutes": True, "refreshTokenThirtyDays": True}
    assert probed["P10"] == {"firewallAssociatedWithPool": True}
    assert probed["P13"] == {"jwksAnswersOverHttps": True}
    results = by_check(capabilities.evaluate(probed))
    # Settings alone never complete a check that needs a live scenario.
    assert {r.outcome for r in results.values()} == {"pending"}
    assert "P7" not in probed


def test_a_strengthened_password_policy_fails_p4_even_with_recorded_samples() -> None:
    recorded = {"P4": {"a4SamplesGiveA4Results": True, "passwordPolicyMatchesA4": True}}
    merged = capabilities.merge(recorded, probe(symbols=True))
    assert by_check(capabilities.evaluate(merged))["P4"].outcome == "failed"


def test_probes_refuse_a_different_caller_account_before_reading_settings() -> None:
    factory, made = provider(account="222222222222")
    with pytest.raises(capabilities.ScopeError):
        capabilities.probe_settings(
            outputs(), environment="dev", account=ACCOUNT, clients=factory, http=jwks()
        )
    made["cognito-idp"].describe_user_pool.assert_not_called()


def test_command_line_passes_only_when_every_check_has_full_evidence(tmp_path, capsys) -> None:
    source = tmp_path / "outputs.json"
    source.write_text(json.dumps(outputs()))
    recorded = tmp_path / "evidence.json"
    base = ["--environment", "dev", "--expected-account", ACCOUNT, "--outputs", str(source)]
    recorded.write_text(json.dumps(evidence({"P7": {"secondCodeAccepted": True}})))
    assert capabilities.main([*base, "--evidence", str(recorded)]) == 1
    text = capsys.readouterr().out
    assert "P7: pending (missing: firstCodeRefusedAfterResend" in text
    assert "Settings probes not run" in text
    recorded.write_text(json.dumps(evidence(all_true())))
    assert capabilities.main([*base, "--evidence", str(recorded)]) == 0
    assert capabilities.main([*base, "--evidence", str(tmp_path / "absent.json")]) == 1


def test_command_line_probes_only_with_execute_and_prints_no_identifiers(
    tmp_path, capsys, monkeypatch
) -> None:
    source = tmp_path / "outputs.json"
    source.write_text(json.dumps(outputs()))
    monkeypatch.setattr(capabilities, "requests", Mock(get=jwks().get, RequestException=Exception))
    factory, made = provider()
    arguments = ["--environment", "dev", "--expected-account", ACCOUNT, "--outputs", str(source)]
    assert capabilities.main([*arguments, "--execute"], clients=factory) == 1
    printed = capsys.readouterr().out
    assert "P4: pending (missing: a4SamplesGiveA4Results)" in printed
    assert POOL not in printed and CLIENT not in printed
    made["sts"].get_caller_identity.assert_called_once()
    wrong, _ = provider(account="222222222222")
    assert capabilities.main([*arguments, "--execute"], clients=wrong) == 1
    assert "Refused" in capsys.readouterr().err


# --- P10 burst (review R-01): injected client and clock, so no AWS call and no real waiting. ---

BODY_MARKER = "SYNTHETIC-PROVIDER-BODY-7f3a"


class Pace:
    """Injected monotonic clock: sleeping and each provider answer move it forward."""

    def __init__(self, latency: float = 0.05) -> None:
        self.now = 500.0
        self.latency = latency
        self.slept: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


class Pool:
    """Public InitiateAuth that answers from a script, then admits every further request."""

    def __init__(self, pace: Pace, script: list[Any] | None = None) -> None:
        self.pace = pace
        self.script = list(script or [])
        self.calls: list[dict[str, Any]] = []
        self.sent_at: list[float] = []

    def initiate_auth(self, **request: Any) -> dict[str, Any]:
        self.calls.append(request)
        self.sent_at.append(self.pace.now)
        self.pace.now += self.pace.latency
        answer = self.script.pop(0) if self.script else None
        if isinstance(answer, Exception):
            raise answer
        return {"ChallengeName": "PASSWORD_VERIFIER", "ChallengeParameters": {"SALT": "ab"}}


def provider_error(code: str, status: int = 400) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": f"{code} {BODY_MARKER}"},
            "ResponseMetadata": {"HTTPStatusCode": status},
        },
        "InitiateAuth",
    )


def burst(script: list[Any] | None = None, latency: float = 0.05) -> tuple[Any, Pool, Pace]:
    pace = Pace(latency)
    pool = Pool(pace, script)
    runtime = capabilities.BurstRuntime(pool, clock=pace.clock, sleep=pace.sleep)
    return runtime, pool, pace


def run_cli(
    tmp_path: Any,
    monkeypatch: Any,
    *,
    environment: str = "dev",
    account: str = ACCOUNT,
    script: list[Any] | None = None,
    recorded: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, Pool, dict[str, Any]]:
    source = tmp_path / "outputs.json"
    source.write_text(json.dumps(outputs()))
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(json.dumps({**evidence(recorded or {}), "environment": environment}))
    monkeypatch.setattr(capabilities, "requests", Mock(get=jwks().get, RequestException=Exception))
    factory, made = provider(account=account)
    runtime, pool, _ = burst(script)
    arguments = ["--environment", environment, "--expected-account", ACCOUNT]
    arguments += ["--outputs", str(source), "--evidence", str(evidence_file)]
    code = capabilities.main([*arguments, "--execute", "--burst"], clients=factory, burst=runtime)
    return code, pool, made


def refusal_after(admitted: int) -> list[Any]:
    return [None] * admitted + [provider_error("ForbiddenException", 403)]


def test_burst_settings_mirror_the_regional_firewall_rules() -> None:
    assert (
        capabilities.ACCOUNT_OPERATION_LIMIT,
        capabilities.GENERAL_OPERATION_LIMIT,
        capabilities.OPERATION_WINDOW_SECONDS,
    ) == (
        stacks.ACCOUNT_OPERATION_LIMIT,
        stacks.GENERAL_OPERATION_LIMIT,
        stacks.OPERATION_WINDOW_SECONDS,
    )
    # Above the account limit, below the general one: only the account rule can refuse it.
    assert stacks.ACCOUNT_OPERATION_LIMIT < capabilities.BURST_BUDGET
    assert capabilities.BURST_BUDGET < stacks.GENERAL_OPERATION_LIMIT
    attempts = capabilities.BURST_BUDGET + capabilities.UNCOUNTED_LIMIT
    assert attempts * capabilities.BURST_INTERVAL_SECONDS < stacks.OPERATION_WINDOW_SECONDS


def test_srp_a_is_a_well_formed_public_value_in_the_cognito_group() -> None:
    prime = capabilities.SRP_N
    assert prime.bit_length() == 3072 and pow(2, prime - 1, prime) == 1
    values = {capabilities.srp_a() for _ in range(3)}
    assert len(values) == 3
    for value in values:
        assert value == value.lower() and 1 < int(value, 16) < prime


def test_a_waf_refusal_completes_p10_with_the_operators_second_caller(
    tmp_path, monkeypatch, capsys
) -> None:
    recorded = {"P10": {"secondCallerUnaffected": True}}
    code, pool, _ = run_cli(tmp_path, monkeypatch, script=refusal_after(120), recorded=recorded)
    printed = capsys.readouterr().out
    assert code == 1  # Other checks are still pending; P10 itself is complete.
    assert "P10 burst: WAF refusal observed (120 admitted, 0 uncounted)" in printed
    assert "P10: passed" in printed
    assert len(pool.calls) == 121  # Stops at the first refusal.
    request = pool.calls[0]
    assert (request["ClientId"], request["AuthFlow"]) == (CLIENT, "USER_SRP_AUTH")
    assert set(request["AuthParameters"]) == {"USERNAME", "SRP_A"}
    assert request["AuthParameters"]["USERNAME"].endswith("@example.invalid")


def test_spending_the_budget_without_a_refusal_fails_p10() -> None:
    runtime, pool, pace = burst()
    outcome = capabilities.run_burst(CLIENT, runtime)
    assert (outcome.admitted, outcome.refused, outcome.conclusive) == (
        capabilities.BURST_BUDGET,
        False,
        True,
    )
    assert len(pool.calls) == capabilities.BURST_BUDGET
    # Paced, and every request inside one evaluation window, so all of them still count.
    assert pace.slept and max(pace.slept) <= capabilities.BURST_INTERVAL_SECONDS
    assert pool.sent_at[-1] - pool.sent_at[0] < capabilities.OPERATION_WINDOW_SECONDS
    merged = capabilities.merge({"P10": {"secondCallerUnaffected": True}}, outcome.evidence())
    result = by_check(capabilities.evaluate(merged))["P10"]
    assert result.outcome == "failed"
    assert set(result.failed) == {"operationClassificationObserved", "burstRefusedForOneCaller"}


@pytest.mark.parametrize(
    "error",
    [
        provider_error("TooManyRequestsException"),
        provider_error("InternalErrorException", 500),
        provider_error("InvalidParameterException"),
        provider_error("AccessDeniedException", 403),  # A 403 is not a WAF refusal by itself.
        EndpointConnectionError(endpoint_url="https://cognito-idp.us-east-1.amazonaws.com/"),
    ],
)
def test_non_waf_errors_are_neither_a_refusal_nor_an_admission(error: Exception) -> None:
    runtime, pool, _ = burst([error] * capabilities.UNCOUNTED_LIMIT)
    outcome = capabilities.run_burst(CLIENT, runtime)
    assert (outcome.admitted, outcome.uncounted) == (0, capabilities.UNCOUNTED_LIMIT)
    assert (outcome.refused, outcome.conclusive, outcome.evidence()) == (False, False, {})
    assert len(pool.calls) == capabilities.UNCOUNTED_LIMIT
    assert "inconclusive" in outcome.describe()
    # Interleaved with admissions, they still do not count toward the budget.
    runtime, pool, _ = burst([None, error, None, error])
    outcome = capabilities.run_burst(CLIENT, runtime)
    assert (outcome.admitted, outcome.uncounted) == (capabilities.BURST_BUDGET, 2)
    assert len(pool.calls) == capabilities.BURST_BUDGET + 2


def test_the_waf_refusal_is_matched_by_error_code_not_http_status() -> None:
    # AWS gives ForbiddenException as HTTP 400 in the API reference and 403 in the guide.
    runtime, _, _ = burst([provider_error("ForbiddenException", 400)])
    outcome = capabilities.run_burst(CLIENT, runtime)
    assert (outcome.admitted, outcome.refused) == (0, True)
    assert outcome.evidence() == {
        "P10": {"operationClassificationObserved": True, "burstRefusedForOneCaller": True}
    }
    for code in ("NotAuthorizedException", "UserNotFoundException"):
        runtime, _, _ = burst([provider_error(code), *refusal_after(0)])
        assert capabilities.run_burst(CLIENT, runtime).admitted == 1


def test_a_burst_that_slips_out_of_one_window_is_inconclusive() -> None:
    runtime, pool, _ = burst(latency=2.5)  # Slower than the pacing interval.
    outcome = capabilities.run_burst(CLIENT, runtime)
    assert (outcome.refused, outcome.conclusive, outcome.evidence()) == (False, False, {})
    assert outcome.admitted < capabilities.BURST_BUDGET
    assert pool.sent_at[-1] - pool.sent_at[0] < capabilities.OPERATION_WINDOW_SECONDS


def test_the_burst_is_refused_for_prd_before_any_request(tmp_path, monkeypatch, capsys) -> None:
    code, pool, made = run_cli(tmp_path, monkeypatch, environment="prd")
    assert code == 1
    assert "Refused: the P10 burst never runs against prd" in capsys.readouterr().err
    assert pool.calls == []
    made["sts"].get_caller_identity.assert_not_called()


@pytest.mark.parametrize(
    "scope", [{"account": "222222222222"}, {"environment": "stg"}], ids=["account", "outputs"]
)
def test_a_scope_mismatch_is_refused_before_any_burst_request(
    tmp_path, monkeypatch, capsys, scope
) -> None:
    code, pool, made = run_cli(tmp_path, monkeypatch, **scope)
    assert code == 1
    assert "Refused" in capsys.readouterr().err
    assert pool.calls == []
    made["cognito-idp"].describe_user_pool.assert_not_called()


def test_the_burst_needs_execute_and_makes_no_request(tmp_path) -> None:
    runtime, pool, _ = burst()
    arguments = ["--environment", "dev", "--expected-account", ACCOUNT]
    with pytest.raises(SystemExit):
        capabilities.main([*arguments, "--outputs", str(tmp_path), "--burst"], burst=runtime)
    assert pool.calls == []


def test_burst_output_holds_no_address_identifier_or_provider_text(
    tmp_path, monkeypatch, capsys
) -> None:
    code, pool, _ = run_cli(tmp_path, monkeypatch, script=refusal_after(3))
    captured = capsys.readouterr()
    printed = captured.out + captured.err
    assert code == 1 and "P10 burst: WAF refusal observed (3 admitted, 0 uncounted)" in printed
    parameters = pool.calls[0]["AuthParameters"]
    for secret_value in (parameters["USERNAME"], parameters["SRP_A"], POOL, CLIENT, BODY_MARKER):
        assert secret_value not in printed
    assert "@" not in printed


def test_the_public_client_sends_a_model_valid_unsigned_single_attempt_request() -> None:
    client = capabilities.public_cognito_client()
    assert client.meta.region_name == "us-east-1"
    assert client.meta.config.signature_version is UNSIGNED
    assert client.meta.config.retries["total_max_attempts"] == 1
    expected = {
        "ClientId": CLIENT,
        "AuthFlow": "USER_SRP_AUTH",
        "AuthParameters": {"USERNAME": ANY, "SRP_A": ANY},
    }
    challenge = {
        "ChallengeName": "PASSWORD_VERIFIER",
        "ChallengeParameters": {"SALT": "ab", "SRP_B": "cd", "SECRET_BLOCK": "ef"},
    }
    pace = Pace()
    with Stubber(client) as stubber:
        stubber.add_response("initiate_auth", challenge, expected)
        stubber.add_client_error("initiate_auth", "ForbiddenException", http_status_code=403)
        runtime = capabilities.BurstRuntime(client, clock=pace.clock, sleep=pace.sleep)
        outcome = capabilities.run_burst(CLIENT, runtime)
        stubber.assert_no_pending_responses()
    assert (outcome.admitted, outcome.refused) == (1, True)
