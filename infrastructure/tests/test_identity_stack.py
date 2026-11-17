"""Identity stack assertions: native C3 settings, environment isolation and no paid Plus."""

from __future__ import annotations

from typing import Any

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template
from conftest import load_contract

from raad_platform.stacks import IdentityStack, require_environment


def template(environment: str = "dev") -> Template:
    app = cdk.App()
    stack = IdentityStack(app, "Identity", environment=environment)
    return Template.from_stack(stack)


def resource(built: Template, kind: str) -> dict[str, Any]:
    found = built.find_resources(kind)
    assert len(found) == 1, kind
    item: dict[str, Any] = next(iter(found.values()))
    return item


def pool(environment: str = "dev") -> dict[str, Any]:
    return resource(template(environment), "AWS::Cognito::UserPool")


def client(environment: str = "dev") -> dict[str, Any]:
    properties: dict[str, Any] = resource(template(environment), "AWS::Cognito::UserPoolClient")[
        "Properties"
    ]
    return properties


def test_identity_uses_cognito_user_pool() -> None:
    template().resource_count_is("AWS::Cognito::UserPool", 1)


def test_mobile_client_has_no_secret() -> None:
    template().has_resource_properties("AWS::Cognito::UserPoolClient", {"GenerateSecret": False})


def test_native_sdk_client_has_no_hosted_ui_oauth_or_domain() -> None:
    built = template()
    built.resource_count_is("AWS::Cognito::UserPoolDomain", 0)
    properties = client()
    assert properties["AllowedOAuthFlowsUserPoolClient"] is False
    assert not {"AllowedOAuthFlows", "AllowedOAuthScopes", "CallbackURLs"} & set(properties)
    assert properties["SupportedIdentityProviders"] == ["COGNITO"]
    # SRP for the app; the IAM-only admin flow serves controlled test fixtures; no plain
    # USER_PASSWORD_AUTH that would send the password itself.
    assert sorted(properties["ExplicitAuthFlows"]) == [
        "ALLOW_ADMIN_USER_PASSWORD_AUTH",
        "ALLOW_REFRESH_TOKEN_AUTH",
        "ALLOW_USER_SRP_AUTH",
    ]


def test_email_is_a_verified_case_insensitive_sign_in_alias() -> None:
    properties = pool()["Properties"]
    assert properties["AutoVerifiedAttributes"] == ["email"]
    assert properties["UsernameAttributes"] == ["email"]
    assert properties["UsernameConfiguration"] == {"CaseSensitive": False}  # C3 P3
    assert properties["AccountRecoverySetting"]["RecoveryMechanisms"] == [
        {"Name": "verified_email", "Priority": 1}
    ]


def test_password_policy_is_exactly_a4_from_the_c3_contract() -> None:
    rule = load_contract("c3-sign-in-client-profile-v1.yaml")["password_rule"]
    policy = pool()["Properties"]["Policies"]["PasswordPolicy"]
    assert policy == {
        "MinimumLength": rule["minimum_characters"],
        "RequireLowercase": rule["requires_latin_lowercase"],
        "RequireUppercase": rule["requires_latin_uppercase"],
        "RequireNumbers": rule["requires_digit"],
        "RequireSymbols": rule["requires_symbol"],
    }

    def admitted(password: str) -> bool:
        return (
            len(password) >= policy["MinimumLength"]
            and (not policy["RequireLowercase"] or any(c.islower() for c in password))
            and (not policy["RequireUppercase"] or any(c.isupper() for c in password))
            and (not policy["RequireNumbers"] or any(c.isdigit() for c in password))
            and (not policy["RequireSymbols"] or any(not c.isalnum() for c in password))
        )

    assert [admitted(p) for p in rule["examples"]["accepted"]] == [True]
    assert [admitted(p) for p in rule["examples"]["refused"]] == [False] * 4


def test_only_email_and_name_are_stored_required_and_immutable() -> None:
    schema = pool()["Properties"]["Schema"]
    assert schema == [
        {"Mutable": False, "Name": "email", "Required": True},
        {"Mutable": False, "Name": "name", "Required": True},
    ]
    properties = client()
    assert sorted(properties["WriteAttributes"]) == ["email", "name"]
    assert sorted(properties["ReadAttributes"]) == ["email", "email_verified", "name"]


def test_generic_refusal_revocation_and_session_lengths_follow_c3() -> None:
    session = load_contract("c3-sign-in-client-profile-v1.yaml")["operations"]["refreshSession"]
    policy = session["session_policy"]
    properties = client()
    assert properties["PreventUserExistenceErrors"] == "ENABLED"  # C3 P6
    assert properties["EnableTokenRevocation"] is True
    assert properties["TokenValidityUnits"] == {
        "AccessToken": "minutes",
        "IdToken": "minutes",
        "RefreshToken": "minutes",
    }
    assert properties["AccessTokenValidity"] == policy["access_token_lifetime_minutes"]
    # Fixed 30-day refresh lifetime from sign-in; the idle rule is U3's (C3 P9).
    assert properties["RefreshTokenValidity"] == policy["refresh_allowed_until_idle_days"] * 1440


def test_environment_name_scopes_pool() -> None:
    template().has_resource_properties("AWS::Cognito::UserPool", {"UserPoolName": "raad-dev"})


def test_hmac_secret_is_environment_scoped() -> None:
    template().has_resource_properties(
        "AWS::SecretsManager::Secret", {"Name": "raad/dev/correlation-hmac"}
    )


@pytest.mark.parametrize("environment", ["dev", "stg", "prd"])
def test_no_paid_plus_and_only_reasoned_identity_exceptions(environment: str) -> None:
    item = pool(environment)
    assert item["Properties"].get("UserPoolTier", "ESSENTIALS") != "PLUS"
    assert "UserPoolAddOns" not in item["Properties"]
    entries = item["Metadata"]["cdk_nag"]["rules_to_suppress"]
    assert sorted(entry["id"] for entry in entries) == ["AwsSolutions-COG1", "AwsSolutions-COG8"]
    assert all(len(entry["reason"]) > 120 for entry in entries)
    plus = next(entry for entry in entries if entry["id"] == "AwsSolutions-COG8")
    assert environment in plus["reason"] and "release risk" in plus["reason"]


@pytest.mark.parametrize(
    "environment,policy", [("dev", "Delete"), ("stg", "Retain"), ("prd", "Retain")]
)
def test_pool_is_retained_outside_dev(environment: str, policy: str) -> None:
    assert pool(environment)["DeletionPolicy"] == policy


def test_unknown_environment_is_refused() -> None:
    with pytest.raises(ValueError, match="dev, stg or prd"):
        require_environment("qa")
    with pytest.raises(ValueError):
        IdentityStack(cdk.App(), "Identity", environment="production")


def statements(built: Template, kind: str = "AWS::IAM::Policy") -> list[dict[str, Any]]:
    return [
        statement
        for policy in built.find_resources(kind).values()
        for statement in policy["Properties"]["PolicyDocument"]["Statement"]
    ]


def logical_id(built: Template, kind: str) -> str:
    [found] = built.find_resources(kind)
    return found


@pytest.mark.parametrize("environment", ["dev", "stg", "prd"])
def test_c2_bus_is_per_environment_and_its_arn_is_published_for_u2(environment: str) -> None:
    built = template(environment)
    bus = logical_id(built, "AWS::Events::EventBus")
    assert resource(built, "AWS::Events::EventBus")["Properties"] == {
        "Name": f"raad-{environment}-identity-events"  # service-owned encryption at rest
    }
    built.has_resource_properties(
        "AWS::SSM::Parameter",
        {
            "Name": f"/raad/{environment}/event-bus/arn",
            "Type": "String",
            "Value": {"Fn::GetAtt": [bus, "Arn"]},
        },
    )


def test_publisher_role_may_send_only_the_contract_source_and_type_to_its_own_bus() -> None:
    built = template()
    bus = logical_id(built, "AWS::Events::EventBus")
    puts = [s for s in statements(built) if s.get("Action") == "events:PutEvents"]
    assert puts == [
        {
            "Action": "events:PutEvents",
            "Condition": {
                "StringEquals": {
                    "events:source": ["raad.identity"],
                    "events:detail-type": ["raad.identity.user-confirmed.v1"],
                }
            },
            "Effect": "Allow",
            "Resource": {"Fn::GetAtt": [bus, "Arn"]},
        }
    ]
    roles = built.find_resources("AWS::IAM::Role")
    assert all(not role["Properties"].get("ManagedPolicyArns") for role in roles.values())


def test_bus_policy_denies_every_other_principal_source_and_detail_type() -> None:
    built = template()
    policies = built.find_resources("AWS::Events::EventBusPolicy")
    by_sid = {p["Properties"]["StatementId"]: p for p in policies.values()}
    assert set(by_sid) == {"DenyOtherPublishers", "DenyOtherSources", "DenyOtherDetailTypes"}
    role = next(
        k
        for k, v in built.find_resources("AWS::IAM::Role").items()
        if k.startswith("IdentityPublisherRole")
    )
    for policy in by_sid.values():
        statement = policy["Properties"]["Statement"]
        assert (statement["Effect"], statement["Principal"], statement["Action"]) == (
            "Deny",
            "*",
            "events:PutEvents",
        )
    assert by_sid["DenyOtherPublishers"]["Properties"]["Statement"]["Condition"] == {
        "ArnNotEquals": {"aws:PrincipalArn": {"Fn::GetAtt": [role, "Arn"]}}
    }
    assert by_sid["DenyOtherSources"]["Properties"]["Statement"]["Condition"] == {
        "StringNotEquals": {"events:source": "raad.identity"}
    }
    # Policy writes on one bus are serialized.
    assert by_sid["DenyOtherDetailTypes"]["DependsOn"] == ["IdentityEventBusDenyOtherSources"]
    assert by_sid["DenyOtherSources"]["DependsOn"] == ["IdentityEventBusDenyOtherPublishers"]


def test_publisher_is_the_only_trigger_and_only_this_pool_may_invoke_it() -> None:
    built = template()
    publisher_id = next(
        k
        for k, v in built.find_resources("AWS::Lambda::Function").items()
        if v["Properties"]["Handler"] == "publisher.handle"
    )
    assert pool()["Properties"]["LambdaConfig"] == {
        "PostConfirmation": {"Fn::GetAtt": [publisher_id, "Arn"]}
    }
    permission = resource(built, "AWS::Lambda::Permission")["Properties"]
    assert permission["Principal"] == "cognito-idp.amazonaws.com"
    assert permission["SourceArn"] == {
        "Fn::GetAtt": [logical_id(built, "AWS::Cognito::UserPool"), "Arn"]
    }


def test_publisher_function_is_bounded_and_environment_bound() -> None:
    built = template("stg")
    function = next(
        v["Properties"]
        for v in built.find_resources("AWS::Lambda::Function").values()
        if v["Properties"]["Handler"] == "publisher.handle"
    )
    assert function["FunctionName"] == "raad-stg-identity-publisher"
    assert (
        function["Timeout"],
        function["MemorySize"],
        function["ReservedConcurrentExecutions"],
    ) == (
        3,
        128,
        2,
    )
    assert function["Architectures"] == ["x86_64"] and function["Runtime"] == "python3.12"
    variables = function["Environment"]["Variables"]
    assert set(variables) == {"ENVIRONMENT", "EVENT_BUS_ARN"}
    assert variables["ENVIRONMENT"] == "stg"
    built.has_resource_properties(
        "AWS::Logs::LogGroup",
        {"LogGroupName": "/raad/stg/identity-publisher", "RetentionInDays": 30},
    )


def test_identity_outputs_are_the_non_secret_values_the_config_writer_reads() -> None:
    outputs = template().to_json()["Outputs"]
    assert set(outputs) == {
        "EnvironmentOutput",
        "UserPoolIdOutput",
        "UserPoolClientIdOutput",
        "EventBusArnOutput",
    }
    assert outputs["EnvironmentOutput"]["Value"] == "dev"
    assert not any("Export" in output for output in outputs.values())


def firewall_rules(environment: str = "dev") -> dict[str, dict[str, Any]]:
    acl = resource(template(environment), "AWS::WAFv2::WebACL")["Properties"]
    return {rule["Name"]: rule for rule in acl["Rules"]}


def scope_regex(rule: dict[str, Any]) -> tuple[str, bool]:
    """Return the operation regex a rule's scope-down uses and whether it is negated."""
    scope = rule["Statement"]["RateBasedStatement"]["ScopeDownStatement"]
    negated = "NotStatement" in scope
    statement = scope["NotStatement"]["Statement"] if negated else scope
    match = statement["RegexMatchStatement"]
    assert match["FieldToMatch"] == {"SingleHeader": {"Name": "x-amzn-cognito-operation-name"}}
    return match["RegexString"], negated


@pytest.mark.parametrize("environment", ["dev", "stg", "prd"])
def test_regional_firewall_is_associated_with_this_environments_pool(environment: str) -> None:
    built = template(environment)
    acl = resource(built, "AWS::WAFv2::WebACL")
    assert acl["Properties"]["Scope"] == "REGIONAL"
    assert acl["Properties"]["Name"] == f"raad-{environment}-identity"
    assert acl["Properties"]["DefaultAction"] == {"Allow": {}}
    association = resource(built, "AWS::WAFv2::WebACLAssociation")["Properties"]
    assert association == {
        "ResourceArn": {"Fn::GetAtt": [logical_id(built, "AWS::Cognito::UserPool"), "Arn"]},
        "WebACLArn": {"Fn::GetAtt": [logical_id(built, "AWS::WAFv2::WebACL"), "Arn"]},
    }


def test_account_operations_are_limited_to_about_100_per_ip_per_five_minutes() -> None:
    import re

    rule = firewall_rules()["AccountOperationsPerIp"]
    rate = rule["Statement"]["RateBasedStatement"]
    assert (rate["Limit"], rate["EvaluationWindowSec"], rate["AggregateKeyType"]) == (
        100,
        300,
        "IP",
    )
    assert rule["Action"] == {"Block": {}}
    pattern, negated = scope_regex(rule)
    assert not negated
    for name in (
        "SignUp",
        "ConfirmSignUp",
        "ResendConfirmationCode",
        "InitiateAuth",
        "RespondToAuthChallenge",
        "ForgotPassword",
        "ConfirmForgotPassword",
    ):
        assert re.fullmatch(pattern, name)
        assert re.fullmatch(pattern, f"AWSCognitoIdentityProviderService.{name}")
    for name in ("GetUser", "AdminInitiateAuth", "SignUpX", "RevokeToken", ""):
        assert not re.fullmatch(pattern, name)


def test_general_bucket_counts_every_operation_except_get_user() -> None:
    import re

    rule = firewall_rules()["GeneralOperationsPerIp"]
    rate = rule["Statement"]["RateBasedStatement"]
    assert (rate["Limit"], rate["EvaluationWindowSec"], rate["AggregateKeyType"]) == (
        300,
        300,
        "IP",
    )
    pattern, negated = scope_regex(rule)
    assert negated  # The scope-down excludes GetUser; everything else is counted.
    assert re.fullmatch(pattern, "GetUser")
    assert re.fullmatch(pattern, "AWSCognitoIdentityProviderService.GetUser")
    for name in ("InitiateAuth", "GetUserAttributeVerificationCode", "AdminGetUser", "RevokeToken"):
        assert not re.fullmatch(pattern, name)


def test_firewall_keeps_sampling_and_request_logging_off_and_no_atp_group() -> None:
    built = template()
    acl = resource(built, "AWS::WAFv2::WebACL")["Properties"]
    configs = [acl["VisibilityConfig"]] + [r["VisibilityConfig"] for r in acl["Rules"]]
    assert all(config["SampledRequestsEnabled"] is False for config in configs)
    assert all(
        config["MetricName"].startswith("raad-dev-identity") and "@" not in config["MetricName"]
        for config in configs
    )
    built.resource_count_is("AWS::WAFv2::LoggingConfiguration", 0)
    assert "ATPRuleSet" not in str(acl)
