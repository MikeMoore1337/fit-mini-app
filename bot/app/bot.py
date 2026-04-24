import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from app.config import settings

dp = Dispatcher()


def mini_app_url() -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/app?v=23"


@dp.message(CommandStart())
async def start(message: Message) -> None:
    web_app = WebAppInfo(url=mini_app_url())
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть FitMiniApp",
                    web_app=web_app,
                )
            ]
        ]
    )

    await message.bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(
            text="Открыть Mini App",
            web_app=web_app,
        ),
    )

    await message.answer(
        "Открой Mini App кнопкой в меню чата или кнопкой под этим сообщением.",
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
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Открыть Mini App",
            web_app=WebAppInfo(url=mini_app_url()),
        ),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
