"""Collect native public durations; never substitute a Lambda handler timer.

CloudFront emits selected fields in its documented order, not configuration
order. Log delivery is best effort: observed windows cannot prove live coverage.
"""

from __future__ import annotations

import base64
import json
import math
import os
import re
import time
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

FIELDS = (
    "timestamp",
    "sc-status",
    "cs-method",
    "x-edge-request-id",
    "time-taken",
    "x-edge-result-type",
    "cache-behavior-path-pattern",
)
PATH = "/money/v1/transfers"
RESULTS = {
    "Hit",
    "RefreshHit",
    "Miss",
    "LimitExceeded",
    "CapacityExceeded",
    "Error",
    "Redirect",
    "LambdaExecutionError",
}
ID_PATTERN = re.compile(r"^[A-Za-z0-9_+=/-]{1,256}$")
MAX_RECORDS = 9999
WINDOW = 300
CONFIG = Config(connect_timeout=0.25, read_timeout=1, retries={"total_max_attempts": 1})


class IncompleteTelemetry(ValueError):
    """Insufficient evidence; cannot emit a healthy evaluation."""


def parse_record(line: str) -> dict[str, Any]:
    """Normalize only the seven approved fields, without logging raw input."""
    fields = line.rstrip("\r\n").split("\t")
    if len(fields) != len(FIELDS):
        raise IncompleteTelemetry("invalid field count")
    row = dict(zip(FIELDS, fields, strict=True))
    stamp, duration = float(row["timestamp"]), float(row["time-taken"]) * 1000
    status = int(row["sc-status"])
    if not math.isfinite(stamp) or stamp <= 0 or not math.isfinite(duration) or duration < 0:
        raise IncompleteTelemetry("invalid time")
    if not 0 <= status <= 599 or row["cs-method"] not in {
        "GET",
        "POST",
        "PUT",
        "HEAD",
        "OPTIONS",
        "PATCH",
        "DELETE",
    }:
        raise IncompleteTelemetry("invalid category")
    if not ID_PATTERN.fullmatch(row["x-edge-request-id"]):
        raise IncompleteTelemetry("invalid native id")
    if row["cache-behavior-path-pattern"] != PATH or row["x-edge-result-type"] not in RESULTS:
        raise IncompleteTelemetry("unclassified response")
    return {
        "kind": "sample",
        "completedAt": stamp,
        "durationMs": duration,
        "status": status,
        "method": row["cs-method"],
        "nativeId": row["x-edge-request-id"],
        "result": row["x-edge-result-type"],
        "behavior": PATH,
    }


def unique_samples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conflicting duplicate identities invalidate the complete population."""
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("kind") != "sample":
            raise IncompleteTelemetry("collector rejected data")
        identity = row["nativeId"]
        if identity in unique and unique[identity] != row:
            raise IncompleteTelemetry("conflicting duplicate")
        unique[identity] = row
    return list(unique.values())


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise IncompleteTelemetry("no observations")
    return sorted(values)[math.ceil(len(values) * quantile) - 1]


def evaluate(rows: list[dict[str, Any]], end: int) -> dict[str, Any]:
    """Evaluate two completed event windows; mixed pairs stay insufficient."""
    if end % WINDOW:
        raise ValueError("window boundary required")
    observations = unique_samples(rows)
    windows: list[dict[str, Any]] = []
    for start in (end - 2 * WINDOW, end - WINDOW):
        values = [
            r["durationMs"]
            for r in observations
            if r["method"] == "POST" and start <= r["completedAt"] < start + WINDOW
        ]
        count = len(values)
        fraction = sum(value > 2000 for value in values) / count if count else None
        windows.append(
            {
                "start": start,
                "count": count,
                "slowFraction": fraction,
                "p95": percentile(values, 0.95) if values else None,
            }
        )
    eligible = all(window["count"] >= 20 for window in windows)
    slow = [window["slowFraction"] > 0.05 for window in windows] if eligible else []
    state = (
        "breach" if slow == [True, True] else "clear" if slow == [False, False] else "insufficient"
    )
    return {"end": end, "windows": windows, "state": state, "coverage": "unknown"}


def reconcile(attempts: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Acceptance is a one-to-one response/native-record join, including failures."""
    samples = {row["nativeId"]: row for row in unique_samples(rows) if row["method"] == "POST"}
    identities = [attempt.get("nativeId") for attempt in attempts]
    if not attempts or None in identities or len(set(identities)) != len(identities):
        raise IncompleteTelemetry("missing response or duplicate attempt")
    if set(identities) != set(samples):
        raise IncompleteTelemetry("incomplete response reconciliation")
    if any(
        attempt.get("outcome") != "success"
        or attempt.get("phase") not in {"idle-start", "sustained"}
        or samples[attempt["nativeId"]]["status"] != 201
        for attempt in attempts
    ):
        raise IncompleteTelemetry("unsuccessful or unclassified attempt")
    combined = [samples[identity]["durationMs"] for identity in identities]
    sustained = [
        samples[attempt["nativeId"]]["durationMs"]
        for attempt in attempts
        if attempt["phase"] == "sustained"
    ]
    if len(combined) < 200 or not any(a["phase"] == "idle-start" for a in attempts):
        raise IncompleteTelemetry("acceptance population incomplete")
    return {
        "count": len(combined),
        "combinedP95": percentile(combined, 0.95),
        "sustainedP95": percentile(sustained, 0.95),
        "passed": percentile(combined, 0.95) <= 2000 and percentile(sustained, 0.95) <= 2000,
    }


def collect_query(client: Any, group: str, start: int, end: int) -> list[dict[str, Any]]:
    """Query full ingestion history by event time, with a hard local deadline."""
    deadline = time.monotonic() + 8
    query = (
        "fields @message | filter completedAt >= "
        + str(start)
        + " and completedAt < "
        + str(end)
        + " or kind = 'invalid' | limit 10000"
    )
    query_id = client.start_query(
        logGroupName=group,
        startTime=max(0, start - 86400),
        endTime=int(time.time()) + 1,
        queryString=query,
        limit=10000,
    )["queryId"]
    try:
        while time.monotonic() < deadline:
            response = client.get_query_results(queryId=query_id)
            if response["status"] == "Complete":
                if response.get("nextToken") or len(response.get("results", [])) > MAX_RECORDS:
                    raise IncompleteTelemetry("query limit reached")
                rows = [
                    json.loads(
                        next(field["value"] for field in row if field["field"] == "@message")
                    )
                    for row in response.get("results", [])
                ]
                return rows
            if response["status"] not in {"Scheduled", "Running"}:
                raise IncompleteTelemetry("query did not complete")
            time.sleep(0.1)
        raise IncompleteTelemetry("query deadline exceeded")
    finally:
        client.stop_query(queryId=query_id)


def _publish(snapshot: dict[str, Any], client: Any, environment: str) -> None:
    dimensions = [{"Name": "Environment", "Value": environment}]
    metrics: list[dict[str, Any]] = []
    for window in snapshot["windows"]:
        stamp = datetime.fromtimestamp(window["start"], UTC)
        values = {"PublicObservedCount": window["count"]}
        if window["p95"] is not None:
            values.update(
                {"PublicP95Ms": window["p95"], "PublicSlowFraction": window["slowFraction"]}
            )
        metrics.extend(
            {"MetricName": name, "Value": value, "Timestamp": stamp, "Dimensions": dimensions}
            for name, value in values.items()
        )
    if snapshot["state"] != "insufficient":
        metrics.append(
            {
                "MetricName": "PublicSlowPair",
                "Value": int(snapshot["state"] == "breach"),
                "Timestamp": datetime.fromtimestamp(snapshot["end"], UTC),
                "Dimensions": dimensions,
            }
        )
    metrics.append(
        {
            "MetricName": "PublicCollectionInsufficient",
            "Value": int(snapshot["state"] == "insufficient"),
            "Dimensions": dimensions,
        }
    )
    client.put_metric_data(Namespace="Raad/Platform", MetricData=metrics)


def handle(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Ingest or aggregate; no money service or table is reachable by this role."""
    environment = os.environ["ENVIRONMENT"]
    if event.get("mode") == "heartbeat":
        # Observation health: proves the collector runs and can publish, once a minute.
        boto3.client("cloudwatch", config=CONFIG).put_metric_data(
            Namespace="Raad/Platform",
            MetricData=[
                {
                    "MetricName": "PublicCollectorHeartbeat",
                    "Value": 1,
                    "Dimensions": [{"Name": "Environment", "Value": environment}],
                }
            ],
        )
        return {"heartbeat": True}
    if event.get("mode") == "aggregate":
        logs = boto3.client("logs", config=CONFIG)
        metrics = boto3.client("cloudwatch", config=CONFIG)
        scheduled = event.get("scheduledTime", time.time())
        if isinstance(scheduled, str):
            scheduled = datetime.fromisoformat(scheduled).timestamp()
        end = int(scheduled) // WINDOW * WINDOW
        try:
            rows = collect_query(logs, os.environ["SAMPLE_LOG_GROUP"], end - 600, end)
            snapshot = evaluate(rows, end)
            _publish(snapshot, metrics, environment)
            return snapshot
        except (ValueError, KeyError, StopIteration, RuntimeError, BotoCoreError, ClientError):
            # Insufficient evidence for the SLO, and a separate observation-health failure.
            dimensions = [{"Name": "Environment", "Value": environment}]
            metrics.put_metric_data(
                Namespace="Raad/Platform",
                MetricData=[
                    {
                        "MetricName": "PublicCollectionInsufficient",
                        "Value": 1,
                        "Dimensions": dimensions,
                    },
                    {
                        "MetricName": "PublicCollectionFailures",
                        "Value": 1,
                        "Dimensions": dimensions,
                    },
                ],
            )
            return {"state": "insufficient", "coverage": "unknown"}
    logs = boto3.client("logs", config=CONFIG)
    stream = os.environ.get("AWS_LAMBDA_LOG_STREAM_NAME", "samples")
    try:
        logs.create_log_stream(logGroupName=os.environ["SAMPLE_LOG_GROUP"], logStreamName=stream)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    events = []
    for record in event.get("Records", []):
        try:
            payload = base64.b64decode(record["kinesis"]["data"], validate=True).decode("utf-8")
            rows = [parse_record(line) for line in payload.splitlines()]
            if not rows:
                raise IncompleteTelemetry("empty record")
        except (ValueError, KeyError, UnicodeError):
            rows = [{"kind": "invalid"}]
        for row in rows:
            row["environment"] = environment
            events.append({"timestamp": int(time.time() * 1000), "message": json.dumps(row)})
    if events:
        logs.put_log_events(
            logGroupName=os.environ["SAMPLE_LOG_GROUP"], logStreamName=stream, logEvents=events
        )
    return {"accepted": len(events)}
