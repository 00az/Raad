"""Edge enforcement of C5 verified-caller limits, before anything reaches MoneyApi."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from raad_platform.edge import handler, rate_store
from raad_platform.edge.rate_store import RateLimiter

NOW = 1_800_000_010.0  # fixed server time: 50 seconds left in the window


class FakeDynamo:
    """Applies TransactWriteItems with DynamoDB's all-or-nothing condition semantics."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.calls = 0

    def transact_write_items(self, TransactItems: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls += 1
        updates = [item["Update"] for item in TransactItems]
        reasons = []
        for update in updates:
            key = update["Key"]["pk"]["S"]
            limit = int(update["ExpressionAttributeValues"][":limit"]["N"])
            reasons.append(
                {"Code": "ConditionalCheckFailed" if self.counts.get(key, 0) >= limit else "None"}
            )
        if any(reason["Code"] != "None" for reason in reasons):
            raise ClientError(
                {
                    "Error": {"Code": "TransactionCanceledException", "Message": "cancelled"},
                    "CancellationReasons": reasons,
                },
                "TransactWriteItems",
            )
        for update in updates:
            key = update["Key"]["pk"]["S"]
            self.counts[key] = self.counts.get(key, 0) + 1
        return {}


@pytest.fixture
def store(monkeypatch) -> FakeDynamo:
    fake = FakeDynamo()
    monkeypatch.setattr(handler, "_origin_secret", lambda: "a" * 64)
    monkeypatch.setenv("ORIGIN_SECRET_ARN", "origin-secret")
    monkeypatch.setattr(
        handler,
        "_rate_limiter",
        lambda: RateLimiter(fake, "table", "dev", [("1", b"k" * 64)], clock=lambda: NOW),
    )
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "https://svc.on.aws/"))
    monkeypatch.setattr(handler, "_protected_correlation", lambda _: ("1", "hmac"))
    credentials = Mock(
        get_frozen_credentials=Mock(return_value=Mock(access_key="a", secret_key="s", token="t"))
    )
    monkeypatch.setattr(
        handler.boto3,
        "Session",
        lambda: Mock(get_credentials=lambda: credentials, region_name="us-east-1"),
    )
    return fake


@pytest.fixture
def upstream(monkeypatch) -> Mock:
    send = Mock(
        return_value=Mock(status_code=200, headers={"content-type": "application/json"}, text="{}")
    )
    monkeypatch.setattr(handler.requests, "request", send)
    return send


def call(method: str, path: str, subject: str, monkeypatch, **headers: str) -> dict[str, Any]:
    monkeypatch.setattr(handler, "_verify", lambda *_: subject)
    request = {
        "headers": {
            "X-Raad-Origin": "a" * 64,
            "Authorization": "Bearer signed-token",
            "X-Correlation-Id": "corr-1",
            "Idempotency-Key": "financial-key-1",
            **headers,
        },
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "rawQueryString": "",
        "body": "{}" if method != "GET" else None,
    }
    return handler.handle(request, None)


def statuses(n: int, method: str, path: str, subject: str, monkeypatch) -> list[int]:
    return [call(method, path, subject, monkeypatch)["statusCode"] for _ in range(n)]


def test_lookups_are_limited_to_thirty_per_minute_per_verified_caller(
    store, upstream, monkeypatch
) -> None:
    assert statuses(30, "POST", "/money/v1/recipients/resolve", "alice", monkeypatch) == [200] * 30
    refused = call("POST", "/money/v1/recipients/resolve", "alice", monkeypatch)
    assert refused["statusCode"] == 429
    assert refused["headers"]["retry-after"] == "50"
    assert refused["headers"]["x-correlation-id"] == "corr-1"
    assert refused["headers"]["cache-control"] == "no-store"
    assert json.loads(refused["body"]) == {
        "code": "RATE_LIMITED",
        "message": "Too many requests. Try again later.",
        "correlationId": "corr-1",
    }
    assert upstream.call_count == 30
    # Another caller is unaffected by the first caller's exhausted window.
    assert call("POST", "/money/v1/recipients/resolve", "bob", monkeypatch)["statusCode"] == 200


def test_sends_are_limited_to_ten_and_each_consumes_one_lookup(
    store, upstream, monkeypatch
) -> None:
    assert statuses(10, "POST", "/money/v1/transfers", "alice", monkeypatch) == [200] * 10
    assert call("POST", "/money/v1/transfers", "alice", monkeypatch)["statusCode"] == 429
    lookups = statuses(21, "POST", "/money/v1/recipients/resolve", "alice", monkeypatch)
    assert lookups == [200] * 20 + [429]


def test_reads_setup_and_history_share_sixty_per_minute(store, upstream, monkeypatch) -> None:
    mixed = [
        ("GET", "/money/v1/wallet"),
        ("PUT", "/money/v1/wallet"),
        ("GET", "/money/v1/transfers"),
    ]
    results = [call(m, p, "alice", monkeypatch)["statusCode"] for m, p in mixed * 20]
    assert results == [200] * 60
    assert call("GET", "/money/v1/wallet", "alice", monkeypatch)["statusCode"] == 429
    # The shared bucket is separate from the money-movement budgets.
    assert call("POST", "/money/v1/transfers", "alice", monkeypatch)["statusCode"] == 200


def test_a_refused_request_never_reaches_money_api_or_its_idempotency_key(
    store, upstream, monkeypatch
) -> None:
    statuses(10, "POST", "/money/v1/transfers", "alice", monkeypatch)
    upstream.reset_mock()
    refused = call(
        "POST", "/money/v1/transfers", "alice", monkeypatch, **{"Idempotency-Key": "new"}
    )
    assert refused["statusCode"] == 429
    upstream.assert_not_called()


def test_spoofed_identity_headers_never_choose_the_charged_caller(
    store, upstream, monkeypatch
) -> None:
    spoof = {"X-User-Id": "bob", "X-Forwarded-User": "bob", "X-Authenticated-User": "bob"}
    for _ in range(30):
        call("POST", "/money/v1/recipients/resolve", "alice", monkeypatch, **spoof)
    assert call("POST", "/money/v1/recipients/resolve", "alice", monkeypatch)["statusCode"] == 429
    assert call("POST", "/money/v1/recipients/resolve", "bob", monkeypatch)["statusCode"] == 200


def test_unauthenticated_requests_are_refused_before_any_counter_is_charged(
    store, upstream, monkeypatch
) -> None:
    request = {
        "headers": {"X-Raad-Origin": "a" * 64},
        "requestContext": {"http": {"method": "POST"}},
        "rawPath": "/money/v1/transfers",
    }
    assert handler.handle(request, None)["statusCode"] == 401
    assert store.calls == 0


def test_counter_failure_is_a_safe_503_with_retry_after_and_no_forwarding(
    monkeypatch, upstream, capsys
) -> None:
    monkeypatch.setattr(handler, "_origin_secret", lambda: "a" * 64)
    monkeypatch.setenv("ORIGIN_SECRET_ARN", "origin-secret")
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "https://svc.on.aws/"))
    failing = Mock(consume=Mock(side_effect=rate_store.RateStoreUnavailable("transport")))
    monkeypatch.setattr(handler, "_rate_limiter", lambda: failing)
    result = call("POST", "/money/v1/transfers", "alice", monkeypatch)
    assert result["statusCode"] == 503
    assert result["headers"]["retry-after"] == "1"
    assert json.loads(result["body"])["code"] == "SERVICE_UNAVAILABLE"
    upstream.assert_not_called()
    metrics = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "_aws" in line]
    assert metrics[-1]["EdgeRateStoreUnavailable"] == 1 and metrics[-1]["Edge5xx"] == 1


def test_limiter_is_built_from_the_environment_table_and_secret_keys(monkeypatch) -> None:
    monkeypatch.setenv("RATE_TABLE_NAME", "raad-stg-platform-rate-windows")
    monkeypatch.setenv("ENVIRONMENT", "stg")
    monkeypatch.setattr(handler, "_rate_keys", lambda: [("3", b"z" * 64)])
    monkeypatch.setattr(handler, "_dynamodb", None)
    factory = Mock(return_value="dynamodb-client")
    monkeypatch.setattr(handler.boto3, "client", factory)
    built = handler._rate_limiter()
    assert (built.client, built.table, built.environment, built.keys) == (
        "dynamodb-client",
        "raad-stg-platform-rate-windows",
        "stg",
        (("3", b"z" * 64),),
    )
    assert factory.call_args.kwargs["config"].retries["total_max_attempts"] == 1


def test_missing_table_configuration_fails_closed(monkeypatch, upstream) -> None:
    monkeypatch.setattr(handler, "_origin_secret", lambda: "a" * 64)
    monkeypatch.setenv("ORIGIN_SECRET_ARN", "origin-secret")
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "https://svc.on.aws/"))
    monkeypatch.delenv("RATE_TABLE_NAME", raising=False)
    monkeypatch.setattr(handler, "_rate_keys", lambda: [("1", b"k" * 64)])
    assert call("GET", "/money/v1/wallet", "alice", monkeypatch)["statusCode"] == 503
    upstream.assert_not_called()


def test_rate_keys_hold_current_and_previous_versions_and_are_cached(monkeypatch) -> None:
    handler._rate_key_cache = None
    monkeypatch.setenv("CORRELATION_SECRET_ARN", "secret-arn")
    secret = {"version": "2", "key": "n" * 64, "previousVersion": "1", "previousKey": "o" * 64}
    client = Mock(get_secret_value=Mock(return_value={"SecretString": json.dumps(secret)}))
    monkeypatch.setattr(handler.boto3, "client", lambda *a, **k: client)
    clock = iter([0.0, 10.0, 61.0])
    monkeypatch.setattr(handler.time, "monotonic", lambda: next(clock))
    expected = [("2", b"n" * 64), ("1", b"o" * 64)]
    assert handler._rate_keys() == expected
    assert handler._rate_keys() == expected
    assert client.get_secret_value.call_count == 1
    handler._rate_keys()
    assert client.get_secret_value.call_count == 2
    handler._rate_key_cache = None


@pytest.mark.parametrize(
    "secret",
    [
        {"version": "1", "key": "short"},
        {"version": "1"},
        {"version": "1", "key": "k" * 64, "previousVersion": "0"},
        ["not", "an", "object"],
    ],
)
def test_unusable_rate_key_material_is_refused(monkeypatch, secret) -> None:
    handler._rate_key_cache = None
    monkeypatch.setenv("CORRELATION_SECRET_ARN", "secret-arn")
    client = Mock(get_secret_value=Mock(return_value={"SecretString": json.dumps(secret)}))
    monkeypatch.setattr(handler.boto3, "client", lambda *a, **k: client)
    with pytest.raises((ValueError, TypeError)):
        handler._rate_keys()
    assert handler._rate_key_cache is None
