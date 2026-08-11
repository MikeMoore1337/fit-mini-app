import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.fitminiapp_bot import support_bot


def user_message(*, user_id: int = 101, username: str | None = "visitor"):
    bot = SimpleNamespace(send_message=AsyncMock(), copy_message=AsyncMock())
    bot.send_message.return_value = SimpleNamespace(message_id=501)
    return SimpleNamespace(
        from_user=SimpleNamespace(
            id=user_id,
            username=username,
            full_name="Test <User>",
        ),
        bot=bot,
        chat=SimpleNamespace(id=user_id),
        message_id=77,
        answer=AsyncMock(),
        reply_to_message=None,
    )


def test_user_message_is_copied_to_each_admin_without_exposing_admin_accounts(monkeypatch):
    monkeypatch.setattr(
        support_bot.settings,
        "support_admin_telegram_user_ids",
        "7001, 7002",
    )
    message = user_message()

    asyncio.run(support_bot.handle_user_message(message))

    assert message.bot.send_message.await_count == 2
    header = message.bot.send_message.await_args_list[0].kwargs["text"]
    assert "#support_101" in header
    assert "Test &lt;User&gt;" in header
    assert message.bot.copy_message.await_count == 2
    assert {call.kwargs["chat_id"] for call in message.bot.copy_message.await_args_list} == {
        7001,
        7002,
    }
    assert "Ответ придёт сюда от имени этого бота" in message.answer.await_args.args[0]


def test_admin_reply_is_copied_back_to_request_author(monkeypatch):
    monkeypatch.setattr(support_bot.settings, "support_admin_telegram_user_ids", "7001")
    bot = SimpleNamespace(copy_message=AsyncMock())
    message = SimpleNamespace(
        bot=bot,
        chat=SimpleNamespace(id=7001),
        message_id=88,
        reply_to_message=SimpleNamespace(text="Новое обращение #support_101"),
        answer=AsyncMock(),
    )

    asyncio.run(support_bot.handle_admin_message(message))

    bot.copy_message.assert_awaited_once_with(
        chat_id=101,
        from_chat_id=7001,
        message_id=88,
    )
    message.answer.assert_awaited_once_with("Ответ доставлен пользователю.")


def test_admin_must_reply_to_service_message():
    message = SimpleNamespace(
        bot=SimpleNamespace(copy_message=AsyncMock()),
        reply_to_message=None,
        answer=AsyncMock(),
    )

    asyncio.run(support_bot.handle_admin_message(message))

    message.bot.copy_message.assert_not_awaited()
    assert "ответьте на служебное сообщение" in message.answer.await_args.args[0]


def test_failed_delivery_returns_safe_retry_message(monkeypatch):
    monkeypatch.setattr(support_bot.settings, "support_admin_telegram_user_ids", "7001")
    message = user_message()
    message.bot.send_message.side_effect = RuntimeError("Telegram unavailable")

    asyncio.run(support_bot.handle_user_message(message))

    message.bot.copy_message.assert_not_awaited()
    assert "попробуйте ещё раз позже" in message.answer.await_args.args[0]


def test_support_admin_ids_accept_commas_and_semicolons(monkeypatch):
    monkeypatch.setattr(
        support_bot.settings,
        "support_admin_telegram_user_ids",
        "7001; 7002,7001",
    )

    assert support_bot.settings.admin_telegram_id_set == {7001, 7002}


def test_id_command_works_before_support_admin_is_configured(monkeypatch):
    monkeypatch.setattr(support_bot.settings, "support_admin_telegram_user_ids", "")
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=7001),
        answer=AsyncMock(),
    )

    asyncio.run(support_bot.show_telegram_id(message))

    message.answer.assert_awaited_once_with("Ваш Telegram ID: 7001")
