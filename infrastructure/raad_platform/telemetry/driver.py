"""Explicit dev-only public load/fault proof; credentials never enter reports.

Run from infrastructure with ``uv run python -m raad_platform.telemetry.driver``.
No operation is performed without --execute. Use an isolated dev environment:
unexpected public records invalidate reconciliation rather than being filtered out.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from urllib3.util import Timeout

from .handler import IncompleteTelemetry, collect_query, evaluate, reconcile, unique_samples

CONFIG = Config(connect_timeout=0.25, read_timeout=0.75, retries={"total_max_attempts": 1})
FAULT_KEYS = {"U1_DEV_FAULT_MODE", "U1_DEV_FAULT_RUN_ID"}


class Driver:
    def __init__(
        self, env: dict[str, str], clients: dict[str, Any], http: Any = requests, clock: Any = time
    ) -> None:
        self.env, self.clients, self.http, self.clock = env, clients, http, clock
        url = urlsplit(env["MONEY_API_BASE_URL"])
        if (
            env.get("ENVIRONMENT") != "dev"
            or url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("an explicit dev HTTPS public origin is required")
        self.base = env["MONEY_API_BASE_URL"].rstrip("/")
        self.run_id = uuid.uuid4().hex
        self.attempts: list[dict[str, Any]] = []
        self.users: list[dict[str, str]] = []
        self.stop = threading.Event()

    def guard(self) -> None:
        """Cross-check supplied identity against the deployed adapter, before mutation."""
        config = self.clients["lambda"].get_function_configuration(
            FunctionName=self.env["RAAD_EDGE_FUNCTION"]
        )
        values = config["Environment"]["Variables"]
        if (
            values.get("ENVIRONMENT") != "dev"
            or values.get("USER_POOL_ID") != self.env["USER_POOL_ID"]
            or values.get("CLIENT_ID") != self.env["USER_POOL_CLIENT_ID"]
            or FAULT_KEYS & set(values)
        ):
            raise ValueError("deployed dev identity mismatch or existing faults")
        alias = self.clients["lambda"].get_alias(
            FunctionName=self.env["RAAD_EDGE_FUNCTION"], Name="live"
        )
        active = self.clients["lambda"].get_function_configuration(
            FunctionName=self.env["RAAD_EDGE_FUNCTION"], Qualifier=alias["FunctionVersion"]
        )
        if FAULT_KEYS & set(active["Environment"]["Variables"]):
            raise ValueError("active adapter still has fault configuration")

    def call(self, method: str, path: str, user: dict[str, str], **kwargs: Any) -> Any:
        return self.http.request(
            method,
            self.base + path,
            headers={"Authorization": "Bearer " + user["token"], **kwargs.pop("headers", {})},
            timeout=Timeout(total=15, connect=0.25, read=14.75),
            allow_redirects=False,
            **kwargs,
        )

    def prepare(self) -> None:
        """100 new confirmed identities, fresh balances, no direct table seeding/reset."""
        fixture = json.loads(
            self.clients["secretsmanager"].get_secret_value(
                SecretId=self.env["TEST_USERS_SECRET_ARN"]
            )["SecretString"]
        )
        template = fixture["users"][0]
        local, domain = template["email"].rsplit("@", 1)
        cognito = self.clients["cognito-idp"]
        for number in range(100):
            email = f"{local.split('+')[0]}+u1-{self.run_id}-{number}@{domain}"
            cognito.admin_create_user(
                UserPoolId=self.env["USER_POOL_ID"],
                Username=email,
                MessageAction="SUPPRESS",
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                    {"Name": "name", "Value": "RAAD dev proof"},
                ],
            )
            cognito.admin_set_user_password(
                UserPoolId=self.env["USER_POOL_ID"],
                Username=email,
                Password=template["password"],
                Permanent=True,
            )
            auth = cognito.admin_initiate_auth(
                UserPoolId=self.env["USER_POOL_ID"],
                ClientId=self.env["USER_POOL_CLIENT_ID"],
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": template["password"]},
            )
            user = {"email": email, "token": auth["AuthenticationResult"]["AccessToken"]}
            ready = self.call("PUT", "/money/v1/wallet", user)
            if (
                ready.status_code not in {200, 201}
                or ready.json()["balance"]["amountHalalas"] != 100000
            ):
                raise RuntimeError("fresh fixture readiness failed")
            self.users.append(user)

    def transfer(self, actor: int, phase: str, probe: bool = False) -> dict[str, Any]:
        """Exactly one submission; never retry even if no HTTP response arrives."""
        started = self.clock.time()
        record: dict[str, Any] = {
            "runId": self.run_id,
            "phase": phase,
            "startedAt": started,
            "outcome": "unknown",
            "nativeId": None,
        }
        try:
            response = self.call(
                "POST",
                "/money/v1/transfers",
                self.users[actor],
                headers={
                    "Idempotency-Key": uuid.uuid4().hex,
                    **({"x-u1-probe-run": self.run_id} if probe else {}),
                },
                json={"recipientEmail": self.users[actor + 10]["email"], "amountHalalas": 100},
            )
            record.update(
                nativeId=response.headers.get("x-amz-cf-id"),
                status=response.status_code,
                outcome="success"
                if response.status_code == 201
                else "refusal"
                if response.status_code in {409, 422}
                else "technical",
            )
            if probe:
                record["adapterMs"] = float(response.headers.get("x-u1-adapter-ms", "nan"))
                record["adapterVersion"] = response.headers.get("x-u1-adapter-version")
        except requests.RequestException:
            pass
        record.update(
            completedAt=self.clock.time(), clientElapsedMs=(self.clock.time() - started) * 1000
        )
        self.attempts.append(record)
        if record["outcome"] != "success" or not record["nativeId"]:
            self.stop.set()
        return record

    def cycle(self, actor: int, phase: str) -> None:
        user = self.users[actor]
        for method, path, kwargs in [
            ("GET", "/money/v1/wallet", {}),
            (
                "POST",
                "/money/v1/recipients/resolve",
                {"json": {"email": self.users[actor + 10]["email"]}},
            ),
        ]:
            response = self.call(method, path, user, **kwargs)
            if response.status_code != 200:
                raise RuntimeError("representative journey prerequisite failed")
            if method == "GET" and response.json()["balance"]["amountHalalas"] < 100:
                raise RuntimeError("fixture funding exhausted; never reset or top up")
        self.transfer(actor, phase)
        if (
            not self.stop.is_set()
            and self.call("GET", "/money/v1/transfers", user).status_code != 200
        ):
            raise RuntimeError("representative history journey failed")

    def load(self) -> dict[str, Any]:
        self.guard()
        self.prepare()
        self.clock.sleep(60)  # Retain the first response after idle; do not discard warmup.
        self.cycle(0, "idle-start")
        start = self.clock.monotonic()
        barrier = threading.Barrier(10)

        def worker(actor: int) -> None:
            barrier.wait(timeout=20)
            try:
                while not self.stop.is_set() and (
                    self.clock.monotonic() - start < 600 or len(self.attempts) < 200
                ):
                    if self.clock.monotonic() - start >= 1800:
                        raise RuntimeError("bounded population extension exhausted")
                    self.cycle(actor, "sustained")
                    self.clock.sleep(1)  # After completion; no overlapping send per actor.
            except Exception:
                self.stop.set()
                raise

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(worker, range(10)))
        duration = self.clock.monotonic() - start
        rows = self.wait_records(self.attempts)
        result = reconcile(self.attempts, rows)
        return {
            **result,
            "registered": len(self.users),
            "active": 10,
            "sustainedSeconds": duration,
            "passed": result["passed"] and duration >= 600 and not self.stop.is_set(),
        }

    def wait_records(self, attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """One deadline, including each bounded query; no population truncation/resend."""
        deadline = self.clock.monotonic() + 120
        start = int(min(a["startedAt"] for a in attempts))
        end = int(max(a["completedAt"] for a in attempts)) + 1
        identities = [a["nativeId"] for a in attempts]
        if None in identities or len(set(identities)) != len(identities):
            raise IncompleteTelemetry("missing response or duplicated response identity")
        while self.clock.monotonic() + 9 <= deadline:
            rows = unique_samples(
                collect_query(self.clients["logs"], self.env["RAAD_SAMPLE_LOG_GROUP"], start, end)
            )
            samples = [r for r in rows if r["method"] == "POST"]
            observed = {r["nativeId"] for r in samples}
            if observed - set(identities):
                raise IncompleteTelemetry("unexpected public response in isolated run")
            if observed == set(identities):
                if any(
                    r["status"] != a.get("status")
                    for r in samples
                    for a in attempts
                    if r["nativeId"] == a["nativeId"]
                ):
                    raise IncompleteTelemetry("response status conflicts with native record")
                return samples
            self.clock.sleep(min(2, max(0, deadline - self.clock.monotonic())))
        raise IncompleteTelemetry(
            "native response reconciliation incomplete after at most 120 seconds"
        )

    def await_update(self) -> dict[str, Any]:
        deadline = self.clock.monotonic() + 120
        while self.clock.monotonic() < deadline:
            config = self.clients["lambda"].get_function_configuration(
                FunctionName=self.env["RAAD_EDGE_FUNCTION"]
            )
            if config.get("LastUpdateStatus") == "Successful":
                return dict(config)
            if config.get("LastUpdateStatus") == "Failed":
                break
            self.clock.sleep(1)
        raise RuntimeError("adapter configuration update failed or timed out")

    @contextmanager
    def fault(self, mode: str) -> Iterator[str]:
        """Publish fresh dev version, restore $LATEST, then route alias; CAS every write."""
        self.guard()
        client, name = self.clients["lambda"], self.env["RAAD_EDGE_FUNCTION"]
        original = client.get_function_configuration(FunctionName=name)
        variables = original["Environment"]["Variables"]
        alias = client.get_alias(FunctionName=name, Name="live")
        configured = {**variables, "U1_DEV_FAULT_MODE": mode, "U1_DEV_FAULT_RUN_ID": self.run_id}
        routed: dict[str, Any] | None = None
        changed = False
        try:
            client.update_function_configuration(
                FunctionName=name,
                RevisionId=original["RevisionId"],
                Environment={"Variables": configured},
            )
            changed = True
            current = self.await_update()
            version = client.publish_version(FunctionName=name, RevisionId=current["RevisionId"])[
                "Version"
            ]
            client.update_function_configuration(
                FunctionName=name,
                RevisionId=current["RevisionId"],
                Environment={"Variables": variables},
            )
            self.await_update()
            changed = False
            routed = client.update_alias(
                FunctionName=name,
                Name="live",
                RevisionId=alias["RevisionId"],
                FunctionVersion=version,
            )
            yield str(version)
        finally:
            if routed is not None:
                client.update_alias(
                    FunctionName=name,
                    Name="live",
                    RevisionId=routed["RevisionId"],
                    FunctionVersion=alias["FunctionVersion"],
                )
            if changed:
                current = self.await_update()
                if current["Environment"]["Variables"] != configured:
                    raise RuntimeError(
                        "concurrent configuration change; automatic overwrite refused"
                    )
                client.update_function_configuration(
                    FunctionName=name,
                    RevisionId=current["RevisionId"],
                    Environment={"Variables": variables},
                )
                self.await_update()

    def window_pair(self, expected: str) -> dict[str, Any]:
        start = (int(self.clock.time()) // 300 + 1) * 300
        for boundary in (start, start + 300):
            self.clock.sleep(max(0, boundary - self.clock.time()))
            batch = [self.transfer(i % 10, "fault-proof", probe=True) for i in range(20)]
            if self.stop.is_set():
                raise RuntimeError("fault proof transfer failed; do not resend")
            self.wait_records(batch)
        end = start + 600
        self.clock.sleep(max(0, end + 120 - self.clock.time()))
        # Invoke the same deployed aggregation path; it publishes the real metric gauge.
        response = self.clients["lambda"].invoke(
            FunctionName=self.env["RAAD_TELEMETRY_FUNCTION"],
            Payload=json.dumps({"mode": "aggregate", "scheduledTime": end + 120}).encode(),
        )
        snapshot = json.loads(response["Payload"].read())
        if response.get("FunctionError") or snapshot["state"] != expected:
            raise IncompleteTelemetry("deployed aggregate did not prove expected pair")
        rows = collect_query(self.clients["logs"], self.env["RAAD_SAMPLE_LOG_GROUP"], start, end)
        if evaluate(rows, end)["state"] != expected:
            raise IncompleteTelemetry("native event windows do not match aggregate")
        deadline = self.clock.monotonic() + 180
        while self.clock.monotonic() < deadline:
            alarm = self.clients["cloudwatch"].describe_alarms(
                AlarmNames=[self.env["RAAD_PUBLIC_LATENCY_ALARM"]]
            )["MetricAlarms"]
            if len(alarm) == 1 and alarm[0]["StateValue"] == (
                "ALARM" if expected == "breach" else "OK"
            ):
                return dict(snapshot)
            self.clock.sleep(5)
        raise IncompleteTelemetry("alarm transition not observed")

    def fault_proof(self) -> dict[str, Any]:
        self.guard()
        self.prepare()
        with self.fault("init") as version:
            probe = self.transfer(0, "fault-proof", probe=True)
            rows = self.wait_records([probe])
            if (
                probe.get("adapterVersion") != version
                or not probe.get("adapterMs", float("nan")) >= 0
                or rows[0]["durationMs"] - probe["adapterMs"] < 2000
                or probe["outcome"] != "success"
            ):
                raise IncompleteTelemetry("fresh initialization exclusion was not proven")
        with self.fault("origin"):
            slow = self.window_pair("breach")
        self.guard()  # Injections must be absent before any normal recovery traffic.
        clear = self.window_pair("clear")
        return {"initialization": "proven", "slow": slow, "recovery": clear, "faultsRemoved": True}

    def investigate(self, correlation: str) -> list[dict[str, Any]]:
        secret = json.loads(
            self.clients["secretsmanager"].get_secret_value(
                SecretId=self.env["CORRELATION_SECRET_ARN"]
            )["SecretString"]
        )
        profiles = [
            secret,
            *([secret["previous"]] if isinstance(secret.get("previous"), dict) else []),
        ]
        keys = [
            hmac.new(
                (p.get("key") or p["material"]).encode(), correlation.encode(), hashlib.sha256
            ).hexdigest()
            for p in profiles
        ]
        client = self.clients["logs"]
        query_id = client.start_query(
            logGroupNames=self.env["RAAD_INVESTIGATION_LOG_GROUPS"].split(","),
            startTime=int(self.clock.time()) - 14 * 86400,
            endTime=int(self.clock.time()),
            queryString="fields component, operation, result, durationMs, correlationKeyVersion | filter correlationKey in "
            + json.dumps(keys)
            + " | limit 1000",
            limit=1000,
        )["queryId"]
        deadline = self.clock.monotonic() + 8
        try:
            while self.clock.monotonic() < deadline:
                response = client.get_query_results(queryId=query_id)
                if response["status"] == "Complete":
                    if response.get("nextToken") or len(response["results"]) >= 1000:
                        raise IncompleteTelemetry("investigation limit reached")
                    allowed = {
                        "component",
                        "operation",
                        "result",
                        "durationMs",
                        "correlationKeyVersion",
                    }
                    return [
                        {f["field"]: f["value"] for f in row if f["field"] in allowed}
                        for row in response["results"]
                    ]
                if response["status"] not in {"Scheduled", "Running"}:
                    break
                self.clock.sleep(0.1)
            raise IncompleteTelemetry("investigation query incomplete")
        finally:
            client.stop_query(queryId=query_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["load", "fault-proof", "investigate"])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-dev-faults", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute or args.mode == "fault-proof" and not args.allow_dev_faults:
        parser.error("execution requires --execute; fault proof also requires --allow-dev-faults")
    clients = {
        "lambda": boto3.client("lambda", config=CONFIG),
        "logs": boto3.client("logs", config=CONFIG),
        "cognito-idp": boto3.client("cognito-idp", config=CONFIG),
        "secretsmanager": boto3.client("secretsmanager", config=CONFIG),
        "cloudwatch": boto3.client("cloudwatch", config=CONFIG),
    }
    driver = Driver(dict(os.environ), clients)
    result: Any = None
    try:
        result = (
            driver.investigate(getpass.getpass("Correlation ID (hidden): "))
            if args.mode == "investigate"
            else driver.load()
            if args.mode == "load"
            else driver.fault_proof()
        )
    except (
        RuntimeError,
        ValueError,
        KeyError,
        BotoCoreError,
        ClientError,
        requests.RequestException,
    ):
        result = {"passed": False, "state": "incomplete"}
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "runId": driver.run_id,
                    "mode": args.mode,
                    "result": result,
                    "attempts": driver.attempts,
                },
                indent=2,
            )
            + "\n"
        )
    if isinstance(result, dict) and (
        result.get("passed") is False or result.get("state") == "incomplete"
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
