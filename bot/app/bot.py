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


async def set_mini_app_menu_button(bot: Bot, user_id: int | None = None) -> None:
    try:
        await bot.set_chat_menu_button(
            user_id=user_id,
            menu_button=MenuButtonWebApp(
                text="Открыть Mini App",
                web_app=WebAppInfo(url=mini_app_url()),
            ),
        )
    except Exception as exc:
        print(f"Failed to set Mini App menu button: {exc}")


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

    await set_mini_app_menu_button(
        message.bot,
        user_id=message.from_user.id if message.from_user else None,
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
    await set_mini_app_menu_button(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
