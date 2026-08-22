from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from bot.fitminiapp_bot import telegram_client
from bot.fitminiapp_bot.config import Settings
from pydantic import ValidationError


def test_bot_proxy_prefers_dedicated_route(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_PROXY_URL", "socks5://bot-proxy.test:1081")

    configured = Settings(_env_file=None)

    assert configured.bot_api_proxy_url == "socks5://bot-proxy.test:1081"


def test_bot_proxy_does_not_reuse_existing_telegram_route(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_PROXY_URL", raising=False)
    monkeypatch.setenv("TELEGRAM_OAUTH_PROXY_URL", "socks5://telegram-proxy.test:1081")

    configured = Settings(_env_file=None)

    assert configured.bot_api_proxy_url == ""


@pytest.mark.parametrize(
    "proxy_url",
    (
        "file:///tmp/proxy",
        "https://proxy.test:1081",
        "socks5://proxy.test:1081/?unsafe=true",
    ),
)
def test_bot_proxy_rejects_unsafe_url(monkeypatch, proxy_url: str) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_PROXY_URL", proxy_url)

    with pytest.raises(ValidationError, match="Telegram proxy URL"):
        Settings(_env_file=None)


def test_bot_api_session_uses_configured_proxy(monkeypatch) -> None:
    session = object()
    session_factory = Mock(return_value=session)
    monkeypatch.setattr(telegram_client, "AiohttpSession", session_factory)
    monkeypatch.setattr(
        telegram_client,
        "settings",
        SimpleNamespace(bot_api_proxy_url="socks5://proxy.test:1081"),
    )

    assert telegram_client.create_bot_api_session(timeout=15) is session
    session_factory.assert_called_once_with(proxy="socks5://proxy.test:1081", timeout=15)


def test_bot_api_session_normalizes_socks5h_for_aiogram(monkeypatch) -> None:
    session_factory = Mock()
    monkeypatch.setattr(telegram_client, "AiohttpSession", session_factory)
    monkeypatch.setattr(
        telegram_client,
        "settings",
        SimpleNamespace(bot_api_proxy_url="socks5h://proxy.test:1081"),
    )

    telegram_client.create_bot_api_session()

    session_factory.assert_called_once_with(proxy="socks5://proxy.test:1081")


def test_bot_api_session_does_not_use_ambient_proxy(monkeypatch) -> None:
    session_factory = Mock()
    monkeypatch.setattr(telegram_client, "AiohttpSession", session_factory)
    monkeypatch.setattr(telegram_client, "settings", SimpleNamespace(bot_api_proxy_url=""))

    telegram_client.create_bot_api_session()

    session_factory.assert_called_once_with()
