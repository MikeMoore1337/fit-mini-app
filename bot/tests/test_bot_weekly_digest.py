from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.fitminiapp_bot import bot as bot_runtime
from bot.fitminiapp_bot import weekly_digest


class FakeMessage:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(type="private", id=9001)
        self.from_user = SimpleNamespace(
            id=9001,
            username="reader",
            first_name="Reader",
            last_name=None,
        )
        self.text = ""
        self.answer = AsyncMock()
        self.edit_reply_markup = AsyncMock()
        self.edit_text = AsyncMock()


def _callback(*, data: str = "wd:off", user_id: int = 9001):
    return SimpleNamespace(
        from_user=SimpleNamespace(
            id=user_id,
            username="reader",
            first_name="Reader",
            last_name=None,
        ),
        message=FakeMessage(),
        data=data,
        answer=AsyncMock(),
    )


def _issue(*, status: str = "draft", blockers: list[str] | None = None) -> dict:
    return {
        "issue_id": "a" * 32,
        "issue_key": "2026-W35",
        "revision": 1,
        "status": status,
        "rendered_text": "<b>Еженедельный дайджест YFC</b>",
        "content_hash": "b" * 64,
        "channel_url": "https://t.me/yfc_test_news",
        "min_items": 3,
        "scheduled_for_utc": None,
        "timezone": "Europe/Moscow",
        "blockers": blockers or [],
        "items": [
            {
                "position": position,
                "headline": f"Материал {position}",
                "takeaway": f"Вывод {position}.",
                "category": "strength",
                "channel_permalink": f"https://t.me/yfc_test_news/{position}",
                "requires_owner_review": False,
            }
            for position in range(1, 4)
        ],
    }


def test_settings_shows_owner_approved_consent_and_explicit_opt_in(monkeypatch) -> None:
    message = FakeMessage()
    monkeypatch.setattr(weekly_digest, "digest_preference", AsyncMock(return_value=False))
    monkeypatch.setattr(weekly_digest.settings, "news_channel_username", "yfc_test_news")

    asyncio.run(weekly_digest.send_digest_settings(message))

    text = message.answer.await_args.args[0]
    assert "до пяти полезных материалов" in text
    assert "не влияет" in text
    assert "/settings" in text
    markup = message.answer.await_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].url == "https://t.me/yfc_test_news"
    assert markup.inline_keyboard[1][0].callback_data == "wd:on"
    assert weekly_digest._user_payload(message.from_user, enabled=True)["consent_version"] == (
        "weekly-news-v1"
    )


def test_settings_callback_updates_visible_state(monkeypatch) -> None:
    callback = _callback(data="wd:on")
    callback.message.text = f"{weekly_digest.CONSENT_COPY}\n\nСейчас дайджест выключен."
    monkeypatch.setattr(weekly_digest, "digest_preference", AsyncMock(return_value=True))
    monkeypatch.setattr(weekly_digest, "Message", FakeMessage)

    asyncio.run(weekly_digest.digest_preference_callback(callback))

    callback.message.edit_text.assert_awaited_once()
    assert "Сейчас дайджест включён." in callback.message.edit_text.await_args.args[0]
    callback.message.edit_reply_markup.assert_not_awaited()


def test_stale_digest_button_unsubscribes_current_private_user_without_confirmation(
    monkeypatch,
) -> None:
    callback = _callback()
    preference = AsyncMock(return_value=False)
    monkeypatch.setattr(weekly_digest, "digest_preference", preference)
    monkeypatch.setattr(weekly_digest, "Message", FakeMessage)

    asyncio.run(weekly_digest.digest_preference_callback(callback))

    preference.assert_awaited_once_with(callback.from_user, enabled=False)
    callback.message.edit_reply_markup.assert_awaited_once()
    callback.answer.assert_awaited_once_with("Дайджест отключён")


def test_digest_preference_callback_rejects_cross_chat_forgery(monkeypatch) -> None:
    callback = _callback()
    callback.message.chat.id = 9002
    preference = AsyncMock()
    monkeypatch.setattr(weekly_digest, "digest_preference", preference)
    monkeypatch.setattr(weekly_digest, "Message", FakeMessage)

    asyncio.run(weekly_digest.digest_preference_callback(callback))

    preference.assert_not_awaited()
    callback.answer.assert_awaited_once_with(
        "Настройка доступна только в личном чате",
        show_alert=True,
    )


def test_owner_preview_uses_exact_recipient_buttons_and_separate_controls() -> None:
    message = FakeMessage()
    asyncio.run(weekly_digest.send_issue_preview(message, _issue()))

    assert message.answer.await_count == 2
    exact_preview_call = message.answer.await_args_list[0]
    assert exact_preview_call.kwargs["parse_mode"] == "HTML"
    recipient_markup = exact_preview_call.kwargs["reply_markup"]
    assert recipient_markup.inline_keyboard[0][0].url == "https://t.me/yfc_test_news"
    assert recipient_markup.inline_keyboard[1][0].callback_data == "wd:off"
    control_call = message.answer.await_args_list[1]
    assert "Artifact:" in control_call.args[0]
    callbacks = [
        button.callback_data
        for row in control_call.kwargs["reply_markup"].inline_keyboard
        for button in row
        if button.callback_data is not None
    ]
    assert any(value.startswith("wda:a:") for value in callbacks)
    assert all(len(value.encode()) <= 64 for value in callbacks)


def test_quality_blocked_preview_has_no_approve_action() -> None:
    markup = weekly_digest._control_keyboard(_issue(blockers=["insufficient_content"]))
    callbacks = [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data is not None
    ]
    assert not any(value.startswith("wda:a:") for value in callbacks)


def test_digest_router_precedes_news_and_generic_handlers() -> None:
    assert bot_runtime.dp.sub_routers.index(
        weekly_digest.router
    ) < bot_runtime.dp.sub_routers.index(bot_runtime.news_editorial_router)
    assert bot_runtime.dp.sub_routers.index(
        weekly_digest.router
    ) < bot_runtime.dp.sub_routers.index(bot_runtime.public_router)
