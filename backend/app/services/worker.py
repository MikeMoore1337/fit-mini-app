from __future__ import annotations

import asyncio
import logging
from time import monotonic

import httpx

from app.core.config import settings
from app.db.session import get_session_context
from app.models.user import User
from app.services.notifications import (
    claim_due_notifications,
    mark_delivery_failed,
    mark_delivery_succeeded,
    sync_workout_reminders,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: int, text: str) -> None:
    if not settings.telegram_bot_token or settings.telegram_bot_token == "replace-me":
        logger.info("BOT token not configured - skip Telegram delivery to %s", chat_id)
        return
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )
        response.raise_for_status()


async def run_once(*, sync_reminders: bool = True) -> None:
    with get_session_context() as db:
        if sync_reminders:
            sync_workout_reminders(db)
        rows = claim_due_notifications(db)
        for row in rows:
            user = db.query(User).filter(User.id == row.user_id).first()
            if not user or not user.is_active:
                row.status = "cancelled"
                row.processing_started_at = None
                db.commit()
                continue
            try:
                await send_telegram_message(user.telegram_user_id, f"{row.title}\n\n{row.body}")
                mark_delivery_succeeded(db, row, user)
            except Exception as exc:
                mark_delivery_failed(db, row, exc)
                logger.exception("Failed to send notification %s", row.id)


async def main() -> None:
    next_reminder_sync = 0.0
    while True:
        current = monotonic()
        should_sync = current >= next_reminder_sync
        await run_once(sync_reminders=should_sync)
        if should_sync:
            next_reminder_sync = current + settings.reminder_sync_seconds
        await asyncio.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    asyncio.run(main())
