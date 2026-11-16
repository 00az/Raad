"""Monitoring assertions for retention, privacy dimensions and alarms."""

import aws_cdk as cdk
from aws_cdk.assertions import Template

from raad_platform.stacks import MonitoringStack


def template() -> Template:
    app = cdk.App()
    return Template.from_stack(
        MonitoringStack(app, "Monitoring", environment="dev", alert_email="")
    )


def test_logs_have_fourteen_day_retention() -> None:
    template().has_resource_properties("AWS::Logs::LogGroup", {"RetentionInDays": 14})


def test_server_error_alarm_requires_two_periods() -> None:
    template().has_resource_properties(
        "AWS::CloudWatch::Alarm", {"EvaluationPeriods": 2, "DatapointsToAlarm": 2}
    )


def test_alarm_treats_missing_data_as_missing() -> None:
    template().has_resource_properties("AWS::CloudWatch::Alarm", {"TreatMissingData": "missing"})


def test_dashboard_exists() -> None:
    template().resource_count_is("AWS::CloudWatch::Dashboard", 1)


def test_metrics_have_only_environment_dimension() -> None:
    rendered = template().to_json()
    for resource in rendered["Resources"].values():
        if resource["Type"] == "AWS::CloudWatch::Alarm":
            dimensions = resource["Properties"].get("Dimensions", [])
            assert all(dimension["Name"] == "Environment" for dimension in dimensions)


def test_email_subscription_is_not_created_without_input() -> None:
    template().resource_count_is("AWS::SNS::Subscription", 0)


def test_sns_publishing_requires_secure_transport():
    policies = template().find_resources("AWS::SNS::TopicPolicy")
    statements = next(iter(policies.values()))["Properties"]["PolicyDocument"]["Statement"]
    assert any(
        s.get("Effect") == "Deny"
        and s.get("Action") == "sns:Publish"
        and s.get("Condition") == {"Bool": {"aws:SecureTransport": "false"}}
        for s in statements
    )


def test_scheduler_can_invoke_only_exact_unqualified_processor():
    policies = template().find_resources("AWS::IAM::Policy")
    invokes = [
        s
        for p in policies.values()
        for s in p["Properties"]["PolicyDocument"]["Statement"]
        if s.get("Action") == "lambda:InvokeFunction"
    ]
    assert len(invokes) == 1
    assert invokes[0]["Resource"] != "*"
    assert ":*" not in str(invokes[0]["Resource"])


def test_api_limited_wildcard_exception_keeps_query_and_metric_controls():
    rendered = template().to_json()
    wildcard = [
        s
        for p in template().find_resources("AWS::IAM::Policy").values()
        for s in p["Properties"]["PolicyDocument"]["Statement"]
        if s.get("Resource") == "*"
    ]
    assert len(wildcard) == 2
    assert all("logs:GetQueryResults" not in s.get("Action", []) for s in wildcard)
    assert any(
        s.get("Condition") == {"StringEquals": {"cloudwatch:namespace": "Raad/Platform"}}
        for s in wildcard
    )
    exceptions = [
        entry
        for r in rendered["Resources"].values()
        for entry in r.get("Metadata", {}).get("cdk_nag", {}).get("rules_to_suppress", [])
        if entry["id"] == "AwsSolutions-IAM5"
    ]
    assert exceptions and all(entry["applies_to"] == ["Resource::*"] for entry in exceptions)
