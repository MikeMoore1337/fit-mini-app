import asyncio
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

from app.config import settings

dp = Dispatcher()
MINI_APP_CACHE_VERSION = "29"


def mini_app_url() -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/app?v={MINI_APP_CACHE_VERSION}"


def is_https_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def web_app_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть FitMiniApp",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


def url_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть FitMiniApp", url=url)]]
    )


async def set_mini_app_menu_button(bot: Bot, chat_id: int | None = None) -> None:
    url = mini_app_url()
    if not is_https_url(url):
        print(f"Skipped Mini App menu button: FRONTEND_BASE_URL must be HTTPS, got {url}")
        return

    try:
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonWebApp(
                text="Открыть Mini App",
                web_app=WebAppInfo(url=url),
            ),
        )
    except Exception as exc:
        print(f"Failed to set Mini App menu button for {url}: {exc!r}")


async def answer_with_open_button(message: Message) -> None:
    url = mini_app_url()

    if is_https_url(url):
        try:
            await message.answer(
                "Открой FitMiniApp кнопкой ниже.",
                reply_markup=web_app_keyboard(url),
            )
            return
        except Exception as exc:
            print(f"Failed to send Mini App web_app button for {url}: {exc!r}")
    else:
        print(f"Mini App web_app button requires HTTPS URL, got {url}")

    try:
        await message.answer(
            "Telegram не принял Mini App кнопку. Открой приложение по ссылке ниже.",
            reply_markup=url_keyboard(url),
        )
    except Exception as exc:
        print(f"Failed to send fallback URL button for {url}: {exc!r}")
        await message.answer(f"Открыть FitMiniApp: {url}")


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await set_mini_app_menu_button(
        message.bot,
        chat_id=message.from_user.id if message.from_user else None,
    )
    await answer_with_open_button(message)


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
