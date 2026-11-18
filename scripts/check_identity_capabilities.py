"""C3 provider capability checklist (P1-P13) for one environment.

A check passes only when every piece of its acceptance evidence is present and true; any false
item fails it, and anything missing leaves it pending, which fails the run. Evidence comes from:

- an operator-recorded evidence file (--evidence): booleans only, so no code, token, address or
  profile can be pasted into it;
- with --execute, read-only settings probes (user pool, app client, WAF association, JWKS), after
  the outputs and the caller's AWS account match the expected environment and account;
- with --execute --burst (dev or stg, never prd), the P10 burst: after those same checks, paced
  unauthenticated InitiateAuth (USER_SRP_AUTH) requests from this one caller for a random,
  unregistered address, stopping at the first regional WAF refusal.

Live scenarios such as P7 (a resent code replaces the earlier one) are never inferred from
settings: they stay pending until recorded. P10's secondCallerUnaffected is always recorded by
the operator. Output is check IDs, outcomes, evidence field names and burst counts only.

Run from infrastructure/:
    uv run python ../scripts/check_identity_capabilities.py --environment dev \
        --expected-account <id> --outputs outputs.json --evidence evidence.json \
        [--execute [--burst]]
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infrastructure"))

import boto3
import requests
from botocore import UNSIGNED
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

# P10 burst. These mirror the regional WAF rules in raad_platform/stacks.py (tests keep them
# equal) so this host script does not load CDK.
ACCOUNT_OPERATION_LIMIT = 100
GENERAL_OPERATION_LIMIT = 300
OPERATION_WINDOW_SECONDS = 300
# Below the general limit, so in a window with no other traffic from this address only the
# account-operation rule can refuse the burst.
BURST_BUDGET = 2 * ACCOUNT_OPERATION_LIMIT
# Every attempt goes out within one evaluation window (240 of 300 seconds), so each admitted
# request still counts when the budget is spent. AWS documents WAF rate limiting as approximate
# and able to lag the limit, usually by under 30 seconds; the 100 requests over the limit cover it.
BURST_INTERVAL_SECONDS = OPERATION_WINDOW_SECONDS * 0.8 / BURST_BUDGET
# Answers that are neither an admission nor a WAF refusal; this many ends the burst inconclusive.
UNCOUNTED_LIMIT = 5
BURST_ENVIRONMENTS = ("dev", "stg")
# Amazon Cognito Developer Guide, "Associate an AWS WAF web ACL with a user pool": the AWS SDKs
# return ForbiddenException for a Block. The InitiateAuth API reference lists the same error for a
# web ACL refusal. The two pages give different HTTP statuses (403, 400), so only the code counts.
WAF_REFUSAL_CODE = "ForbiddenException"
# The user pool itself answered, so the request passed the web ACL: a (simulated) SRP challenge,
# the generic NotAuthorizedException, or UserNotFoundException where existence is not suppressed.
ADMITTED_CODES = frozenset({"NotAuthorizedException", "UserNotFoundException"})
ADMITTED, REFUSED, UNCOUNTED = "admitted", "refused", "uncounted"
# SRP group of the Cognito SDKs (AuthenticationHelper initN, g = 2): the RFC 3526 3072-bit prime.
SRP_N = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64"
    "ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7"
    "ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6B"
    "F12FFA06D98A0864D87602733EC86A64521F2B18177B200C"
    "BBE117577A615D6C770988C0BAD946E208E24FA074E5AB31"
    "43DB5BFCE0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF",
    16,
)
SRP_G = 2
# Unsigned, as the app's public client calls; one attempt per request so the counts are exact.
BURST_SDK_CONFIG = Config(
    region_name="us-east-1",
    signature_version=UNSIGNED,
    connect_timeout=2,
    read_timeout=5,
    retries={"total_max_attempts": 1},
)


class ScopeError(RuntimeError):
    """Outputs, evidence or caller identity do not match the expected environment/account."""


@dataclass(frozen=True)
class CheckResult:
    check: str
    outcome: str
    missing: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()


@dataclass(frozen=True)
class BurstRuntime:
    """The burst's provider client and pacing clock, injected so tests run offline and at once."""

    client: Any
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


@dataclass(frozen=True)
class BurstOutcome:
    admitted: int
    uncounted: int
    refused: bool
    conclusive: bool

    def evidence(self) -> dict[str, dict[str, bool]]:
        """True on a WAF refusal, false when the budget passed without one, nothing otherwise."""
        if not self.conclusive:
            return {}
        return {
            "P10": {
                "operationClassificationObserved": self.refused,
                "burstRefusedForOneCaller": self.refused,
            }
        }

    def describe(self) -> str:
        counts = f"{self.admitted} admitted, {self.uncounted} uncounted"
        if self.refused:
            return f"P10 burst: WAF refusal observed ({counts})"
        if self.conclusive:
            return f"P10 burst: no WAF refusal within {BURST_BUDGET} admitted requests ({counts})"
        return f"P10 burst: inconclusive, no burst evidence recorded ({counts})"


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


def srp_a() -> str:
    """A well-formed SRP_A, g^a mod N for a throwaway a, in the SDKs' unpadded hex.

    N is prime, so A is never 0 mod N. The burst never answers the challenge.
    """
    return format(pow(SRP_G, secrets.randbits(1024) | 1, SRP_N), "x")


def _attempt(client: Any, client_id: str, parameters: Mapping[str, str]) -> str:
    """Classify one InitiateAuth; nothing from the request or its answer is kept or printed."""
    try:
        client.initiate_auth(
            ClientId=client_id, AuthFlow="USER_SRP_AUTH", AuthParameters=dict(parameters)
        )
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code == WAF_REFUSAL_CODE:
            return REFUSED
        return ADMITTED if code in ADMITTED_CODES else UNCOUNTED
    except BotoCoreError:
        return UNCOUNTED
    return ADMITTED


def run_burst(client_id: str, runtime: BurstRuntime) -> BurstOutcome:
    """P10 from one caller: paced sign-in starts until a WAF refusal or the budget is spent.

    The address is random and unregistered, so no account, code or email results, and it never
    leaves this function. Only admitted answers count toward the budget. Throttling, network and
    other provider errors are uncounted: never a refusal and never an admission. Too many of them,
    or pacing that slips past one evaluation window, ends the burst as inconclusive.
    """
    parameters = {"USERNAME": f"p10-probe-{uuid.uuid4().hex}@example.invalid", "SRP_A": srp_a()}
    start = runtime.clock()
    admitted = uncounted = 0
    while admitted < BURST_BUDGET and uncounted < UNCOUNTED_LIMIT:
        delay = start + (admitted + uncounted) * BURST_INTERVAL_SECONDS - runtime.clock()
        if delay > 0:
            runtime.sleep(delay)
        if runtime.clock() - start >= OPERATION_WINDOW_SECONDS:
            return BurstOutcome(admitted, uncounted, refused=False, conclusive=False)
        answer = _attempt(runtime.client, client_id, parameters)
        if answer == REFUSED:
            return BurstOutcome(admitted, uncounted, refused=True, conclusive=True)
        if answer == ADMITTED:
            admitted += 1
        else:
            uncounted += 1
    return BurstOutcome(admitted, uncounted, refused=False, conclusive=admitted >= BURST_BUDGET)


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


def public_cognito_client() -> Any:
    factory: Callable[..., Any] = boto3.client
    return factory("cognito-idp", config=BURST_SDK_CONFIG)


def main(
    argv: list[str] | None = None,
    clients: Callable[[str], Any] | None = None,
    burst: BurstRuntime | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--environment", required=True, choices=ENVIRONMENTS)
    parser.add_argument("--expected-account", required=True)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--execute", action="store_true", help="run read-only settings probes")
    parser.add_argument(
        "--burst", action="store_true", help="with --execute, run the P10 burst (dev or stg)"
    )
    args = parser.parse_args(argv)
    if args.burst and not args.execute:
        parser.error("--burst needs --execute")
    if args.burst and args.environment not in BURST_ENVIRONMENTS:
        print(f"Refused: the P10 burst never runs against {args.environment}", file=sys.stderr)
        return 1
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
            outputs = json.loads(args.outputs.read_text(encoding="utf-8"))
            probed = probe_settings(
                outputs,
                environment=args.environment,
                account=args.expected_account,
                clients=clients or aws_client,
                http=requests,
            )
            if args.burst:
                # Runs only after probe_settings accepted the outputs, environment and account.
                identity = outputs[f"RaadIdentity-{args.environment}"]
                outcome = run_burst(
                    identity["UserPoolClientIdOutput"],
                    burst or BurstRuntime(public_cognito_client()),
                )
                print(outcome.describe())
                probed = merge(probed, outcome.evidence())
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
