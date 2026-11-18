"""C2 provider tests: exact emission, sign-up-only trigger, failure isolation and privacy."""

from __future__ import annotations

import copy
import json
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from unittest.mock import Mock

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.stub import ANY, Stubber
from conftest import load_contract
from jsonschema import Draft202012Validator, FormatChecker

from raad_platform.identity import publisher

BUS = "arn:aws:events:us-east-1:111111111111:event-bus/raad-dev-identity-events"
SUBJECT = "4f3c2b1a-0000-4000-8000-00000000abcd"
EMAIL = "Synthetic.Person+u4@example.test"
NAME = "Synthetic Person Name"
EVENT_ID = "8a1b9c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d"
NOW = datetime(2026, 11, 17, 10, 0, 0, 123000, tzinfo=UTC)
CONTRACT = load_contract("c2-identity-events-v1.asyncapi.yaml")
ROUTING = CONTRACT["channels"]["userConfirmedV1"]["x-eventbridge"]
PAYLOAD_SCHEMA = CONTRACT["components"]["schemas"]["UserConfirmedPayload"]


def trigger(source: str = "PostConfirmation_ConfirmSignUp", **attributes: Any) -> dict[str, Any]:
    """A Cognito post-confirmation event, including fields this function must ignore."""
    values = {
        "sub": SUBJECT,
        "email": EMAIL,
        "email_verified": "true",
        "name": NAME,
        "cognito:user_status": "CONFIRMED",
    }
    values.update(attributes)
    return {
        "version": "1",
        "region": "us-east-1",
        "userPoolId": "us-east-1_Synthetic1",
        "userName": SUBJECT,
        "triggerSource": source,
        "callerContext": {"awsSdkVersion": "x", "clientId": "syntheticclient1"},
        "request": {"userAttributes": values, "clientMetadata": {"note": "unknown-field"}},
        "response": {},
        "futureCognitoField": {"kept": True},
    }


def run(event: dict[str, Any], client: Any, **overrides: Any) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "client_factory": lambda: client,
        "environment": "dev",
        "bus": BUS,
        "clock": lambda: NOW,
        "new_id": lambda: EVENT_ID,
    }
    settings.update(overrides)
    return publisher.process(event, **settings)


def stubbed() -> tuple[Any, Stubber]:
    client = boto3.client("events", region_name="us-east-1")
    return client, Stubber(client)


def logged(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line]


def assert_private(text: str) -> None:
    for value in (SUBJECT, EMAIL, EMAIL.lower(), NAME, "Synthetic", "@example.test"):
        assert value not in text


def test_routing_constants_match_the_canonical_c2_file() -> None:
    assert publisher.EVENT_SOURCE == ROUTING["source"]
    assert publisher.EVENT_DETAIL_TYPE == ROUTING["detail-type"]
    assert ROUTING["payload-location"] == "detail"
    assert set(publisher.EMITTED_FIELDS) == set(PAYLOAD_SCHEMA["required"])


def test_sign_up_confirmation_publishes_exactly_the_declared_fields(capsys) -> None:
    client, stub = stubbed()
    captured: dict[str, Any] = {}

    def keep(params: dict[str, Any], **_kwargs: Any) -> None:
        captured.update(params)

    client.meta.events.register("provide-client-params.events.PutEvents", keep)
    stub.add_response(
        "put_events",
        {"FailedEntryCount": 0, "Entries": [{"EventId": "accepted-1"}]},
        {
            "Entries": [
                {
                    "Source": ROUTING["source"],
                    "DetailType": ROUTING["detail-type"],
                    "Detail": ANY,
                    "EventBusName": BUS,
                }
            ]
        },
    )
    event = trigger()
    original = copy.deepcopy(event)
    with stub:
        result = run(event, client)
    stub.assert_no_pending_responses()
    assert result is event and event == original
    detail = json.loads(captured["Entries"][0]["Detail"])
    # Consumers tolerate additions; the provider emits only what its current contract declares.
    assert set(detail) == set(PAYLOAD_SCHEMA["properties"])
    Draft202012Validator(PAYLOAD_SCHEMA, format_checker=FormatChecker()).validate(detail)
    assert detail == {
        "specVersion": "1.0",
        "eventId": EVENT_ID,
        "occurredAt": "2026-11-17T10:00:00.123+00:00",
        "environment": "dev",
        "userId": SUBJECT,
        "email": EMAIL,
        "displayName": NAME,
    }
    [line] = logged(capsys)
    assert line["result"] == "published" and line["IdentityEventsPublished"] == 1
    assert line["eventId"] == EVENT_ID and line["Environment"] == "dev"
    assert_private(json.dumps(line))


@pytest.mark.parametrize(
    "source",
    [
        "PostConfirmation_ConfirmForgotPassword",
        "PreSignUp_SignUp",
        "PostConfirmation_ConfirmSignUp ",
        None,
    ],
)
def test_other_triggers_never_publish_and_return_the_event_untouched(capsys, source) -> None:
    factory = Mock(side_effect=AssertionError("must not create a client"))
    event = trigger(source=source)
    original = copy.deepcopy(event)
    assert run(event, None, client_factory=factory) is event
    assert event == original
    factory.assert_not_called()
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "attributes,reason",
    [
        ({"email_verified": "false"}, "unverified-email"),
        ({"email_verified": None}, "unverified-email"),
        ({"name": "   "}, "invalid-name"),
        ({"name": "n" * 201}, "invalid-name"),
        ({"email": "not-an-address"}, "invalid-email"),
        ({"email": "a" * 250 + "@example.test"}, "invalid-email"),
        ({"sub": ""}, "invalid-subject"),
        ({"sub": " padded"}, "invalid-subject"),
    ],
)
def test_incomplete_or_unverified_profile_is_skipped_without_publishing(
    capsys, attributes, reason
) -> None:
    factory = Mock(side_effect=AssertionError("must not publish"))
    event = trigger(**attributes)
    assert run(event, None, client_factory=factory) is event
    factory.assert_not_called()
    [line] = logged(capsys)
    assert (line["result"], line["reason"], line["IdentityEventsSkipped"]) == (
        "skipped",
        reason,
        1,
    )
    assert_private(json.dumps(line))


def test_partial_put_events_failure_is_recorded_and_confirmation_still_succeeds(capsys) -> None:
    client, stub = stubbed()
    stub.add_response(
        "put_events",
        {
            "FailedEntryCount": 1,
            "Entries": [{"ErrorCode": "InternalFailure", "ErrorMessage": f"echo {EMAIL}"}],
        },
    )
    event = trigger()
    with stub:
        assert run(event, client) is event
    [line] = logged(capsys)
    assert (line["result"], line["reason"]) == ("failed", "InternalFailure")
    assert line["IdentityEventPublishFailures"] == 1
    assert_private(json.dumps(line))


def test_thrown_put_events_error_is_distinguished_from_a_per_entry_failure(capsys) -> None:
    client, stub = stubbed()
    stub.add_client_error(
        "put_events", service_error_code="ThrottlingException", service_message=EMAIL
    )
    event = trigger()
    with stub:
        assert run(event, client) is event
    [line] = logged(capsys)
    assert (line["result"], line["reason"]) == ("failed", "ThrottlingException")
    assert_private(json.dumps(line))


@pytest.mark.parametrize(
    "failure,reason",
    [
        (EndpointConnectionError(endpoint_url="https://events.example.test"), "sdk-unavailable"),
        (RuntimeError(f"boom {EMAIL}"), "unexpected"),
    ],
)
def test_transport_and_unexpected_failures_never_fail_confirmation(capsys, failure, reason) -> None:
    client = Mock(put_events=Mock(side_effect=failure))
    event = trigger()
    assert run(event, client) is event
    [line] = logged(capsys)
    assert (line["result"], line["reason"]) == ("failed", reason)
    assert_private(json.dumps(line))


@pytest.mark.parametrize(
    "overrides", [{"environment": "production"}, {"bus": ""}, {"bus": "raad-dev-identity-events"}]
)
def test_missing_or_invalid_configuration_fails_closed_without_publishing(
    capsys, overrides
) -> None:
    factory = Mock(side_effect=AssertionError("must not publish"))
    assert run(trigger(), None, client_factory=factory, **overrides)["triggerSource"]
    factory.assert_not_called()
    [line] = logged(capsys)
    assert (line["result"], line["reason"]) == ("failed", "configuration")


def test_occurred_at_is_the_trusted_clock_converted_to_utc() -> None:
    riyadh = datetime(2026, 11, 17, 13, 0, tzinfo=timezone(timedelta(hours=3)))
    detail = publisher.build_detail(
        trigger(), environment="stg", occurred_at=riyadh, event_id=EVENT_ID
    )
    assert detail["occurredAt"] == "2026-11-17T10:00:00.000+00:00"
    assert detail["environment"] == "stg"
    with pytest.raises(ValueError):
        publisher.build_detail(
            trigger(), environment="dev", occurred_at=datetime(2026, 11, 17), event_id=EVENT_ID
        )


def test_lambda_entry_uses_environment_configuration_and_a_fresh_uuid(monkeypatch, capsys) -> None:
    client, stub = stubbed()
    stub.add_response("put_events", {"FailedEntryCount": 0, "Entries": [{"EventId": "e-1"}]})
    monkeypatch.setattr(publisher, "_client", client)
    monkeypatch.setenv("ENVIRONMENT", "prd")
    monkeypatch.setenv("EVENT_BUS_ARN", BUS)
    with stub:
        publisher.handle(trigger(), None)
    [line] = logged(capsys)
    assert line["Environment"] == "prd" and line["result"] == "published"
    assert str(uuid.UUID(line["eventId"])) == line["eventId"]


def test_events_client_is_created_once_with_bounded_sdk_settings(monkeypatch) -> None:
    factory = Mock(return_value="client")
    monkeypatch.setattr(publisher, "_client", None)
    monkeypatch.setattr(publisher.boto3, "client", factory)
    assert publisher._events_client() == "client"
    assert publisher._events_client() == "client"
    factory.assert_called_once()
    config = factory.call_args.kwargs["config"]
    assert config.retries == {"total_max_attempts": 2}
    assert config.read_timeout == 1
