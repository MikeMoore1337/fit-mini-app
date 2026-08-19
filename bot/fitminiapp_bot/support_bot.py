import asyncio
import html
import logging
import re

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, Message

from .logging_config import configure_logging
from .support_config import settings

logger = logging.getLogger(__name__)

SUPPORT_MARKER_PATTERN = re.compile(r"(?:^|\s)#support_(\d+)(?:\s|$)")
dp = Dispatcher()


def safe_error_code(error: Exception) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        return f"http_status:{error.response.status_code}"
    if isinstance(error, httpx.TimeoutException):
        return "timeout"
    if isinstance(error, httpx.RequestError):
        return "transport_error"
    return f"unexpected:{type(error).__name__}"


def support_marker(telegram_user_id: int) -> str:
    return f"#support_{telegram_user_id}"


def support_target_from_reply(message: Message) -> int | None:
    replied = message.reply_to_message
    if replied is None or not replied.text:
        return None
    match = SUPPORT_MARKER_PATTERN.search(replied.text)
    return int(match.group(1)) if match else None


def support_request_header(message: Message) -> str:
    user = message.from_user
    if user is None:
        raise ValueError("Support message has no sender")

    display_name = html.escape(user.full_name or "Без имени")
    username = f" (@{html.escape(user.username)})" if user.username else ""
    return (
        f"Новое обращение {support_marker(user.id)}\n"
        f'Пользователь: <a href="tg://user?id={user.id}">{display_name}</a>{username}\n\n'
        "Ответьте именно на это служебное сообщение — бот доставит ответ пользователю."
    )


async def handle_user_message(message: Message) -> None:
    if message.from_user is None or message.bot is None:
        return

    delivered = 0
    for admin_id in settings.admin_telegram_id_set:
        try:
            header = await message.bot.send_message(
                chat_id=admin_id,
                text=support_request_header(message),
                parse_mode="HTML",
            )
            await message.bot.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                reply_to_message_id=header.message_id,
            )
            delivered += 1
        except Exception as exc:
            logger.error(
                "support_request_delivery_failed",
                extra={"error_code": safe_error_code(exc)},
            )

    if delivered:
        await message.answer(
            "Сообщение передано в поддержку. Ответ придёт сюда от имени этого бота."
        )
        return

    await message.answer(
        "Не удалось передать сообщение в поддержку. Пожалуйста, попробуйте ещё раз позже."
    )


async def handle_admin_message(message: Message) -> None:
    if message.bot is None:
        return

    target_user_id = support_target_from_reply(message)
    if target_user_id is None:
        await message.answer(
            "Чтобы ответить пользователю, ответьте на служебное сообщение с номером обращения."
        )
        return

    try:
        await message.bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception as exc:
        logger.error(
            "support_response_delivery_failed",
            extra={"error_code": safe_error_code(exc)},
        )
        await message.answer("Не удалось доставить ответ пользователю.")
        return

    await message.answer("Ответ доставлен пользователю.")


@dp.message(CommandStart(), F.chat.type == "private")
async def start(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Это поддержка Your Fitness Coach.\n\n"
        "Опишите вопрос и при необходимости приложите скриншот. "
        "Специалист ответит вам здесь от имени бота."
    )


@dp.message(Command("id"), F.chat.type == "private")
async def show_telegram_id(message: Message) -> None:
    if message.from_user is None:
        return
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")


@dp.message(F.chat.type == "private")
async def route_support_message(message: Message) -> None:
    if message.chat.id in settings.admin_telegram_id_set:
        await handle_admin_message(message)
        return
    await handle_user_message(message)


async def main() -> None:
    configure_logging()
    if not settings.support_bot_enabled:
        logger.warning("support_bot_disabled")
        while True:
            await asyncio.sleep(3600)

    if not settings.support_bot_token or settings.support_bot_token in {"change-me", "replace-me"}:
        raise RuntimeError("SUPPORT_BOT_TOKEN must be configured")

    bot = Bot(settings.support_bot_token)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть поддержку"),
            BotCommand(command="id", description="Показать мой Telegram ID"),
        ]
    )
    try:
        logger.info("support_bot_polling_started")
        await dp.start_polling(bot, polling_timeout=settings.support_bot_polling_timeout)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
