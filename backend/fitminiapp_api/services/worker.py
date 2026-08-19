from __future__ import annotations

import asyncio
import logging
from time import monotonic
from urllib.parse import urlsplit

import httpx

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.logging_config import configure_logging
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.user import User
from fitminiapp_api.services.notifications import (
    claim_due_notifications,
    mark_delivery_failed,
    mark_delivery_succeeded,
    safe_delivery_error,
    sync_weekly_check_in_reminders,
    sync_workout_reminders,
)

logger = logging.getLogger(__name__)


def _log_delivery_failure(notification_id: int, error: Exception) -> None:
    logger.error(
        "notification_delivery_failed",
        extra={
            "notification_id": notification_id,
            "delivery_error": safe_delivery_error(error),
        },
    )


async def send_telegram_message(
    client: httpx.AsyncClient,
    chat_id: int,
    text: str,
    *,
    open_app_path: str | None = None,
) -> None:
    if not settings.telegram_bot_token or settings.telegram_bot_token == "replace-me":
        logger.info("BOT token not configured - skip Telegram delivery to %s", chat_id)
        return
    payload: dict = {"chat_id": chat_id, "text": text}
    if open_app_path:
        parsed = urlsplit(open_app_path)
        if parsed.scheme or parsed.netloc or parsed.path != "/app":
            raise ValueError("unsafe app notification URL")
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {
                        "text": "Открыть приложение",
                        "web_app": {
                            "url": f"{settings.frontend_base_url.rstrip('/')}{open_app_path}"
                        },
                    }
                ]
            ]
        }
    response = await client.post(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
        json=payload,
    )
    response.raise_for_status()


async def run_once(*, sync_reminders: bool = True) -> None:
    with get_session_context() as db:
        if sync_reminders:
            sync_workout_reminders(db)
            sync_weekly_check_in_reminders(db)
        rows = claim_due_notifications(db)
        users = {
            user.id: user
            for user in db.query(User).filter(User.id.in_({row.user_id for row in rows})).all()
        }
        deliveries: list[tuple[int, int, str, str | None]] = []
        for row in rows:
            user = users.get(row.user_id)
            if not user or not user.is_active:
                row.status = "cancelled"
                row.processing_started_at = None
                continue
            if row.channel == "telegram" and user.telegram_user_id is None:
                row.status = "cancelled"
                row.last_error = "telegram_identity_not_linked"
                row.processing_started_at = None
                continue
            open_app_path = row.action_url
            if (
                open_app_path is None
                and row.dedupe_key
                and row.dedupe_key.startswith("trainer_request:")
            ):
                open_app_path = "/app"
            deliveries.append(
                (
                    row.id,
                    user.telegram_user_id,
                    f"{row.title}\n\n{row.body}",
                    open_app_path,
                )
            )
        db.commit()

        if not deliveries:
            return

        semaphore = asyncio.Semaphore(settings.notification_delivery_concurrency)

        async with httpx.AsyncClient(timeout=20) as client:

            async def deliver(
                item: tuple[int, int, str, str | None],
            ) -> tuple[int, Exception | None]:
                notification_id, chat_id, text, open_app_path = item
                try:
                    async with semaphore:
                        await send_telegram_message(
                            client, chat_id, text, open_app_path=open_app_path
                        )
                    return notification_id, None
                except Exception as exc:
                    return notification_id, exc

            results = await asyncio.gather(*(deliver(item) for item in deliveries))

        result_by_id = dict(results)
        delivered_rows: dict[int, Notification] = {
            row.id: row
            for row in db.query(Notification).filter(Notification.id.in_(result_by_id)).all()
        }
        delivered_users = {
            user.id: user
            for user in db.query(User)
            .filter(User.id.in_({row.user_id for row in delivered_rows.values()}))
            .all()
        }
        for notification_id, error in results:
            delivered_row = delivered_rows.get(notification_id)
            if delivered_row is None:
                continue
            if error is None:
                user = delivered_users.get(delivered_row.user_id)
                if user is not None and user.is_active:
                    mark_delivery_succeeded(db, delivered_row, user, commit=False)
                else:
                    delivered_row.status = "cancelled"
                    delivered_row.processing_started_at = None
            else:
                mark_delivery_failed(db, delivered_row, error, commit=False)
                _log_delivery_failure(delivered_row.id, error)
        db.commit()


async def main() -> None:
    configure_logging(
        debug=settings.app_debug,
        service="notification-worker",
        sensitive_values=(
            settings.secret_key,
            settings.telegram_bot_token,
            settings.bot_internal_token,
            settings.smtp_password,
            settings.telegram_oauth_client_secret,
            settings.google_oauth_client_secret,
            settings.yandex_oauth_client_secret,
            settings.apple_oauth_client_secret,
            settings.database_url,
        ),
    )
    logger.info("worker_started")
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
