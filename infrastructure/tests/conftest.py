"""Shared offline fixtures: inline Lambda assets, no AWS credentials, canonical contracts.

Everything here is synthetic. No test may reach AWS: the credential chain is blanked so an
accidental real client fails fast instead of discovering a developer's session.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from aws_cdk import aws_lambda as lambda_

REPOSITORY = Path(__file__).resolve().parents[2]
CONTRACTS = REPOSITORY / "contracts"

# Synthetic deployment fixture values; none of them is an owned or deployed resource.
SYNTHETIC_ACCOUNT = "111111111111"
SYNTHETIC_CERTIFICATE = (
    "arn:aws:acm:us-east-1:111111111111:certificate/00000000-0000-0000-0000-000000000000"
)
SYNTHETIC_ZONE = "Z0123456789"


def load_contract(name: str) -> Any:
    """Read one canonical contract file from this repo's contracts/ directory."""
    with (CONTRACTS / name).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


@pytest.fixture(autouse=True)
def use_inline_lambda_assets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep construct assertions independent of local Docker/ECR credentials.

    Production stacks still use their Docker bundling configuration; CI's explicit
    `cdk synth` exercises that packaging path separately.
    """
    monkeypatch.setattr(
        lambda_.Code,
        "from_asset",
        lambda *_args, **_kwargs: lambda_.Code.from_inline("def handle(event, context): return {}"),
    )


@pytest.fixture(autouse=True)
def no_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Blank every credential source so offline tests can never authenticate to AWS."""
    for name in (
        "AWS_PROFILE",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
        "AWS_ROLE_ARN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/dev/null")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/dev/null")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
