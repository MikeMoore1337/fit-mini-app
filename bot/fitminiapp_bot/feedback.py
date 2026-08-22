from __future__ import annotations

import html
import logging
import re
import time
from dataclasses import dataclass
from typing import Literal, cast

import httpx
from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from .config import settings
from .error_codes import safe_error_code

logger = logging.getLogger(__name__)
router = Router(name="feedback")

FeedbackCategory = Literal["bug", "account", "idea", "contact", "other"]
ReplyOutcome = Literal["delivered", "blocked", "failed"]
SupportCaseStatus = Literal[
    "pending_relay",
    "open",
    "replying",
    "replied",
    "relay_failed",
    "undeliverable",
    "expired",
]

FEEDBACK_TTL_SECONDS = 15 * 60
SUPPORT_CASE_PATTERN = re.compile(r"(?:^|\s)#yfc_support_([0-9a-f]{32})(?:\s|$)")
SUPPORTED_CONTENT_TYPES = frozenset({ContentType.TEXT, ContentType.PHOTO, ContentType.DOCUMENT})
CATEGORY_LABELS: dict[FeedbackCategory, str] = {
    "bug": "Ошибка",
    "account": "Вход или аккаунт",
    "idea": "Предложение",
    "contact": "Связаться с разработчиком",
    "other": "Другое",
}
START_PAYLOAD_CATEGORIES: dict[str, FeedbackCategory | None] = {
    "support": None,
    "support_bug": "bug",
    "support_account": "account",
    "support_idea": "idea",
    "support_contact": "contact",
}


class FeedbackStates(StatesGroup):
    awaiting_message = State()


@dataclass(frozen=True)
class CreatedSupportCase:
    status: Literal["created", "duplicate", "rate_limited", "failed"]
    case_id: str | None = None
    case_status: SupportCaseStatus | None = None


@dataclass(frozen=True)
class ClaimedSupportReply:
    status: Literal["claimed", "already_processed", "unavailable", "expired", "failed"]
    telegram_user_id: int | None = None


def categories_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"support:category:{category}")]
            for category, label in CATEGORY_LABELS.items()
        ]
    )


def support_case_marker(case_id: str) -> str:
    return f"#yfc_support_{case_id}"


def support_case_from_admin_reply(message: Message) -> str | None:
    replied = message.reply_to_message
    if replied is None or message.bot is None or replied.from_user is None:
        return None
    if replied.from_user.id != message.bot.id:
        return None
    body = replied.text or replied.caption or ""
    if not body.startswith("Новое обращение · "):
        return None
    match = SUPPORT_CASE_PATTERN.search(body)
    return match.group(1) if match else None


def feedback_state_expired(data: dict[str, object], *, now: float | None = None) -> bool:
    started_at = data.get("started_at")
    if not isinstance(started_at, (int, float)) or isinstance(started_at, bool):
        return True
    return (now if now is not None else time.monotonic()) - float(
        started_at
    ) >= FEEDBACK_TTL_SECONDS


def support_request_header(message: Message, *, case_id: str, category: FeedbackCategory) -> str:
    user = message.from_user
    if user is None:
        raise ValueError("Support message has no sender")
    display_name = html.escape(user.full_name or "Без имени")
    username = f" (@{html.escape(user.username)})" if user.username else ""
    return (
        f"Новое обращение · {CATEGORY_LABELS[category]}\n"
        f'Пользователь: <a href="tg://user?id={user.id}">{display_name}</a>{username}\n'
        f"{support_case_marker(case_id)}\n\n"
        "Ответьте именно на это служебное сообщение. Текст обращения находится в ответе ниже."
    )


async def create_support_case(message: Message, category: FeedbackCategory) -> CreatedSupportCase:
    if message.from_user is None:
        return CreatedSupportCase(status="failed")
    url = f"{settings.backend_internal_url.rstrip('/')}/api/v1/bot/support/cases"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                headers={"X-Bot-Token": settings.bot_internal_token},
                json={
                    "telegram_user_id": message.from_user.id,
                    "request_message_id": message.message_id,
                    "category": category,
                },
            )
            if response.status_code == 429:
                return CreatedSupportCase(status="rate_limited")
            response.raise_for_status()
            payload = response.json()
        status = payload.get("status")
        case_id = payload.get("case_id")
        case_status = payload.get("case_status")
        if status not in {"created", "duplicate"}:
            return CreatedSupportCase(status="failed")
        if not isinstance(case_id, str) or not re.fullmatch(r"[0-9a-f]{32}", case_id):
            return CreatedSupportCase(status="failed")
        if case_status not in {
            "pending_relay",
            "open",
            "replying",
            "replied",
            "relay_failed",
            "undeliverable",
            "expired",
        }:
            return CreatedSupportCase(status="failed")
        return CreatedSupportCase(
            status=status,
            case_id=case_id,
            case_status=cast(SupportCaseStatus, case_status),
        )
    except Exception as exc:
        logger.error(
            "support_case_creation_failed",
            extra={"error_code": safe_error_code(exc)},
        )
        return CreatedSupportCase(status="failed")


async def record_relay_result(case_id: str, *, delivered: bool) -> None:
    url = (
        f"{settings.backend_internal_url.rstrip('/')}/api/v1/bot/support/cases/"
        f"{case_id}/relay-result"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                headers={"X-Bot-Token": settings.bot_internal_token},
                json={"delivered": delivered},
            )
            response.raise_for_status()
    except Exception as exc:
        logger.error(
            "support_relay_result_failed",
            extra={"error_code": safe_error_code(exc)},
        )


async def claim_support_reply(
    *,
    case_id: str,
    admin_telegram_user_id: int,
    reply_message_id: int,
) -> ClaimedSupportReply:
    url = (
        f"{settings.backend_internal_url.rstrip('/')}/api/v1/bot/support/cases/"
        f"{case_id}/reply-claim"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                headers={"X-Bot-Token": settings.bot_internal_token},
                json={
                    "admin_telegram_user_id": admin_telegram_user_id,
                    "reply_message_id": reply_message_id,
                },
            )
            response.raise_for_status()
            payload = response.json()
        status = payload.get("status")
        target = payload.get("telegram_user_id")
        if status == "claimed" and isinstance(target, int) and target > 0:
            return ClaimedSupportReply(status="claimed", telegram_user_id=target)
        if status in {"already_processed", "unavailable", "expired"}:
            return ClaimedSupportReply(status=status)
        return ClaimedSupportReply(status="failed")
    except Exception as exc:
        logger.error(
            "support_reply_claim_failed",
            extra={"error_code": safe_error_code(exc)},
        )
        return ClaimedSupportReply(status="failed")


async def record_reply_result(
    *,
    case_id: str,
    admin_telegram_user_id: int,
    reply_message_id: int,
    outcome: ReplyOutcome,
) -> bool:
    url = (
        f"{settings.backend_internal_url.rstrip('/')}/api/v1/bot/support/cases/"
        f"{case_id}/reply-result"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                headers={"X-Bot-Token": settings.bot_internal_token},
                json={
                    "admin_telegram_user_id": admin_telegram_user_id,
                    "reply_message_id": reply_message_id,
                    "outcome": outcome,
                },
            )
            response.raise_for_status()
        return True
    except Exception as exc:
        logger.error(
            "support_reply_result_failed",
            extra={"error_code": safe_error_code(exc)},
        )
        return False


async def open_feedback_flow(
    message: Message,
    state: FSMContext,
    *,
    category: FeedbackCategory | None = None,
) -> None:
    await state.clear()
    if category is None:
        await message.answer(
            "С чем помочь? Выберите категорию обращения.",
            reply_markup=categories_keyboard(),
        )
        return
    await state.set_state(FeedbackStates.awaiting_message)
    await state.update_data(category=category, started_at=time.monotonic())
    await message.answer(
        f"Категория: {CATEGORY_LABELS[category]}. Опишите вопрос одним сообщением. "
        "Можно приложить фото или документ.\n\n"
        "Не отправляйте пароли, коды подтверждения, токены, платёжные данные "
        "и лишние документы. Для отмены используйте /cancel."
    )


async def handle_feedback_start_payload(
    message: Message,
    state: FSMContext,
    payload: str | None,
) -> bool:
    normalized = (payload or "").strip()
    if normalized not in START_PAYLOAD_CATEGORIES:
        return False
    if message.chat.type != "private":
        await message.answer("Поддержка доступна в личном чате с ботом.")
        return True
    await open_feedback_flow(message, state, category=START_PAYLOAD_CATEGORIES[normalized])
    return True


@router.message(Command("cancel"), F.chat.type == "private")
async def cancel_feedback(message: Message, state: FSMContext) -> None:
    active = await state.get_state()
    await state.clear()
    if active is None:
        await message.answer("Активного обращения нет. Начать новое: /support")
    else:
        await message.answer("Обращение отменено. Начать заново: /support")


@router.message(Command("support", "feedback"), F.chat.type == "private")
async def support_command(message: Message, state: FSMContext) -> None:
    await open_feedback_flow(message, state)


@router.callback_query(F.data.startswith("support:category:"))
async def select_feedback_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = (callback.data or "").removeprefix("support:category:")
    if (
        category not in CATEGORY_LABELS
        or not isinstance(callback.message, Message)
        or callback.message.chat.type != "private"
        or callback.message.chat.id != callback.from_user.id
    ):
        await callback.answer("Категория недоступна", show_alert=True)
        return
    await open_feedback_flow(callback.message, state, category=category)
    await callback.answer()


def _is_admin_reply_candidate(message: Message) -> bool:
    return bool(
        message.from_user
        and message.chat.type == "private"
        and message.chat.id == message.from_user.id
        and message.from_user.id in settings.admin_telegram_id_set
        and message.reply_to_message is not None
    )


@router.message(_is_admin_reply_candidate)
async def handle_admin_reply(message: Message) -> None:
    admin = message.from_user
    if admin is None or message.bot is None:
        return
    if (
        admin.id not in settings.admin_telegram_id_set
        or message.chat.type != "private"
        or message.chat.id != admin.id
    ):
        return
    case_id = support_case_from_admin_reply(message)
    if case_id is None:
        await message.answer("Ответьте на служебное сообщение конкретного обращения.")
        return
    if message.content_type not in SUPPORTED_CONTENT_TYPES or (
        message.text is not None and message.text.lstrip().startswith("/")
    ):
        await message.answer("В ответе поддерживаются текст, фото или документ.")
        return

    claim = await claim_support_reply(
        case_id=case_id,
        admin_telegram_user_id=admin.id,
        reply_message_id=message.message_id,
    )
    if claim.status == "already_processed":
        await message.answer("Этот ответ уже обработан.")
        return
    if claim.status == "expired":
        await message.answer(
            "Срок ответа на обращение истёк. Попросите пользователя создать новое."
        )
        return
    if claim.status != "claimed" or claim.telegram_user_id is None:
        await message.answer("Обращение недоступно для ответа или уже обработано.")
        return

    outcome: ReplyOutcome = "failed"
    intro_message_id: int | None = None
    try:
        intro = await message.bot.send_message(
            chat_id=claim.telegram_user_id,
            text="Ответ команды Your Fitness Coach:",
        )
        intro_message_id = intro.message_id
        await message.bot.copy_message(
            chat_id=claim.telegram_user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=intro.message_id,
        )
        outcome = "delivered"
    except TelegramForbiddenError, TelegramNotFound:
        outcome = "blocked"
    except Exception as exc:
        logger.error(
            "support_response_delivery_failed",
            extra={"error_code": safe_error_code(exc)},
        )
        if intro_message_id is not None:
            try:
                await message.bot.delete_message(
                    chat_id=claim.telegram_user_id,
                    message_id=intro_message_id,
                )
            except Exception:
                logger.warning("support_response_preamble_cleanup_failed")

    result_recorded = await record_reply_result(
        case_id=case_id,
        admin_telegram_user_id=admin.id,
        reply_message_id=message.message_id,
        outcome=outcome,
    )
    if not result_recorded:
        await message.answer(
            "Ответ обработан Telegram, но итоговый статус не подтверждён backend. "
            "Не повторяйте ответ на это обращение: оно заблокировано от повторной доставки."
        )
        return
    if outcome == "delivered":
        logger.info("support_response_delivered")
        await message.answer("Ответ доставлен пользователю.")
    elif outcome == "blocked":
        logger.info("support_response_undeliverable")
        await message.answer("Пользователь заблокировал бота или удалил чат. Повторов не будет.")
    else:
        await message.answer("Не удалось доставить ответ. Можно повторить новым ответом позже.")


@router.message(FeedbackStates.awaiting_message, F.chat.type == "private")
async def handle_feedback_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if feedback_state_expired(data):
        await state.clear()
        await message.answer("Время ожидания истекло. Начните новое обращение: /support")
        return
    category = data.get("category")
    if category not in CATEGORY_LABELS:
        await state.clear()
        await message.answer("Состояние обращения сброшено. Начните заново: /support")
        return
    if message.content_type not in SUPPORTED_CONTENT_TYPES or (
        message.text is not None and message.text.lstrip().startswith("/")
    ):
        await message.answer(
            "Поддерживаются текст, фото или документ. Отправьте один из этих вариантов "
            "или используйте /cancel."
        )
        return
    if message.from_user is None or message.bot is None:
        await state.clear()
        return
    if not settings.admin_telegram_id_set:
        await state.clear()
        await message.answer("Поддержка временно недоступна. Попробуйте позже.")
        return

    created = await create_support_case(message, category)
    if created.status == "duplicate" and created.case_status != "pending_relay":
        await state.clear()
        if created.case_status == "relay_failed":
            await message.answer(
                "Предыдущая попытка не была доставлена. Начните новое обращение: /support"
            )
        else:
            await message.answer("Это сообщение уже принято как обращение.")
        return
    if created.status == "rate_limited":
        await state.clear()
        logger.info("support_request_rate_limited")
        await message.answer(
            "Слишком много обращений этой категории. Подождите и попробуйте позже."
        )
        return
    if created.status not in {"created", "duplicate"} or created.case_id is None:
        await state.clear()
        await message.answer("Не удалось создать обращение. Попробуйте ещё раз позже.")
        return

    delivered = 0
    for admin_id in settings.admin_telegram_id_set:
        try:
            header = await message.bot.send_message(
                chat_id=admin_id,
                text=support_request_header(message, case_id=created.case_id, category=category),
                parse_mode="HTML",
                reply_markup=ForceReply(
                    selective=True,
                    input_field_placeholder="Ответ пользователю",
                ),
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

    await record_relay_result(created.case_id, delivered=delivered > 0)
    await state.clear()
    if delivered:
        logger.info("support_request_relayed")
        await message.answer(
            "Обращение передано команде Your Fitness Coach. Ответ придёт в этот чат."
        )
    else:
        await message.answer("Не удалось передать обращение. Попробуйте ещё раз позже.")
