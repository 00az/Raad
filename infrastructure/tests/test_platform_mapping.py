"""NFR13.10: a dev-only stub mapped by its own path, isolated from /money and from stg/prd."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from raad_platform.edge import handler, stub
from raad_platform.stacks import IdentityStack, MonitoringStack, PublicEdgeStack


def edge(environment: str) -> dict[str, Any]:
    app = cdk.App()
    identity = IdentityStack(app, "Identity", environment=environment)
    monitoring = MonitoringStack(app, "Monitoring", environment=environment, alert_email="")
    stack = PublicEdgeStack(
        app,
        "Edge",
        environment=environment,
        identity=identity,
        monitoring=monitoring,
        domain_name=f"{environment}.api.example.test",  # synthetic fixture host
        hosted_zone_id="",
        certificate_arn="arn:aws:acm:us-east-1:111111111111:certificate/abcd",
        service_parameter=f"/raad/{environment}/money-api/function-url",
    )
    rendered: dict[str, Any] = Template.from_stack(stack).to_json()
    return rendered


def of_type(built: dict[str, Any], kind: str) -> dict[str, Any]:
    return {k: v for k, v in built["Resources"].items() if v["Type"] == kind}


def functions(built: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        v["Properties"]["Handler"]: {"id": k, **v["Properties"]}
        for k, v in of_type(built, "AWS::Lambda::Function").items()
    }


def request(path: str, method: str = "GET", origin: str | None = "a" * 64) -> dict[str, Any]:
    headers = {"X-Correlation-Id": "stub-1"}
    if origin is not None:
        headers["X-Raad-Origin"] = origin
    return {"headers": headers, "requestContext": {"http": {"method": method}}, "rawPath": path}


@pytest.fixture(autouse=True)
def origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORIGIN_SECRET_ARN", "origin-secret")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setattr(handler, "_origin_secret", lambda: "a" * 64)


def test_dev_maps_only_the_stub_path_to_the_stub_function() -> None:
    built = edge("dev")
    stub_id = functions(built)["raad_platform.edge.stub.entry"]["id"]
    routes = {
        r["Properties"]["RouteKey"]: r["Properties"]
        for r in of_type(built, "AWS::ApiGatewayV2::Route").values()
    }
    assert set(routes) == {"ANY /money/v1", "ANY /money/v1/{proxy+}", "GET /stub/v1/{proxy+}"}
    integrations = of_type(built, "AWS::ApiGatewayV2::Integration")
    stub_target = integrations[routes["GET /stub/v1/{proxy+}"]["Target"]["Fn::Join"][1][1]["Ref"]]
    assert stub_target["Properties"]["IntegrationUri"] == {"Fn::GetAtt": [stub_id, "Arn"]}


@pytest.mark.parametrize("environment", ["stg", "prd"])
def test_stg_and_prd_have_no_stub_route_function_or_catch_all(environment: str) -> None:
    built = edge(environment)
    keys = sorted(
        r["Properties"]["RouteKey"] for r in of_type(built, "AWS::ApiGatewayV2::Route").values()
    )
    assert keys == ["ANY /money/v1", "ANY /money/v1/{proxy+}"]
    assert "raad_platform.edge.stub.entry" not in functions(built)
    assert "/stub/" not in json.dumps(built)


def test_money_mapping_is_unchanged_by_the_stub() -> None:
    dev, prd = edge("dev"), edge("prd")
    for built in (dev, prd):
        money = functions(built)["raad_platform.edge.handler.entry"]
        assert money["Environment"]["Variables"]["SERVICE_URL_PARAMETER"].startswith("/raad/")
    money_routes = [
        r
        for r in of_type(dev, "AWS::ApiGatewayV2::Route").values()
        if "money" in r["Properties"]["RouteKey"]
    ]
    assert len(money_routes) == 2


def test_stub_role_can_read_only_the_origin_secret_and_write_its_own_logs() -> None:
    built = edge("dev")
    stub_fn = functions(built)["raad_platform.edge.stub.entry"]
    assert set(stub_fn["Environment"]["Variables"]) == {"ENVIRONMENT", "ORIGIN_SECRET_ARN"}
    role = stub_fn["Role"]["Fn::GetAtt"][0]
    statements = [
        s
        for p in of_type(built, "AWS::IAM::Policy").values()
        if {"Ref": role} in p["Properties"]["Roles"]
        for s in p["Properties"]["PolicyDocument"]["Statement"]
    ]
    actions = sorted(
        a
        for s in statements
        for a in ([s["Action"]] if isinstance(s["Action"], str) else s["Action"])
    )
    assert actions == [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
    ]
    rendered = json.dumps(statements)
    assert "lambda:Invoke" not in rendered and "dynamodb" not in rendered


def test_stub_answers_its_path_with_a_fixed_nonfinancial_document() -> None:
    result = stub.entry(request("/stub/v1/ping"), None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {
        "service": "platform-stub",
        "environment": "dev",
        "status": "ok",
    }
    assert result["headers"]["x-correlation-id"] == "stub-1"


@pytest.mark.parametrize(
    "path,method",
    [
        ("/stub/v1/other", "GET"),
        ("/stub/v1/ping/", "GET"),
        ("/stub/v1/ping", "POST"),
        ("/money/v1/wallet", "GET"),
    ],
)
def test_unknown_stub_paths_and_methods_fail_closed(path: str, method: str) -> None:
    result = stub.entry(request(path, method), None)
    assert result["statusCode"] == 404
    assert json.loads(result["body"])["code"] == "NOT_FOUND"


@pytest.mark.parametrize("value", [None, "wrong", "a" * 63])
def test_direct_origin_requests_are_refused_before_the_stub_answers(value, capsys) -> None:
    result = stub.entry(request("/stub/v1/ping", origin=value), None)
    assert result["statusCode"] == 403
    assert json.loads(result["body"])["code"] == "FORBIDDEN"
    assert capsys.readouterr().out == ""


def test_stub_refuses_everything_outside_dev(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "prd")
    assert stub.entry(request("/stub/v1/ping"), None)["statusCode"] == 404


def test_missing_origin_configuration_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_origin_secret", Mock(side_effect=KeyError("absent")))
    result = stub.entry(request("/stub/v1/ping"), None)
    assert result["statusCode"] == 503
    assert "absent" not in result["body"]
