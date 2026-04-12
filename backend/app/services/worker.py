from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.db.session import get_session_context
from app.models.user import User
from app.services.notifications import get_due_notifications

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


async def run_once() -> None:
    with get_session_context() as db:
        rows = get_due_notifications(db)
        for row in rows:
            user = db.query(User).filter(User.id == row.user_id).first()
            try:
                await send_telegram_message(user.telegram_user_id, f"{row.title}\n\n{row.body}")
                row.status = "sent"
                from datetime import datetime

                row.sent_at = datetime.utcnow()
                row.last_error = None
            except Exception as exc:
                row.status = "failed"
                row.last_error = str(exc)
                logger.exception("Failed to send notification %s", row.id)


async def main() -> None:
    while True:
        await run_once()
        await asyncio.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    asyncio.run(main())
