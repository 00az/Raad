"""C3 provider capability checklist (P1-P13) for one environment.

A check passes only when every piece of its acceptance evidence is present and true; any false
item fails it, and anything missing leaves it pending, which fails the run. Evidence comes from:

- an operator-recorded evidence file (--evidence): booleans only, so no code, token, address or
  profile can be pasted into it;
- with --execute, read-only settings probes (user pool, app client, WAF association, JWKS), after
  the outputs and the caller's AWS account match the expected environment and account.

Live scenarios such as P7 (a resent code replaces the earlier one) are never inferred from
settings: they stay pending until recorded. Output is check IDs, outcomes and evidence field
names only.

Run from infrastructure/:
    uv run python ../scripts/check_identity_capabilities.py --environment dev \
        --expected-account <id> --outputs outputs.json --evidence evidence.json [--execute]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infrastructure"))

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from raad_platform.configuration import ENVIRONMENTS, ConfigurationError, build_configuration

PASSED, FAILED, PENDING = "passed", "failed", "pending"
SDK_CONFIG = Config(connect_timeout=2, read_timeout=5, retries={"total_max_attempts": 2})
# Acceptance evidence per C3 check (contracts/c3-sign-in-client-profile-v1.yaml).
REQUIRED_EVIDENCE: dict[str, tuple[str, ...]] = {
    "P1": ("accessTokenCarriesSubIssuerClientIdTokenUse", "sameSubAcrossSignIns"),
    "P2": ("getUserReturnsConfirmedEmailAndName", "profileSubjectMatchesTokenSub"),
    "P3": ("caseAndSpaceVariantRefusedEmailInUse",),
    "P4": ("passwordPolicyMatchesA4", "a4SamplesGiveA4Results"),
    "P5": ("requestedAttributesAreEmailAndName", "listedAccountHoldsOnlyEmailAndName"),
    "P6": ("preventUserExistenceErrorsEnabled", "threeRefusalsIndistinguishable"),
    "P7": (
        "firstCodeRefusedAfterResend",
        "secondCodeAccepted",
        "resendAcknowledgementSameForUnknownAndConfirmed",
    ),
    "P8": ("resetAcknowledgementSameForKnownAndUnknown",),
    "P9": ("accessTokenSixtyMinutes", "refreshTokenThirtyDays", "mobileIdleRuleVerified"),
    "P10": (
        "firewallAssociatedWithPool",
        "operationClassificationObserved",
        "burstRefusedForOneCaller",
        "secondCallerUnaffected",
    ),
    "P11": ("everyExpectedFailureCodeObserved",),
    "P12": ("oneUserConfirmedEventObserved", "u2WalletCreatedOnceFromEvent"),
    "P13": ("jwksAnswersOverHttps", "tokenHeaderNamesRs256"),
}


class ScopeError(RuntimeError):
    """Outputs, evidence or caller identity do not match the expected environment/account."""


@dataclass(frozen=True)
class CheckResult:
    check: str
    outcome: str
    missing: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()


def load_evidence(document: Any, *, environment: str, account: str) -> dict[str, dict[str, bool]]:
    """Accept only known checks and fields with boolean values for this environment/account."""
    if not isinstance(document, dict) or set(document) - {"environment", "account", "checks"}:
        raise ScopeError("evidence must hold only environment, account and checks")
    if document.get("environment") != environment or document.get("account") != account:
        raise ScopeError("evidence belongs to another environment or account")
    checks = document.get("checks", {})
    if not isinstance(checks, dict):
        raise ScopeError("evidence checks must be an object")
    evidence: dict[str, dict[str, bool]] = {}
    for check, fields in checks.items():
        if check not in REQUIRED_EVIDENCE or not isinstance(fields, dict):
            raise ScopeError("evidence names an unknown check")
        for name, value in fields.items():
            if name not in REQUIRED_EVIDENCE[check]:
                raise ScopeError(f"evidence for {check} names an unknown field")
            if not isinstance(value, bool):
                raise ScopeError(f"evidence for {check} must be true/false only")
        evidence[check] = dict(fields)
    return evidence


def evaluate(evidence: Mapping[str, Mapping[str, bool]]) -> list[CheckResult]:
    results = []
    for check, required in REQUIRED_EVIDENCE.items():
        recorded = evidence.get(check, {})
        failed = tuple(name for name in required if recorded.get(name) is False)
        missing = tuple(name for name in required if name not in recorded)
        outcome = FAILED if failed else PENDING if missing else PASSED
        results.append(CheckResult(check, outcome, missing, failed))
    return results


def probe_settings(
    outputs: Any,
    *,
    environment: str,
    account: str,
    clients: Callable[[str], Any],
    http: Any,
) -> dict[str, dict[str, bool]]:
    """Read-only settings evidence; never a substitute for the live scenarios."""
    try:
        config = build_configuration(outputs, environment=environment, account=account)
    except ConfigurationError as error:
        raise ScopeError(str(error)) from error
    if clients("sts").get_caller_identity().get("Account") != account:
        raise ScopeError("the caller's AWS account is not the expected account")
    identity = outputs[f"RaadIdentity-{environment}"]
    pool_id, client_id = identity["UserPoolIdOutput"], identity["UserPoolClientIdOutput"]
    cognito = clients("cognito-idp")
    pool = cognito.describe_user_pool(UserPoolId=pool_id)["UserPool"]
    client = cognito.describe_user_pool_client(UserPoolId=pool_id, ClientId=client_id)[
        "UserPoolClient"
    ]
    policy = pool.get("Policies", {}).get("PasswordPolicy", {})
    schema_names = {
        attribute["Name"]
        for attribute in pool.get("SchemaAttributes", [])
        if attribute.get("Required")
    }
    units = client.get("TokenValidityUnits", {})
    pool_arn = f"arn:aws:cognito-idp:us-east-1:{account}:userpool/{pool_id}"
    association = clients("wafv2").get_web_acl_for_resource(ResourceArn=pool_arn)
    acl_name = (association.get("WebACL") or {}).get("Name")
    keys = http.get(config.verifier["jwksUri"], timeout=10, allow_redirects=False)
    jwks = keys.json() if keys.status_code == 200 else {}
    return {
        "P4": {
            "passwordPolicyMatchesA4": policy.get("MinimumLength") == 8
            and policy.get("RequireLowercase") is True
            and policy.get("RequireUppercase") is True
            and policy.get("RequireNumbers") is True
            and policy.get("RequireSymbols") is False
        },
        "P5": {"requestedAttributesAreEmailAndName": schema_names == {"email", "name"}},
        "P6": {
            "preventUserExistenceErrorsEnabled": client.get("PreventUserExistenceErrors")
            == "ENABLED"
        },
        "P9": {
            "accessTokenSixtyMinutes": client.get("AccessTokenValidity") == 60
            and units.get("AccessToken") == "minutes",
            "refreshTokenThirtyDays": client.get("RefreshTokenValidity") == 43200
            and units.get("RefreshToken") == "minutes",
        },
        "P10": {"firewallAssociatedWithPool": acl_name == f"raad-{environment}-identity"},
        "P13": {
            "jwksAnswersOverHttps": config.verifier["jwksUri"].startswith("https://")
            and bool(jwks.get("keys"))
            and all(key.get("kty") == "RSA" for key in jwks.get("keys", []))
        },
    }


def merge(*sources: Mapping[str, Mapping[str, bool]]) -> dict[str, dict[str, bool]]:
    """A false item from any source wins, so a probe can never mask recorded failure."""
    merged: dict[str, dict[str, bool]] = {}
    for source in sources:
        for check, fields in source.items():
            for name, value in fields.items():
                current = merged.setdefault(check, {}).get(name, True)
                merged[check][name] = current and value
    return merged


def aws_client(name: str) -> Any:
    factory: Callable[..., Any] = boto3.client
    return factory(name, config=SDK_CONFIG)


def main(argv: list[str] | None = None, clients: Callable[[str], Any] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--environment", required=True, choices=ENVIRONMENTS)
    parser.add_argument("--expected-account", required=True)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--execute", action="store_true", help="run read-only settings probes")
    args = parser.parse_args(argv)
    try:
        recorded: dict[str, dict[str, bool]] = {}
        if args.evidence:
            recorded = load_evidence(
                json.loads(args.evidence.read_text(encoding="utf-8")),
                environment=args.environment,
                account=args.expected_account,
            )
        probed: dict[str, dict[str, bool]] = {}
        if args.execute:
            probed = probe_settings(
                json.loads(args.outputs.read_text(encoding="utf-8")),
                environment=args.environment,
                account=args.expected_account,
                clients=clients or aws_client,
                http=requests,
            )
    except ScopeError as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, KeyError, BotoCoreError, ClientError):
        print("Refused: evidence, outputs or provider settings unavailable", file=sys.stderr)
        return 1
    except requests.RequestException:
        print("Refused: key discovery unavailable", file=sys.stderr)
        return 1
    if not args.execute:
        print("Settings probes not run: pass --execute to read provider settings.")
    results = evaluate(merge(recorded, probed))
    for result in results:
        detail = ""
        if result.failed:
            detail = " (false: " + ", ".join(result.failed) + ")"
        elif result.missing:
            detail = " (missing: " + ", ".join(result.missing) + ")"
        print(f"{result.check}: {result.outcome}{detail}")
    return 0 if all(result.outcome == PASSED for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
