from __future__ import annotations

import re
from typing import Literal

import httpx
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from .config import settings

router = Router()
NEWS_CALLBACK_PATTERN = re.compile(r"news:([sdra]):([0-9a-f]{32})\Z")
ACTION_BY_CODE: dict[str, Literal["skip", "defer", "regenerate", "accept_for_design"]] = {
    "s": "skip",
    "d": "defer",
    "r": "regenerate",
    "a": "accept_for_design",
}
STATUS_TEXT = {
    "accepted": "Решение сохранено",
    "queued": "Новая revision поставлена в очередь",
    "deferred": "Черновик отложен",
    "already_processed": "Это действие уже учтено",
    "stale": "Revision уже устарела",
    "limit_reached": "Лимит перегенераций исчерпан",
    "unavailable": "Черновик недоступен",
}


async def moderate_news_draft(
    *,
    draft_id: str,
    admin_telegram_user_id: int,
    action: str,
) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.backend_internal_url}/v1/bot/news/drafts/{draft_id}/moderate",
                headers={"X-Bot-Token": settings.bot_internal_token},
                json={
                    "admin_telegram_user_id": admin_telegram_user_id,
                    "action": action,
                },
            )
    except httpx.HTTPError:
        return "unavailable"
    if response.status_code == 403:
        return "forbidden"
    if not response.is_success:
        return "unavailable"
    try:
        status = response.json().get("status")
    except ValueError:
        return "unavailable"
    return status if status in STATUS_TEXT else "unavailable"


@router.callback_query(F.data.startswith("news:"))
async def news_editorial_callback(callback: CallbackQuery) -> None:
    telegram_user_id = callback.from_user.id
    if telegram_user_id not in settings.admin_telegram_id_set:
        await callback.answer("Действие доступно только редактору", show_alert=True)
        return
    if not isinstance(callback.message, Message) or callback.message.chat.type != "private":
        await callback.answer("Черновик доступен только в личном чате", show_alert=True)
        return
    match = NEWS_CALLBACK_PATTERN.fullmatch(callback.data or "")
    if match is None:
        await callback.answer("Некорректное действие", show_alert=True)
        return
    action = ACTION_BY_CODE[match.group(1)]
    status = await moderate_news_draft(
        draft_id=match.group(2),
        admin_telegram_user_id=telegram_user_id,
        action=action,
    )
    if status == "forbidden":
        await callback.answer("Действие недоступно", show_alert=True)
        return
    if status in {
        "accepted",
        "queued",
        "deferred",
        "already_processed",
        "stale",
        "limit_reached",
    }:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(
        STATUS_TEXT.get(status, STATUS_TEXT["unavailable"]), show_alert=status == "unavailable"
    )
