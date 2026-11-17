"""Rate-window store: exact wire requests, windows, atomic charging and bounded failure."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.stub import Stubber
from conftest import load_contract

from raad_platform.edge import rate_store
from raad_platform.edge.rate_store import Decision, RateLimiter, RateStoreUnavailable

TABLE = "raad-dev-platform-rate-windows"
KEY = b"k" * 64
SUBJECT = "4f3c2b1a-0000-4000-8000-00000000abcd"


def limiter(client: Any, clock: float = 600.5, **kwargs: Any) -> RateLimiter:
    settings: dict[str, Any] = {"clock": lambda: clock, "sleep": Mock()}
    settings.update(kwargs)
    keys = settings.pop("keys", [("1", KEY)])
    return RateLimiter(client, TABLE, settings.pop("environment", "dev"), keys, **settings)


def stubbed() -> tuple[Any, Stubber]:
    client = boto3.client("dynamodb", region_name="us-east-1")
    return client, Stubber(client)


def update(counter: str, window: int = 10, version: str = "1", key: bytes = KEY) -> dict[str, Any]:
    protected = rate_store.protected_subject(key, "dev", SUBJECT)
    return {
        "Update": {
            "TableName": TABLE,
            "Key": {"pk": {"S": f"dev#{counter}#{window}#{version}#{protected}"}},
            "UpdateExpression": "SET #count = if_not_exists(#count, :zero) + :one, "
            "#expires = :expires",
            "ConditionExpression": "attribute_not_exists(#count) OR #count < :limit",
            "ExpressionAttributeNames": {"#count": "count", "#expires": "expiresAt"},
            "ExpressionAttributeValues": {
                ":zero": {"N": "0"},
                ":one": {"N": "1"},
                ":limit": {"N": str(rate_store.LIMITS[counter])},
                ":expires": {"N": str((window + 1) * 60 + 7200)},
            },
        }
    }


def cancelled(stub: Stubber, *codes: str) -> None:
    stub.add_client_error(
        "transact_write_items",
        service_error_code="TransactionCanceledException",
        service_message="Transaction cancelled",
        modeled_fields={"CancellationReasons": [{"Code": code} for code in codes]},
    )


def test_limits_and_policies_are_the_canonical_c5_values() -> None:
    counters = load_contract("c5-money-edge-v1.yaml")["rate_limits"]["counters"]
    assert rate_store.LIMITS == {name: c["limit_per_window"] for name, c in counters.items()}
    assert rate_store.POLICIES["transfer"] == ("transfer", *counters["transfer"]["also_consumes"])
    assert rate_store.RETENTION_SECONDS == 7200 and rate_store.WINDOW_SECONDS == 60


@pytest.mark.parametrize(
    "method,path,policy",
    [
        ("POST", "/money/v1/recipients/resolve", "recipient_lookup"),
        ("POST", "/money/v1/transfers", "transfer"),
        ("GET", "/money/v1/transfers", "other"),
        ("GET", "/money/v1/wallet", "other"),
        ("PUT", "/money/v1/wallet", "other"),
        ("POST", "/money/v1/transfers/", "other"),
        ("GET", "/money/v1/recipients/resolve", "other"),
    ],
)
def test_only_exact_c1_operations_get_their_own_budget(method, path, policy) -> None:
    assert rate_store.classify(method, path) == policy


def test_protected_subject_is_keyed_environment_bound_and_never_the_raw_sub() -> None:
    dev = rate_store.protected_subject(KEY, "dev", SUBJECT)
    assert dev == rate_store.protected_subject(KEY, "dev", SUBJECT)
    assert dev != rate_store.protected_subject(KEY, "stg", SUBJECT)
    assert dev != rate_store.protected_subject(b"x" * 64, "dev", SUBJECT)
    assert dev != rate_store.protected_subject(KEY, "dev", SUBJECT + "x")
    assert SUBJECT not in dev and len(dev) == 64


def test_lookup_charges_one_conditional_counter_in_the_server_minute() -> None:
    client, stub = stubbed()
    stub.add_response("transact_write_items", {}, {"TransactItems": [update("recipient_lookup")]})
    with stub:
        assert limiter(client).consume(SUBJECT, "recipient_lookup") == Decision(True, 60)
    stub.assert_no_pending_responses()


def test_transfer_charges_its_own_and_the_lookup_counter_in_one_transaction() -> None:
    client, stub = stubbed()
    expected = [update("transfer"), update("recipient_lookup")]
    stub.add_response("transact_write_items", {}, {"TransactItems": expected})
    with stub:
        assert limiter(client).consume(SUBJECT, "transfer").admitted


@pytest.mark.parametrize(
    "reasons", [("ConditionalCheckFailed",), ("None", "ConditionalCheckFailed")]
)
def test_a_failed_condition_on_any_counter_refuses_without_retrying(reasons) -> None:
    client, stub = stubbed()
    cancelled(stub, *reasons)
    sleep = Mock()
    with stub:
        decision = limiter(client, clock=659.2, sleep=sleep).consume(SUBJECT, "transfer")
    assert decision == Decision(False, 1)
    sleep.assert_not_called()


def test_contention_is_retried_a_bounded_number_of_times() -> None:
    client, stub = stubbed()
    cancelled(stub, "TransactionConflict")
    stub.add_response("transact_write_items", {})
    sleep = Mock()
    with stub:
        assert limiter(client, sleep=sleep).consume(SUBJECT, "other").admitted
    sleep.assert_called_once()
    client, stub = stubbed()
    for _ in range(3):
        cancelled(stub, "TransactionConflict")
    with stub, pytest.raises(RateStoreUnavailable):
        limiter(client).consume(SUBJECT, "other")
    stub.assert_no_pending_responses()


@pytest.mark.parametrize(
    "code", ["ValidationException", "ResourceNotFoundException", "AccessDeniedException"]
)
def test_store_errors_fail_closed_without_retry(code) -> None:
    client, stub = stubbed()
    stub.add_client_error("transact_write_items", service_error_code=code)
    with stub, pytest.raises(RateStoreUnavailable, match=code):
        limiter(client).consume(SUBJECT, "recipient_lookup")


def test_unreachable_store_fails_closed() -> None:
    client = Mock(
        transact_write_items=Mock(side_effect=EndpointConnectionError(endpoint_url="http://x"))
    )
    with pytest.raises(RateStoreUnavailable, match="transport"):
        limiter(client).consume(SUBJECT, "recipient_lookup")
    client.transact_write_items.assert_called_once()


def test_rotated_keys_keep_charging_the_previous_key_so_active_windows_never_reset() -> None:
    client, stub = stubbed()
    old, new = b"o" * 64, b"n" * 64
    expected = [
        update("transfer", version="2", key=new),
        update("transfer", version="1", key=old),
        update("recipient_lookup", version="2", key=new),
        update("recipient_lookup", version="1", key=old),
    ]
    stub.add_response("transact_write_items", {}, {"TransactItems": expected})
    with stub:
        assert limiter(client, keys=[("2", new), ("1", old)]).consume(SUBJECT, "transfer").admitted


def test_window_and_retry_after_follow_the_server_minute_boundary() -> None:
    client = Mock()
    limiter(client, clock=119.9).consume(SUBJECT, "other")
    before = client.transact_write_items.call_args.kwargs["TransactItems"][0]["Update"]
    assert before["Key"]["pk"]["S"].startswith("dev#other#1#")
    assert limiter(client, clock=119.9).consume(SUBJECT, "other").retry_after == 1
    limiter(client, clock=120.0).consume(SUBJECT, "other")
    after = client.transact_write_items.call_args.kwargs["TransactItems"][0]["Update"]
    assert after["Key"]["pk"]["S"].startswith("dev#other#2#")
    assert limiter(client, clock=120.0).consume(SUBJECT, "other").retry_after == 60
    assert after["ExpressionAttributeValues"][":expires"] == {"N": str(180 + 7200)}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"environment": "qa"},
        {"keys": []},
        {"keys": [("1", b"")]},
        {"keys": [("", KEY)]},
        {"max_attempts": 0},
        {"max_attempts": 9},
    ],
)
def test_invalid_configuration_is_refused(kwargs) -> None:
    with pytest.raises(ValueError):
        limiter(Mock(), **kwargs)
    with pytest.raises(ValueError):
        RateLimiter(Mock(), "", "dev", [("1", KEY)])


@pytest.mark.parametrize("subject", ["", "x" * 257, None])
def test_a_missing_or_malformed_subject_is_refused_before_any_store_call(subject) -> None:
    client = Mock()
    with pytest.raises(ValueError):
        limiter(client).consume(subject, "other")
    client.transact_write_items.assert_not_called()
