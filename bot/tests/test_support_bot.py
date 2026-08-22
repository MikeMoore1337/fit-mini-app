import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.fitminiapp_bot import support_bot


def test_legacy_support_bot_only_redirects_without_relaying_content() -> None:
    message = SimpleNamespace(answer=AsyncMock())

    asyncio.run(support_bot.redirect_to_main_bot(message))

    message.answer.assert_awaited_once()
    text = message.answer.await_args.args[0]
    keyboard = message.answer.await_args.kwargs["reply_markup"]
    assert "переехала" in text
    assert "не пересылаются" in text
    assert keyboard.inline_keyboard[0][0].url == (
        "https://t.me/your_fitness_coach_bot?start=support"
    )
