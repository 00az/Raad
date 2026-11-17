"""Canonical C2-C5 contract files: schema validity, closed outputs and consumer compatibility."""

from __future__ import annotations

import copy
import re
import uuid
from typing import Any

import pytest
from conftest import load_contract
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

C2 = "c2-identity-events-v1.asyncapi.yaml"
C3 = "c3-sign-in-client-profile-v1.yaml"
C4 = "c4-mobile-environment-config-v1.schema.yaml"
C5 = "c5-money-edge-v1.yaml"

# The exact representation U2's TokenVerifier.from_environment requires (RaadMoneyService
# src/raad_money/identity.py, branch aidlc/u2-money-service at 2b3660b): it refuses any other set.
U2_VERIFIER_KEYS = {
    "configVersion",
    "environment",
    "issuer",
    "audience",
    "audienceClaim",
    "tokenTypeMarker",
    "jwksUri",
    "acceptedAlgorithms",
    "profileAttributeSource",
    "userProfileUri",
}
# The shape RaadMobile's dev build compares against (scripts/run_mobile_dev.py expected_config).
MOBILE_C4_KEYS = {
    "configVersion",
    "environment",
    "apiBaseUrl",
    "moneyBasePath",
    "authIssuer",
    "authClientId",
    "authAudience",
}
# C1 Error.code enum (RaadMoneyService openapi/raad-money-v1.yaml, components.schemas.Error).
C1_ERROR_CODES = {
    "VALIDATION_ERROR",
    "AUTHENTICATION_REQUIRED",
    "FORBIDDEN",
    "WALLET_NOT_FOUND",
    "RECIPIENT_NOT_FOUND",
    "SELF_TRANSFER",
    "AMOUNT_OUT_OF_RANGE",
    "INSUFFICIENT_FUNDS",
    "IDEMPOTENCY_KEY_REUSED",
    "CURSOR_INVALID_OR_EXPIRED",
    "RATE_LIMITED",
    "INTERNAL_ERROR",
    "SERVICE_UNAVAILABLE",
    "TOKEN_VERIFIER_UNAVAILABLE",
}
DESIGN_CORRELATION = re.compile(r"^[A-Za-z0-9._~-]{1,128}$")
U2_CORRELATION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
POOL = "us-east-1_Synthetic1"
ISSUER = f"https://cognito-idp.us-east-1.amazonaws.com/{POOL}"


def validator(schema: dict[str, Any]) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def c2_schema() -> dict[str, Any]:
    schema: dict[str, Any] = load_contract(C2)["components"]["schemas"]["UserConfirmedPayload"]
    return schema


def c4_schema() -> dict[str, Any]:
    schema: dict[str, Any] = load_contract(C4)["schema"]
    return schema


def c5_verifier_schema() -> dict[str, Any]:
    schema: dict[str, Any] = load_contract(C5)["token_verification"]["configuration"]["schema"]
    return schema


def c2_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "specVersion": "1.0",
        "eventId": str(uuid.uuid4()),
        "occurredAt": "2026-11-17T10:00:00.000+00:00",
        "environment": "dev",
        "userId": "4f3c2b1a-0000-4000-8000-000000000001",
        "email": "synthetic.user@example.test",
        "displayName": "Synthetic User",
    }
    payload.update(overrides)
    return payload


def c4_config(**overrides: Any) -> dict[str, Any]:
    config = {
        "configVersion": "1.0",
        "environment": "dev",
        "apiBaseUrl": "https://dev.api.example.test",
        "moneyBasePath": "/money/v1",
        "authIssuer": ISSUER,
        "authAudience": "syntheticclient1",
        "authClientId": "syntheticclient1",
    }
    config.update(overrides)
    return config


def verifier(**overrides: Any) -> dict[str, Any]:
    config: dict[str, Any] = {
        "configVersion": "1.0",
        "environment": "dev",
        "issuer": ISSUER,
        "audience": "syntheticclient1",
        "audienceClaim": "client_id",
        "tokenTypeMarker": {"location": "claim", "name": "token_use", "expectedValue": "access"},
        "jwksUri": ISSUER + "/.well-known/jwks.json",
        "acceptedAlgorithms": ["RS256"],
        "profileAttributeSource": "user-profile-endpoint",
        "userProfileUri": "https://cognito-idp.us-east-1.amazonaws.com/",
    }
    config.update(overrides)
    return config


def test_every_canonical_file_names_its_owner_version_and_pre_release_state() -> None:
    assert load_contract(C2)["info"]["version"] == "1.0.0-rc.1"
    for name, owner_key in ((C3, "contract"), (C4, "shared-schema"), (C5, "contract")):
        document = load_contract(name)
        assert document[owner_key]
        assert document["owner"] == "u4-platform"
        assert re.fullmatch(r"1\.0\.0-rc\.[0-9]+", document["version"])


def test_c2_routing_is_unchanged_for_the_u2_rule() -> None:
    channel = load_contract(C2)["channels"]["userConfirmedV1"]
    assert channel["address"] == "raad.identity.user-confirmed.v1"
    assert channel["x-eventbridge"] == {
        "source": "raad.identity",
        "detail-type": "raad.identity.user-confirmed.v1",
        "payload-location": "detail",
    }


def test_c2_declares_exactly_the_seven_provider_fields_and_tolerates_unknown_ones() -> None:
    schema = c2_schema()
    assert set(schema["properties"]) == set(schema["required"])
    assert len(schema["required"]) == 7
    # Consumers ignore additive fields; U4's emission test separately refuses undeclared ones.
    assert schema["additionalProperties"] is True
    validator(schema).validate(c2_payload(laterMinorField="ignored"))


@pytest.mark.parametrize(
    "change",
    [
        {"environment": "qa"},
        {"specVersion": "2.0"},
        {"eventId": "not-a-uuid"},
        {"userId": ""},
        {"displayName": "x" * 201},
        {"email": "x" * 250 + "@example.test"},
    ],
)
def test_c2_schema_refuses_invalid_payload_values(change: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        validator(c2_schema()).validate(c2_payload(**change))


def test_c2_schema_refuses_a_missing_required_field() -> None:
    payload = c2_payload()
    del payload["displayName"]
    with pytest.raises(ValidationError):
        validator(c2_schema()).validate(payload)


def test_c3_password_rule_and_examples_match_a4_without_a_symbol_requirement() -> None:
    rule = load_contract(C3)["password_rule"]
    assert rule["minimum_characters"] == 8
    assert rule["requires_symbol"] is False

    def meets(password: str) -> bool:
        return (
            len(password) >= rule["minimum_characters"]
            and any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        )

    assert all(meets(p) for p in rule["examples"]["accepted"])
    assert not any(meets(p) for p in rule["examples"]["refused"])
    assert rule["examples"]["accepted"] == ["Abcdef12"]


def test_c3_session_privacy_and_capability_checklist_are_complete() -> None:
    profile = load_contract(C3)
    session = profile["operations"]["refreshSession"]["session_policy"]
    assert session["access_token_lifetime_minutes"] == 60
    assert session["refresh_allowed_until_idle_days"] == 30
    assert profile["stored_user_attributes"] == ["email", "displayName"]
    assert profile["email_normalization"]["mutable_after_signup"] == {
        "email": False,
        "displayName": False,
    }
    assert {"password", "confirmationCode", "accessToken", "refreshToken", "email"} <= set(
        profile["privacy"]["never_log"]
    )
    assert [check["id"] for check in profile["capability_checks"]] == [
        f"P{n}" for n in range(1, 14)
    ]
    assert all(check["acceptance"] and check["fallback"] for check in profile["capability_checks"])


def test_c4_schema_is_closed_and_matches_the_existing_mobile_shape() -> None:
    schema = c4_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"]) == MOBILE_C4_KEYS
    validator(schema).validate(c4_config())
    secret_words = ("secret", "password", "token", "privatekey", "clientsecret")
    assert not any(word in key.lower() for key in schema["properties"] for word in secret_words)


@pytest.mark.parametrize(
    "change",
    [
        {"configVersion": "2.0"},
        {"environment": "production"},
        {"apiBaseUrl": "http://dev.api.example.test"},
        {"moneyBasePath": "/money/v2"},
        {"authClientId": ""},
        {"clientSecret": "never"},
    ],
)
def test_c4_schema_refuses_missing_extra_or_invalid_values(change: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        validator(c4_schema()).validate(c4_config(**change))
    missing = c4_config()
    del missing["authIssuer"]
    with pytest.raises(ValidationError):
        validator(c4_schema()).validate(missing)


def test_c5_verifier_schema_accepts_the_exact_representation_u2_loads() -> None:
    schema = c5_verifier_schema()
    assert set(schema["properties"]) == U2_VERIFIER_KEYS
    validator(schema).validate(verifier())


@pytest.mark.parametrize(
    "change",
    [
        {"acceptedAlgorithms": ["HS256"]},
        {"acceptedAlgorithms": ["RS256", "RS512"]},
        {"audienceClaim": "azp"},
        {"issuer": "http://cognito-idp.us-east-1.amazonaws.com/x"},
        {"tokenTypeMarker": {"location": "claim", "name": "token_use"}},
        {"privateKey": "never"},
        {"profileAttributeSource": "access-token-claims"},
    ],
)
def test_c5_verifier_schema_refuses_unsafe_or_inconsistent_configuration(
    change: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError):
        validator(c5_verifier_schema()).validate(verifier(**change))


def test_c5_profile_uri_is_required_exactly_for_the_user_profile_source() -> None:
    missing = verifier()
    del missing["userProfileUri"]
    with pytest.raises(ValidationError):
        validator(c5_verifier_schema()).validate(missing)
    claims_only = verifier(profileAttributeSource="access-token-claims")
    del claims_only["userProfileUri"]
    validator(c5_verifier_schema()).validate(claims_only)


# Generated with fullmatch semantics, as the edge and U2 both apply the pattern with fullmatch.
@given(
    st.from_regex(
        load_contract(C5)["forwarding"]["correlation_id"]["accepted_pattern"], fullmatch=True
    )
)
def test_c5_correlation_pattern_only_preserves_values_both_design_and_u2_accept(
    value: str,
) -> None:
    assert DESIGN_CORRELATION.fullmatch(value)
    assert U2_CORRELATION.fullmatch(value)


@pytest.mark.parametrize(
    "value,kept", [(uuid.uuid4().hex, True), ("~abc", False), ("a:b", False), ("-x", False)]
)
def test_c5_correlation_pattern_examples(value: str, kept: bool) -> None:
    pattern = load_contract(C5)["forwarding"]["correlation_id"]["accepted_pattern"]
    assert bool(re.fullmatch(pattern, value)) is kept


def test_c5_envelope_schema_matches_the_transport_u2_parses() -> None:
    schema = load_contract(C5)["transport"]["edge_to_money_api"]["envelope"]
    envelope = {
        "version": 1,
        "request": {
            "method": "POST",
            "path": "/money/v1/transfers",
            "query": "",
            "headers": {"authorization": "Bearer synthetic", "x-correlation-id": "abc"},
            "body": "{}",
        },
    }
    validator(schema).validate(envelope)
    spoofed = copy.deepcopy(envelope)
    spoofed["request"]["headers"]["x-user-id"] = "spoofed"
    with pytest.raises(ValidationError):
        validator(schema).validate(spoofed)
    outside = copy.deepcopy(envelope)
    outside["request"]["path"] = "/money/v2/transfers"
    with pytest.raises(ValidationError):
        validator(schema).validate(outside)


def test_c5_edge_errors_use_c1_codes_and_flat_error_fields() -> None:
    contract = load_contract(C5)
    codes = {mapping["code"] for mapping in contract["edge_errors"]["mappings"].values()}
    assert codes <= C1_ERROR_CODES
    assert contract["edge_errors"]["body_fields"] == ["code", "message", "correlationId"]
    assert contract["edge_errors"]["mappings"]["rate_limit"]["requiredHeader"] == "Retry-After"
    # An unmatched route is answered outside C1 and is never forwarded.
    assert contract["failure_behavior"]["no_matching_route"]["httpStatus"] == 404
    assert contract["failure_behavior"]["no_matching_route"]["code"] not in C1_ERROR_CODES


def test_c5_rate_limits_charge_a_transfer_against_the_lookup_budget() -> None:
    counters = load_contract(C5)["rate_limits"]["counters"]
    assert counters["recipient_lookup"]["limit_per_window"] == 30
    assert counters["transfer"]["limit_per_window"] == 10
    assert counters["transfer"]["also_consumes"] == ["recipient_lookup"]
    assert counters["other"]["limit_per_window"] == 60
