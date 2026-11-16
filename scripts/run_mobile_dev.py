"""Run the two dev mobile journeys using private, short-lived fixture files."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


def fixture_defines(fixture: Any, expected_run: str) -> dict[str, dict[str, str]]:
    """Reject stale, malformed or overlapping fixtures before either device runs."""
    if not re.fullmatch(r"[0-9a-f]{12}", expected_run):
        raise ValueError("invalid fixture run")
    if not isinstance(fixture, dict) or fixture.get("runId") != expected_run:
        raise ValueError("fixture run does not match setup")
    journeys = fixture.get("journeys")
    if not isinstance(journeys, dict):
        raise TypeError("missing fixture journeys")
    seen: set[str] = set()
    result = {}
    for phase in ("api", "ios", "android"):
        pair = journeys.get(phase)
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("missing fixture pair")
        defines = {"RAAD_E2E_TARGET": "dev"}
        for role, user in zip(("SENDER", "RECIPIENT"), pair, strict=True):
            if not isinstance(user, dict):
                raise TypeError("invalid fixture account")
            email, password = user.get("email"), user.get("password")
            if (
                not isinstance(email, str)
                or not isinstance(password, str)
                or not password
                or email.count("@") != 1
                or f"+u1-{expected_run}-{phase}@" not in email
                or email.casefold() in seen
            ):
                raise ValueError("invalid or overlapping fixture account")
            seen.add(email.casefold())
            defines[f"RAAD_E2E_{role}_EMAIL"] = email
            defines[f"RAAD_E2E_{role}_PASSWORD"] = password
        if phase != "api":
            result[phase] = defines
    return result


def run_journeys(env: dict[str, str], expected_run: str, mobile: Path) -> None:
    config_path = (mobile / "config/dev.json").resolve()
    if not config_path.is_file():
        raise ValueError("mobile dev configuration missing")
    pool = env["USER_POOL_ID"]
    region = pool.split("_", 1)[0]
    expected_config = {
        "configVersion": "1.0",
        "environment": "dev",
        "apiBaseUrl": env["MONEY_API_BASE_URL"].rstrip("/"),
        "moneyBasePath": "/money/v1",
        "authIssuer": f"https://cognito-idp.{region}.amazonaws.com/{pool}",
        "authClientId": env["USER_POOL_CLIENT_ID"],
        "authAudience": env["USER_POOL_CLIENT_ID"],
    }
    if json.loads(config_path.read_text()) != expected_config:
        raise ValueError("mobile configuration does not match dev runtime")
    devices = {phase: env[f"RAAD_{phase.upper()}_DEVICE_ID"] for phase in ("ios", "android")}
    if not all(devices.values()) or len(set(devices.values())) != 2:
        raise ValueError("distinct devices required")
    client = boto3.client(
        "secretsmanager",
        config=Config(connect_timeout=0.25, read_timeout=1, retries={"total_max_attempts": 1}),
    )
    secret = client.get_secret_value(SecretId=env["TEST_USERS_SECRET_ARN"])
    fixtures = fixture_defines(json.loads(secret["SecretString"]), expected_run)
    # Flutter output can contain test account text; expose only safe phase status.
    with tempfile.TemporaryDirectory(prefix="raad-u1-mobile-") as directory:
        root = Path(directory)
        root.chmod(0o700)
        for phase in ("ios", "android"):
            path = root / f"{phase}.json"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as stream:
                json.dump(fixtures[phase], stream)
            subprocess.run(
                [
                    "flutter",
                    "test",
                    "integration_test/walking_skeleton_test.dart",
                    "-d",
                    devices[phase],
                    f"--dart-define-from-file={config_path}",
                    f"--dart-define-from-file={path}",
                    "--dart-define=RAAD_E2E_TARGET=dev",
                ],
                cwd=mobile,
                check=True,
                timeout=1200,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            path.unlink()
            print(f"{phase} dev journey passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup-result", required=True)
    parser.add_argument("--mobile", required=True, type=Path)
    args = parser.parse_args()
    try:
        setup = json.loads(args.setup_result)
        if not isinstance(setup, dict) or setup.get("prepared") != 6:
            raise ValueError("setup incomplete")
        run_journeys(dict(os.environ), setup["runId"], args.mobile.resolve())
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        BotoCoreError,
        ClientError,
        subprocess.SubprocessError,
    ):
        print("Mobile dev verification failed; temporary fixture files removed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
