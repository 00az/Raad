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
