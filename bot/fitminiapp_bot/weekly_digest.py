from __future__ import annotations

import logging
import re
import time
from datetime import datetime

import httpx
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from .config import settings
from .error_codes import safe_error_code

logger = logging.getLogger(__name__)
router = Router()

CONSENT_COPY = (
    "Еженедельный дайджест\n\n"
    "Раз в неделю мы можем присылать в этот чат до пяти полезных материалов из нашего "
    "Telegram-канала. Если достойных материалов недостаточно, дайджеста не будет. "
    "Подписка необязательна и не влияет на работу приложения или продуктовые уведомления. "
    "Отключить её можно одним нажатием под любым дайджестом или в /settings."
)
CONSENT_VERSION = "weekly-news-v1"
DIGEST_CALLBACK_PATTERN = re.compile(r"wd([ia]):([a-z]):([0-9a-f]{32}):([1-5]):([0-9a-f]{16})\Z")
DIGEST_ACTION_PATTERN = re.compile(r"wda:([aiscr]):([0-9a-f]{32}):([0-9a-f]{16})\Z")
SCHEDULE_INPUT_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})\s+([A-Za-z_+-]+(?:/[A-Za-z0-9_+.-]+)+)\Z"
)
INPUT_TTL_SECONDS = 15 * 60


class WeeklyDigestStates(StatesGroup):
    awaiting_intro = State()
    awaiting_item = State()
    awaiting_schedule = State()


def _user_payload(user: User, *, enabled: bool | None) -> dict[str, object]:
    return {
        "telegram_user_id": user.id,
        "enabled": enabled,
        "consent_version": CONSENT_VERSION if enabled is True else None,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


async def _backend_post(path: str, payload: dict[str, object]) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{settings.backend_internal_url.rstrip('/')}{path}",
                headers={"X-Bot-Token": settings.bot_internal_token},
                json=payload,
            )
        if not response.is_success:
            logger.error(
                "weekly_digest_backend_failed",
                extra={"operation": path.rsplit("/", 1)[-1], "status_code": response.status_code},
            )
            return None
        data = response.json()
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.error(
            "weekly_digest_backend_unavailable",
            extra={"error_code": safe_error_code(exc)},
        )
        return None


async def digest_preference(user: User, *, enabled: bool | None = None) -> bool | None:
    data = await _backend_post(
        "/api/v1/bot/digest/preference", _user_payload(user, enabled=enabled)
    )
    return (
        data.get("enabled") if data is not None and isinstance(data.get("enabled"), bool) else None
    )


def digest_settings_keyboard(
    *, enabled: bool, channel_url: str | None = None
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if channel_url:
        rows.append([InlineKeyboardButton(text="Открыть Telegram-канал", url=channel_url)])
    rows.append(
        [
            InlineKeyboardButton(
                text=("Не получать дайджест" if enabled else "Получать еженедельный дайджест"),
                callback_data="wd:off" if enabled else "wd:on",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_digest_settings(message: Message) -> None:
    if message.from_user is None:
        return
    enabled = await digest_preference(message.from_user)
    if enabled is None:
        await message.answer("Настройки дайджеста временно недоступны. Попробуйте позже.")
        return
    state = "Сейчас дайджест включён." if enabled else "Сейчас дайджест выключен."
    channel_username = settings.news_channel_username.strip().removeprefix("@").lower()
    channel_url = f"https://t.me/{channel_username}" if channel_username else None
    await message.answer(
        f"{CONSENT_COPY}\n\n{state}",
        reply_markup=digest_settings_keyboard(enabled=enabled, channel_url=channel_url),
    )


def recipient_digest_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Telegram-канал", url=channel_url)],
            [
                InlineKeyboardButton(
                    text="Отключить еженедельный дайджест",
                    callback_data="wd:off",
                )
            ],
        ]
    )


def _control_keyboard(issue: dict) -> InlineKeyboardMarkup:
    issue_id = str(issue["issue_id"])
    digest_hash = str(issue["content_hash"])[:16]
    status = str(issue["status"])
    rows: list[list[InlineKeyboardButton]] = []
    for item in issue.get("items", []):
        position = int(item["position"])
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"↑ {position}",
                    callback_data=f"wdi:u:{issue_id}:{position}:{digest_hash}",
                ),
                InlineKeyboardButton(
                    text=f"↓ {position}",
                    callback_data=f"wdi:d:{issue_id}:{position}:{digest_hash}",
                ),
                InlineKeyboardButton(
                    text=f"Изменить {position}",
                    callback_data=f"wdi:e:{issue_id}:{position}:{digest_hash}",
                ),
                InlineKeyboardButton(
                    text=f"Убрать {position}",
                    callback_data=f"wdi:r:{issue_id}:{position}:{digest_hash}",
                ),
            ]
        )
    if status == "draft":
        rows.append(
            [
                InlineKeyboardButton(
                    text="Изменить вступление",
                    callback_data=f"wda:i:{issue_id}:{digest_hash}",
                )
            ]
        )
        if not issue.get("blockers"):
            rows.append(
                [
                    InlineKeyboardButton(
                        text="Одобрить exact revision",
                        callback_data=f"wda:a:{issue_id}:{digest_hash}",
                    )
                ]
            )
        rows.append(
            [
                InlineKeyboardButton(
                    text="Отклонить неделю",
                    callback_data=f"wda:r:{issue_id}:{digest_hash}",
                )
            ]
        )
    elif status == "approved":
        rows.append(
            [
                InlineKeyboardButton(
                    text="Запланировать",
                    callback_data=f"wda:s:{issue_id}:{digest_hash}",
                ),
                InlineKeyboardButton(
                    text="Отменить",
                    callback_data=f"wda:c:{issue_id}:{digest_hash}",
                ),
            ]
        )
    elif status == "scheduled":
        rows.append(
            [
                InlineKeyboardButton(
                    text="Отменить рассылку",
                    callback_data=f"wda:c:{issue_id}:{digest_hash}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_issue_preview(message: Message, issue: dict) -> None:
    await message.answer(
        str(issue["rendered_text"]),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=recipient_digest_keyboard(str(issue["channel_url"])),
    )
    blockers = issue.get("blockers") or []
    status_line = f"Статус: {issue['status']} · revision {issue['revision']}"
    blocker_line = f"\nBlockers: {', '.join(map(str, blockers))}" if blockers else ""
    schedule_line = (
        f"\nЗапланирован UTC: {issue['scheduled_for_utc']}"
        if issue.get("scheduled_for_utc")
        else ""
    )
    await message.answer(
        f"Дайджест {issue['issue_key']}\n{status_line}\nArtifact: {str(issue['content_hash'])[:16]}"
        f"{schedule_line}{blocker_line}\n\nPreview выше — exact личное сообщение с кнопками.",
        reply_markup=_control_keyboard(issue),
    )


async def _issue_action(
    *,
    issue_id: str,
    admin_id: int,
    action: str,
    digest_hash: str,
    position: int | None = None,
    text_value: str | None = None,
    scheduled_local: str | None = None,
    timezone: str | None = None,
) -> dict | None:
    payload: dict[str, object] = {
        "admin_telegram_user_id": admin_id,
        "action": action,
        "expected_content_hash": digest_hash,
    }
    if position is not None:
        payload["position"] = position
    if text_value is not None:
        payload["text"] = text_value
    if scheduled_local is not None:
        payload["scheduled_local"] = scheduled_local
    if timezone is not None:
        payload["timezone"] = timezone
    return await _backend_post(f"/api/v1/bot/digest/issues/{issue_id}/actions", payload)


@router.callback_query(F.data.in_({"wd:on", "wd:off"}))
async def digest_preference_callback(callback: CallbackQuery) -> None:
    if (
        not isinstance(callback.message, Message)
        or callback.message.chat.type != "private"
        or callback.message.chat.id != callback.from_user.id
    ):
        await callback.answer("Настройка доступна только в личном чате", show_alert=True)
        return
    enabled = callback.data == "wd:on"
    saved = await digest_preference(callback.from_user, enabled=enabled)
    if saved is None:
        await callback.answer("Не удалось сохранить настройку", show_alert=True)
        return
    channel_username = settings.news_channel_username.strip().removeprefix("@").lower()
    channel_url = f"https://t.me/{channel_username}" if channel_username else None
    markup = digest_settings_keyboard(enabled=saved, channel_url=channel_url)
    if (callback.message.text or "").startswith("Еженедельный дайджест"):
        state = "Сейчас дайджест включён." if saved else "Сейчас дайджест выключен."
        await callback.message.edit_text(
            f"{CONSENT_COPY}\n\n{state}",
            reply_markup=markup,
        )
    else:
        await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer("Дайджест включён" if saved else "Дайджест отключён")


@router.message(Command("news_off", "unsubscribe", "stop_news"), F.chat.type == "private")
async def digest_unsubscribe_command(message: Message) -> None:
    if message.from_user is None:
        return
    saved = await digest_preference(message.from_user, enabled=False)
    if saved is None:
        await message.answer("Не удалось отключить дайджест. Попробуйте позже.")
        return
    await message.answer(
        "Еженедельный дайджест отключён. Продуктовые и важные уведомления не изменены.",
        reply_markup=digest_settings_keyboard(enabled=False),
    )


@router.message(Command("digest_review"), F.chat.type == "private")
async def digest_review_command(message: Message) -> None:
    if message.from_user is None or message.from_user.id not in settings.admin_telegram_id_set:
        await message.answer("Команда доступна только редактору.")
        return
    data = await _backend_post(
        "/api/v1/bot/digest/issues/draft",
        {"admin_telegram_user_id": message.from_user.id},
    )
    if data is None:
        await message.answer("Не удалось подготовить дайджест.")
        return
    await send_issue_preview(message, data)


@router.callback_query(F.data.startswith("wdi:"))
async def digest_item_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.admin_telegram_id_set:
        await callback.answer("Действие доступно только редактору", show_alert=True)
        return
    if not isinstance(callback.message, Message) or callback.message.chat.type != "private":
        await callback.answer("Действие доступно только в личном чате", show_alert=True)
        return
    match = DIGEST_CALLBACK_PATTERN.fullmatch(callback.data or "")
    if match is None or match.group(1) != "i":
        await callback.answer("Некорректное действие", show_alert=True)
        return
    action_code, issue_id, position_raw, digest_hash = match.groups()[1:]
    action = {"u": "move_up", "d": "move_down", "r": "remove", "e": "edit_item"}.get(action_code)
    if action is None:
        await callback.answer("Некорректное действие", show_alert=True)
        return
    position = int(position_raw)
    if action == "edit_item":
        await state.set_state(WeeklyDigestStates.awaiting_item)
        await state.set_data(
            {
                "issue_id": issue_id,
                "position": position,
                "digest_hash": digest_hash,
                "started_at": time.monotonic(),
            }
        )
        await callback.message.answer(
            "Пришлите новый takeaway: одно или два предложения, только на основе одобренного поста. "
            "Для отмены: /cancel"
        )
        await callback.answer()
        return
    data = await _issue_action(
        issue_id=issue_id,
        admin_id=callback.from_user.id,
        action=action,
        digest_hash=digest_hash,
        position=position,
    )
    if data is None or data.get("issue") is None:
        await callback.answer("Preview устарел или действие недоступно", show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    await send_issue_preview(callback.message, data["issue"])
    await callback.answer("Создана новая revision")


@router.callback_query(F.data.startswith("wda:"))
async def digest_action_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.admin_telegram_id_set:
        await callback.answer("Действие доступно только редактору", show_alert=True)
        return
    if not isinstance(callback.message, Message) or callback.message.chat.type != "private":
        await callback.answer("Действие доступно только в личном чате", show_alert=True)
        return
    match = DIGEST_ACTION_PATTERN.fullmatch(callback.data or "")
    if match is None:
        await callback.answer("Некорректное действие", show_alert=True)
        return
    action_code, issue_id, digest_hash = match.groups()
    if action_code == "i":
        await state.set_state(WeeklyDigestStates.awaiting_intro)
        await state.set_data(
            {"issue_id": issue_id, "digest_hash": digest_hash, "started_at": time.monotonic()}
        )
        await callback.message.answer("Пришлите новое вступление. Для отмены: /cancel")
        await callback.answer()
        return
    if action_code == "s":
        await state.set_state(WeeklyDigestStates.awaiting_schedule)
        await state.set_data(
            {"issue_id": issue_id, "digest_hash": digest_hash, "started_at": time.monotonic()}
        )
        await callback.message.answer(
            "Пришлите дату, время и IANA timezone: 2026-08-31 12:00 Europe/Moscow. "
            "Для отмены: /cancel"
        )
        await callback.answer()
        return
    action = {"a": "approve", "c": "cancel", "r": "reject"}.get(action_code)
    if action is None:
        await callback.answer("Некорректное действие", show_alert=True)
        return
    data = await _issue_action(
        issue_id=issue_id,
        admin_id=callback.from_user.id,
        action=action,
        digest_hash=digest_hash,
    )
    if data is None or data.get("issue") is None:
        await callback.answer("Preview устарел или действие недоступно", show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    await send_issue_preview(callback.message, data["issue"])
    await callback.answer(str(data.get("status", "Готово")))


def _state_valid(data: dict) -> bool:
    started_at = data.get("started_at")
    return (
        isinstance(started_at, (int, float)) and time.monotonic() - started_at <= INPUT_TTL_SECONDS
    )


@router.message(WeeklyDigestStates.awaiting_intro, F.text, ~F.text.startswith("/"))
async def digest_intro_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.from_user is None or not _state_valid(data):
        await state.clear()
        await message.answer("Редактирование устарело. Откройте новый preview.")
        return
    response = await _issue_action(
        issue_id=str(data["issue_id"]),
        admin_id=message.from_user.id,
        action="edit_intro",
        digest_hash=str(data["digest_hash"]),
        text_value=message.text,
    )
    await state.clear()
    if response is None or response.get("issue") is None:
        await message.answer("Не удалось сохранить вступление.")
        return
    await send_issue_preview(message, response["issue"])


@router.message(WeeklyDigestStates.awaiting_item, F.text, ~F.text.startswith("/"))
async def digest_item_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.from_user is None or not _state_valid(data):
        await state.clear()
        await message.answer("Редактирование устарело. Откройте новый preview.")
        return
    response = await _issue_action(
        issue_id=str(data["issue_id"]),
        admin_id=message.from_user.id,
        action="edit_item",
        digest_hash=str(data["digest_hash"]),
        position=int(data["position"]),
        text_value=message.text,
    )
    await state.clear()
    if response is None or response.get("issue") is None:
        await message.answer("Takeaway не сохранён: нужны одно или два коротких предложения.")
        return
    await send_issue_preview(message, response["issue"])


@router.message(WeeklyDigestStates.awaiting_schedule, F.text, ~F.text.startswith("/"))
async def digest_schedule_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    match = SCHEDULE_INPUT_PATTERN.fullmatch(message.text or "")
    if message.from_user is None or not _state_valid(data) or match is None:
        await message.answer("Формат: 2026-08-31 12:00 Europe/Moscow или /cancel")
        return
    scheduled_local = datetime.fromisoformat(f"{match.group(1)}T{match.group(2)}:00")
    response = await _issue_action(
        issue_id=str(data["issue_id"]),
        admin_id=message.from_user.id,
        action="schedule",
        digest_hash=str(data["digest_hash"]),
        scheduled_local=scheduled_local.isoformat(),
        timezone=match.group(3),
    )
    await state.clear()
    if response is None or response.get("issue") is None:
        await message.answer("Не удалось запланировать: проверьте время, timezone и feature flag.")
        return
    if response.get("status") == "no_recipients":
        await message.answer("Нет пользователей с действующим opt-in; выпуск не запланирован.")
    await send_issue_preview(message, response["issue"])


@router.message(StateFilter(WeeklyDigestStates), Command("cancel"))
async def cancel_digest_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие с дайджестом отменено.")
