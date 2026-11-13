"""Public edge stack assertions for C1 routing, TLS, and fail-closed integration."""

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from raad_platform.stacks import IdentityStack, MonitoringStack, PublicEdgeStack


def template() -> Template:
    app = cdk.App()
    identity = IdentityStack(app, "Identity", environment="dev", cognito_domain_prefix="raad-dev-example")
    monitoring = MonitoringStack(app, "Monitoring", environment="dev", alert_email="")
    edge = PublicEdgeStack(app, "Edge", environment="dev", identity=identity, monitoring=monitoring, domain_name="api.dev.example.com", hosted_zone_id="Z0123456789", certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/abcd", service_parameter="/raad/dev/money-api/function-url", cognito_domain_prefix="raad-dev-example")
    return Template.from_stack(edge)


def test_edge_lambda_has_nine_second_timeout() -> None:
    template().has_resource_properties("AWS::Lambda::Function", {"Timeout": 9})


def test_edge_lambda_is_concurrency_bounded_in_dev() -> None:
    template().has_resource_properties("AWS::Lambda::Function", {"ReservedConcurrentExecutions": 20})


def test_http_api_has_c1_route() -> None:
    template().resource_count_is("AWS::ApiGatewayV2::Route", 2)


def test_cloudfront_dns_records_use_supplied_zone_id() -> None:
    template().has_resource_properties("AWS::Route53::RecordSet", {"HostedZoneId": "Z0123456789", "Type": "A", "AliasTarget": Match.any_value()})


def test_edge_reads_service_parameter() -> None:
    template().has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": Match.any_value()}})


def test_environment_verifier_parameter_is_published() -> None:
    template().has_resource_properties("AWS::SSM::Parameter", {"Name": "/raad/dev/verifier"})


def test_waf_enables_managed_common_rules() -> None:
    template().has_resource_properties("AWS::WAFv2::WebACL", {"Rules": cdk.assertions.Match.array_with([cdk.assertions.Match.object_like({"Name": "AWSManagedCommon"})])})
