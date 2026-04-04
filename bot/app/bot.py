import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from app.config import settings

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть FitMiniApp",
                    web_app=WebAppInfo(url=f"{settings.frontend_base_url}/app?v=4"),
                )
            ]
        ]
    )

    await message.answer(
        "Открой Mini App кнопкой под этим сообщением.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await message.answer(
        "Нажми кнопку ниже:",
        reply_markup=inline_keyboard,
    )


async def main() -> None:
    if not settings.bot_token or settings.bot_token == "replace-me":
        print("BOT_TOKEN not configured - bot is idle")
        while True:
            await asyncio.sleep(3600)

    bot = Bot(settings.bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
