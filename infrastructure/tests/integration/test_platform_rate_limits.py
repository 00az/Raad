"""Real local DynamoDB boundary for platform rate windows (no mocks, no AWS).

Run from infrastructure/ after `docker compose -f docker-compose.yml up -d --wait rate-dynamodb`:

    RAAD_RATE_DYNAMODB_ENDPOINT=http://127.0.0.1:8002 \
        uv run pytest tests/integration/test_platform_rate_limits.py --no-cov -q

A missing endpoint fails this module instead of skipping it. Only loopback endpoints are
accepted, credentials are fixed dummy values, and each run uses its own table, removed at the end.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import urlsplit

import boto3
import pytest
from botocore.config import Config

from raad_platform.edge import rate_store
from raad_platform.edge.rate_store import Decision, RateLimiter, RateStoreUnavailable

KEY = b"integration-key-" * 4
NOW = 1_800_000_000.0  # A fixed server minute well inside one window.


def local_endpoint() -> str:
    endpoint = os.environ.get("RAAD_RATE_DYNAMODB_ENDPOINT", "")
    if not endpoint:
        pytest.fail(
            "Local rate store unavailable: start `docker compose up -d --wait rate-dynamodb` "
            "and set RAAD_RATE_DYNAMODB_ENDPOINT=http://127.0.0.1:8002",
            pytrace=False,
        )
    parts = urlsplit(endpoint)
    if parts.scheme != "http" or parts.hostname not in {"127.0.0.1", "localhost"}:
        pytest.fail("Only a loopback DynamoDB Local endpoint is allowed", pytrace=False)
    return endpoint


def local_client(endpoint: str, **config: Any) -> Any:
    return boto3.client(
        "dynamodb",
        endpoint_url=endpoint,
        region_name="us-east-1",
        aws_access_key_id="local",
        aws_secret_access_key="local",
        config=Config(retries={"total_max_attempts": 1}, **config),
    )


@pytest.fixture(scope="module")
def table() -> Iterator[tuple[Any, str]]:
    client = local_client(local_endpoint())
    name = f"raad-test-rate-{uuid.uuid4().hex[:12]}"
    client.create_table(
        TableName=name,
        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    client.get_waiter("table_exists").wait(TableName=name)
    try:
        yield client, name
    finally:
        client.delete_table(TableName=name)


def make(table: tuple[Any, str], clock: float = NOW, environment: str = "dev") -> RateLimiter:
    client, name = table
    return RateLimiter(client, name, environment, [("1", KEY)], clock=lambda: clock)


def stored(
    table: tuple[Any, str], subject: str, counter: str, clock: float = NOW, environment: str = "dev"
) -> int:
    client, name = table
    protected = rate_store.protected_subject(KEY, environment, subject)
    key = rate_store.counter_key(environment, counter, int(clock // 60), "1", protected)
    item = client.get_item(TableName=name, Key={"pk": {"S": key}}, ConsistentRead=True)
    return int(item.get("Item", {}).get("count", {}).get("N", "0"))


def definitive(limiter: RateLimiter, subject: str, policy: str) -> bool:
    """Retry only contention-driven unavailability, as a client would; never count it."""
    for _ in range(50):
        try:
            return limiter.consume(subject, policy).admitted
        except RateStoreUnavailable:
            time.sleep(0.01)
    raise AssertionError("store stayed unavailable under contention")


def burst(count: int, call: Callable[[], bool]) -> list[bool]:
    with ThreadPoolExecutor(max_workers=16) as pool:
        return list(pool.map(lambda _: call(), range(count)))


def subject() -> str:
    return str(uuid.uuid4())


def test_concurrent_lookups_are_admitted_exactly_up_to_the_limit(table) -> None:
    caller, limiter = subject(), make(table)
    results = burst(45, lambda: definitive(limiter, caller, "recipient_lookup"))
    assert results.count(True) == 30 and results.count(False) == 15
    assert stored(table, caller, "recipient_lookup") == 30


def test_concurrent_transfers_stop_at_ten_and_charge_lookup_in_step(table) -> None:
    caller, limiter = subject(), make(table)
    results = burst(25, lambda: definitive(limiter, caller, "transfer"))
    assert results.count(True) == 10
    assert stored(table, caller, "transfer") == 10
    assert stored(table, caller, "recipient_lookup") == 10


def test_a_refused_combined_send_consumes_neither_counter(table) -> None:
    caller, limiter = subject(), make(table)
    assert all(definitive(limiter, caller, "recipient_lookup") for _ in range(29))
    assert limiter.consume(caller, "transfer") == Decision(True, 60 - int(NOW % 60))
    # Lookup is now at 30: the next send is refused and must not charge the transfer counter.
    assert not limiter.consume(caller, "transfer").admitted
    assert stored(table, caller, "transfer") == 1
    assert stored(table, caller, "recipient_lookup") == 30


def test_a_full_transfer_budget_does_not_spend_the_lookup_budget(table) -> None:
    caller, limiter = subject(), make(table)
    assert all(limiter.consume(caller, "transfer").admitted for _ in range(10))
    assert not limiter.consume(caller, "transfer").admitted
    assert stored(table, caller, "recipient_lookup") == 10
    assert limiter.consume(caller, "recipient_lookup").admitted
    assert stored(table, caller, "recipient_lookup") == 11


def test_the_next_server_minute_opens_a_new_window_and_leaves_the_old_one(table) -> None:
    caller = subject()
    end = NOW - NOW % 60 + 59.9
    first = make(table, clock=end)
    assert all(first.consume(caller, "other").admitted for _ in range(60))
    assert first.consume(caller, "other") == Decision(False, 1)
    assert make(table, clock=end + 0.1).consume(caller, "other").admitted
    assert stored(table, caller, "other", clock=end) == 60


def test_expired_but_undeleted_items_never_reopen_or_pollute_a_window(table) -> None:
    client, name = table
    caller = subject()
    protected = rate_store.protected_subject(KEY, "dev", caller)
    window = int(NOW // 60)
    for current, count in ((window, 60), (window - 1, 60)):
        client.put_item(
            TableName=name,
            Item={
                "pk": {"S": rate_store.counter_key("dev", "other", current, "1", protected)},
                "count": {"N": str(count)},
                "expiresAt": {"N": "1"},  # TTL long past; deletion has simply not happened.
            },
        )
    assert not make(table).consume(caller, "other").admitted
    assert make(table, clock=NOW + 60).consume(caller, "other").admitted


def test_callers_and_environments_are_isolated(table) -> None:
    noisy, quiet = subject(), subject()
    dev = make(table)
    assert all(dev.consume(noisy, "recipient_lookup").admitted for _ in range(30))
    assert not dev.consume(noisy, "recipient_lookup").admitted
    assert dev.consume(quiet, "recipient_lookup").admitted
    assert make(table, environment="stg").consume(noisy, "recipient_lookup").admitted


def test_unavailable_or_missing_store_fails_closed_promptly(table) -> None:
    started = time.monotonic()
    offline = local_client("http://127.0.0.1:9", connect_timeout=0.25, read_timeout=0.25)
    with pytest.raises(RateStoreUnavailable):
        RateLimiter(offline, "absent", "dev", [("1", KEY)], clock=lambda: NOW).consume(
            subject(), "other"
        )
    assert time.monotonic() - started < 5
    client, _ = table
    with pytest.raises(RateStoreUnavailable):
        RateLimiter(client, "raad-test-missing", "dev", [("1", KEY)]).consume(subject(), "other")
