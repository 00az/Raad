"""Offline checks of the host-side private fixture handoff."""

import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SPEC = importlib.util.spec_from_file_location(
    "mobile_dev_runner", Path(__file__).resolve().parents[2] / "scripts/run_mobile_dev.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
RUN = "012345abcdef"


def fixture():
    return {
        "runId": RUN,
        "journeys": {
            phase: [
                {"email": f"{role}+u1-{RUN}-{phase}@example.test", "password": "private"}
                for role in ("sender", "recipient")
            ]
            for phase in ("api", "ios", "android")
        },
    }


@pytest.fixture
def context(tmp_path, monkeypatch):
    mobile = tmp_path / "mobile"
    (mobile / "config").mkdir(parents=True)
    config = {
        "configVersion": "1.0",
        "environment": "dev",
        "apiBaseUrl": "https://dev.example.test",
        "moneyBasePath": "/money/v1",
        "authIssuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool",
        "authClientId": "client",
        "authAudience": "client",
    }
    (mobile / "config/dev.json").write_text(json.dumps(config))
    env = {
        "USER_POOL_ID": "us-east-1_pool",
        "USER_POOL_CLIENT_ID": "client",
        "MONEY_API_BASE_URL": "https://dev.example.test",
        "TEST_USERS_SECRET_ARN": "secret",
        "RAAD_IOS_DEVICE_ID": "ios-device",
        "RAAD_ANDROID_DEVICE_ID": "android-device",
    }
    client = Mock()
    client.get_secret_value.return_value = {"SecretString": json.dumps(fixture())}
    factory = Mock(return_value=client)
    monkeypatch.setattr(runner.boto3, "client", factory)
    return mobile, env, config, factory


@pytest.mark.parametrize(
    "failure",
    [None, subprocess.CalledProcessError(1, "flutter"), subprocess.TimeoutExpired("flutter", 1200)],
)
def test_private_files_arguments_and_cleanup(context, monkeypatch, failure):
    mobile, env, _, factory = context
    paths = []
    calls = []

    def invoke(command, **kwargs):
        calls.append(command)
        path = Path(command[-2].split("=", 1)[1])
        paths.append(path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
        data = json.loads(path.read_text())
        phase = "ios" if len(calls) == 1 else "android"
        assert f"-{phase}@" in data["RAAD_E2E_SENDER_EMAIL"]
        assert command[-1] == "--dart-define=RAAD_E2E_TARGET=dev"
        assert command[-3] == f"--dart-define-from-file={mobile / 'config/dev.json'}"
        assert data["RAAD_E2E_SENDER_EMAIL"] not in str(command)
        assert "PASSWORD=" not in str(command)
        assert kwargs["stdout"] == kwargs["stderr"] == subprocess.DEVNULL
        assert kwargs["cwd"] == mobile
        assert kwargs["check"] and kwargs["timeout"] == 1200
        if failure:
            raise failure

    monkeypatch.setattr(runner.subprocess, "run", invoke)
    if failure:
        with pytest.raises(subprocess.SubprocessError):
            runner.run_journeys(env, RUN, mobile)
    else:
        runner.run_journeys(env, RUN, mobile)
        assert [call[4] for call in calls] == ["ios-device", "android-device"]
    assert paths and all(not path.parent.exists() for path in paths)
    assert factory.call_args.kwargs["config"].retries["total_max_attempts"] == 1


@pytest.mark.parametrize("mutation", ["stale", "missing", "overlap", "empty", "bad-run"])
def test_rejects_invalid_pairs(mutation):
    data = fixture()
    expected = RUN
    if mutation == "stale":
        data["runId"] = "f" * 12
    elif mutation == "missing":
        del data["journeys"]["android"]
    elif mutation == "overlap":
        data["journeys"]["ios"][1] = data["journeys"]["ios"][0]
    elif mutation == "empty":
        data["journeys"]["ios"][0]["password"] = ""
    else:
        expected = "bad"
    with pytest.raises(ValueError):
        runner.fixture_defines(data, expected)


@pytest.mark.parametrize(
    "field",
    ["environment", "apiBaseUrl", "authIssuer", "authClientId", "authAudience", "moneyBasePath"],
)
def test_rejects_wrong_target_before_secret_read(context, monkeypatch, field):
    mobile, env, config, factory = context
    config[field] = "wrong"
    (mobile / "config/dev.json").write_text(json.dumps(config))
    invoke = Mock()
    monkeypatch.setattr(runner.subprocess, "run", invoke)
    with pytest.raises(ValueError):
        runner.run_journeys(env, RUN, mobile)
    factory.assert_not_called()
    invoke.assert_not_called()


def test_main_does_not_print_secret_errors(context, monkeypatch, capsys):
    mobile, env, _, factory = context
    monkeypatch.setattr(runner.os, "environ", env)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--setup-result",
            json.dumps({"prepared": 6, "runId": RUN}),
            "--mobile",
            str(mobile),
        ],
    )
    factory.side_effect = OSError("private-password")
    assert runner.main() == 1
    assert "private-password" not in capsys.readouterr().err
