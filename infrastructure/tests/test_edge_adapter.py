"""C5 adapter checks for authentication, signed forwarding, correlation, and safe failures."""

from unittest.mock import Mock
import hashlib
import hmac
import json

import jwt
import pytest
from raad_platform.edge import handler


def event() -> dict:
    return {"headers": {"Authorization": "Bearer signed-token", "X-Correlation-Id": "request-123", "X-User-Id": "spoofed"}, "requestContext": {"http": {"method": "GET"}}, "rawPath": "/money/v1/wallet", "rawQueryString": ""}


def test_missing_token_returns_safe_401(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_profile", lambda: (_ for _ in ()).throw(AssertionError("must not read target")))
    result = handler.handle({**event(), "headers": {}}, None)
    assert result["statusCode"] == 401
    assert "wallet" not in result["body"]


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
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "https://service.lambda-url.us-east-1.on.aws/"))
    monkeypatch.setattr(handler, "_verify", lambda *_: None)
    credentials = Mock(get_frozen_credentials=Mock(return_value=Mock(access_key="a", secret_key="s", token="t")))
    monkeypatch.setattr(handler.boto3, "Session", lambda: Mock(get_credentials=lambda: credentials, region_name="us-east-1"))
    request = Mock(status_code=200, headers={"content-type": "application/json"}, text='{"ok":true}')
    captured = {}
    def send(*args, **kwargs):
        captured.update(kwargs)
        captured["url"] = args[1]
        return request
    monkeypatch.setattr(handler.requests, "request", send)
    monkeypatch.setattr(handler, "_protected_correlation", lambda _: ("1", "hmac"))
    result = handler.handle(event(), None)
    assert result["statusCode"] == 200
    assert captured["url"] == "https://service.lambda-url.us-east-1.on.aws/money/v1/wallet"
    assert "X-User-Id" not in captured["headers"]
    assert captured["auth"] is not None


def test_invalid_correlation_is_replaced(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_profile", lambda: (_ for _ in ()).throw(KeyError("offline")))
    request = event()
    request["headers"]["X-Correlation-Id"] = "contains\r\nunsafe"
    result = handler.handle(request, None)
    assert result["headers"]["x-correlation-id"] != "contains\r\nunsafe"


def test_upstream_timeout_returns_safe_503(monkeypatch) -> None:
    monkeypatch.setattr(handler, "_profile", lambda: ("https://issuer", "https://service.lambda-url.us-east-1.on.aws/"))
    monkeypatch.setattr(handler, "_verify", lambda *_: None)
    credentials = Mock(get_frozen_credentials=Mock(return_value=Mock(access_key="a", secret_key="s", token="t")))
    monkeypatch.setattr(handler.boto3, "Session", lambda: Mock(get_credentials=lambda: credentials, region_name="us-east-1"))
    monkeypatch.setattr(handler, "_protected_correlation", lambda _: ("1", "hmac"))
    monkeypatch.setattr(handler.requests, "request", Mock(side_effect=handler.requests.Timeout()))
    result = handler.handle(event(), None)
    assert result["statusCode"] == 503
    assert "Timeout" not in result["body"]


def test_service_target_comes_from_environment_ssm_parameter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_POOL_ID", "us-east-1_pool123")
    monkeypatch.setenv("SERVICE_URL_PARAMETER", "/raad/dev/money-api/function-url")
    client = Mock(get_parameter=Mock(return_value={"Parameter": {"Value": "https://service.lambda-url.us-east-1.on.aws/"}}))
    monkeypatch.setattr(handler.boto3, "client", lambda name: client)
    assert handler._profile() == ("https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool123", "https://service.lambda-url.us-east-1.on.aws/")
    client.get_parameter.assert_called_once_with(Name="/raad/dev/money-api/function-url")


def test_token_verifier_checks_cognito_access_token_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIENT_ID", "client-1")
    signing_key = Mock(key="public-key")
    monkeypatch.setattr(handler, "PyJWKClient", lambda *args, **kwargs: Mock(get_signing_key_from_jwt=Mock(return_value=signing_key)))
    decoded = {"token_use": "access", "client_id": "client-1"}
    monkeypatch.setattr(jwt, "decode", lambda *args, **kwargs: decoded)
    handler._verify("token", "https://issuer.example.test")
    assert signing_key is not None


def test_token_verifier_rejects_wrong_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIENT_ID", "client-1")
    monkeypatch.setattr(handler, "PyJWKClient", lambda *args, **kwargs: Mock(get_signing_key_from_jwt=Mock(return_value=Mock(key="public-key"))))
    monkeypatch.setattr(jwt, "decode", lambda *args, **kwargs: {"token_use": "access", "client_id": "wrong"})
    with pytest.raises(jwt.InvalidTokenError):
        handler._verify("token", "https://issuer.example.test")


def test_correlation_hmac_uses_secret_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORRELATION_SECRET_ARN", "secret-arn")
    client = Mock(get_secret_value=Mock(return_value={"SecretString": '{"version":"7","key":"secret-key"}'}))
    monkeypatch.setattr(handler.boto3, "client", lambda name: client)
    version, digest = handler._protected_correlation("correlation-123")
    expected = hmac.new(b"secret-key", b"correlation-123", hashlib.sha256).hexdigest()
    assert (version, digest) == ("7", expected)


def test_transfer_metrics_distinguish_slow_success_and_business_refusal(capsys: pytest.CaptureFixture[str]) -> None:
    handler._publish_metrics(201, 2_500, "/money/v1/transfers", "POST")
    success = json.loads(capsys.readouterr().out)
    assert success["ValidTransferSuccesses"] == 1
    assert success["TransferOver2s"] == 1
    handler._publish_metrics(422, 50, "/money/v1/transfers", "POST")
    refusal = json.loads(capsys.readouterr().out)
    assert refusal["BusinessTransferRefusals"] == 1
