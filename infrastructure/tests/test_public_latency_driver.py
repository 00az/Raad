"""Offline safety tests for the explicit dev-only proof runner.

Fakes exercise orchestration and failure handling, never deployed acceptance.
No test creates an AWS client or sends an HTTP request.
"""

import hashlib
import hmac
import io
import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import requests

from raad_platform.telemetry import driver as module
from raad_platform.telemetry.driver import Driver
from raad_platform.telemetry.handler import IncompleteTelemetry


class Clock:
    def __init__(self):
        self.now = 1000.0

    def time(self):
        return self.now

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def response(status=201, native_id="native-1", balance=100000, **headers):
    return SimpleNamespace(
        status_code=status,
        headers={"x-amz-cf-id": native_id, **headers},
        json=lambda: {"balance": {"amountHalalas": balance}},
    )


@pytest.fixture
def runner():
    env = {
        "ENVIRONMENT": "dev",
        "MONEY_API_BASE_URL": "https://api.example.test/",
        "RAAD_EDGE_FUNCTION": "raad-dev-edge",
        "USER_POOL_ID": "us-east-1_fixture",
        "USER_POOL_CLIENT_ID": "fixture-client",
        "TEST_USERS_SECRET_ARN": "fixture-secret",
        "RAAD_SAMPLE_LOG_GROUP": "fixture-samples",
        "RAAD_TELEMETRY_FUNCTION": "raad-dev-telemetry",
        "RAAD_PUBLIC_LATENCY_ALARM": "fixture-alarm",
        "CORRELATION_SECRET_ARN": "correlation-secret",
        "RAAD_INVESTIGATION_LOG_GROUPS": "edge-log,money-log",
    }
    clients = {
        name: MagicMock()
        for name in ("lambda", "logs", "cognito-idp", "secretsmanager", "cloudwatch")
    }
    variables = {
        "ENVIRONMENT": "dev",
        "USER_POOL_ID": env["USER_POOL_ID"],
        "CLIENT_ID": env["USER_POOL_CLIENT_ID"],
    }
    clients["lambda"].get_function_configuration.return_value = {
        "Environment": {"Variables": variables},
        "RevisionId": "config-r1",
        "LastUpdateStatus": "Successful",
    }
    clients["lambda"].get_alias.return_value = {"FunctionVersion": "4", "RevisionId": "alias-r1"}
    http = MagicMock()
    http.request.return_value = response()
    value = Driver(env, clients, http=http, clock=Clock())
    value.users = [
        {"email": f"user-{i}@example.test", "token": "synthetic-token"} for i in range(20)
    ]
    return value


@pytest.mark.parametrize(
    "url,environment",
    [
        ("http://api.example.test", "dev"),
        ("https://api.example.test/path", "dev"),
        ("https://user:password@api.example.test", "dev"),
        ("https://api.example.test?token=secret", "dev"),
        ("https://api.example.test#fragment", "dev"),
        ("https://api.example.test", "prd"),
    ],
)
def test_rejects_non_dev_or_unsafe_origin(runner, url, environment):
    with pytest.raises(ValueError, match="dev HTTPS"):
        Driver({**runner.env, "MONEY_API_BASE_URL": url, "ENVIRONMENT": environment}, {})


def test_deployed_guard_checks_latest_and_active_version(runner):
    runner.guard()
    calls = runner.clients["lambda"].get_function_configuration.call_args_list
    assert len(calls) == 2
    assert calls[1].kwargs["Qualifier"] == "4"


@pytest.mark.parametrize("location", ["latest", "active"])
def test_guard_refuses_preexisting_fault_in_either_version(runner, location):
    good = runner.clients["lambda"].get_function_configuration.return_value
    bad = {
        **good,
        "Environment": {
            "Variables": {**good["Environment"]["Variables"], "U1_DEV_FAULT_MODE": "origin"}
        },
    }
    runner.clients["lambda"].get_function_configuration.side_effect = (
        [bad] if location == "latest" else [good, bad]
    )
    with pytest.raises(ValueError, match="fault"):
        runner.guard()
    runner.clients["lambda"].update_function_configuration.assert_not_called()


def test_guard_refuses_wrong_identity_before_mutation(runner):
    runner.clients["lambda"].get_function_configuration.return_value["Environment"]["Variables"][
        "CLIENT_ID"
    ] = "other"
    with pytest.raises(ValueError, match="identity mismatch"):
        runner.guard()
    runner.clients["lambda"].update_alias.assert_not_called()


def test_call_bounds_http_preserves_headers_and_disables_redirects(runner):
    runner.call("POST", "/money/v1/transfers", runner.users[0], headers={"Idempotency-Key": "key"})
    call = runner.http.request.call_args
    assert call.args == ("POST", "https://api.example.test/money/v1/transfers")
    assert call.kwargs["allow_redirects"] is False
    assert call.kwargs["timeout"].total == 15
    assert call.kwargs["headers"] == {
        "Authorization": "Bearer synthetic-token",
        "Idempotency-Key": "key",
    }


@pytest.mark.parametrize(
    "status,outcome", [(201, "success"), (409, "refusal"), (422, "refusal"), (503, "technical")]
)
def test_transfer_records_safe_outcome_and_never_retries(runner, status, outcome):
    runner.http.request.return_value = response(
        status, **{"x-u1-adapter-ms": "12", "x-u1-adapter-version": "5"}
    )
    record = runner.transfer(0, "fault-proof", probe=True)
    assert record["outcome"] == outcome
    assert runner.stop.is_set() == (status != 201)
    assert runner.http.request.call_count == 1
    assert record["adapterMs"] == 12
    assert record["adapterVersion"] == "5"
    assert "synthetic-token" not in json.dumps(record)
    assert "example.test" not in json.dumps(record)


def test_transfer_retains_unknown_network_outcome_without_retry(runner):
    runner.http.request.side_effect = requests.Timeout("synthetic timeout")
    record = runner.transfer(0, "sustained")
    assert record["outcome"] == "unknown"
    assert record["nativeId"] is None
    assert runner.stop.is_set()
    assert runner.attempts == [record]
    assert runner.http.request.call_count == 1


def test_transfer_stops_when_native_response_id_is_missing(runner):
    runner.http.request.return_value = response(native_id=None)
    runner.transfer(0, "sustained")
    assert runner.stop.is_set()


def test_prepare_creates_fresh_confirmed_identities_through_api(runner):
    runner.users = []
    runner.clients["secretsmanager"].get_secret_value.return_value = {
        "SecretString": json.dumps(
            {"users": [{"email": "fixture+old@example.test", "password": "synthetic-password"}]}
        )
    }
    runner.clients["cognito-idp"].admin_initiate_auth.return_value = {
        "AuthenticationResult": {"AccessToken": "synthetic-token"}
    }
    runner.http.request.return_value = response(201)
    runner.prepare()
    assert len(runner.users) == 100
    assert len({u["email"] for u in runner.users}) == 100
    assert runner.clients["cognito-idp"].admin_create_user.call_count == 100
    assert runner.http.request.call_count == 100
    assert all(c.args[0] == "PUT" for c in runner.http.request.call_args_list)


def test_prepare_rejects_reused_or_unfunded_wallet(runner):
    runner.clients["secretsmanager"].get_secret_value.return_value = {
        "SecretString": json.dumps(
            {"users": [{"email": "fixture@example.test", "password": "synthetic"}]}
        )
    }
    runner.clients["cognito-idp"].admin_initiate_auth.return_value = {
        "AuthenticationResult": {"AccessToken": "synthetic-token"}
    }
    runner.http.request.return_value = response(200, balance=99999)
    with pytest.raises(RuntimeError, match="readiness"):
        runner.prepare()
    assert runner.http.request.call_count == 1


def test_cycle_performs_representative_read_resolve_transfer_history(runner):
    runner.http.request.side_effect = [response(200), response(200), response(201), response(200)]
    runner.cycle(0, "sustained")
    assert [call.args[0] for call in runner.http.request.call_args_list] == [
        "GET",
        "POST",
        "POST",
        "GET",
    ]
    assert len(runner.attempts) == 1


@pytest.mark.parametrize(
    "results,error",
    [
        ([response(503)], "prerequisite"),
        ([response(200, balance=99)], "funding exhausted"),
        ([response(200), response(200), response(201), response(503)], "history"),
    ],
)
def test_cycle_fails_visibly_without_resetting_balances(runner, results, error):
    runner.http.request.side_effect = results
    with pytest.raises(RuntimeError, match=error):
        runner.cycle(0, "sustained")
    assert runner.http.request.call_count == len(results)


def attempt(native_id="native-1"):
    return {"nativeId": native_id, "startedAt": 1000, "completedAt": 1001, "status": 201}


def sample(native_id="native-1", status=201):
    return {
        "nativeId": native_id,
        "status": status,
        "method": "POST",
        "durationMs": 100,
        "completedAt": 1001,
        "kind": "sample",
    }


def test_wait_records_reconciles_late_delivery_within_one_deadline(runner, monkeypatch):
    query = MagicMock(side_effect=[[], [sample()]])
    monkeypatch.setattr(module, "collect_query", query)
    assert runner.wait_records([attempt()]) == [sample()]
    assert query.call_count == 2
    assert runner.clock.now == 1002


@pytest.mark.parametrize(
    "attempts,rows,error",
    [
        ([attempt(None)], [], "missing response"),
        ([attempt(), attempt()], [], "duplicated"),
        ([attempt()], [sample("other")], "unexpected public"),
        ([attempt()], [sample(status=500)], "status conflicts"),
    ],
)
def test_wait_records_rejects_incomplete_or_conflicting_population(
    runner, monkeypatch, attempts, rows, error
):
    monkeypatch.setattr(module, "collect_query", lambda *_args: rows)
    with pytest.raises(IncompleteTelemetry, match=error):
        runner.wait_records(attempts)


def test_wait_records_missing_delivery_expires_without_resubmission(runner, monkeypatch):
    monkeypatch.setattr(module, "collect_query", lambda *_args: [])
    with pytest.raises(IncompleteTelemetry, match="120 seconds"):
        runner.wait_records([attempt()])
    assert runner.clock.now <= 1120
    runner.http.request.assert_not_called()


@pytest.mark.parametrize("state", ["Failed", "InProgress"])
def test_await_update_bounds_failure_and_timeout(runner, state):
    runner.clients["lambda"].get_function_configuration.return_value = {"LastUpdateStatus": state}
    with pytest.raises(RuntimeError, match="failed or timed out"):
        runner.await_update()
    assert runner.clock.now <= 1120


def test_fault_restores_latest_before_routing_and_restores_alias_on_error(runner):
    client = runner.clients["lambda"]
    client.publish_version.return_value = {"Version": "5"}
    client.update_alias.return_value = {"RevisionId": "alias-r2"}
    with pytest.raises(RuntimeError, match="probe failed"), runner.fault("origin") as version:
        assert version == "5"
        assert client.update_function_configuration.call_count == 2
        raise RuntimeError("probe failed")
    assert client.update_alias.call_args.kwargs == {
        "FunctionName": "raad-dev-edge",
        "Name": "live",
        "RevisionId": "alias-r2",
        "FunctionVersion": "4",
    }
    restore = client.update_function_configuration.call_args.kwargs
    assert "U1_DEV_FAULT_MODE" not in restore["Environment"]["Variables"]


def test_fault_refuses_overwrite_when_cleanup_detects_concurrent_change(runner):
    client = runner.clients["lambda"]
    original = client.get_function_configuration.return_value
    client.get_function_configuration.side_effect = [original] * 5
    client.publish_version.side_effect = RuntimeError("publish failed")
    with (
        pytest.raises(RuntimeError, match="concurrent configuration change"),
        runner.fault("init"),
    ):
        pytest.fail("failed publication must not route")
    assert client.update_function_configuration.call_count == 1
    client.update_alias.assert_not_called()


def test_investigation_uses_current_and_previous_hmac_and_safe_projection(runner):
    runner.clients["secretsmanager"].get_secret_value.return_value = {
        "SecretString": json.dumps(
            {"key": "synthetic-current", "previous": {"material": "synthetic-old"}}
        )
    }
    logs = runner.clients["logs"]
    logs.start_query.return_value = {"queryId": "query-1"}
    logs.get_query_results.return_value = {
        "status": "Complete",
        "results": [
            [{"field": "component", "value": "edge"}, {"field": "token", "value": "never-export"}]
        ],
    }
    assert runner.investigate("synthetic-correlation") == [{"component": "edge"}]
    query = logs.start_query.call_args.kwargs["queryString"]
    assert "synthetic-correlation" not in query
    for key in ("synthetic-current", "synthetic-old"):
        assert hmac.new(key.encode(), b"synthetic-correlation", hashlib.sha256).hexdigest() in query
    logs.stop_query.assert_called_once_with(queryId="query-1")


@pytest.mark.parametrize(
    "result",
    [
        {"status": "Complete", "results": [], "nextToken": "more"},
        {"status": "Failed"},
        {"status": "Running"},
    ],
)
def test_investigation_fails_closed_on_limits_failure_or_timeout(runner, result):
    runner.clients["secretsmanager"].get_secret_value.return_value = {
        "SecretString": json.dumps({"key": "synthetic-current"})
    }
    logs = runner.clients["logs"]
    logs.start_query.return_value = {"queryId": "query-1"}
    logs.get_query_results.return_value = result
    with pytest.raises(IncompleteTelemetry):
        runner.investigate("synthetic-correlation")
    logs.stop_query.assert_called_once()


def test_window_pair_verifies_deployed_aggregate_native_windows_and_alarm(runner, monkeypatch):
    runner.transfer = MagicMock(return_value=attempt())
    runner.wait_records = MagicMock(return_value=[sample()])
    runner.clients["lambda"].invoke.return_value = {"Payload": io.BytesIO(b'{"state":"breach"}')}
    runner.clients["cloudwatch"].describe_alarms.return_value = {
        "MetricAlarms": [{"StateValue": "ALARM"}]
    }
    monkeypatch.setattr(module, "collect_query", lambda *_args: [sample()])
    monkeypatch.setattr(module, "evaluate", lambda *_args: {"state": "breach"})
    assert runner.window_pair("breach") == {"state": "breach"}
    assert runner.transfer.call_count == 40
    assert runner.wait_records.call_count == 2


def test_fault_proof_requires_fresh_version_and_native_initialization_duration(runner):
    runner.guard = MagicMock()
    runner.prepare = MagicMock()

    @contextmanager
    def fake_fault(_mode):
        yield "5"

    runner.fault = fake_fault
    runner.transfer = MagicMock(
        return_value={"adapterVersion": "5", "adapterMs": 10, "outcome": "success"}
    )
    runner.wait_records = MagicMock(return_value=[{"durationMs": 2200}])
    runner.window_pair = MagicMock(side_effect=[{"state": "breach"}, {"state": "clear"}])
    assert runner.fault_proof()["faultsRemoved"] is True
    runner.window_pair.assert_any_call("breach")
    runner.window_pair.assert_any_call("clear")
    runner.transfer.return_value["adapterVersion"] = "4"
    with pytest.raises(IncompleteTelemetry, match="initialization"):
        runner.fault_proof()


def test_cli_requires_explicit_execution_before_client_creation(monkeypatch, tmp_path):
    client = MagicMock(side_effect=AssertionError("must not create client"))
    monkeypatch.setattr(module.boto3, "client", client)
    monkeypatch.setattr("sys.argv", ["driver", "load", "--output", str(tmp_path / "result.json")])
    with pytest.raises(SystemExit) as error:
        module.main()
    assert error.value.code == 2
    client.assert_not_called()
