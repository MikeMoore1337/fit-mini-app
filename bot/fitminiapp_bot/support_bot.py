"""Temporary owner-controlled redirect for the former public support bot.

This module must be removed together with its token/service only after the owner confirms that
the transition window is complete. It never accepts or relays support request content.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .logging_config import configure_logging
from .support_config import settings

logger = logging.getLogger(__name__)
dp = Dispatcher()
MAIN_SUPPORT_URL = "https://t.me/your_fitness_coach_bot?start=support"
REDIRECT_TEXT = (
    "Поддержка Your Fitness Coach переехала в основной бот. "
    "Нажмите кнопку ниже и выберите категорию обращения. "
    "Сообщения, отправленные в этот старый бот, не пересылаются."
)


def redirect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Перейти в поддержку", url=MAIN_SUPPORT_URL)]]
    )


@dp.message(F.chat.type == "private")
async def redirect_to_main_bot(message: Message) -> None:
    await message.answer(REDIRECT_TEXT, reply_markup=redirect_keyboard())


async def main() -> None:
    configure_logging()
    if not settings.support_bot_enabled:
        logger.warning("legacy_support_redirect_disabled")
        while True:
            await asyncio.sleep(3600)

    if not settings.support_bot_token or settings.support_bot_token in {"change-me", "replace-me"}:
        raise RuntimeError("SUPPORT_BOT_TOKEN must be configured for the temporary redirect")

    bot = Bot(settings.support_bot_token)
    try:
        logger.info("legacy_support_redirect_polling_started")
        await dp.start_polling(bot, polling_timeout=settings.support_bot_polling_timeout)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
