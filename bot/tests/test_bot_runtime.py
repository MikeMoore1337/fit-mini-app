import asyncio
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from aiogram.exceptions import TelegramConflictError
from bot.fitminiapp_bot import bot as bot_module
from bot.fitminiapp_bot.bot import PollingConflict, PollingFileLock, StableDispatcher
from bot.fitminiapp_bot.logging_config import JsonFormatter

BOT_TOKEN = "123456:telegram-bot-secret"
INTERNAL_TOKEN = "backend-internal-secret"


class _FakeSession:
    timeout = 10


class _ConflictingBot:
    id = 123
    session = _FakeSession()

    async def __call__(self, method, **kwargs):
        raise TelegramConflictError(method=method, message="terminated by other getUpdates request")


def test_dispatcher_escalates_polling_conflict_without_retrying():
    async def consume_updates() -> None:
        updates = StableDispatcher._listen_updates(_ConflictingBot())

        with pytest.raises(PollingConflict, match="telegram_polling_conflict"):
            await anext(updates)

    asyncio.run(consume_updates())


def test_polling_lock_filename_is_stable_and_does_not_expose_token(tmp_path: Path):
    first = PollingFileLock(str(tmp_path), "secret-token")
    second = PollingFileLock(str(tmp_path), "secret-token")

    assert first.path == second.path
    assert "secret-token" not in first.path.name


def test_polling_lock_waiter_takes_over_after_release(tmp_path: Path, monkeypatch):
    if bot_module.fcntl is None:
        pytest.skip("fcntl is only available in the Linux production environment")

    async def exercise_takeover() -> None:
        leader = PollingFileLock(str(tmp_path), "shared-token")
        standby = PollingFileLock(str(tmp_path), "shared-token")
        await leader.acquire()

        async def release_leader(_seconds: float) -> None:
            leader.release()

        monkeypatch.setattr(bot_module.asyncio, "sleep", release_leader)
        try:
            await standby.acquire()
            assert standby._file is not None
        finally:
            leader.release()
            standby.release()

    asyncio.run(exercise_takeover())


@pytest.mark.parametrize("status_code", [429, 500])
def test_timezone_delivery_reports_backend_http_errors(
    status_code: int,
    monkeypatch,
    caplog,
):
    real_async_client = httpx.AsyncClient

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, request=request, json={"detail": "temporary"})

    transport = httpx.MockTransport(respond)

    def client_factory(*, timeout: int):
        return real_async_client(timeout=timeout, transport=transport)

    monkeypatch.setattr(bot_module.httpx, "AsyncClient", client_factory)
    monkeypatch.setattr(
        bot_module.settings,
        "backend_internal_url",
        "https://backend.example/raw-url-secret",
    )
    monkeypatch.setattr(bot_module.settings, "bot_internal_token", INTERNAL_TOKEN)
    telegram_user = SimpleNamespace(id=123, username="tester", first_name="Test", last_name="User")

    with caplog.at_level(logging.ERROR, logger=bot_module.__name__):
        result = asyncio.run(bot_module.save_timezone_from_bot(telegram_user, "Europe/Moscow"))

    assert result is False
    record = caplog.records[-1]
    rendered = JsonFormatter().format(record)
    payload = json.loads(rendered)
    assert record.exc_info is None
    assert payload["message"] == "timezone_backend_update_failed"
    assert payload["error_code"] == f"http_status:{status_code}"
    assert INTERNAL_TOKEN not in rendered
    assert "backend.example" not in rendered
    assert "raw-url-secret" not in rendered


def test_timezone_delivery_reports_backend_timeout(monkeypatch):
    real_async_client = httpx.AsyncClient

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("backend timed out", request=request)

    transport = httpx.MockTransport(timeout)

    def client_factory(*, timeout: int):
        return real_async_client(timeout=timeout, transport=transport)

    monkeypatch.setattr(bot_module.httpx, "AsyncClient", client_factory)
    telegram_user = SimpleNamespace(id=123, username=None, first_name="Test", last_name=None)

    assert asyncio.run(bot_module.save_timezone_from_bot(telegram_user, "Europe/Moscow")) is False


def test_link_telegram_delivery_sends_identity_to_internal_api(monkeypatch):
    real_async_client = httpx.AsyncClient
    captured: dict[str, object] = {}

    def respond(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, request=request, json={"status": "linked"})

    transport = httpx.MockTransport(respond)

    def client_factory(*, timeout: int):
        return real_async_client(timeout=timeout, transport=transport)

    monkeypatch.setattr(bot_module.httpx, "AsyncClient", client_factory)
    monkeypatch.setattr(bot_module.settings, "bot_internal_token", INTERNAL_TOKEN)
    telegram_user = SimpleNamespace(
        id=12345,
        username="linked_user",
        first_name="Linked",
        last_name="User",
    )

    outcome = asyncio.run(bot_module.link_telegram_from_bot(telegram_user, "a" * 43))

    assert outcome == "linked"
    assert captured["payload"] == {
        "token": "a" * 43,
        "telegram_user_id": 12345,
        "username": "linked_user",
        "first_name": "Linked",
        "last_name": "User",
    }
    assert captured["headers"]["x-bot-token"] == INTERNAL_TOKEN


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(400, "invalid"), (409, "conflict"), (500, "failed")],
)
def test_link_telegram_delivery_maps_safe_outcomes(status_code, expected, monkeypatch):
    real_async_client = httpx.AsyncClient

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, request=request, json={"detail": "hidden"})

    transport = httpx.MockTransport(respond)

    def client_factory(*, timeout: int):
        return real_async_client(timeout=timeout, transport=transport)

    monkeypatch.setattr(bot_module.httpx, "AsyncClient", client_factory)
    telegram_user = SimpleNamespace(id=12345, username=None, first_name="Test", last_name=None)

    assert asyncio.run(bot_module.link_telegram_from_bot(telegram_user, "b" * 43)) == expected


def test_start_link_payload_is_validated_and_reports_success(monkeypatch):
    assert bot_module.telegram_link_token("trainer_other") is None
    assert bot_module.telegram_link_token("link_short") is None
    assert bot_module.telegram_link_token(f"link_{'c' * 43}") == "c" * 43

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=12345),
        bot=object(),
        answer=AsyncMock(),
    )
    monkeypatch.setattr(bot_module, "link_telegram_from_bot", AsyncMock(return_value="linked"))
    monkeypatch.setattr(bot_module, "set_mini_app_menu_button", AsyncMock(return_value=True))

    asyncio.run(bot_module.start(message, SimpleNamespace(args=f"link_{'c' * 43}")))

    assert message.answer.await_count == 1
    assert "одни и те же данные" in message.answer.await_args.args[0]


def test_json_formatter_excludes_arbitrary_message_and_exception_values() -> None:
    try:
        raise RuntimeError(
            f"request to https://api.telegram.org/bot{BOT_TOKEN}/getUpdates "
            f"used header {INTERNAL_TOKEN}"
        )
    except RuntimeError:
        record = logging.LogRecord(
            name="aiogram.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=f"failed https://api.telegram.org/bot{BOT_TOKEN}/getUpdates with {INTERNAL_TOKEN}",
            args=(),
            exc_info=sys.exc_info(),
        )

    rendered = JsonFormatter().format(record)
    payload = json.loads(rendered)

    assert payload["message"] == "application_log"
    assert payload["exception_type"] == "RuntimeError"
    assert "exception" not in payload
    assert BOT_TOKEN not in rendered
    assert INTERNAL_TOKEN not in rendered
    assert "api.telegram.org" not in rendered
