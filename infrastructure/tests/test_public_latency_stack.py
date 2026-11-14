"""Public-latency resource wiring and privacy assertions."""

import json

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from raad_platform.stacks import IdentityStack, MonitoringStack, PublicEdgeStack
from raad_platform.telemetry.handler import FIELDS


def stacks() -> tuple[Template, Template]:
    app = cdk.App()
    identity = IdentityStack(app, "Identity", environment="dev", cognito_domain_prefix="raad-test")
    monitor = MonitoringStack(app, "Monitoring", environment="dev", alert_email="")
    edge = PublicEdgeStack(
        app,
        "Edge",
        environment="dev",
        identity=identity,
        monitoring=monitor,
        domain_name="api.example.test",
        hosted_zone_id="Z12345",
        certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/test",
        service_parameter="/raad/dev/money-api/function-url",
        cognito_domain_prefix="raad-test",
    )
    return Template.from_stack(monitor), Template.from_stack(edge)


def test_exact_safe_fields_and_full_sampling() -> None:
    _, edge = stacks()
    edge.has_resource_properties(
        "AWS::CloudFront::RealtimeLogConfig", {"Fields": list(FIELDS), "SamplingRate": 100}
    )


def test_transfer_behavior_attaches_realtime_log_and_disables_caching() -> None:
    _, edge = stacks()
    edge.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": {
                "CacheBehaviors": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "PathPattern": "/money/v1/transfers",
                                "RealtimeLogConfigArn": Match.any_value(),
                                "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
                            }
                        )
                    ]
                )
            }
        },
    )


def test_stream_is_encrypted_single_shard_with_24h_retention() -> None:
    monitor, _ = stacks()
    monitor.has_resource_properties(
        "AWS::Kinesis::Stream",
        {
            "ShardCount": 1,
            "RetentionPeriodHours": 24,
            "StreamEncryption": Match.object_like({"EncryptionType": "KMS"}),
        },
    )


def test_processor_concurrency_retention_and_stream_mapping() -> None:
    monitor, _ = stacks()
    monitor.has_resource_properties(
        "AWS::Lambda::Function", {"ReservedConcurrentExecutions": 2, "Timeout": 20}
    )
    monitor.has_resource_properties(
        "AWS::Logs::LogGroup", {"LogGroupName": "/raad/dev/public-latency", "RetentionInDays": 14}
    )
    monitor.has_resource_properties(
        "AWS::Lambda::EventSourceMapping", {"BatchSize": 50, "MaximumRetryAttempts": 2}
    )


def test_processor_has_no_money_data_or_invocation_permissions() -> None:
    monitor, _ = stacks()
    policies = json.dumps(monitor.find_resources("AWS::IAM::Policy"))
    assert "dynamodb:" not in policies
    assert "lambda:InvokeFunctionUrl" not in policies


def test_schedule_is_grace_delayed_and_account_scoped() -> None:
    monitor, _ = stacks()
    monitor.has_resource_properties(
        "AWS::Scheduler::Schedule",
        {
            "ScheduleExpression": "cron(2/5 * * * ? *)",
            "ScheduleExpressionTimezone": "UTC",
            "FlexibleTimeWindow": {"Mode": "OFF"},
        },
    )
    monitor.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Principal": {"Service": "scheduler.amazonaws.com"},
                                "Condition": Match.object_like(
                                    {
                                        "StringEquals": Match.any_value(),
                                        "ArnEquals": Match.any_value(),
                                    }
                                ),
                            }
                        )
                    ]
                )
            }
        },
    )


def test_pair_alarm_uses_maximum_missing_and_recovery_notifications() -> None:
    monitor, _ = stacks()
    monitor.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "MetricName": "PublicSlowPair",
            "Statistic": "Maximum",
            "TreatMissingData": "missing",
            "EvaluationPeriods": 1,
            "OKActions": Match.any_value(),
        },
    )


def test_dashboard_exposes_best_effort_unknown_coverage() -> None:
    monitor, _ = stacks()
    dashboard = json.dumps(monitor.find_resources("AWS::CloudWatch::Dashboard"))
    assert "unknown" in dashboard and "insufficient" in dashboard
