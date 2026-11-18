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
    identity = IdentityStack(app, "Identity", environment="dev")
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
    # Two C1 routes, plus the dev-only stub mapping (stg/prd are covered in test_platform_mapping).
    routes = template().find_resources("AWS::ApiGatewayV2::Route")
    keys = sorted(route["Properties"]["RouteKey"] for route in routes.values())
    assert keys == ["ANY /money/v1", "ANY /money/v1/{proxy+}", "GET /stub/v1/{proxy+}"]


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


def platform(environment: str) -> list[dict]:
    app = cdk.App()
    identity = IdentityStack(app, "Identity", environment=environment)
    monitoring = MonitoringStack(app, "Monitoring", environment=environment, alert_email="")
    edge = PublicEdgeStack(
        app,
        "Edge",
        environment=environment,
        identity=identity,
        monitoring=monitoring,
        domain_name=f"{environment}.api.example.test",  # synthetic fixture host
        hosted_zone_id="",
        certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/abcd",
        service_parameter=f"/raad/{environment}/money-api/function-url",
    )
    return [Template.from_stack(stack).to_json() for stack in (identity, monitoring, edge)]


@pytest.mark.parametrize("environment", ["dev", "stg", "prd"])
def test_every_shared_output_u2_and_u3_read_is_published_once_per_environment(environment):
    names = sorted(
        resource["Properties"]["Name"]
        for built in platform(environment)
        for resource in built["Resources"].values()
        if resource["Type"] == "AWS::SSM::Parameter"
    )
    assert names == sorted(
        f"/raad/{environment}/{suffix}"
        for suffix in (
            "event-bus/arn",
            "alarm-topic/arn",
            "platform-edge-role-arn",
            "correlation-hmac/arn",
            "verifier",
            "public-api-url",
        )
    )
    others = {"dev", "stg", "prd"} - {environment}
    rendered = json.dumps(platform(environment))
    assert not any(f"/raad/{other}/" in rendered for other in others)


def test_platform_never_depends_on_the_u2_stack_at_deploy_time():
    rendered = json.dumps(platform("dev"))
    assert "RaadMoneyService" not in rendered
    imports = [value for built in platform("dev") for value in _find(built, "Fn::ImportValue")]
    # Only intra-platform exports (identity/monitoring -> edge); U2 is reached at runtime
    # through the SSM function-URL parameter and the named function, never an import.
    assert all("Identity" in str(v) or "Monitoring" in str(v) for v in imports)


def _find(node, key):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == key:
                yield v
            else:
                yield from _find(v, key)
    elif isinstance(node, list):
        for item in node:
            yield from _find(item, key)


@pytest.mark.parametrize(
    "environment,deletion", [("dev", "Delete"), ("stg", "Retain"), ("prd", "Retain")]
)
def test_rate_window_table_is_on_demand_ttl_cleaned_and_encrypted(environment, deletion):
    edge = platform(environment)[2]
    [table] = [r for r in edge["Resources"].values() if r["Type"] == "AWS::DynamoDB::Table"]
    properties = table["Properties"]
    assert properties["TableName"] == f"raad-{environment}-platform-rate-windows"
    assert properties["BillingMode"] == "PAY_PER_REQUEST"
    assert properties["KeySchema"] == [{"AttributeName": "pk", "KeyType": "HASH"}]
    assert properties["TimeToLiveSpecification"] == {"AttributeName": "expiresAt", "Enabled": True}
    # SSEEnabled false is DynamoDB's always-on AWS-owned-key encryption; no customer key.
    assert properties["SSESpecification"] == {"SSEEnabled": False}
    assert properties["PointInTimeRecoverySpecification"] == {"PointInTimeRecoveryEnabled": True}
    assert table["DeletionPolicy"] == deletion


def test_edge_may_only_update_its_own_rate_table_and_has_no_money_table_access():
    edge = platform("dev")[2]
    table = next(k for k, r in edge["Resources"].items() if r["Type"] == "AWS::DynamoDB::Table")
    dynamo = [
        s
        for r in edge["Resources"].values()
        if r["Type"] == "AWS::IAM::Policy"
        for s in r["Properties"]["PolicyDocument"]["Statement"]
        if "dynamodb" in json.dumps(s.get("Action"))
    ]
    assert dynamo == [
        {
            "Action": "dynamodb:UpdateItem",
            "Effect": "Allow",
            "Resource": [{"Fn::GetAtt": [table, "Arn"]}],
        }
    ]
    function = next(
        r["Properties"]
        for r in edge["Resources"].values()
        if r["Type"] == "AWS::Lambda::Function"
        and "RATE_TABLE_NAME" in r["Properties"]["Environment"]["Variables"]
    )
    assert function["Environment"]["Variables"]["RATE_TABLE_NAME"] == {"Ref": table}


def test_edge_bundle_keeps_the_package_layout_its_handler_path_imports(monkeypatch):
    from aws_cdk import aws_lambda as lambda_

    commands = []

    def asset(*args, **kwargs):
        if kwargs.get("bundling"):
            commands.append(kwargs["bundling"].command[-1])
        return lambda_.Code.from_inline("def handle(event, context): return {}")

    monkeypatch.setattr(lambda_.Code, "from_asset", asset)
    built = template()
    [command] = commands
    assert "cp -au . /asset-output/raad_platform/edge" in command
    assert "touch /asset-output/raad_platform/__init__.py" in command
    handlers = {
        r["Properties"]["Handler"]
        for r in built.find_resources("AWS::Lambda::Function").values()
        if "RATE_TABLE_NAME" in r["Properties"]["Environment"]["Variables"]
    }
    assert handlers == {"raad_platform.edge.handler.entry"}


def test_cloudfront_keeps_its_own_coarse_ip_limit_independent_of_the_identity_firewall():
    acl = next(iter(template().find_resources("AWS::WAFv2::WebACL").values()))["Properties"]
    assert acl["Scope"] == "CLOUDFRONT"
    [rate] = [r for r in acl["Rules"] if r["Name"] == "BasicRateLimit"]
    assert rate["Statement"]["RateBasedStatement"] == {"Limit": 1000, "AggregateKeyType": "IP"}
    assert acl["VisibilityConfig"]["SampledRequestsEnabled"] is False


SYNTHETIC_ALERT = "synthetic-alert@example.test"


def deploy_inputs(**overrides):
    from raad_platform.stacks import read_deployment_inputs

    environ = {
        "RAAD_ENVIRONMENT": "stg",
        "CDK_DEFAULT_ACCOUNT": "111111111111",
        "CDK_DEFAULT_REGION": "us-east-1",
        "RAAD_DOMAIN_NAME": "stg.api.example.test",
        "RAAD_HOSTED_ZONE_ID": "Z0123456789",
        "RAAD_CERTIFICATE_ARN": "arn:aws:acm:us-east-1:111111111111:certificate/0000-1111",
        "RAAD_ALERT_EMAIL": SYNTHETIC_ALERT,
    }
    environ.update(overrides)
    environ = {k: v for k, v in environ.items() if v is not None}
    return read_deployment_inputs(environ, lambda _key: None)


def test_deployment_inputs_accept_one_coherent_environment_and_hide_the_alert_address():
    inputs = deploy_inputs()
    assert (inputs.environment, inputs.account, inputs.region) == (
        "stg",
        "111111111111",
        "us-east-1",
    )
    assert inputs.alert_email == SYNTHETIC_ALERT
    assert SYNTHETIC_ALERT not in repr(inputs)


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"RAAD_ENVIRONMENT": None}, "dev, stg or prd"),
        ({"RAAD_ENVIRONMENT": "production"}, "dev, stg or prd"),
        ({"CDK_DEFAULT_REGION": "eu-west-1"}, "us-east-1"),
        ({"CDK_DEFAULT_REGION": None}, "us-east-1"),
        ({"CDK_DEFAULT_ACCOUNT": None}, "12-digit"),
        ({"CDK_DEFAULT_ACCOUNT": "1234"}, "12-digit"),
        ({"RAAD_EXPECTED_ACCOUNT": "222222222222"}, "RAAD_EXPECTED_ACCOUNT"),
        (
            {"RAAD_CERTIFICATE_ARN": "arn:aws:acm:us-east-1:222222222222:certificate/x"},
            "belong to CDK_DEFAULT_ACCOUNT",
        ),
        ({"RAAD_HOSTED_ZONE_ID": "not-a-zone"}, "hosted zone"),
        ({"RAAD_DOMAIN_NAME": "x.cloudfront.net"}, "custom hostname"),
        ({"RAAD_ALERT_EMAIL": None}, "RAAD_ALERT_EMAIL"),
        ({"RAAD_ALERT_EMAIL": "not an address"}, "RAAD_ALERT_EMAIL"),
    ],
)
def test_incoherent_deployment_inputs_fail_before_any_stack_is_built(overrides, message):
    with pytest.raises(ValueError, match=message) as refused:
        deploy_inputs(**overrides)
    assert SYNTHETIC_ALERT not in str(refused.value)
    assert "not an address" not in str(refused.value)


def test_region_falls_back_to_the_ci_region_variables_only():
    inputs = deploy_inputs(CDK_DEFAULT_REGION=None, AWS_REGION="us-east-1")
    assert inputs.region == "us-east-1"
    with pytest.raises(ValueError):
        deploy_inputs(CDK_DEFAULT_REGION=None, AWS_DEFAULT_REGION="us-west-2")


@pytest.mark.parametrize("environment,days", [("dev", 14), ("stg", 30), ("prd", 30)])
def test_every_platform_log_group_follows_the_environment_retention(environment, days):
    groups = [
        resource["Properties"]
        for built in platform(environment)
        for resource in built["Resources"].values()
        if resource["Type"] == "AWS::Logs::LogGroup"
    ]
    # Publisher, edge, public samples, telemetry processor and HTTP API access logs, plus the
    # dev-only stub's group.
    assert len(groups) == (6 if environment == "dev" else 5)
    assert {group["RetentionInDays"] for group in groups} == {days}


# Logical IDs recorded from the unchanged tree before U4 (Step 1 baseline), synthesized with
# stack IDs "I", "M" and "E". The Kinesis event-source mapping ID embeds its stack's unique path,
# so the check builds with the same stack IDs. The hosted UI domain was removed on purpose; the
# edge's CurrentVersion ID embeds a configuration hash and changes by design.
BASELINE_LOGICAL_IDS = {
    "identity": [
        "CorrelationHmac4BEB0311",
        "UserPool6BA7E5F2",
        "UserPoolMobileClient046093C2",
    ],
    "monitoring": [
        "Alerts91F83244",
        "AlertsPolicy425C338D",
        "Dashboard9E4231ED",
        "EdgeLogs3E8D2A9E",
        "LogKeyE83D0C1B",
        "LogsKeyA6AB43B2",
        "PublicLatencyProcessor237E9717",
        "PublicLatencyProcessorKinesisEventSourceMPublicLatencyStreamC50FBD7F9B27FADD",
        "PublicLatencyStream2D51E677",
        "PublicSamples4878B0DF",
        "PublicSlowTransfers59510201",
        "ServerErrors4EF9A950",
        "TechnicalTransferFailureBA4BCF04",
        "TelemetryExecutionRoleBE209092",
        "TelemetryExecutionRoleDefaultPolicy25E26DDB",
        "TelemetryLogs8A16482F",
        "TelemetrySchedule",
        "TelemetryScheduleGroup",
        "TelemetrySchedulerRole2FB0ADA3",
        "TelemetrySchedulerRoleDefaultPolicy82D4CCD0",
    ],
    "edge": [
        "ApiAccessLogsE9DF007D",
        "ApiAlias",
        "ApiAliasIpv6",
        "BasicFirewall",
        "CloudFrontTelemetryRoleCB07EDE0",
        "CloudFrontTelemetryRoleDefaultPolicyB6C1A087",
        "CorrelationSecretArnCFEF31F0",
        "Distribution830FAC52",
        "EdgeExecutionRole458F73EA",
        "EdgeExecutionRoleDefaultPolicy1D754AD3",
        "EnvironmentVerifier4BAE2646",
        "MoneyEdgeAliaslive0FF3D072",
        "MoneyEdgeB33C76DB",
        "MoneyHttpApi079F316F",
        "MoneyHttpApiANYmoneyv1DE2535FD",
        "MoneyHttpApiANYmoneyv1MoneyRootIntegration003C042D",
        "MoneyHttpApiANYmoneyv1MoneyRootIntegrationPermission9D510097",
        "MoneyHttpApiANYmoneyv1proxy3FAFB190",
        "MoneyHttpApiANYmoneyv1proxyMoneyEdgeIntegration0A4F00D9",
        "MoneyHttpApiANYmoneyv1proxyMoneyEdgeIntegrationPermissionF43040ED",
        "MoneyHttpApiDefaultStageD7505A69",
        "OriginVerificationSecretA993ECBA",
        "PlatformEdgeRoleArnEA882A30",
        "PublicApiUrl8B7FDA0F",
        "TransferRealtimeLogs",
    ],
}


@pytest.mark.parametrize("environment", ["dev", "stg", "prd"])
def test_existing_logical_ids_are_preserved_so_no_resource_is_replaced_by_rename(environment):
    app = cdk.App()
    identity = IdentityStack(app, "I", environment=environment)
    monitoring = MonitoringStack(app, "M", environment=environment, alert_email="")
    edge = PublicEdgeStack(
        app,
        "E",
        environment=environment,
        identity=identity,
        monitoring=monitoring,
        domain_name="api.example.test",
        hosted_zone_id="Z0123456789",
        certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/abcd",
        service_parameter=f"/raad/{environment}/money-api/function-url",
    )
    for name, stack in (("identity", identity), ("monitoring", monitoring), ("edge", edge)):
        present = set(Template.from_stack(stack).to_json()["Resources"])
        assert set(BASELINE_LOGICAL_IDS[name]) <= present, name


def test_edge_and_rate_table_throttles_alarm_to_the_environment_topic():
    edge = platform("dev")[2]
    alarms = {
        k: r["Properties"]
        for k, r in edge["Resources"].items()
        if r["Type"] == "AWS::CloudWatch::Alarm"
    }
    by_metric = {props["MetricName"]: props for props in alarms.values()}
    assert set(by_metric) == {"Throttles", "WriteThrottleEvents"}
    for props in by_metric.values():
        assert (props["Period"], props["Threshold"], props["EvaluationPeriods"]) == (60, 1, 2)
        assert props["AlarmActions"] and "one healthy evaluation" in props["AlarmDescription"]
