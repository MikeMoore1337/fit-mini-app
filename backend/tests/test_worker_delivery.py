import asyncio
import json
import logging
from datetime import datetime

import httpx
import pytest

from fitminiapp_api.core.logging_config import JsonFormatter
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.user import User
from fitminiapp_api.services.notifications import mark_delivery_failed, safe_delivery_error
from fitminiapp_api.services.worker import (
    _log_delivery_failure,
    send_telegram_message,
    telegram_transport_options,
)

SECRET_TOKEN = "123456:telegram-secret-token"


def test_worker_uses_dedicated_bot_api_proxy(monkeypatch) -> None:
    monkeypatch.setattr(
        "fitminiapp_api.services.worker.settings.telegram_bot_proxy_url",
        "socks5://bot-proxy.test:1081",
    )
    assert telegram_transport_options() == {
        "trust_env": False,
        "proxy": "socks5://bot-proxy.test:1081",
    }


def test_worker_does_not_reuse_telegram_oauth_proxy(monkeypatch) -> None:
    monkeypatch.setattr(
        "fitminiapp_api.services.worker.settings.telegram_bot_proxy_url",
        "",
    )
    monkeypatch.setattr(
        "fitminiapp_api.services.worker.settings.telegram_oauth_proxy_url",
        "socks5://telegram-proxy.test:1081",
    )

    assert telegram_transport_options() == {"trust_env": False}


def test_worker_does_not_inherit_ambient_proxy(monkeypatch) -> None:
    monkeypatch.setattr(
        "fitminiapp_api.services.worker.settings.telegram_bot_proxy_url",
        "",
    )
    monkeypatch.setattr(
        "fitminiapp_api.services.worker.settings.telegram_oauth_proxy_url",
        "",
    )

    assert telegram_transport_options() == {"trust_env": False}


def telegram_http_error(status_code: int = 500) -> httpx.HTTPStatusError:
    request = httpx.Request(
        "POST",
        f"https://api.telegram.org/bot{SECRET_TOKEN}/sendMessage",
    )
    response = httpx.Response(status_code, request=request, json={"ok": False})
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return error
    raise AssertionError("expected an HTTPStatusError")


@pytest.mark.parametrize("status_code", [429, 500])
def test_telegram_delivery_propagates_retryable_http_errors(status_code: int) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, request=request, json={"ok": False})

    async def deliver() -> None:
        transport = httpx.MockTransport(respond)
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await send_telegram_message(client, 123456, "test notification")
        assert exc_info.value.response.status_code == status_code

    asyncio.run(deliver())


def test_telegram_delivery_propagates_timeout() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Telegram timed out", request=request)

    async def deliver() -> None:
        transport = httpx.MockTransport(timeout)
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(httpx.ReadTimeout, match="Telegram timed out"):
                await send_telegram_message(client, 123456, "test notification")

    asyncio.run(deliver())


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (telegram_http_error(429), "http_status:429"),
        (httpx.ReadTimeout("secret timeout details"), "timeout"),
        (httpx.ConnectError("secret transport details"), "transport_error"),
        (RuntimeError("secret unexpected details"), "unexpected:RuntimeError"),
    ],
)
def test_delivery_error_is_reduced_to_safe_diagnostic_code(
    error: Exception,
    expected: str,
) -> None:
    diagnostic = safe_delivery_error(error)

    assert diagnostic == expected
    assert SECRET_TOKEN not in diagnostic
    assert "api.telegram.org" not in diagnostic
    assert "secret" not in diagnostic


def test_delivery_failure_does_not_persist_telegram_url_or_token() -> None:
    scheduled_for = datetime(2026, 8, 9, 12)
    with get_session_context() as session:
        user = session.query(User).first()
        assert user is not None
        notification = Notification(
            user_id=user.id,
            title="Sensitive failure test",
            body="Body",
            scheduled_for=scheduled_for,
            scheduled_for_utc=scheduled_for,
            status="processing",
            attempt_count=0,
        )
        session.add(notification)
        session.flush()
        notification_id = notification.id
        mark_delivery_failed(session, notification, telegram_http_error())

    with get_session_context() as session:
        stored = session.query(Notification).filter(Notification.id == notification_id).one()
        assert stored.last_error == "http_status:500"
        assert SECRET_TOKEN not in stored.last_error
        assert "api.telegram.org" not in stored.last_error


def test_delivery_failure_json_log_excludes_exception_and_sensitive_url(caplog) -> None:
    with caplog.at_level(logging.ERROR, logger="fitminiapp_api.services.worker"):
        _log_delivery_failure(42, telegram_http_error())

    record = caplog.records[-1]
    rendered = JsonFormatter(service="notification-worker").format(record)
    payload = json.loads(rendered)

    assert record.exc_info is None
    assert payload["message"] == "notification_delivery_failed"
    assert payload["notification_id"] == 42
    assert payload["delivery_error"] == "http_status:500"
    assert SECRET_TOKEN not in rendered
    assert "api.telegram.org" not in rendered
