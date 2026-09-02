from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from pydantic import ValidationError

import fitminiapp_api.main as main_module
from fitminiapp_api.api.v1 import auth as auth_api
from fitminiapp_api.core.config import Settings, settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.token import RefreshToken
from fitminiapp_api.models.user import User
from fitminiapp_api.services import oauth_login


def _settings_values(*, app_env: str = "dev") -> dict[str, object]:
    return {
        "app_env": app_env,
        "app_name": "Telegram proxy test",
        "app_debug": False,
        "secret_key": "production-secret-key-that-is-long-enough",
        "access_token_expire_minutes": 60,
        "refresh_token_expire_days": 30,
        "database_url": "sqlite://",
        "enable_dev_auth": False,
        "enable_web_auth": True,
        "telegram_bot_token": "123456:configured-token",
        "bot_internal_token": "production-bot-token-that-is-long-enough",
        "frontend_base_url": "https://app.example.test",
        "telegram_oauth_client_id": "telegram-client",
        "telegram_oauth_client_secret": "telegram-secret",
    }


def test_production_telegram_browser_oauth_requires_dedicated_proxy() -> None:
    values = _settings_values(app_env="prod")

    with pytest.raises(ValidationError, match="TELEGRAM_OAUTH_PROXY_URL"):
        Settings(**values, telegram_oauth_proxy_url="")

    configured = Settings(
        **values,
        telegram_oauth_proxy_url="socks5://host.docker.internal:1081",
    )
    assert configured.telegram_oauth_proxy_url == "socks5://host.docker.internal:1081"

    disabled_web = Settings(**{**values, "enable_web_auth": False}, telegram_oauth_proxy_url="")
    assert disabled_web.telegram_oauth_proxy_url == ""

    disabled_telegram = Settings(
        **{**values, "telegram_oauth_client_secret": ""},
        telegram_oauth_proxy_url="",
    )
    assert disabled_telegram.telegram_oauth_proxy_url == ""


def test_invalid_proxy_configuration_does_not_echo_credentials() -> None:
    unsafe_proxy = "file://proxy-user:proxy-password@tunnel.example.test/socket"

    with pytest.raises(ValidationError) as error:
        Settings(**_settings_values(), telegram_oauth_proxy_url=unsafe_proxy)

    rendered = str(error.value)
    assert "OAuth proxy URL" in rendered
    assert unsafe_proxy not in rendered
    assert "proxy-password" not in rendered


def test_canonical_telegram_client_uses_only_its_dedicated_proxy(monkeypatch) -> None:
    telegram_proxy = "socks5://telegram-proxy.test:1081"
    general_proxy = "socks5://general-oauth-proxy.test:1082"
    captured: dict[str, object] = {}

    def capture_init(self, *args, **kwargs) -> None:
        self.session = None
        del args
        captured.update(kwargs)

    monkeypatch.setattr(oauth_login.AsyncOAuth2Client, "__init__", capture_init)
    monkeypatch.setattr(oauth_login.settings, "telegram_oauth_proxy_url", telegram_proxy)
    monkeypatch.setattr(oauth_login.settings, "oauth_proxy_url", general_proxy)
    monkeypatch.setattr(oauth_login.settings, "oauth_force_ipv4", True)

    oauth_login.TelegramOAuthAsyncOAuth2Client(
        client_id="telegram-client",
        client_secret="telegram-secret",
        scope="openid profile",
        trust_env=False,
        timeout=17,
    )

    assert captured["proxy"] == telegram_proxy
    assert captured["trust_env"] is False
    assert captured["timeout"] == 17
    assert "transport" not in captured
    assert captured.get("verify", True) is not False
    assert oauth_login.oauth_transport_options() == {"proxy": general_proxy}


def test_telegram_tunnel_failure_is_controlled_and_retryable(client, monkeypatch, caplog) -> None:
    leaked_proxy = "socks5://proxy-user:proxy-password@telegram-proxy.test:1081"

    class UnavailableTunnelClient:
        async def create_authorization_url(self, redirect_uri):
            del redirect_uri
            raise httpx.ConnectError(f"tunnel unavailable: {leaked_proxy}")

        async def authorize_access_token(self, request):
            del request
            raise httpx.ProxyError(f"tunnel unavailable: {leaked_proxy}")

    class CallbackFailureClient:
        async def create_authorization_url(self, redirect_uri):
            state = "telegram-callback-failure-state"
            return {
                "url": f"https://telegram.example/authorize?state={state}",
                "state": state,
                "code_verifier": "telegram-callback-failure-verifier",
                "redirect_uri": redirect_uri,
            }

        async def authorize_access_token(self, request):
            del request
            raise httpx.ProxyError(f"tunnel unavailable: {leaked_proxy}")

    class RecoveredTunnelClient:
        async def create_authorization_url(self, redirect_uri):
            state = "telegram-recovered-state"
            return {
                "url": f"https://telegram.example/authorize?state={state}",
                "state": state,
                "code_verifier": "telegram-recovered-verifier",
                "redirect_uri": redirect_uri,
            }

        async def authorize_access_token(self, request):
            del request
            return {
                "userinfo": {
                    "sub": "9810001",
                    "preferred_username": "telegram_tunnel_recovered",
                    "name": "Telegram Tunnel Recovered",
                }
            }

    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: UnavailableTunnelClient() if provider == "telegram" else None,
    )
    with get_session_context() as db:
        counts_before = (
            db.query(User).count(),
            db.query(AuthIdentity).count(),
            db.query(RefreshToken).count(),
        )

    started = client.get("/api/v1/auth/oauth/telegram/start", follow_redirects=False)
    failed = client.get("/api/v1/auth/oauth/telegram/callback", follow_redirects=False)

    assert started.status_code == 303
    assert started.headers["location"] == (
        "/login?next=%2Fapp&auth_error=unavailable&oauth_provider=telegram"
    )
    assert failed.status_code == 303
    assert failed.headers["location"] == (
        "/login?next=%2Fapp&auth_error=invalid_state&oauth_provider=telegram"
    )
    assert settings.refresh_cookie_name not in failed.headers.get("set-cookie", "")
    assert leaked_proxy not in caplog.text
    assert "proxy-password" not in caplog.text
    with get_session_context() as db:
        assert (
            db.query(User).count(),
            db.query(AuthIdentity).count(),
            db.query(RefreshToken).count(),
        ) == counts_before

    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: CallbackFailureClient() if provider == "telegram" else None,
    )
    started = client.get("/api/v1/auth/oauth/telegram/start", follow_redirects=False)
    state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
    failed = client.get(
        "/api/v1/auth/oauth/telegram/callback",
        params={"code": "telegram-code", "state": state},
        follow_redirects=False,
    )

    assert started.status_code == 302
    assert failed.status_code == 303
    assert failed.headers["location"] == (
        "/login?next=%2Fapp&auth_error=provider_failure&oauth_provider=telegram"
    )
    assert settings.refresh_cookie_name not in failed.headers.get("set-cookie", "")
    assert leaked_proxy not in caplog.text
    assert "proxy-password" not in caplog.text

    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: RecoveredTunnelClient() if provider == "telegram" else None,
    )
    started = client.get("/api/v1/auth/oauth/telegram/start", follow_redirects=False)
    state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
    recovered = client.get(
        "/api/v1/auth/oauth/telegram/callback",
        params={"code": "telegram-code", "state": state},
        follow_redirects=False,
    )

    assert recovered.status_code == 303
    assert recovered.headers["location"] == "/app"
    assert settings.refresh_cookie_name in recovered.headers["set-cookie"]
    with get_session_context() as db:
        identity = (
            db.query(AuthIdentity)
            .filter(AuthIdentity.provider == "telegram", AuthIdentity.subject == "9810001")
            .one()
        )
        assert identity.user_id > 0


def test_runtime_and_compose_keep_proxy_configuration_server_only(monkeypatch) -> None:
    proxy_url = "socks5://proxy-user:proxy-password@telegram-proxy.test:1081"
    monkeypatch.setattr(settings, "telegram_oauth_proxy_url", proxy_url)

    assert proxy_url in main_module._application_sensitive_values()

    root = Path(__file__).resolve().parents[2]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    backend_service = compose.split("  backend:", maxsplit=1)[1].split("\n  setup:", maxsplit=1)[0]
    assert "env_file: .env" in backend_service
    assert '"host.docker.internal:host-gateway"' in backend_service
    assert "TELEGRAM_OAUTH_PROXY_URL" not in compose
