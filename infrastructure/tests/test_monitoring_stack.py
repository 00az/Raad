"""Monitoring assertions for retention, privacy dimensions and alarms."""

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from raad_platform.stacks import MonitoringStack


def template() -> Template:
    app = cdk.App()
    return Template.from_stack(
        MonitoringStack(app, "Monitoring", environment="dev", alert_email="")
    )


def test_logs_have_fourteen_day_retention() -> None:
    template().has_resource_properties("AWS::Logs::LogGroup", {"RetentionInDays": 14})


def test_edge_logs_use_the_key_arn_and_the_key_lets_cloudwatch_logs_use_it() -> None:
    t = template()
    keys = t.find_resources("AWS::KMS::Key")
    assert len(keys) == 1
    key_id = next(iter(keys))
    t.has_resource_properties(
        "AWS::Logs::LogGroup",
        {
            "LogGroupName": "/raad/dev/platform-edge",
            "KmsKeyId": {"Fn::GetAtt": [key_id, "Arn"]},
        },
    )
    t.has_resource_properties(
        "AWS::KMS::Key",
        {
            "KeyPolicy": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Principal": {
                                    "Service": {
                                        "Fn::Join": Match.array_with(
                                            [Match.array_with([".amazonaws.com"])]
                                        )
                                    }
                                },
                                "Action": Match.array_with(["kms:GenerateDataKey*"]),
                                "Condition": {
                                    "ArnLike": {
                                        "kms:EncryptionContext:aws:logs:arn": Match.any_value()
                                    }
                                },
                            }
                        )
                    ]
                )
            }
        },
    )


def test_server_error_alarm_requires_two_periods() -> None:
    template().has_resource_properties(
        "AWS::CloudWatch::Alarm", {"EvaluationPeriods": 2, "DatapointsToAlarm": 2}
    )


def test_alarm_treats_missing_data_as_missing() -> None:
    template().has_resource_properties("AWS::CloudWatch::Alarm", {"TreatMissingData": "missing"})


def test_dashboard_exists() -> None:
    template().resource_count_is("AWS::CloudWatch::Dashboard", 1)


def _dimensions(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "Dimensions":
                yield from value
            else:
                yield from _dimensions(value)
    elif isinstance(node, list):
        for item in node:
            yield from _dimensions(item)


def test_metrics_have_only_bounded_non_personal_dimensions() -> None:
    rendered = template().to_json()
    alarms = [r for r in rendered["Resources"].values() if r["Type"] == "AWS::CloudWatch::Alarm"]
    dimensions = [d for alarm in alarms for d in _dimensions(alarm)]
    assert dimensions and {d["Name"] for d in dimensions} <= {"Environment", "FunctionName"}
    for dimension in dimensions:
        if dimension["Name"] == "Environment":
            assert dimension["Value"] == "dev"
        else:  # A platform function, by reference or by its fixed name.
            assert (
                dimension["Value"] == "raad-dev-identity-publisher" or "Ref" in dimension["Value"]
            )


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


def test_alarm_topic_arn_is_published_at_the_ssm_path_u2_reads() -> None:
    built = template()
    [topic] = built.find_resources("AWS::SNS::Topic")
    built.has_resource_properties("AWS::SNS::Topic", {"TopicName": "raad-dev-alerts"})
    built.has_resource_properties(
        "AWS::SSM::Parameter",
        {"Name": "/raad/dev/alarm-topic/arn", "Type": "String", "Value": {"Ref": topic}},
    )


def test_cloudwatch_may_publish_alarms_only_from_this_account() -> None:
    policies = template().find_resources("AWS::SNS::TopicPolicy")
    statements = next(iter(policies.values()))["Properties"]["PolicyDocument"]["Statement"]
    [allow] = [s for s in statements if s["Effect"] == "Allow"]
    assert allow["Principal"] == {"Service": "cloudwatch.amazonaws.com"}
    assert allow["Action"] == "sns:Publish"
    assert set(allow["Condition"]) == {"StringEquals", "ArnLike"}
    assert allow["Condition"]["StringEquals"] == {"aws:SourceAccount": {"Ref": "AWS::AccountId"}}


def alarms(environment: str = "dev") -> dict:
    built = Template.from_stack(
        MonitoringStack(cdk.App(), "Monitoring", environment=environment, alert_email="")
    )
    return {
        logical: resource["Properties"]
        for logical, resource in built.find_resources("AWS::CloudWatch::Alarm").items()
    }


def named(prefix: str) -> dict:
    [found] = [props for logical, props in alarms().items() if logical.startswith(prefix)]
    return found


def test_server_error_rate_needs_one_percent_of_twenty_requests_in_two_windows() -> None:
    alarm = named("ServerErrors")
    expression = next(m for m in alarm["Metrics"] if "Expression" in m)
    assert expression["Expression"] == "IF(requests >= 20, 100 * FILL(errors, 0) / requests)"
    periods = {m["MetricStat"]["Period"] for m in alarm["Metrics"] if "MetricStat" in m}
    assert periods == {300}
    assert (alarm["Threshold"], alarm["EvaluationPeriods"], alarm["DatapointsToAlarm"]) == (1, 2, 2)
    assert alarm["ComparisonOperator"] == "GreaterThanOrEqualToThreshold"


def test_technical_transfer_failures_need_three_per_window_for_two_windows() -> None:
    alarm = named("TechnicalTransferFailure")
    assert (alarm["Period"], alarm["Statistic"], alarm["Threshold"]) == (300, "Sum", 3)
    assert (alarm["EvaluationPeriods"], alarm["DatapointsToAlarm"]) == (2, 2)


def test_collector_heartbeat_absent_three_minutes_alarms_and_runs_every_minute() -> None:
    alarm = named("CollectorHeartbeatMissing")
    assert alarm["MetricName"] == "PublicCollectorHeartbeat"
    assert (alarm["Period"], alarm["EvaluationPeriods"], alarm["DatapointsToAlarm"]) == (60, 3, 3)
    assert alarm["ComparisonOperator"] == "LessThanThreshold"
    assert alarm["TreatMissingData"] == "breaching"
    template().has_resource_properties(
        "AWS::Scheduler::Schedule",
        {
            "ScheduleExpression": "rate(1 minute)",
            "Target": Match.object_like({"Input": '{"mode":"heartbeat"}'}),
        },
    )


def test_observation_failures_are_alarmed_separately_from_the_latency_slo() -> None:
    alarm = named("PublicCollectionFailure")
    assert (alarm["MetricName"], alarm["Statistic"], alarm["Period"]) == (
        "PublicCollectionFailures",
        "Maximum",
        300,
    )
    assert (alarm["EvaluationPeriods"], alarm["TreatMissingData"]) == (2, "missing")


def test_throttles_publisher_and_rate_store_failures_alarm_on_two_one_minute_windows() -> None:
    publisher = named("IdentityPublisherThrottles")
    assert publisher["Dimensions"] == [
        {"Name": "FunctionName", "Value": "raad-dev-identity-publisher"}
    ]
    for prefix in (
        "IdentityPublisherThrottles",
        "TelemetryProcessorThrottles",
        "RateStoreUnavailable",
    ):
        alarm = named(prefix)
        assert (alarm["Period"], alarm["Threshold"], alarm["EvaluationPeriods"]) == (60, 1, 2)
    failure = named("IdentityEventPublishFailure")
    assert (failure["MetricName"], failure["Threshold"]) == ("IdentityEventPublishFailures", 1)


def test_every_alarm_notifies_and_records_the_accepted_native_recovery_deviation() -> None:
    for props in alarms("prd").values():
        assert props["AlarmActions"], props
        assert "one healthy evaluation" in props["AlarmDescription"]
        assert "accepted deviation" in props["AlarmDescription"]
        if props.get("MetricName") != "PublicCollectorHeartbeat":
            assert props["TreatMissingData"] == "missing"


def _monitoring(context: dict[str, str], environment: str = "dev") -> Template:
    app = cdk.App(context=context)
    return Template.from_stack(
        MonitoringStack(app, "Monitoring", environment=environment, alert_email="")
    )


def test_reserved_concurrency_is_kept_by_default() -> None:
    _monitoring({}).has_resource_properties(
        "AWS::Lambda::Function", {"ReservedConcurrentExecutions": 2}
    )


def test_dev_can_turn_reserved_concurrency_off_for_a_new_account() -> None:
    functions = _monitoring({"raad:reservedConcurrency": "off"}).find_resources(
        "AWS::Lambda::Function"
    )
    assert functions
    assert all("ReservedConcurrentExecutions" not in f["Properties"] for f in functions.values())


def test_stg_and_prd_refuse_turning_reserved_concurrency_off() -> None:
    import pytest

    for environment in ("stg", "prd"):
        with pytest.raises(ValueError, match="only in dev"):
            _monitoring({"raad:reservedConcurrency": "off"}, environment)


def test_an_unknown_reserved_concurrency_setting_is_refused() -> None:
    import pytest

    with pytest.raises(ValueError, match="on or off"):
        _monitoring({"raad:reservedConcurrency": "maybe"})
