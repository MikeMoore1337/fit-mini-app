import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import httpx
import pytest
from authlib.integrations.base_client.errors import OAuthError
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from fitminiapp_api.api.v1 import auth as auth_api
from fitminiapp_api.core.config import Settings, settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.services import oauth_login
from fitminiapp_api.services.oauth_login import normalize_oauth_claims
from fitminiapp_api.services.telegram_auth import parse_init_data


def _signed_init_data(
    *,
    auth_date: int,
    user_id: int = 9_120_001,
    user_data: dict[str, object] | None = None,
) -> str:
    data = {
        "auth_date": str(auth_date),
        "query_id": "AAE-provider-readiness",
        "user": json.dumps(
            user_data or {"id": user_id, "first_name": "Telegram", "username": "provider_test"},
            separators=(",", ":"),
        ),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.telegram_bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()
    data["hash"] = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return urlencode(data)


class _FakeOAuthClient:
    def __init__(self, claims: dict[str, object] | None = None, error: Exception | None = None):
        self.claims = claims or {}
        self.error = error

    async def authorize_redirect(self, request, redirect_uri):
        request.session["fake_redirect_uri"] = redirect_uri
        return RedirectResponse("https://provider.example/authorize", status_code=302)

    async def authorize_access_token(self, request):
        del request
        if self.error is not None:
            raise self.error
        return {"userinfo": self.claims}


class _FakeProfileResponse:
    def __init__(self, payload: object):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class _FakeYandexClient(_FakeOAuthClient):
    async def authorize_access_token(self, request):
        del request
        return {"access_token": "provider-access-token", "token_type": "bearer"}

    async def get(self, path, token):
        assert path == "info?format=json"
        assert token["access_token"] == "provider-access-token"
        return _FakeProfileResponse(self.claims)


def test_oidc_and_yandex_registrations_enable_pkce_and_safe_transport(monkeypatch):
    registrations: list[tuple[str, dict[str, object]]] = []

    def fake_register(name: str, **kwargs: object) -> None:
        registrations.append((name, kwargs))

    monkeypatch.setattr(oauth_login.oauth, "register", fake_register)
    monkeypatch.setattr(oauth_login.settings, "oauth_http_timeout_seconds", 19)

    oauth_login._register_oidc(
        "google",
        "google-client",
        "google-secret",
        "https://accounts.google.com/.well-known/openid-configuration",
        "openid profile email",
        use_pkce=True,
    )
    oauth_login._register_yandex("yandex-client", "yandex-secret")

    google = registrations[0][1]
    assert google["server_metadata_url"] == (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    assert google["client_kwargs"] == {
        "scope": "openid profile email",
        "trust_env": False,
        "timeout": 19,
        "code_challenge_method": "S256",
    }
    yandex = registrations[1][1]
    assert yandex["authorize_url"] == "https://oauth.yandex.ru/authorize"
    assert yandex["access_token_url"] == "https://oauth.yandex.ru/token"
    assert yandex["api_base_url"] == "https://login.yandex.ru/"
    assert yandex["client_cls"] is oauth_login.OAuthStarletteOAuth2App
    assert yandex["client_kwargs"] == {
        "scope": "login:info login:email",
        "trust_env": False,
        "timeout": 19,
        "code_challenge_method": "S256",
    }


def test_partial_provider_credentials_disable_provider_safely():
    configured = Settings(
        app_env="dev",
        app_name="Provider test",
        app_debug=False,
        secret_key="test-secret",
        database_url="sqlite://",
        telegram_bot_token="test-token",
        telegram_oauth_client_id="telegram-client-without-secret",
        telegram_oauth_client_secret="",
        google_oauth_client_id="",
        google_oauth_client_secret="google-secret-without-client",
        yandex_oauth_client_id="yandex-client-without-secret",
        yandex_oauth_client_secret="",
        vk_oauth_client_id="vk-client",
        apple_oauth_client_id="",
        apple_oauth_client_secret="",
    )

    assert configured.oauth_provider_names == ["vk"]


@pytest.mark.parametrize("max_age", [59, 3601])
def test_telegram_init_data_freshness_window_is_bounded(max_age):
    with pytest.raises(ValidationError, match="telegram_init_data_max_age_seconds"):
        Settings(
            app_env="dev",
            app_name="Provider test",
            app_debug=False,
            secret_key="test-secret",
            database_url="sqlite://",
            telegram_bot_token="test-token",
            telegram_init_data_max_age_seconds=max_age,
        )


@pytest.mark.parametrize(
    ("provider", "claims"),
    [
        ("google", {"sub": True}),
        ("google", {"sub": ["not", "scalar"]}),
        ("yandex", {"id": False}),
        ("vk", {"user_id": {"nested": "value"}}),
    ],
)
def test_provider_claims_reject_non_scalar_subjects(provider, claims):
    assert normalize_oauth_claims(provider, claims)["subject"] == ""


def test_provider_email_verification_semantics_are_fail_closed():
    assert (
        normalize_oauth_claims(
            "google",
            {"sub": "google-subject", "email": "owner@example.com", "email_verified": True},
        )["email_verified"]
        is True
    )
    assert (
        normalize_oauth_claims(
            "google",
            {"sub": "google-subject", "email": "owner@example.com", "email_verified": "true"},
        )["email_verified"]
        is False
    )
    assert (
        normalize_oauth_claims(
            "yandex", {"id": "yandex-subject", "default_email": "owner@yandex.ru"}
        )["email_verified"]
        is False
    )
    assert (
        normalize_oauth_claims("vk", {"user_id": "vk-subject", "email": "owner@example.com"})[
            "email_verified"
        ]
        is False
    )
    assert (
        normalize_oauth_claims(
            "apple",
            {"sub": "apple-subject", "email": "relay@example.com", "email_verified": "true"},
        )["email_verified"]
        is True
    )


def test_provider_profile_fields_are_bounded_before_persistence():
    claims = normalize_oauth_claims(
        "google",
        {
            "sub": "google-subject",
            "name": "n" * 129,
            "given_name": "g" * 65,
            "family_name": "f" * 65,
            "picture": "p" * 513,
        },
    )

    assert claims["full_name"] is None
    assert claims["first_name"] is None
    assert claims["last_name"] is None
    assert claims["photo_url"] is None


def test_telegram_init_endpoint_accepts_valid_and_rejects_invalid_or_stale_data(
    client, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_init_data_max_age_seconds", 300)
    now = int(time.time())

    valid = client.post(
        "/api/v1/auth/telegram/init",
        json={"init_data": _signed_init_data(auth_date=now)},
    )
    assert valid.status_code == 200
    assert valid.json()["access_token"]

    tampered = _signed_init_data(auth_date=now, user_id=9_120_002).replace(
        "provider_test", "attacker"
    )
    invalid = client.post("/api/v1/auth/telegram/init", json={"init_data": tampered})
    assert invalid.status_code == 401

    stale = client.post(
        "/api/v1/auth/telegram/init",
        json={"init_data": _signed_init_data(auth_date=now - 301, user_id=9_120_003)},
    )
    assert stale.status_code == 401

    invalid_profile = client.post(
        "/api/v1/auth/telegram/init",
        json={
            "init_data": _signed_init_data(
                auth_date=now,
                user_data={"id": 9_120_004, "username": ["not", "a", "string"]},
            )
        },
    )
    assert invalid_profile.status_code == 401


def test_telegram_init_data_rejects_duplicate_parameters():
    with pytest.raises(ValueError, match="повторяющиеся"):
        parse_init_data("auth_date=1&auth_date=2&hash=unused")


def test_yandex_callback_uses_stable_id_and_unverified_contact_email(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: (
            _FakeYandexClient(
                {
                    "id": "yandex-stable-id",
                    "login": "owner",
                    "default_email": "owner@yandex.ru",
                    "display_name": "Yandex Owner",
                }
            )
            if provider == "yandex"
            else None
        ),
    )

    response = client.get("/api/v1/auth/oauth/yandex/callback", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    with get_session_context() as db:
        identity = db.query(AuthIdentity).filter(AuthIdentity.provider == "yandex").one()
        assert identity.subject == "yandex-stable-id"
        assert identity.email == "owner@yandex.ru"
        assert identity.email_verified is False


@pytest.mark.parametrize(
    ("error", "expected"),
    [("access_denied", "denied"), ("mismatching_state", "invalid_state")],
)
def test_oauth_library_errors_are_normalized(client, monkeypatch, error, expected):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: _FakeOAuthClient(error=OAuthError(error=error)),
    )

    response = client.get("/api/v1/auth/oauth/google/callback", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/login?next=%2Fapp&auth_error={expected}"


def test_provider_timeout_is_safe_on_start_and_callback(client, monkeypatch):
    class TimeoutClient(_FakeOAuthClient):
        async def authorize_redirect(self, request, redirect_uri):
            del request, redirect_uri
            raise httpx.ConnectTimeout("provider timeout")

    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: TimeoutClient(error=httpx.ReadTimeout("provider timeout")),
    )

    started = client.get("/api/v1/auth/oauth/google/start", follow_redirects=False)
    callback = client.get("/api/v1/auth/oauth/google/callback", follow_redirects=False)

    assert started.status_code == 303
    assert started.headers["location"] == "/login?next=%2Fapp&auth_error=unavailable"
    assert callback.status_code == 303
    assert callback.headers["location"] == "/login?next=%2Fapp&auth_error=provider_failure"


def test_post_callback_cancel_is_normalized_without_provider_call(client, monkeypatch):
    class UnexpectedClient(_FakeOAuthClient):
        async def authorize_access_token(self, request):
            del request
            pytest.fail("provider token exchange must not run after cancellation")

    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(auth_api, "configured_oauth_client", lambda provider: UnexpectedClient())

    response = client.post(
        "/api/v1/auth/oauth/apple/callback",
        data={"error": "user_cancelled"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2Fapp&auth_error=denied"


def test_post_callback_success_keeps_form_available_for_provider_client(client, monkeypatch):
    class FormReadingClient(_FakeOAuthClient):
        async def authorize_access_token(self, request):
            async with request.form() as form:
                assert form.get("code") == "apple-code"
                assert form.get("state") == "apple-state"
            return {
                "userinfo": {
                    "sub": "apple-form-subject",
                    "email": "relay@example.com",
                    "email_verified": "true",
                }
            }

    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(auth_api, "configured_oauth_client", lambda provider: FormReadingClient())

    response = client.post(
        "/api/v1/auth/oauth/apple/callback",
        data={"code": "apple-code", "state": "apple-state"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"


def test_public_config_never_exposes_provider_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "telegram_oauth_client_id", "telegram-client-sensitive")
    monkeypatch.setattr(settings, "telegram_oauth_client_secret", "telegram-secret-sensitive")
    monkeypatch.setattr(settings, "google_oauth_client_id", "google-client-sensitive")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "google-secret-sensitive")
    monkeypatch.setattr(settings, "yandex_oauth_client_id", "yandex-client-sensitive")
    monkeypatch.setattr(settings, "yandex_oauth_client_secret", "yandex-secret-sensitive")
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client-sensitive")
    monkeypatch.setattr(settings, "apple_oauth_client_id", "")
    monkeypatch.setattr(settings, "apple_oauth_client_secret", "")

    response = client.get("/api/v1/public/config")

    assert response.status_code == 200
    assert response.json()["oauth_providers"] == ["telegram", "google", "yandex", "vk"]
    serialized = response.text.lower()
    assert "client-sensitive" not in serialized
    assert "secret-sensitive" not in serialized
