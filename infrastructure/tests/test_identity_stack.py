"""Identity stack assertions for environment isolation and mobile-safe Cognito."""

import aws_cdk as cdk
from aws_cdk.assertions import Template

from raad_platform.stacks import IdentityStack


def template() -> Template:
    app = cdk.App()
    stack = IdentityStack(
        app, "Identity", environment="dev", cognito_domain_prefix="raad-dev-example"
    )
    return Template.from_stack(stack)


def test_identity_uses_cognito_user_pool() -> None:
    template().resource_count_is("AWS::Cognito::UserPool", 1)


def test_mobile_client_has_no_secret() -> None:
    template().has_resource_properties("AWS::Cognito::UserPoolClient", {"GenerateSecret": False})


def test_mobile_client_enables_authorization_code_pkce_flow() -> None:
    template().has_resource_properties(
        "AWS::Cognito::UserPoolClient", {"AllowedOAuthFlows": ["code"]}
    )


def test_email_is_a_verified_alias() -> None:
    template().has_resource_properties(
        "AWS::Cognito::UserPool", {"AutoVerifiedAttributes": ["email"]}
    )


def test_environment_name_scopes_pool() -> None:
    template().has_resource_properties("AWS::Cognito::UserPool", {"UserPoolName": "raad-dev"})


def test_hmac_secret_is_environment_scoped() -> None:
    template().has_resource_properties(
        "AWS::SecretsManager::Secret", {"Name": "raad/dev/correlation-hmac"}
    )


def test_dev_only_plus_exception_preserves_identity_controls():
    rendered = template().to_json()
    pool = next(r for r in rendered["Resources"].values() if r["Type"] == "AWS::Cognito::UserPool")
    assert pool["Properties"]["Policies"]["PasswordPolicy"]["MinimumLength"] == 12
    assert pool["Properties"]["AutoVerifiedAttributes"] == ["email"]
    entries = pool["Metadata"]["cdk_nag"]["rules_to_suppress"]
    assert [entry["id"] for entry in entries] == ["AwsSolutions-COG8"]
    assert "dev-only" in entries[0]["reason"]
