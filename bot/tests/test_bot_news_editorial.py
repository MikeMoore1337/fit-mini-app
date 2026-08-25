from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.fitminiapp_bot import news_editorial


class FakeMessage:
    def __init__(self, *, chat_type: str = "private") -> None:
        self.chat = SimpleNamespace(type=chat_type)
        self.edit_reply_markup = AsyncMock()


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
