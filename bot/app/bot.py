import asyncio
import math
from functools import lru_cache
from urllib.parse import urlparse
from zoneinfo import available_timezones

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

from app.config import settings

dp = Dispatcher()
MINI_APP_CACHE_VERSION = "33"
TIMEZONE_PAGE_SIZE = 8
TIMEZONE_REGIONS = [
    "Europe",
    "Asia",
    "America",
    "Africa",
    "Australia",
    "Pacific",
    "Atlantic",
    "Indian",
    "Antarctica",
    "Etc",
]


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


@lru_cache(maxsize=len(TIMEZONE_REGIONS))
def region_timezones(region: str) -> tuple[str, ...]:
    if region == "Etc":
        return tuple(
            sorted(
                timezone
                for timezone in available_timezones()
                if timezone == "UTC" or timezone.startswith("Etc/")
            )
        )
    return tuple(
        sorted(timezone for timezone in available_timezones() if timezone.startswith(f"{region}/"))
    )


def timezone_regions_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []
    for region in TIMEZONE_REGIONS:
        current_row.append(InlineKeyboardButton(text=region, callback_data=f"tz:r:{region}:0"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append(
        [InlineKeyboardButton(text="MSK / Europe/Moscow", callback_data="tz:set:Europe/Moscow")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def timezone_page_keyboard(region: str, page: int = 0) -> InlineKeyboardMarkup:
    timezones = region_timezones(region)
    total_pages = max(1, math.ceil(len(timezones) / TIMEZONE_PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    start = page * TIMEZONE_PAGE_SIZE
    page_timezones = timezones[start : start + TIMEZONE_PAGE_SIZE]

    rows = [
        [InlineKeyboardButton(text=timezone, callback_data=f"tz:set:{timezone}")]
        for timezone in page_timezones
    ]

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="Назад", callback_data=f"tz:r:{region}:{page - 1}")
        )
    nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="tz:noop"))
    if page + 1 < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Дальше", callback_data=f"tz:r:{region}:{page + 1}")
        )
    rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="К регионам", callback_data="tz:regions")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def save_timezone_from_bot(telegram_user, timezone: str) -> bool:
    if not telegram_user:
        return False

    payload = {
        "telegram_user_id": telegram_user.id,
        "timezone": timezone,
        "username": telegram_user.username,
        "first_name": telegram_user.first_name,
        "last_name": telegram_user.last_name,
    }
    url = f"{settings.backend_internal_url.rstrip('/')}/api/v1/bot/timezone"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                headers={"X-Bot-Token": settings.bot_token},
                json=payload,
            )
            response.raise_for_status()
        return True
    except Exception as exc:
        print(f"Failed to save timezone {timezone} via backend {url}: {exc!r}", flush=True)
        return False


async def set_mini_app_menu_button(bot: Bot, chat_id: int | None = None) -> bool:
    url = mini_app_url()
    if not is_https_url(url):
        print(
            f"Skipped Mini App menu button: FRONTEND_BASE_URL must be HTTPS, got {url}", flush=True
        )
        return False

    try:
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonWebApp(
                text="Открыть Mini App",
                web_app=WebAppInfo(url=url),
            ),
        )
        print(f"Mini App menu button configured for {url}", flush=True)
        return True
    except Exception as exc:
        print(f"Failed to set Mini App menu button for {url}: {exc!r}", flush=True)
        return False


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
            print(f"Failed to send Mini App web_app button for {url}: {exc!r}", flush=True)
    else:
        print(f"Mini App web_app button requires HTTPS URL, got {url}", flush=True)

    try:
        await message.answer(
            "Telegram не принял Mini App кнопку. Открой приложение по ссылке ниже.",
            reply_markup=url_keyboard(url),
        )
    except Exception as exc:
        print(f"Failed to send fallback URL button for {url}: {exc!r}", flush=True)
        await message.answer(f"Открыть FitMiniApp: {url}")


@dp.message(CommandStart())
async def start(message: Message) -> None:
    menu_button_ok = await set_mini_app_menu_button(
        message.bot,
        chat_id=message.from_user.id if message.from_user else None,
    )
    if menu_button_ok:
        await message.answer("Кнопка Mini App закреплена внизу. Часовой пояс: /timezone")
        return

    await answer_with_open_button(message)


@dp.message(Command("timezone"))
async def timezone_command(message: Message) -> None:
    await message.answer(
        "Выберите регион часового пояса.",
        reply_markup=timezone_regions_keyboard(),
    )


@dp.callback_query(lambda callback: bool(callback.data and callback.data.startswith("tz:")))
async def timezone_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""

    if data == "tz:noop":
        await callback.answer()
        return

    if data == "tz:regions":
        if callback.message:
            await callback.message.edit_text(
                "Выберите регион часового пояса.",
                reply_markup=timezone_regions_keyboard(),
            )
        await callback.answer()
        return

    if data.startswith("tz:r:"):
        _, _, region, page_raw = data.split(":", 3)
        page = int(page_raw) if page_raw.isdigit() else 0
        if callback.message:
            await callback.message.edit_text(
                f"Регион: {region}. Выберите часовой пояс.",
                reply_markup=timezone_page_keyboard(region, page),
            )
        await callback.answer()
        return

    if data.startswith("tz:set:"):
        timezone = data.removeprefix("tz:set:")
        if not callback.message:
            await callback.answer("Не удалось сохранить часовой пояс", show_alert=True)
            return

        ok = await save_timezone_from_bot(callback.from_user, timezone)
        if ok:
            await callback.message.edit_text(f"Часовой пояс сохранён: {timezone}")
            await callback.answer("Сохранено")
            return

        await callback.answer("Не удалось сохранить часовой пояс", show_alert=True)


async def main() -> None:
    if not settings.bot_token or settings.bot_token == "replace-me":
        print("BOT_TOKEN not configured - bot is idle", flush=True)
        while True:
            await asyncio.sleep(3600)

    bot = Bot(settings.bot_token)
    print(f"Bot starting polling. Mini App URL: {mini_app_url()}", flush=True)
    await set_mini_app_menu_button(bot)
    print("Bot polling started", flush=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
