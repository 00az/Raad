"""Offline tests of the C3 P1-P13 capability checklist: no fake pass, scoped, booleans only."""

from __future__ import annotations

import importlib.util
import json
import sys
from typing import Any
from unittest.mock import Mock

import pytest
from conftest import REPOSITORY, load_contract

from raad_platform import configuration

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
