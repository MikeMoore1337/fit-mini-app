from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from aiogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    WebAppInfo,
)

EXPECTED_BOT_USERNAME = "your_fitness_coach_bot"
PUBLIC_BOT_NAME = "Your Fitness Coach"
PUBLIC_BOT_SHORT_DESCRIPTION = (
    "Тренировки, питание, прогресс и работа с тренером - в одном приложении."
)
PUBLIC_BOT_DESCRIPTION = (
    "Your Fitness Coach помогает планировать тренировки, вести дневник питания и "
    "отслеживать прогресс в Telegram и браузере.\n\n"
    "Откройте приложение, чтобы работать с программами, тренировками, питанием и "
    "результатами. Через этого же бота можно получить помощь, сообщить об ошибке или "
    "предложить улучшение."
)
MENU_BUTTON_LABEL = "Открыть приложение"
AVATAR_PATH = Path(__file__).with_name("assets") / "yfc-bot-avatar.jpg"


@dataclass(frozen=True, slots=True)
class PublicCommand:
    command: str
    description: str


PUBLIC_COMMANDS = (
    PublicCommand("start", "Главное меню"),
    PublicCommand("app", "Открыть приложение"),
    PublicCommand("support", "Помощь и обратная связь"),
    PublicCommand("settings", "Настройки и уведомления"),
    PublicCommand("help", "Возможности и команды"),
    PublicCommand("privacy", "Политика конфиденциальности"),
)
HIDDEN_COMMANDS = (
    "feedback",
    "cancel",
    "timezone",
    "digest_review",
    "news_off",
    "unsubscribe",
    "stop_news",
)


def is_valid_public_https_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or port not in {None, 443}
        or hostname == "localhost"
        or hostname.endswith((".localhost", ".local", ".internal"))
    ):
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return "." in hostname
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


def canonical_mini_app_url(frontend_base_url: str) -> str:
    return f"{frontend_base_url.rstrip('/')}/app"


def notification_settings_url(frontend_base_url: str) -> str:
    return f"{canonical_mini_app_url(frontend_base_url)}?section=profile#profile-notifications"


def bot_commands() -> list[BotCommand]:
    return [
        BotCommand(command=command.command, description=command.description)
        for command in PUBLIC_COMMANDS
    ]


def menu_button(frontend_base_url: str) -> MenuButtonWebApp:
    return MenuButtonWebApp(
        text=MENU_BUTTON_LABEL,
        web_app=WebAppInfo(url=canonical_mini_app_url(frontend_base_url)),
    )


def menu_button_matches(current: object, frontend_base_url: str) -> bool:
    target = menu_button(frontend_base_url)
    return (
        isinstance(current, MenuButtonWebApp)
        and current.text == target.text
        and current.web_app.url == target.web_app.url
    )


def main_menu_keyboard(frontend_base_url: str) -> InlineKeyboardMarkup:
    url = canonical_mini_app_url(frontend_base_url)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=MENU_BUTTON_LABEL,
                    web_app=WebAppInfo(url=url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Помощь и обратная связь",
                    callback_data="public:support",
                )
            ],
            [InlineKeyboardButton(text="Настройки", callback_data="public:settings")],
            [InlineKeyboardButton(text="Что умеет бот", callback_data="public:help")],
        ]
    )


def notification_settings_keyboard(frontend_base_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть настройки уведомлений",
                    web_app=WebAppInfo(url=notification_settings_url(frontend_base_url)),
                )
            ]
        ]
    )


def help_text() -> str:
    visible = "\n".join(
        f"/{command.command} - {command.description}" for command in PUBLIC_COMMANDS
    )
    return (
        "Бот открывает приложение, помогает настроить часовой пояс и передать обращение "
        f"команде поддержки.\n\n{visible}"
    )
