"""CDK unit tests synthesize Lambda assets without invoking Docker."""

import pytest
from aws_cdk import aws_lambda as lambda_


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
