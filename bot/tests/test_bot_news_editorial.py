from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.fitminiapp_bot import bot as bot_runtime
from bot.fitminiapp_bot import feedback, news_editorial


class FakeMessage:
    def __init__(self, *, chat_type: str = "private") -> None:
        self.chat = SimpleNamespace(type=chat_type)
        self.text = (
            "Канал: @yfc_test_news (staging)\n\n"
            "Служебное представление text revision (не финальный preview канала)"
        )
        self.caption = None
        self.edit_reply_markup = AsyncMock()
        self.answer = AsyncMock()


def _callback(*, user_id: int, data: str = f"news:a:{'a' * 32}"):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id),
        message=FakeMessage(),
        data=data,
        answer=AsyncMock(),
    )


def test_generic_user_cannot_forge_news_callback(monkeypatch) -> None:
    callback = _callback(user_id=7999)
    backend_call = AsyncMock()
    monkeypatch.setattr(news_editorial, "moderate_news_draft", backend_call)
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)

    asyncio.run(news_editorial.news_editorial_callback(callback))

    backend_call.assert_not_awaited()
    callback.answer.assert_awaited_once_with("Действие доступно только редактору", show_alert=True)


def test_admin_callback_is_private_revision_bound_and_removes_stale_buttons(monkeypatch) -> None:
    callback = _callback(user_id=7001)
    backend_call = AsyncMock(return_value="queued")
    monkeypatch.setattr(news_editorial, "moderate_news_draft", backend_call)
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)

    asyncio.run(news_editorial.news_editorial_callback(callback))

    backend_call.assert_awaited_once_with(
        draft_id="a" * 32,
        admin_telegram_user_id=7001,
        action="accept_for_design",
    )
    callback.message.edit_reply_markup.assert_awaited_once_with(reply_markup=None)
    callback.answer.assert_awaited_once_with(
        "Новая revision поставлена в очередь", show_alert=False
    )


def test_malformed_news_callback_never_calls_backend(monkeypatch) -> None:
    callback = _callback(user_id=7001, data="news:publish:anything")
    backend_call = AsyncMock()
    monkeypatch.setattr(news_editorial, "moderate_news_draft", backend_call)
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)

    asyncio.run(news_editorial.news_editorial_callback(callback))

    backend_call.assert_not_awaited()
    callback.answer.assert_awaited_once_with("Некорректное действие", show_alert=True)


def test_destructive_news_action_requires_confirmation(monkeypatch) -> None:
    callback = _callback(user_id=7001, data=f"newsp:x:{'a' * 32}:2")
    backend_call = AsyncMock()
    state = AsyncMock()
    monkeypatch.setattr(news_editorial, "moderate_news_draft", backend_call)
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)

    asyncio.run(news_editorial.news_publishing_callback(callback, state))

    backend_call.assert_not_awaited()
    callback.message.answer.assert_awaited_once()
    callback.answer.assert_awaited_once_with()


def test_publish_confirmation_repeats_channel_and_marks_payload_provisional(monkeypatch) -> None:
    callback = _callback(user_id=7001, data=f"newsp:p:{'a' * 32}:2")
    state = AsyncMock()
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)

    asyncio.run(news_editorial.news_publishing_callback(callback, state))

    confirmation = callback.message.answer.await_args.args[0]
    assert "Канал: @yfc_test_news (staging)" in confirmation
    assert "не финальный preview канала" in confirmation
    assert "production и финальный formatted preview" in confirmation
    callback.answer.assert_awaited_once_with()


def test_schedule_parser_accepts_nested_iana_timezone() -> None:
    match = news_editorial.SCHEDULE_INPUT_PATTERN.fullmatch(
        "2026-08-27 12:30 America/Argentina/Buenos_Aires"
    )
    assert match is not None
    assert match.group(3) == "America/Argentina/Buenos_Aires"


def test_uncertain_reconcile_keeps_exact_snapshot_id(monkeypatch) -> None:
    callback = _callback(user_id=7001, data=f"newsrec:r:{'b' * 32}")
    state = AsyncMock()
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)

    asyncio.run(news_editorial.news_reconcile_callback(callback, state))

    state.set_state.assert_awaited_once_with(
        news_editorial.NewsEditorialStates.awaiting_reconcile_message_id
    )
    saved = state.set_data.await_args.args[0]
    assert saved["snapshot_id"] == "b" * 32
    callback.answer.assert_awaited_once_with()


def test_uncertain_retry_calls_exact_owner_bound_snapshot(monkeypatch) -> None:
    callback = _callback(user_id=7001, data=f"newsrec:t:{'c' * 32}")
    state = AsyncMock()
    retry = AsyncMock(return_value="queued")
    monkeypatch.setattr(news_editorial, "Message", FakeMessage)
    monkeypatch.setattr(news_editorial, "retry_uncertain_publication", retry)

    asyncio.run(news_editorial.news_reconcile_callback(callback, state))

    retry.assert_awaited_once_with(
        snapshot_id="c" * 32,
        admin_telegram_user_id=7001,
    )
    state.set_state.assert_not_awaited()
    callback.message.edit_reply_markup.assert_awaited_once_with(reply_markup=None)
    callback.answer.assert_awaited_once_with("Повтор поставлен в очередь", show_alert=False)


def test_news_fsm_router_precedes_generic_support_handlers() -> None:
    assert bot_runtime.dp.sub_routers.index(news_editorial.router) < (
        bot_runtime.dp.sub_routers.index(feedback.router)
    )
