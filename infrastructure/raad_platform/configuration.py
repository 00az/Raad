"""C4 mobile configuration and C5 verifier configuration, built from one environment's outputs.

The input is the document `cdk deploy --outputs-file` writes for one environment's platform
stacks. Nothing here calls AWS. Every value is checked against the same environment's other
outputs and the expected account, not against host-name substrings, and the result is refused on
any missing, extra, cross-environment or secret-looking value.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ENVIRONMENTS = ("dev", "stg", "prd")
CONFIG_VERSION = "1.0"
MONEY_BASE_PATH = "/money/v1"
C4_KEYS = (
    "configVersion",
    "environment",
    "apiBaseUrl",
    "moneyBasePath",
    "authIssuer",
    "authAudience",
    "authClientId",
)
IDENTITY_OUTPUTS = frozenset(
    {"EnvironmentOutput", "UserPoolIdOutput", "UserPoolClientIdOutput", "EventBusArnOutput"}
)
EDGE_OUTPUTS = frozenset(
    {"EnvironmentOutput", "PublicApiUrlOutput", "VerifierConfigOutput", "HttpApiEndpointOutput"}
)
# CDK adds these outputs itself for cross-stack references (resource IDs and ARNs only); they
# are not part of the contract, so key comparison skips them while secret scanning still covers
# them.
CDK_EXPORT_PREFIX = "ExportsOutput"
_SECRET_WORDS = ("secret", "password", "token", "privatekey", "clientsecret")
_SECRET_VALUES = (
    re.compile(r"-----BEGIN"),
    re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
)


class ConfigurationError(ValueError):
    """The outputs cannot produce a coherent configuration; the message names no value."""


@dataclass(frozen=True)
class PlatformConfiguration:
    environment: str
    mobile: dict[str, str]
    verifier: dict[str, Any]


def issuer_for(region: str, user_pool_id: str) -> str:
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"


def verifier_config(
    environment: str, region: str, user_pool_id: str, client_id: str
) -> dict[str, Any]:
    """C5 raad-token-verifier-config for the native SDK flow, in the shape U2 loads.

    SDK (SRP/admin) access tokens authorize the provider's GetUser, not OAuth userInfo, so the
    profile source is the user-profile endpoint (C3 P2) and the audience claim is client_id.
    """
    issuer = issuer_for(region, user_pool_id)
    return {
        "configVersion": CONFIG_VERSION,
        "environment": environment,
        "issuer": issuer,
        "audience": client_id,
        "audienceClaim": "client_id",
        "tokenTypeMarker": {"location": "claim", "name": "token_use", "expectedValue": "access"},
        "jwksUri": issuer + "/.well-known/jwks.json",
        "acceptedAlgorithms": ["RS256"],
        "profileAttributeSource": "user-profile-endpoint",
        "userProfileUri": f"https://cognito-idp.{region}.amazonaws.com/",
    }


def build_configuration(
    outputs: Any, *, environment: str, account: str, region: str = "us-east-1"
) -> PlatformConfiguration:
    """Validate one environment's outputs document and derive C4 and the C5 verifier."""
    if environment not in ENVIRONMENTS:
        raise ConfigurationError("environment must be dev, stg or prd")
    if not re.fullmatch(r"[0-9]{12}", account):
        raise ConfigurationError("account must be a 12-digit account ID")
    if region != "us-east-1":
        raise ConfigurationError("region must be us-east-1")
    identity, edge = _stack_outputs(outputs, environment)
    _refuse_secret_material(outputs)
    pool_id = identity["UserPoolIdOutput"]
    client_id = identity["UserPoolClientIdOutput"]
    if not re.fullmatch(re.escape(region) + r"_[A-Za-z0-9]{1,55}", pool_id):
        raise ConfigurationError("UserPoolIdOutput does not belong to the expected region")
    if not re.fullmatch(r"[A-Za-z0-9]{1,128}", client_id):
        raise ConfigurationError("UserPoolClientIdOutput is not a client identifier")
    bus = f"arn:aws:events:{region}:{account}:event-bus/raad-{environment}-identity-events"
    if identity["EventBusArnOutput"] != bus:
        raise ConfigurationError("EventBusArnOutput does not belong to this account/environment")
    api = _public_origin(edge["PublicApiUrlOutput"])
    if not re.fullmatch(
        r"https://[a-z0-9]{1,32}\.execute-api\." + re.escape(region) + r"\.amazonaws\.com",
        edge["HttpApiEndpointOutput"],
    ):
        raise ConfigurationError("HttpApiEndpointOutput is not this region's HTTP API endpoint")
    if urlsplit(api).hostname == urlsplit(edge["HttpApiEndpointOutput"]).hostname:
        raise ConfigurationError("PublicApiUrlOutput must be the protected public host")
    verifier = _verifier(edge["VerifierConfigOutput"])
    expected = verifier_config(environment, region, pool_id, client_id)
    if verifier != expected:
        raise ConfigurationError("VerifierConfigOutput does not match this environment's pool")
    mobile = {
        "configVersion": CONFIG_VERSION,
        "environment": environment,
        "apiBaseUrl": api,
        "moneyBasePath": MONEY_BASE_PATH,
        "authIssuer": expected["issuer"],
        "authAudience": client_id,
        "authClientId": client_id,
    }
    if tuple(mobile) != C4_KEYS or any(
        word in key.lower() for key in mobile for word in _SECRET_WORDS
    ):
        raise ConfigurationError("C4 keys are not exactly the contract keys")
    return PlatformConfiguration(environment, mobile, verifier)


def write_configuration(configuration: PlatformConfiguration, output_dir: Path) -> list[Path]:
    """Write config/<env>.json (C4) and verifier/<env>.json (C5) into an existing directory.

    An existing target is replaced only when it is a regular file that already holds this
    environment's configuration; anything else is refused and left untouched.
    """
    root = Path(output_dir)
    if root.is_symlink() or not root.is_dir():
        raise ConfigurationError("output directory must be an existing, real directory")
    targets = [
        (root / "config" / f"{configuration.environment}.json", configuration.mobile),
        (root / "verifier" / f"{configuration.environment}.json", configuration.verifier),
    ]
    for path, _ in targets:
        _check_replaceable(path, configuration.environment)
    written = []
    for path, document in targets:
        path.parent.mkdir(exist_ok=True)
        if path.parent.is_symlink():
            raise ConfigurationError("output subdirectory must not be a link")
        _atomic_write(path, json.dumps(document, indent=2, sort_keys=False) + "\n")
        written.append(path)
    return written


def _stack_outputs(outputs: Any, environment: str) -> tuple[Mapping[str, str], Mapping[str, str]]:
    if not isinstance(outputs, dict):
        raise ConfigurationError("outputs document must be an object")
    names = {
        f"RaadIdentity-{environment}": IDENTITY_OUTPUTS,
        f"RaadPublicEdge-{environment}": EDGE_OUTPUTS,
        f"RaadMonitoring-{environment}": frozenset(),
    }
    unknown = set(outputs) - set(names)
    if unknown:
        raise ConfigurationError(
            "outputs document holds stacks of another environment or unknown stacks"
        )
    for stack, expected in names.items():
        section = outputs.get(stack, {} if not expected else None)
        if isinstance(section, dict):
            section = {k: v for k, v in section.items() if not k.startswith(CDK_EXPORT_PREFIX)}
        if not isinstance(section, dict) or set(section) != expected:
            raise ConfigurationError(f"{stack} outputs are missing or have extra keys")
        if not all(isinstance(value, str) and value for value in section.values()):
            raise ConfigurationError(f"{stack} outputs must be non-empty strings")
        if expected and section["EnvironmentOutput"] != environment:
            raise ConfigurationError(f"{stack} belongs to another environment")
    identity = outputs[f"RaadIdentity-{environment}"]
    edge = outputs[f"RaadPublicEdge-{environment}"]
    return identity, edge


def _refuse_secret_material(node: Any, key: str = "") -> None:
    if any(word in key.lower() for word in _SECRET_WORDS):
        raise ConfigurationError("outputs contain a secret-looking key")
    if isinstance(node, dict):
        for child_key, value in node.items():
            _refuse_secret_material(value, str(child_key))
    elif isinstance(node, str) and any(pattern.search(node) for pattern in _SECRET_VALUES):
        raise ConfigurationError("outputs contain secret-looking material")


def _public_origin(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.port
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
        or parts.hostname.endswith(".cloudfront.net")
    ):
        raise ConfigurationError("PublicApiUrlOutput must be an HTTPS origin with no path")
    return f"https://{parts.hostname}"


def _verifier(text: str) -> dict[str, Any]:
    try:
        verifier = json.loads(text)
    except json.JSONDecodeError as error:
        raise ConfigurationError("VerifierConfigOutput is not JSON") from error
    if not isinstance(verifier, dict):
        raise ConfigurationError("VerifierConfigOutput must be an object")
    _refuse_secret_material({k: v for k, v in verifier.items() if k != "tokenTypeMarker"})
    return verifier


def _check_replaceable(path: Path, environment: str) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or not path.is_file():
        raise ConfigurationError("refusing to replace a link or non-file target")
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConfigurationError("refusing to replace an unrelated file") from error
    if (
        not isinstance(existing, dict)
        or existing.get("configVersion") != CONFIG_VERSION
        or existing.get("environment") != environment
    ):
        raise ConfigurationError("refusing to replace an unrelated file")


def _atomic_write(path: Path, text: str) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
