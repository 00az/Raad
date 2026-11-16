"""Public edge stack assertions for C1 routing, TLS, and fail-closed integration."""

import json

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from raad_platform.stacks import (
    IdentityStack,
    MonitoringStack,
    PublicEdgeStack,
    validate_public_domain,
)


def template(*, custom: bool = True) -> Template:
    app = cdk.App()
    identity = IdentityStack(
        app, "Identity", environment="dev", cognito_domain_prefix="raad-dev-example"
    )
    monitoring = MonitoringStack(app, "Monitoring", environment="dev", alert_email="")
    edge = PublicEdgeStack(
        app,
        "Edge",
        environment="dev",
        identity=identity,
        monitoring=monitoring,
        # Synthetic local configuration; these are not deployed/owned host values.
        domain_name="api.dev.example.test",
        hosted_zone_id="Z0123456789" if custom else "",
        certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/abcd",
        service_parameter="/raad/dev/money-api/function-url",
        cognito_domain_prefix="raad-dev-example",
    )
    return Template.from_stack(edge)


def test_external_dns_pair_preserves_protections_without_route53_resources():
    built = template(custom=False)
    built.resource_count_is("AWS::CloudFront::Distribution", 1)
    built.resource_count_is("AWS::CloudFront::RealtimeLogConfig", 1)
    built.resource_count_is("AWS::WAFv2::WebACL", 1)
    built.resource_count_is("AWS::Route53::RecordSet", 0)
    distribution = next(iter(built.find_resources("AWS::CloudFront::Distribution").values()))[
        "Properties"
    ]["DistributionConfig"]
    assert distribution["ViewerCertificate"]["MinimumProtocolVersion"] == "TLSv1.2_2021"
    assert distribution["ViewerCertificate"]["AcmCertificateArn"].endswith("certificate/abcd")
    assert distribution["Aliases"] == ["api.dev.example.test"]
    assert "WebACLId" in distribution
    assert distribution["CacheBehaviors"][0]["RealtimeLogConfigArn"]
    for origin in distribution["Origins"]:
        assert origin["OriginCustomHeaders"][0]["HeaderName"] == "X-Raad-Origin"
    assert distribution["DefaultCacheBehavior"]["CachePolicyId"]


@pytest.mark.parametrize("custom", [False, True])
def test_actual_public_url_is_published_without_fabricated_runtime_values(custom):
    built = template(custom=custom)
    parameters = built.find_resources("AWS::SSM::Parameter")
    public = next(
        v["Properties"]["Value"]
        for v in parameters.values()
        if v["Properties"]["Name"] == "/raad/dev/public-api-url"
    )
    output = built.to_json()["Outputs"]["PublicApiUrlOutput"]["Value"]
    assert output == public
    assert public == "https://api.dev.example.test"  # synthetic local fixture


@pytest.mark.parametrize(
    "parts",
    [
        ("domain", "", ""),
        ("", "zone", ""),
        ("", "", "cert"),
        ("domain", "zone", ""),
        ("", "zone", "cert"),
    ],
)
def test_partial_custom_domain_configuration_is_rejected(parts):
    with pytest.raises(ValueError, match="together"):
        validate_public_domain("dev", *parts)


def test_custom_certificate_must_be_in_cloudfront_region():
    with pytest.raises(ValueError, match="us-east-1"):
        validate_public_domain("dev", "api.example.test", "zone", "arn:aws:acm:eu-west-1:1:cert/a")


def test_default_certificate_is_rejected_in_every_environment():
    with pytest.raises(ValueError, match="default TLS"):
        validate_public_domain("prd", "", "", "")


def test_edge_lambda_has_nine_second_timeout() -> None:
    template().has_resource_properties("AWS::Lambda::Function", {"Timeout": 9})


def test_edge_lambda_declares_matching_x86_runtime():
    template().has_resource_properties("AWS::Lambda::Function", {"Architectures": ["x86_64"]})


def test_edge_lambda_is_concurrency_bounded_in_dev() -> None:
    template().has_resource_properties(
        "AWS::Lambda::Function", {"ReservedConcurrentExecutions": 20}
    )


def test_http_api_has_c1_route() -> None:
    template().resource_count_is("AWS::ApiGatewayV2::Route", 2)


def test_cloudfront_dns_records_use_supplied_zone_id() -> None:
    template().has_resource_properties(
        "AWS::Route53::RecordSet",
        {"HostedZoneId": "Z0123456789", "Type": "A", "AliasTarget": Match.any_value()},
    )


def test_edge_reads_service_parameter() -> None:
    template().has_resource_properties(
        "AWS::IAM::Policy", {"PolicyDocument": {"Statement": Match.any_value()}}
    )


def test_environment_verifier_parameter_is_published() -> None:
    template().has_resource_properties("AWS::SSM::Parameter", {"Name": "/raad/dev/verifier"})


def test_waf_enables_managed_common_rules() -> None:
    template().has_resource_properties(
        "AWS::WAFv2::WebACL",
        {
            "Rules": cdk.assertions.Match.array_with(
                [cdk.assertions.Match.object_like({"Name": "AWSManagedCommon"})]
            )
        },
    )


def test_every_cloudfront_origin_overwrites_origin_credential_with_secret_reference():
    built = template().to_json()
    origins = next(
        item["Properties"]["DistributionConfig"]["Origins"]
        for item in built["Resources"].values()
        if item["Type"] == "AWS::CloudFront::Distribution"
    )
    for origin in origins:
        headers = origin["OriginCustomHeaders"]
        assert len(headers) == 1 and headers[0]["HeaderName"] == "X-Raad-Origin"
        assert "resolve:secretsmanager" in json.dumps(headers[0]["HeaderValue"])
    template().has_resource_properties(
        "AWS::SecretsManager::Secret",
        {
            "Name": "raad/dev/cloudfront-origin",
            "GenerateSecretString": {"PasswordLength": 64, "ExcludePunctuation": True},
        },
    )


def test_edge_receives_only_origin_secret_arn_and_its_scoped_read_permission():
    built = template().to_json()
    secret_id = next(
        k for k, v in built["Resources"].items() if v["Type"] == "AWS::SecretsManager::Secret"
    )
    template().has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Environment": {
                "Variables": Match.object_like(
                    {
                        "ORIGIN_SECRET_ARN": {"Ref": secret_id},
                    }
                )
            },
        },
    )
    template().has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Action": [
                                    "secretsmanager:GetSecretValue",
                                    "secretsmanager:DescribeSecret",
                                ],
                                "Resource": {"Ref": secret_id},
                            }
                        )
                    ]
                )
            },
        },
    )


def test_environment_profile_selects_sdk_compatible_get_user_not_oauth_user_info():
    built = json.dumps(template().to_json())
    assert "user-profile-endpoint" in built
    assert "cognito-idp." in built
    assert "oauth2/userInfo" not in built


def test_execution_role_has_no_managed_baseline_and_scoped_log_writes():
    roles = template().find_resources("AWS::IAM::Role")
    assert all(not role["Properties"].get("ManagedPolicyArns") for role in roles.values())
    policies = template().find_resources("AWS::IAM::Policy")
    for policy in policies.values():
        for statement in policy["Properties"]["PolicyDocument"]["Statement"]:
            if "logs:PutLogEvents" in statement.get("Action", []):
                assert statement["Resource"] != "*"


def test_http_api_access_logs_only_publish_safe_fields():
    built = template()
    stage = next(iter(built.find_resources("AWS::ApiGatewayV2::Stage").values()))
    fields = json.loads(stage["Properties"]["AccessLogSettings"]["Format"])
    assert set(fields) == {"requestId", "status", "latencyMs"}
    assert "authoriz" not in json.dumps(fields).lower()


def test_security_exceptions_are_local_documented_and_never_suppress_tls():
    resources = template().to_json()["Resources"]
    entries = [
        entry
        for resource in resources.values()
        for entry in resource.get("Metadata", {}).get("cdk_nag", {}).get("rules_to_suppress", [])
    ]
    ids = {entry["id"] for entry in entries}
    assert ids == {
        "AwsSolutions-L1",
        "AwsSolutions-SMG4",
        "AwsSolutions-APIG4",
        "AwsSolutions-CFR3",
    }
    assert all(len(entry["reason"]) > 80 for entry in entries)
    assert "AwsSolutions-CFR4" not in ids


def test_edge_bundle_targets_native_x86_ci_platform(monkeypatch):
    from aws_cdk import aws_lambda as lambda_

    platforms = []

    def asset(*args, **kwargs):
        if kwargs.get("bundling"):
            platforms.append(kwargs["bundling"].platform)
        return lambda_.Code.from_inline("def handle(event, context): return {}")

    monkeypatch.setattr(lambda_.Code, "from_asset", asset)
    template()
    assert platforms == ["linux/amd64"]
