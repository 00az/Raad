"""C5 adapter checks for authentication, signed forwarding, correlation, and safe failures."""

import hashlib
import hmac
import json
from unittest.mock import Mock

import jwt
import pytest

from raad_platform.edge import handler

READ_ORIGIN_SECRET = handler._origin_secret


@pytest.fixture(autouse=True)
def isolate_key_cache(monkeypatch):
    handler._jwk_clients.clear()
    handler._origin_cache = None
    monkeypatch.setenv("ORIGIN_SECRET_ARN", "origin-secret")
    monkeypatch.setattr(handler, "_origin_secret", lambda: "a" * 64)


def event() -> dict:
    return {
        "headers": {
            "X-Raad-Origin": "a" * 64,
            "Authorization": "Bearer signed-token",
            "X-Correlation-Id": "request-123",
            "X-User-Id": "spoofed",
        },
        "requestContext": {"http": {"method": "GET"}},
        "rawPath": "/money/v1/wallet",
        "rawQueryString": "",
    }


def test_missing_token_returns_safe_401(monkeypatch) -> None:
    monkeypatch.setattr(
        handler, "_profile", lambda: (_ for _ in ()).throw(AssertionError("must not read target"))
    )
    result = handler.handle({**event(), "headers": {"X-Raad-Origin": "a" * 64}}, None)
    assert result["statusCode"] == 401
    assert "wallet" not in result["body"]


@pytest.mark.parametrize("value", [None, "wrong", "a" * 63, "a" * 64 + ",wrong"])
def test_direct_origin_is_refused_before_auth_forwarding_or_public_metrics(
    monkeypatch, capsys, value
):
    request = event()
    request["headers"].pop("X-Raad-Origin")
    if value is not None:
        request["headers"]["x-raad-origin"] = value
    profile = Mock(side_effect=AssertionError("must not authenticate"))
    forward = Mock(side_effect=AssertionError("must not forward"))
    metrics = Mock(side_effect=AssertionError("must not count bypass traffic"))
    monkeypatch.setattr(handler, "_profile", profile)
    monkeypatch.setattr(handler.requests, "request", forward)
    monkeypatch.setattr(handler, "_publish_metrics", metrics)
    result = handler.entry(request, None)
    assert result["statusCode"] == 403
    assert json.loads(result["body"])["code"] == "FORBIDDEN"
    profile.assert_not_called()
    forward.assert_not_called()
    metrics.assert_not_called()
    assert capsys.readouterr().out == ""
    assert "a" * 64 not in result["body"]


@pytest.mark.parametrize("kind", ["missing-config", "missing-secret", "malformed-secret"])
def test_origin_configuration_fails_closed_without_disclosing_secret(monkeypatch, capsys, kind):
    if kind == "missing-config":
        monkeypatch.delenv("ORIGIN_SECRET_ARN")
    elif kind == "missing-secret":
        monkeypatch.setattr(handler, "_origin_secret", Mock(side_effect=KeyError("private")))
    else:
        monkeypatch.setattr(handler, "_origin_secret", READ_ORIGIN_SECRET)
        monkeypatch.setattr(
            handler.boto3,
            "client",
            lambda *a, **kw: Mock(get_secret_value=Mock(return_value={"SecretString": "private"})),
        )
    result = handler.handle(event(), None)
    assert result["statusCode"] == 503
    assert "private" not in result["body"] + capsys.readouterr().out


def test_origin_secret_cache_expires_and_never_uses_stale_value_on_read_failure(monkeypatch):
    client = Mock(
        get_secret_value=Mock(
            side_effect=[
                {"SecretString": "a" * 64},
                {"SecretString": "b" * 64},
                KeyError("unavailable"),
            ]
        )
    )
    factory = Mock(return_value=client)
    clock = Mock(side_effect=[10, 20, 71, 132])
    monkeypatch.setattr(handler.boto3, "client", factory)
    monkeypatch.setattr(handler.time, "monotonic", clock)
    assert READ_ORIGIN_SECRET() == "a" * 64
    assert READ_ORIGIN_SECRET() == "a" * 64
    assert READ_ORIGIN_SECRET() == "b" * 64
    with pytest.raises(KeyError):
        READ_ORIGIN_SECRET()
    assert client.get_secret_value.call_count == 3
    assert factory.call_args.kwargs["config"].retries["total_max_attempts"] == 1


def test_missing_service_parameter_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_profile", lambda: (_ for _ in ()).throw(KeyError("missing")))
    result = handler.handle(event(), None)
    assert result["statusCode"] == 503
    assert "missing" not in result["body"]


def test_non_https_target_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "http://internal-target"))
    monkeypatch.setattr(handler, "_verify", lambda *_: None)
    result = handler.handle(event(), None)
    assert result["statusCode"] == 503


def test_signed_forwarding_preserves_c1_path_and_strips_spoofed_identity(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "_profile",
        lambda: ("https://issuer", "https://service.lambda-url.us-east-1.on.aws/"),
    )
    monkeypatch.setattr(handler, "_verify", lambda *_: None)
    credentials = Mock(
        get_frozen_credentials=Mock(return_value=Mock(access_key="a", secret_key="s", token="t"))
    )
    monkeypatch.setattr(
        handler.boto3,
        "Session",
        lambda: Mock(get_credentials=lambda: credentials, region_name="us-east-1"),
    )
    request = Mock(
        status_code=200, headers={"content-type": "application/json"}, text='{"ok":true}'
    )
    captured = {}

    def send(*args, **kwargs):
        captured.update(kwargs)
        captured["url"] = args[1]
        return request

    monkeypatch.setattr(handler.requests, "request", send)
    monkeypatch.setattr(handler, "_protected_correlation", lambda _: ("1", "hmac"))
    result = handler.handle(event(), None)
    assert result["statusCode"] == 200
    assert captured["url"] == "https://service.lambda-url.us-east-1.on.aws/"
    restored = json.loads(captured["data"])["request"]
    assert restored["path"] == "/money/v1/wallet"
    assert restored["headers"]["authorization"] == "Bearer signed-token"
    assert "X-User-Id" not in captured["headers"]
    assert captured["headers"]["Authorization"].startswith("AWS4-HMAC-SHA256 ")


def test_invalid_correlation_is_replaced(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_profile", lambda: (_ for _ in ()).throw(KeyError("offline")))
    request = event()
    request["headers"]["X-Correlation-Id"] = "contains\r\nunsafe"
    result = handler.handle(request, None)
    assert result["headers"]["x-correlation-id"] != "contains\r\nunsafe"


def test_upstream_timeout_returns_safe_503(monkeypatch) -> None:
    monkeypatch.setattr(
        handler,
        "_profile",
        lambda: ("https://issuer", "https://service.lambda-url.us-east-1.on.aws/"),
    )
    monkeypatch.setattr(handler, "_verify", lambda *_: None)
    credentials = Mock(
        get_frozen_credentials=Mock(return_value=Mock(access_key="a", secret_key="s", token="t"))
    )
    monkeypatch.setattr(
        handler.boto3,
        "Session",
        lambda: Mock(get_credentials=lambda: credentials, region_name="us-east-1"),
    )
    monkeypatch.setattr(handler, "_protected_correlation", lambda _: ("1", "hmac"))
    monkeypatch.setattr(handler.requests, "request", Mock(side_effect=handler.requests.Timeout()))
    result = handler.handle(event(), None)
    assert result["statusCode"] == 503
    assert "Timeout" not in result["body"]


def test_service_target_comes_from_environment_ssm_parameter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USER_POOL_ID", "us-east-1_pool123")
    monkeypatch.setenv("SERVICE_URL_PARAMETER", "/raad/dev/money-api/function-url")
    client = Mock(
        get_parameter=Mock(
            return_value={"Parameter": {"Value": "https://service.lambda-url.us-east-1.on.aws/"}}
        )
    )
    monkeypatch.setattr(handler.boto3, "client", lambda name, **kwargs: client)
    assert handler._profile() == (
        "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool123",
        "https://service.lambda-url.us-east-1.on.aws/",
    )
    client.get_parameter.assert_called_once_with(Name="/raad/dev/money-api/function-url")


def test_token_verifier_checks_cognito_access_token_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLIENT_ID", "client-1")
    signing_key = Mock(key="public-key")
    monkeypatch.setattr(
        handler,
        "PyJWKClient",
        lambda *args, **kwargs: Mock(get_signing_key_from_jwt=Mock(return_value=signing_key)),
    )
    decoded = {"token_use": "access", "client_id": "client-1"}
    monkeypatch.setattr(jwt, "decode", lambda *args, **kwargs: decoded)
    handler._verify("token", "https://issuer.example.test")
    assert signing_key is not None


def test_token_verifier_rejects_wrong_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIENT_ID", "client-1")
    monkeypatch.setattr(
        handler,
        "PyJWKClient",
        lambda *args, **kwargs: Mock(
            get_signing_key_from_jwt=Mock(return_value=Mock(key="public-key"))
        ),
    )
    monkeypatch.setattr(
        jwt, "decode", lambda *args, **kwargs: {"token_use": "access", "client_id": "wrong"}
    )
    with pytest.raises(jwt.InvalidTokenError):
        handler._verify("token", "https://issuer.example.test")


def test_correlation_hmac_uses_secret_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORRELATION_SECRET_ARN", "secret-arn")
    client = Mock(
        get_secret_value=Mock(return_value={"SecretString": '{"version":"7","key":"secret-key"}'})
    )
    monkeypatch.setattr(handler.boto3, "client", lambda name, **kwargs: client)
    version, digest = handler._protected_correlation("correlation-123")
    expected = hmac.new(b"secret-key", b"correlation-123", hashlib.sha256).hexdigest()
    assert (version, digest) == ("7", expected)


def test_transfer_metrics_distinguish_slow_success_and_business_refusal(
    capsys: pytest.CaptureFixture[str],
) -> None:
    handler._publish_metrics(201, 2_500, "/money/v1/transfers", "POST")
    success = json.loads(capsys.readouterr().out)
    assert success["ValidTransferSuccesses"] == 1
    assert success["TransferOver2s"] == 1
    handler._publish_metrics(422, 50, "/money/v1/transfers", "POST")
    refusal = json.loads(capsys.readouterr().out)
    assert refusal["BusinessTransferRefusals"] == 1


def test_key_cache_is_reused_with_one_second_fetch_and_one_minute_cooldown(monkeypatch):
    factory = Mock(return_value=Mock(get_signing_key_from_jwt=Mock(return_value=Mock(key="key"))))
    monkeypatch.setattr(handler, "PyJWKClient", factory)
    monkeypatch.setenv("CLIENT_ID", "client")
    monkeypatch.setattr(
        jwt, "decode", lambda *args, **kwargs: {"token_use": "access", "client_id": "client"}
    )
    handler._verify("token", "https://issuer")
    handler._verify("token", "https://issuer")
    factory.assert_called_once()
    assert factory.call_args.kwargs["lifespan"] == 21600
    assert factory.call_args.kwargs["cooldown_duration"] == 60
    assert factory.call_args.kwargs["timeout"] == 1


@pytest.mark.parametrize(
    "failure,status,code",
    [
        (jwt.ExpiredSignatureError(), 401, "AUTHENTICATION_REQUIRED"),
        (jwt.PyJWKClientConnectionError(), 503, "TOKEN_VERIFIER_UNAVAILABLE"),
    ],
)
def test_verifier_failure_mapping_is_distinct(monkeypatch, failure, status, code):
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "https://service"))
    monkeypatch.setattr(handler, "_verify", Mock(side_effect=failure))
    response = handler.handle(event(), None)
    assert response["statusCode"] == status
    assert json.loads(response["body"])["code"] == code
