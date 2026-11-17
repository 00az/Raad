"""C4/C5 writer: coherent outputs only, exact keys, safe destinations, never an AWS call."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template
from conftest import REPOSITORY, load_contract
from jsonschema import Draft202012Validator

from raad_platform import configuration
from raad_platform.configuration import ConfigurationError, build_configuration, write_configuration

ACCOUNT = "111111111111"
POOL = "us-east-1_Synthetic1"
CLIENT = "syntheticclient1"
SPEC = importlib.util.spec_from_file_location(
    "write_platform_config", REPOSITORY / "scripts/write_platform_config.py"
)
assert SPEC and SPEC.loader
writer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(writer)


def outputs(environment: str = "dev") -> dict[str, Any]:
    verifier = configuration.verifier_config(environment, "us-east-1", POOL, CLIENT)
    return {
        f"RaadIdentity-{environment}": {
            "EnvironmentOutput": environment,
            "UserPoolIdOutput": POOL,
            "UserPoolClientIdOutput": CLIENT,
            "EventBusArnOutput": (
                f"arn:aws:events:us-east-1:{ACCOUNT}:event-bus/raad-{environment}-identity-events"
            ),
            "ExportsOutputRefUserPool6BA7E5F296FD7236": POOL,
        },
        # CDK's own cross-stack export outputs appear in a real outputs file.
        f"RaadMonitoring-{environment}": {"ExportsOutputRefAlerts91F83244": "arn:aws:sns:x"},
        f"RaadPublicEdge-{environment}": {
            "EnvironmentOutput": environment,
            "PublicApiUrlOutput": f"https://{environment}.api.example.test",
            "VerifierConfigOutput": json.dumps(verifier),
            "HttpApiEndpointOutput": "https://abc123defg.execute-api.us-east-1.amazonaws.com",
        },
    }


def build(
    document: dict[str, Any], environment: str = "dev"
) -> configuration.PlatformConfiguration:
    return build_configuration(document, environment=environment, account=ACCOUNT)


def test_generated_files_follow_the_canonical_c4_and_c5_schemas(tmp_path: Path) -> None:
    written = write_configuration(build(outputs("stg"), "stg"), tmp_path)
    assert [p.relative_to(tmp_path).as_posix() for p in written] == [
        "config/stg.json",
        "verifier/stg.json",
    ]
    mobile = json.loads((tmp_path / "config/stg.json").read_text())
    verifier = json.loads((tmp_path / "verifier/stg.json").read_text())
    Draft202012Validator(
        load_contract("c4-mobile-environment-config-v1.schema.yaml")["schema"]
    ).validate(mobile)
    Draft202012Validator(
        load_contract("c5-money-edge-v1.yaml")["token_verification"]["configuration"]["schema"]
    ).validate(verifier)
    assert list(mobile) == list(configuration.C4_KEYS)
    assert mobile == {
        "configVersion": "1.0",
        "environment": "stg",
        "apiBaseUrl": "https://stg.api.example.test",
        "moneyBasePath": "/money/v1",
        "authIssuer": f"https://cognito-idp.us-east-1.amazonaws.com/{POOL}",
        "authAudience": CLIENT,
        "authClientId": CLIENT,
    }
    assert verifier["issuer"] == mobile["authIssuer"] and verifier["audience"] == CLIENT


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda d: d["RaadIdentity-dev"].pop("UserPoolIdOutput"), "missing or have extra"),
        (lambda d: d["RaadPublicEdge-dev"].update(Extra="x"), "missing or have extra"),
        (lambda d: d.pop("RaadPublicEdge-dev"), "missing or have extra"),
        (lambda d: d.update({"RaadIdentity-stg": {}}), "another environment"),
        (lambda d: d["RaadMonitoring-dev"].update(Note="x"), "missing or have extra"),
        (
            lambda d: d["RaadIdentity-dev"].update(ExportsOutputRefKey="AKIA" + "B" * 16),
            "secret",
        ),
        (lambda d: d["RaadPublicEdge-dev"].update(EnvironmentOutput="stg"), "another environment"),
        (lambda d: d["RaadIdentity-dev"].update(UserPoolIdOutput="eu-west-1_Abc"), "region"),
        (
            lambda d: d["RaadIdentity-dev"].update(
                EventBusArnOutput="arn:aws:events:us-east-1:222222222222:event-bus/raad-dev-identity-events"
            ),
            "account/environment",
        ),
        (
            lambda d: d["RaadIdentity-dev"].update(
                EventBusArnOutput=f"arn:aws:events:us-east-1:{ACCOUNT}:event-bus/raad-stg-identity-events"
            ),
            "account/environment",
        ),
        (lambda d: d["RaadIdentity-dev"].update(UserPoolClientIdOutput="other"), "pool"),
        (lambda d: d["RaadPublicEdge-dev"].update(PublicApiUrlOutput="http://x.test"), "HTTPS"),
        (
            lambda d: d["RaadPublicEdge-dev"].update(PublicApiUrlOutput="https://x.test/money"),
            "no path",
        ),
        (
            lambda d: d["RaadPublicEdge-dev"].update(
                PublicApiUrlOutput="https://d1.cloudfront.net"
            ),
            "HTTPS origin",
        ),
        (
            lambda d: d["RaadPublicEdge-dev"].update(
                PublicApiUrlOutput="https://abc123defg.execute-api.us-east-1.amazonaws.com"
            ),
            "protected public host",
        ),
        (lambda d: d["RaadPublicEdge-dev"].update(VerifierConfigOutput="{"), "not JSON"),
        (
            lambda d: d["RaadIdentity-dev"].update(UserPoolClientIdOutput="AKIA" + "A" * 16),
            "secret",
        ),
    ],
)
def test_incoherent_outputs_are_refused_without_naming_values(mutate, message) -> None:
    document = outputs()
    mutate(document)
    with pytest.raises(ConfigurationError, match=message) as refused:
        build(document)
    assert "AKIA" not in str(refused.value) and POOL not in str(refused.value)


def test_secret_looking_output_keys_are_refused() -> None:
    document = outputs()
    document["RaadIdentity-dev"]["ClientSecretOutput"] = "x"
    with pytest.raises(ConfigurationError):
        build(document)
    tampered = outputs()
    verifier = json.loads(tampered["RaadPublicEdge-dev"]["VerifierConfigOutput"])
    verifier["privateKey"] = "x"
    tampered["RaadPublicEdge-dev"]["VerifierConfigOutput"] = json.dumps(verifier)
    with pytest.raises(ConfigurationError, match="secret"):
        build(tampered)


@pytest.mark.parametrize(
    "kwargs", [{"environment": "qa"}, {"account": "1234"}, {"region": "eu-west-1"}]
)
def test_invalid_target_arguments_are_refused(kwargs) -> None:
    settings = {"environment": "dev", "account": ACCOUNT, **kwargs}
    with pytest.raises(ConfigurationError):
        build_configuration(outputs(), **settings)


def test_regeneration_replaces_only_the_same_environments_previous_files(tmp_path: Path) -> None:
    write_configuration(build(outputs()), tmp_path)
    write_configuration(build(outputs()), tmp_path)  # same environment: replaced
    unrelated = tmp_path / "config" / "dev.json"
    unrelated.write_text('{"name": "not a config"}')
    with pytest.raises(ConfigurationError, match="unrelated"):
        write_configuration(build(outputs()), tmp_path)
    assert unrelated.read_text() == '{"name": "not a config"}'
    (tmp_path / "config" / "dev.json").write_text(
        json.dumps({"configVersion": "1.0", "environment": "prd"})
    )
    with pytest.raises(ConfigurationError):
        write_configuration(build(outputs()), tmp_path)


def test_links_and_missing_directories_are_never_written_through(tmp_path: Path) -> None:
    target = tmp_path / "elsewhere.json"
    target.write_text("{}")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "dev.json").symlink_to(target)
    with pytest.raises(ConfigurationError, match="link"):
        write_configuration(build(outputs()), tmp_path)
    assert target.read_text() == "{}"
    with pytest.raises(ConfigurationError, match="directory"):
        write_configuration(build(outputs()), tmp_path / "absent")
    link = tmp_path / "linked"
    link.symlink_to(tmp_path / "config")
    with pytest.raises(ConfigurationError, match="directory"):
        write_configuration(build(outputs()), link)


def test_command_line_writes_files_without_any_aws_call(tmp_path, monkeypatch, capsys) -> None:
    import boto3

    monkeypatch.setattr(boto3, "client", Mock(side_effect=AssertionError("no AWS call")))
    monkeypatch.setattr(boto3, "Session", Mock(side_effect=AssertionError("no AWS call")))
    source = tmp_path / "outputs.json"
    source.write_text(json.dumps(outputs("prd")))
    out = tmp_path / "out"
    out.mkdir()
    arguments = ["--environment", "prd", "--account", ACCOUNT, "--outputs", str(source)]
    assert writer.main([*arguments, "--output-dir", str(out)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "Wrote config/prd.json",
        "Wrote verifier/prd.json",
    ]
    assert (
        writer.main(
            [
                "--environment",
                "dev",
                "--account",
                ACCOUNT,
                "--outputs",
                str(source),
                "--output-dir",
                str(out),
            ]
        )
        == 1
    )
    error = capsys.readouterr().err
    assert error.startswith("Configuration refused:") and CLIENT not in error
    source.write_text("not json")
    assert writer.main([*arguments, "--output-dir", str(out)]) == 1


def test_stack_outputs_carry_the_same_verifier_as_the_ssm_parameter() -> None:
    from raad_platform.stacks import IdentityStack, MonitoringStack, PublicEdgeStack

    app = cdk.App()
    identity = IdentityStack(app, "Identity", environment="dev")
    monitoring = MonitoringStack(app, "Monitoring", environment="dev", alert_email="")
    edge = PublicEdgeStack(
        app,
        "Edge",
        environment="dev",
        identity=identity,
        monitoring=monitoring,
        domain_name="dev.api.example.test",
        hosted_zone_id="",
        certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/abcd",
        service_parameter="/raad/dev/money-api/function-url",
    )
    built = Template.from_stack(edge).to_json()
    outputs_section = built["Outputs"]
    assert set(outputs_section) == configuration.EDGE_OUTPUTS
    parameter = next(
        r["Properties"]["Value"]
        for r in built["Resources"].values()
        if r["Type"] == "AWS::SSM::Parameter" and r["Properties"]["Name"] == "/raad/dev/verifier"
    )
    assert outputs_section["VerifierConfigOutput"]["Value"] == parameter
    identity_outputs = Template.from_stack(identity).to_json()["Outputs"]
    declared = {k for k in identity_outputs if not k.startswith(configuration.CDK_EXPORT_PREFIX)}
    assert declared == configuration.IDENTITY_OUTPUTS
    # The cross-stack exports CDK adds are present, which is why the writer tolerates the prefix.
    assert len(identity_outputs) > len(declared)
    assert copy.deepcopy(outputs_section["EnvironmentOutput"]["Value"]) == "dev"
