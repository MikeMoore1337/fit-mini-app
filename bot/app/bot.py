import asyncio
import hashlib
import logging
import math
from functools import lru_cache
from pathlib import Path
from typing import TextIO
from urllib.parse import urlparse
from zoneinfo import available_timezones

import httpx
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.dispatcher import DEFAULT_BACKOFF_CONFIG
from aiogram.exceptions import TelegramConflictError
from aiogram.filters import Command, CommandStart
from aiogram.methods import GetUpdates
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)
from aiogram.utils.backoff import Backoff, BackoffConfig

from .config import settings

try:
    import fcntl
except ImportError:  # pragma: no cover - production container runs Linux
    fcntl = None


logger = logging.getLogger(__name__)


class PollingConflict(RuntimeError):
    """Another process is already receiving updates for this Telegram bot."""


class StableDispatcher(Dispatcher):
    @classmethod
    async def _listen_updates(
        cls,
        bot: Bot,
        polling_timeout: int = 30,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: list[str] | None = None,
    ):
        """Retry network errors, but let the supervisor handle polling conflicts."""
        backoff = Backoff(config=backoff_config)
        get_updates = GetUpdates(timeout=polling_timeout, allowed_updates=allowed_updates)
        request_kwargs = {}
        if bot.session.timeout:
            request_kwargs["request_timeout"] = int(bot.session.timeout + polling_timeout)

        failed = False
        while True:
            try:
                updates = await bot(get_updates, **request_kwargs)
            except TelegramConflictError as exc:
                raise PollingConflict(str(exc)) from exc
            except Exception as exc:
                failed = True
                logger.error(
                    "Не удалось получить обновления Telegram: %s: %s", type(exc).__name__, exc
                )
                logger.warning(
                    "Повтор получения обновлений через %.1f с (попытка %d, bot id=%d)",
                    backoff.next_delay,
                    backoff.counter,
                    bot.id,
                )
                await backoff.asleep()
                continue

            if failed:
                logger.info(
                    "Связь с Telegram восстановлена (попыток: %d, bot id=%d)",
                    backoff.counter,
                    bot.id,
                )
                backoff.reset()
                failed = False

            for update in updates:
                yield update
                get_updates.offset = update.update_id + 1


class PollingFileLock:
    """Cross-container lock backed by a shared Docker volume."""

    def __init__(self, directory: str, bot_token: str) -> None:
        token_hash = hashlib.sha256(bot_token.encode("utf-8")).hexdigest()[:24]
        self.path = Path(directory) / f"polling-{token_hash}.lock"
        self._file: TextIO | None = None

    async def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a+", encoding="utf-8")

        if fcntl is None:
            logger.warning("Файловая singleton-блокировка недоступна на этой платформе")
            return

        waiting_logged = False
        while True:
            try:
                fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info("Получена singleton-блокировка Telegram polling: %s", self.path)
                return
            except BlockingIOError:
                if not waiting_logged:
                    logger.warning(
                        "Другой контейнер уже обслуживает этого Telegram-бота; ожидаем блокировку %s",
                        self.path,
                    )
                    waiting_logged = True
                await asyncio.sleep(5)

    def release(self) -> None:
        if self._file is None:
            return
        if fcntl is not None:
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()
        self._file = None


dp = StableDispatcher()
MINI_APP_CACHE_VERSION = "56"
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
TIMEZONE_REGION_LABELS = {
    "Europe": "Европа",
    "Asia": "Азия",
    "America": "Америка",
    "Africa": "Африка",
    "Australia": "Австралия",
    "Pacific": "Тихий океан",
    "Atlantic": "Атлантика",
    "Indian": "Индийский океан",
    "Antarctica": "Антарктика",
    "Etc": "UTC и прочие",
}


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
        current_row.append(
            InlineKeyboardButton(
                text=TIMEZONE_REGION_LABELS.get(region, region),
                callback_data=f"tz:r:{region}:0",
            )
        )
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([InlineKeyboardButton(text="MSK / Москва", callback_data="tz:set:Europe/Moscow")])
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
                headers={"X-Bot-Token": settings.bot_internal_token},
                json=payload,
            )
            response.raise_for_status()
        return True
    except Exception as exc:
        print(
            f"Не удалось сохранить часовой пояс {timezone} через backend {url}: {exc!r}", flush=True
        )
        return False


async def set_mini_app_menu_button(bot: Bot, chat_id: int | None = None) -> bool:
    url = mini_app_url()
    if not is_https_url(url):
        print(
            f"Кнопка меню FitMiniApp пропущена: FRONTEND_BASE_URL должен быть HTTPS, получено {url}",
            flush=True,
        )
        return False

    try:
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonWebApp(
                text="Открыть FitMiniApp",
                web_app=WebAppInfo(url=url),
            ),
        )
        print(f"Кнопка меню FitMiniApp настроена для {url}", flush=True)
        return True
    except Exception as exc:
        print(f"Не удалось настроить кнопку меню FitMiniApp для {url}: {exc!r}", flush=True)
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
            print(f"Не удалось отправить кнопку FitMiniApp для {url}: {exc!r}", flush=True)
    else:
        print(f"Кнопке FitMiniApp нужен HTTPS URL, получено {url}", flush=True)

    await message.answer(
        "Кнопка FitMiniApp временно недоступна. Попробуйте открыть приложение через меню бота позже."
    )


@dp.message(CommandStart())
async def start(message: Message) -> None:
    menu_button_ok = await set_mini_app_menu_button(
        message.bot,
        chat_id=message.from_user.id if message.from_user else None,
    )
    if menu_button_ok:
        await message.answer("Кнопка FitMiniApp закреплена внизу. Часовой пояс: /timezone")
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
                f"Регион: {TIMEZONE_REGION_LABELS.get(region, region)}. Выберите часовой пояс.",
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
    if not settings.bot_polling_enabled:
        print("Polling бота отключён: BOT_POLLING_ENABLED=false", flush=True)
        while True:
            await asyncio.sleep(3600)

    if not settings.bot_token or settings.bot_token == "replace-me":
        print("Токен бота не настроен, бот ожидает", flush=True)
        while True:
            await asyncio.sleep(3600)

    polling_lock = PollingFileLock(settings.bot_polling_lock_dir, settings.bot_token)

    while True:
        await polling_lock.acquire()
        bot = Bot(settings.bot_token)
        conflict = False
        try:
            print(
                f"Бот запускает получение сообщений. URL FitMiniApp: {mini_app_url()}", flush=True
            )
            await set_mini_app_menu_button(bot)
            print("Получение сообщений ботом запущено", flush=True)
            await dp.start_polling(bot)
        except PollingConflict as exc:
            conflict = True
            logger.critical(
                "Обнаружен TelegramConflictError: тот же токен используется вне текущей "
                "singleton-блокировки. Локальный polling остановлен на %d секунд: %s",
                settings.bot_conflict_retry_seconds,
                exc,
            )
        finally:
            polling_lock.release()

        if not conflict:
            return
        await asyncio.sleep(settings.bot_conflict_retry_seconds)


if __name__ == "__main__":
    asyncio.run(main())
