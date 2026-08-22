import asyncio
import logging
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from bot.fitminiapp_bot import feedback
from bot.fitminiapp_bot.bot import dp
from bot.fitminiapp_bot.logging_config import JsonFormatter


class FakeState:
    def __init__(self, data=None, state="feedback"):
        self.data = dict(data or {})
        self.state = state

    async def clear(self):
        self.data.clear()
        self.state = None

    async def get_state(self):
        return self.state

    async def get_data(self):
        return dict(self.data)

    async def set_state(self, state):
        self.state = state

    async def update_data(self, **values):
        self.data.update(values)


def user_message(*, content_type=ContentType.TEXT, text="Нужна помощь", message_id=77):
    bot = SimpleNamespace(id=999, send_message=AsyncMock(), copy_message=AsyncMock())
    bot.send_message.return_value = SimpleNamespace(message_id=501)
    return SimpleNamespace(
        from_user=SimpleNamespace(
            id=101,
            username="visitor",
            full_name="Test <User>",
        ),
        bot=bot,
        chat=SimpleNamespace(id=101, type="private"),
        message_id=message_id,
        content_type=content_type,
        text=text,
        answer=AsyncMock(),
        reply_to_message=None,
    )


def test_support_deep_links_open_categories_and_privacy_warning() -> None:
    for payload, category in {
        "support_bug": "bug",
        "support_account": "account",
        "support_idea": "idea",
        "support_contact": "contact",
    }.items():
        message = user_message()
        state = FakeState()
        handled = asyncio.run(feedback.handle_feedback_start_payload(message, state, payload))
        assert handled is True
        assert state.data["category"] == category
        assert "пароли" in message.answer.await_args.args[0]

    generic = user_message()
    generic_state = FakeState()
    assert asyncio.run(feedback.handle_feedback_start_payload(generic, generic_state, "support"))
    keyboard = generic.answer.await_args.kwargs["reply_markup"]
    assert [row[0].text for row in keyboard.inline_keyboard] == list(
        feedback.CATEGORY_LABELS.values()
    )
    assert (
        asyncio.run(feedback.handle_feedback_start_payload(generic, generic_state, "unknown"))
        is False
    )


def test_supported_message_is_copied_to_admins_without_persisting_body(monkeypatch) -> None:
    monkeypatch.setattr(feedback.settings, "admin_telegram_user_ids", "7001,7002")
    monkeypatch.setattr(
        feedback,
        "create_support_case",
        AsyncMock(
            return_value=feedback.CreatedSupportCase(
                status="created",
                case_id="a" * 32,
                case_status="pending_relay",
            )
        ),
    )
    relay_result = AsyncMock()
    monkeypatch.setattr(feedback, "record_relay_result", relay_result)
    message = user_message(text="private support body")
    state = FakeState(data={"category": "bug", "started_at": 100.0})
    monkeypatch.setattr(feedback.time, "monotonic", lambda: 101.0)

    asyncio.run(feedback.handle_feedback_message(message, state))

    assert message.bot.send_message.await_count == 2
    headers = [call.kwargs["text"] for call in message.bot.send_message.await_args_list]
    assert all("private support body" not in header for header in headers)
    assert all("#yfc_support_" in header for header in headers)
    assert message.bot.copy_message.await_count == 2
    relay_result.assert_awaited_once_with("a" * 32, delivered=True)
    assert state.state is None
    assert "передано" in message.answer.await_args.args[0]


def test_duplicate_pending_relay_is_resumed_after_pre_delivery_crash(monkeypatch) -> None:
    monkeypatch.setattr(feedback.settings, "admin_telegram_user_ids", "7001")
    monkeypatch.setattr(
        feedback,
        "create_support_case",
        AsyncMock(
            return_value=feedback.CreatedSupportCase(
                status="duplicate",
                case_id="d" * 32,
                case_status="pending_relay",
            )
        ),
    )
    relay_result = AsyncMock()
    monkeypatch.setattr(feedback, "record_relay_result", relay_result)
    message = user_message(message_id=79)
    state = FakeState(data={"category": "bug", "started_at": 100.0})
    monkeypatch.setattr(feedback.time, "monotonic", lambda: 101.0)

    asyncio.run(feedback.handle_feedback_message(message, state))

    message.bot.copy_message.assert_awaited_once()
    relay_result.assert_awaited_once_with("d" * 32, delivered=True)
    assert "передано" in message.answer.await_args.args[0]


def test_unsupported_media_and_expired_state_are_not_relayed(monkeypatch) -> None:
    create_case = AsyncMock()
    monkeypatch.setattr(feedback, "create_support_case", create_case)
    monkeypatch.setattr(feedback.settings, "admin_telegram_user_ids", "7001")

    unsupported = user_message(content_type=ContentType.VIDEO, text=None)
    active = FakeState(data={"category": "other", "started_at": 100.0})
    monkeypatch.setattr(feedback.time, "monotonic", lambda: 101.0)
    asyncio.run(feedback.handle_feedback_message(unsupported, active))
    assert "текст, фото или документ" in unsupported.answer.await_args.args[0]

    expired = user_message(message_id=78)
    stale = FakeState(data={"category": "bug", "started_at": 100.0})
    monkeypatch.setattr(
        feedback.time,
        "monotonic",
        lambda: 100.0 + feedback.FEEDBACK_TTL_SECONDS,
    )
    asyncio.run(feedback.handle_feedback_message(expired, stale))
    assert stale.state is None
    assert "истекло" in expired.answer.await_args.args[0]
    create_case.assert_not_awaited()


def test_cancel_resets_active_feedback_state() -> None:
    message = user_message()
    state = FakeState(data={"category": "idea", "started_at": 100.0})

    asyncio.run(feedback.cancel_feedback(message, state))

    assert state.state is None
    assert "отменено" in message.answer.await_args.args[0]


def test_free_text_outside_feedback_state_is_unhandled() -> None:
    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(UTC),
            chat=Chat(id=101, type="private"),
            from_user=User(id=101, is_bot=False, first_name="Test"),
            text="Это не обращение",
        ),
    )

    async def feed_update():
        bot = Bot("123456:test-token")
        try:
            return await dp.feed_update(bot, update)
        finally:
            await bot.session.close()

    assert asyncio.run(feed_update()) is UNHANDLED


def test_admin_reply_requires_allowlist_bot_header_and_backend_binding(monkeypatch) -> None:
    monkeypatch.setattr(feedback.settings, "admin_telegram_user_ids", "7001")
    claim = AsyncMock(
        return_value=feedback.ClaimedSupportReply(status="claimed", telegram_user_id=101)
    )
    result = AsyncMock(return_value=True)
    monkeypatch.setattr(feedback, "claim_support_reply", claim)
    monkeypatch.setattr(feedback, "record_reply_result", result)
    bot = SimpleNamespace(
        id=999,
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=601)),
        copy_message=AsyncMock(),
        delete_message=AsyncMock(),
    )
    admin_message = SimpleNamespace(
        from_user=SimpleNamespace(id=7001),
        bot=bot,
        chat=SimpleNamespace(id=7001, type="private"),
        message_id=88,
        content_type=ContentType.TEXT,
        text="Ответ",
        reply_to_message=SimpleNamespace(
            from_user=SimpleNamespace(id=999),
            text=(
                "Новое обращение · Ошибка\n"
                f"Пользователь: Test\n{feedback.support_case_marker('b' * 32)}"
            ),
            caption=None,
        ),
        answer=AsyncMock(),
    )

    asyncio.run(feedback.handle_admin_reply(admin_message))

    claim.assert_awaited_once_with(
        case_id="b" * 32,
        admin_telegram_user_id=7001,
        reply_message_id=88,
    )
    bot.copy_message.assert_awaited_once_with(
        chat_id=101,
        from_chat_id=7001,
        message_id=88,
        reply_to_message_id=601,
    )
    result.assert_awaited_once_with(
        case_id="b" * 32,
        admin_telegram_user_id=7001,
        reply_message_id=88,
        outcome="delivered",
    )

    forged = SimpleNamespace(**vars(admin_message))
    forged.from_user = SimpleNamespace(id=8001)
    forged.chat = SimpleNamespace(id=8001, type="private")
    asyncio.run(feedback.handle_admin_reply(forged))
    assert claim.await_count == 1


def test_blocked_user_is_terminal_without_retry(monkeypatch) -> None:
    monkeypatch.setattr(feedback.settings, "admin_telegram_user_ids", "7001")
    monkeypatch.setattr(
        feedback,
        "claim_support_reply",
        AsyncMock(
            return_value=feedback.ClaimedSupportReply(status="claimed", telegram_user_id=101)
        ),
    )
    result = AsyncMock(return_value=True)
    monkeypatch.setattr(feedback, "record_reply_result", result)
    bot = SimpleNamespace(
        id=999,
        send_message=AsyncMock(
            side_effect=TelegramForbiddenError(
                method=SendMessage(chat_id=101, text="Ответ команды Your Fitness Coach:"),
                message="Forbidden",
            )
        ),
        copy_message=AsyncMock(),
    )
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=7001),
        bot=bot,
        chat=SimpleNamespace(id=7001, type="private"),
        message_id=89,
        content_type=ContentType.TEXT,
        text="Ответ",
        reply_to_message=SimpleNamespace(
            from_user=SimpleNamespace(id=999),
            text=(
                "Новое обращение · Ошибка\n"
                f"Пользователь: Test\n{feedback.support_case_marker('c' * 32)}"
            ),
            caption=None,
        ),
        answer=AsyncMock(),
    )

    asyncio.run(feedback.handle_admin_reply(message))

    bot.copy_message.assert_not_awaited()
    result.assert_awaited_once_with(
        case_id="c" * 32,
        admin_telegram_user_id=7001,
        reply_message_id=89,
        outcome="blocked",
    )
    assert "Повторов не будет" in message.answer.await_args.args[0]


def test_uncertain_reply_result_warns_admin_and_does_not_invite_retry(monkeypatch) -> None:
    monkeypatch.setattr(feedback.settings, "admin_telegram_user_ids", "7001")
    monkeypatch.setattr(
        feedback,
        "claim_support_reply",
        AsyncMock(
            return_value=feedback.ClaimedSupportReply(status="claimed", telegram_user_id=101)
        ),
    )
    monkeypatch.setattr(feedback, "record_reply_result", AsyncMock(return_value=False))
    bot = SimpleNamespace(
        id=999,
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=602)),
        copy_message=AsyncMock(),
        delete_message=AsyncMock(),
    )
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=7001),
        bot=bot,
        chat=SimpleNamespace(id=7001, type="private"),
        message_id=90,
        content_type=ContentType.TEXT,
        text="Ответ",
        reply_to_message=SimpleNamespace(
            from_user=SimpleNamespace(id=999),
            text=(
                "Новое обращение · Ошибка\n"
                f"Пользователь: Test\n{feedback.support_case_marker('e' * 32)}"
            ),
            caption=None,
        ),
        answer=AsyncMock(),
    )

    asyncio.run(feedback.handle_admin_reply(message))

    bot.copy_message.assert_awaited_once()
    assert "Не повторяйте ответ" in message.answer.await_args.args[0]


def test_support_logs_do_not_serialize_private_text_or_ids() -> None:
    record = logging.LogRecord(
        name="bot.fitminiapp_bot.feedback",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="private body from 123456789",
        args=(),
        exc_info=None,
    )
    rendered = JsonFormatter().format(record)
    assert "private body" not in rendered
    assert "123456789" not in rendered
    assert '"message":"application_log"' in rendered
