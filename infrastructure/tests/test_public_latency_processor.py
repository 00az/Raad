"""Public-boundary telemetry: privacy, completeness, windows and fault handling."""

import base64
import json
from unittest.mock import Mock

import pytest

from raad_platform.telemetry import handler


def sample(identity: str = "native-one", stamp: int = 601, duration: float = 100) -> dict:
    return handler.parse_record(
        f"{stamp}\t201\tPOST\t{identity}\t{duration / 1000}\tMiss\t/money/v1/transfers"
    )


def population(duration: float = 100) -> list[dict]:
    return [sample(f"request-{i}", 601 + (i // 20) * 300, duration) for i in range(40)]


def test_selected_field_order_and_public_duration_include_initialization() -> None:
    parsed = sample(duration=2501)
    assert parsed["durationMs"] == 2501
    assert set(parsed) == {
        "kind",
        "completedAt",
        "durationMs",
        "status",
        "method",
        "nativeId",
        "result",
        "behavior",
    }


@pytest.mark.parametrize(
    "line",
    [
        "token\temail",
        "nan\t201\tPOST\tid\t1\tMiss\t/money/v1/transfers",
        "601\t201\tPOST\tid\t-1\tMiss\t/money/v1/transfers",
        "601\t201\tPOST\tuser@example.com\t1\tMiss\t/money/v1/transfers",
    ],
)
def test_invalid_or_personal_field_values_are_rejected(line: str) -> None:
    with pytest.raises(ValueError):
        handler.parse_record(line)


def test_duplicate_delivery_does_not_inflate_unique_window_count() -> None:
    rows = population(2500)
    result = handler.evaluate(rows + rows, 1200)
    assert [window["count"] for window in result["windows"]] == [20, 20]
    assert result["state"] == "breach"


def test_conflicting_duplicate_and_malformed_marker_block_health() -> None:
    rows = population()
    with pytest.raises(handler.IncompleteTelemetry):
        handler.evaluate(rows + [{**rows[0], "durationMs": 999}], 1200)
    with pytest.raises(handler.IncompleteTelemetry):
        handler.evaluate(rows + [{"kind": "invalid"}], 1200)


@pytest.mark.parametrize(
    "rows,state",
    [
        (population(), "clear"),
        (population(2001), "breach"),
        (population()[:20], "insufficient"),
        ([], "insufficient"),
        (population()[:20] + population(2500)[20:], "insufficient"),
    ],
)
def test_two_eligible_consecutive_windows_required(rows: list[dict], state: str) -> None:
    assert handler.evaluate(rows, 1200)["state"] == state


def test_late_event_and_other_method_cannot_make_empty_window_eligible() -> None:
    rows = population()[:20] + [{**r, "completedAt": 1} for r in population()[20:]]
    assert handler.evaluate(rows, 1200)["state"] == "insufficient"
    assert (
        handler.evaluate([{**r, "method": "GET"} for r in population()], 1200)["state"]
        == "insufficient"
    )


def test_acceptance_requires_all_attempts_joined_and_separate_phase_percentiles() -> None:
    rows = [sample(f"attempt-{i}", 601, 100) for i in range(200)]
    attempts = [
        {
            "nativeId": r["nativeId"],
            "outcome": "success",
            "phase": "idle-start" if i == 0 else "sustained",
        }
        for i, r in enumerate(rows)
    ]
    assert handler.reconcile(attempts, rows + [rows[0]])["passed"]
    with pytest.raises(handler.IncompleteTelemetry):
        handler.reconcile(attempts, rows[:-1])
    with pytest.raises(handler.IncompleteTelemetry):
        handler.reconcile([{**attempts[0], "nativeId": None}, *attempts[1:]], rows)
    with pytest.raises(handler.IncompleteTelemetry):
        handler.reconcile([{**attempts[0], "outcome": "unknown"}, *attempts[1:]], rows)


def test_query_truncation_and_failed_status_are_not_partial_success() -> None:
    client = Mock()
    client.start_query.return_value = {"queryId": "q"}
    client.get_query_results.return_value = {
        "status": "Complete",
        "nextToken": "more",
        "results": [],
    }
    with pytest.raises(handler.IncompleteTelemetry):
        handler.collect_query(client, "group", 600, 1200)
    client.stop_query.assert_called_once_with(queryId="q")
    client.get_query_results.return_value = {"status": "Failed"}
    with pytest.raises(handler.IncompleteTelemetry):
        handler.collect_query(client, "group", 600, 1200)


def test_query_deadline_stops_running_query(monkeypatch) -> None:
    client = Mock()
    client.start_query.return_value = {"queryId": "q"}
    client.get_query_results.return_value = {"status": "Running"}
    ticks = iter([0, 1, 10])
    monkeypatch.setattr(handler.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(handler.time, "sleep", lambda _: None)
    with pytest.raises(handler.IncompleteTelemetry):
        handler.collect_query(client, "group", 600, 1200)
    client.stop_query.assert_called_once()


def test_repeated_publication_uses_identical_source_window_timestamps() -> None:
    client = Mock()
    snapshot = handler.evaluate(population(), 1200)
    handler._publish(snapshot, client, "dev")
    handler._publish(snapshot, client, "dev")
    one, two = client.put_metric_data.call_args_list
    assert one == two
    assert all(
        d["Name"] == "Environment" for m in one.kwargs["MetricData"] for d in m["Dimensions"]
    )


def test_ingestion_drops_raw_invalid_payload_and_handles_multiple_records(monkeypatch) -> None:
    client = Mock()
    client.exceptions.ResourceAlreadyExistsException = type("Exists", (Exception,), {})
    monkeypatch.setattr(handler.boto3, "client", lambda *args, **kwargs: client)
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("SAMPLE_LOG_GROUP", "group")
    text = "601\t201\tPOST\tid\t2.5\tMiss\t/money/v1/transfers"
    result = handler.handle(
        {
            "Records": [
                {"kinesis": {"data": base64.b64encode(text.encode()).decode()}},
                {"kinesis": {"data": base64.b64encode(b"password-user@example.com").decode()}},
            ]
        },
        None,
    )
    assert result == {"accepted": 2}
    messages = [
        json.loads(e["message"]) for e in client.put_log_events.call_args.kwargs["logEvents"]
    ]
    assert messages[1] == {"kind": "invalid", "environment": "dev"}
    assert "password" not in json.dumps(messages)


def test_scheduled_collection_failure_emits_insufficient_only(monkeypatch) -> None:
    client = Mock()
    monkeypatch.setattr(handler.boto3, "client", lambda *args, **kwargs: client)
    monkeypatch.setattr(
        handler, "collect_query", Mock(side_effect=handler.IncompleteTelemetry("missing"))
    )
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("SAMPLE_LOG_GROUP", "group")
    assert (
        handler.handle({"mode": "aggregate", "scheduledTime": "2026-11-14T01:02:00Z"}, None)[
            "state"
        ]
        == "insufficient"
    )
    assert [m["MetricName"] for m in client.put_metric_data.call_args.kwargs["MetricData"]] == [
        "PublicCollectionInsufficient"
    ]
