from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from time import monotonic

import httpx
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.logging_config import configure_logging
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.user import User
from fitminiapp_api.services.account_exports import prune_account_exports
from fitminiapp_api.services.bot_support import prune_support_cases
from fitminiapp_api.services.notifications import (
    NotificationDeliveryError,
    claim_due_notifications,
    mark_delivery_failed,
    mark_delivery_succeeded,
    neutral_telegram_text,
    quiet_hours_retry_at,
    reminder_category_enabled,
    resolve_notification_destination,
    safe_delivery_error,
    sync_measurement_reminders,
    sync_weekly_check_in_reminders,
    sync_workout_reminders,
    validate_notification_destination,
)

logger = logging.getLogger(__name__)
TELEGRAM_DELIVERY_RATE_PER_SECOND = 20


class TelegramRateLimiter:
    """Keep one worker below Telegram's global bulk-send limit."""

    def __init__(
        self,
        rate_per_second: int,
        *,
        clock: Callable[[], float] = monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._interval = 1 / rate_per_second
        self._clock = clock
        self._sleep = sleep
        self._lock = asyncio.Lock()
        self._next_send_at = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = self._clock()
            if now < self._next_send_at:
                await self._sleep(self._next_send_at - now)
                now = self._clock()
            self._next_send_at = max(now, self._next_send_at) + self._interval

    async def defer(self, delay_seconds: float) -> None:
        async with self._lock:
            self._next_send_at = max(
                self._next_send_at,
                self._clock() + delay_seconds,
            )


def _telegram_delivery_error(response: httpx.Response) -> NotificationDeliveryError:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    error_code = payload.get("error_code")
    if not isinstance(error_code, int):
        error_code = response.status_code
    description = payload.get("description")
    normalized_description = description.lower() if isinstance(description, str) else ""

    if error_code == 429:
        parameters = payload.get("parameters")
        retry_after_seconds = (
            parameters.get("retry_after") if isinstance(parameters, dict) else None
        )
        retry_after = (
            timedelta(seconds=retry_after_seconds)
            if isinstance(retry_after_seconds, int) and retry_after_seconds > 0
            else None
        )
        return NotificationDeliveryError("telegram_rate_limited", retry_after=retry_after)

    if error_code == 403 or (
        error_code == 400
        and any(
            marker in normalized_description for marker in ("chat not found", "user is deactivated")
        )
    ):
        return NotificationDeliveryError(
            "telegram_chat_unavailable",
            terminal_status="cancelled",
        )

    if 400 <= error_code < 500:
        return NotificationDeliveryError(
            f"telegram_http_status:{error_code}",
            terminal_status="failed",
        )
    return NotificationDeliveryError(f"telegram_http_status:{error_code}")


def _log_delivery_failure(notification_id: int, error: Exception) -> None:
    notification_ref = hmac.new(
        settings.secret_key.encode("utf-8"),
        str(notification_id).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()[:16]
    logger.error(
        "notification_delivery_failed",
        extra={
            "notification_ref": f"notification:{notification_ref}",
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
    if not settings.telegram_bot_token or settings.telegram_bot_token in {
        "change-me",
        "replace-me",
    }:
        raise NotificationDeliveryError(
            "bot_token_not_configured",
            terminal_status="failed",
        )
    payload: dict = {"chat_id": chat_id, "text": text}
    if open_app_path:
        destination = validate_notification_destination(open_app_path)
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {
                        "text": "Открыть приложение",
                        "web_app": {
                            "url": f"{settings.frontend_base_url.rstrip('/')}{destination}"
                        },
                    }
                ]
            ]
        }
    response = await client.post(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
        json=payload,
    )
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = None
    if (
        response.is_success
        and isinstance(response_payload, dict)
        and response_payload.get("ok") is True
    ):
        return
    raise _telegram_delivery_error(response)


def _prepare_delivery(
    db: Session,
    row: Notification,
    user: User | None,
    setting: NotificationSetting | None,
) -> tuple[int, str, str] | None:
    if row.status != "processing":
        return None
    if user is None or not user.is_active:
        row.status = "cancelled"
        row.last_error = "account_unavailable"
        row.processing_started_at = None
        return None
    if row.channel != "telegram":
        mark_delivery_succeeded(db, row, user, commit=False)
        return None
    if user.telegram_user_id is None:
        row.status = "cancelled"
        row.last_error = "telegram_identity_not_linked"
        row.processing_started_at = None
        return None
    if setting is None or not setting.telegram_enabled:
        row.status = "cancelled"
        row.last_error = "telegram_channel_disabled"
        row.processing_started_at = None
        return None
    if not reminder_category_enabled(row, setting):
        row.status = "cancelled"
        row.last_error = "reminder_category_disabled"
        row.processing_started_at = None
        return None
    if row.event_kind != "security":
        retry_at = quiet_hours_retry_at(setting, user)
        if retry_at is not None:
            row.status = "queued"
            row.next_attempt_at = retry_at
            row.processing_started_at = None
            return None
    open_app_path, _ = resolve_notification_destination(db, user, row)
    return user.telegram_user_id, neutral_telegram_text(row), open_app_path


async def run_once(*, sync_reminders: bool = True) -> None:
    with get_session_context() as db:
        prune_account_exports(db)
        if sync_reminders:
            prune_support_cases(db)
            sync_workout_reminders(db)
            sync_weekly_check_in_reminders(db)
            sync_measurement_reminders(db)
        rows = claim_due_notifications(db)
        users = {
            user.id: user
            for user in db.query(User).filter(User.id.in_({row.user_id for row in rows})).all()
        }
        notification_settings = {
            row.user_id: row
            for row in db.query(NotificationSetting)
            .filter(NotificationSetting.user_id.in_(users))
            .all()
        }
        deliveries: list[int] = []
        for row in rows:
            user = users.get(row.user_id)
            setting = notification_settings.get(user.id) if user is not None else None
            if _prepare_delivery(db, row, user, setting) is not None:
                deliveries.append(row.id)
        db.commit()

        if not deliveries:
            return

        semaphore = asyncio.Semaphore(settings.notification_delivery_concurrency)
        rate_limiter = TelegramRateLimiter(TELEGRAM_DELIVERY_RATE_PER_SECOND)

        async with httpx.AsyncClient(timeout=20) as client:

            async def deliver(
                notification_id: int,
            ) -> tuple[int, bool, Exception | None]:
                try:
                    async with semaphore:
                        await rate_limiter.acquire()
                        with get_session_context() as preflight_db:
                            current_row = preflight_db.get(Notification, notification_id)
                            current_user = (
                                preflight_db.get(User, current_row.user_id)
                                if current_row is not None
                                else None
                            )
                            current_setting = (
                                preflight_db.query(NotificationSetting)
                                .filter(NotificationSetting.user_id == current_user.id)
                                .first()
                                if current_user is not None
                                else None
                            )
                            prepared = (
                                _prepare_delivery(
                                    preflight_db,
                                    current_row,
                                    current_user,
                                    current_setting,
                                )
                                if current_row is not None
                                else None
                            )
                        if prepared is None:
                            return notification_id, False, None
                        chat_id, text, open_app_path = prepared
                        await send_telegram_message(
                            client, chat_id, text, open_app_path=open_app_path
                        )
                    return notification_id, True, None
                except NotificationDeliveryError as exc:
                    if exc.retry_after is not None:
                        await rate_limiter.defer(exc.retry_after.total_seconds())
                    return notification_id, True, exc
                except Exception as exc:
                    return notification_id, True, exc

            results = await asyncio.gather(
                *(deliver(notification_id) for notification_id in deliveries)
            )

        attempted_results = [
            (notification_id, error) for notification_id, attempted, error in results if attempted
        ]
        if not attempted_results:
            return
        result_by_id = dict(attempted_results)
        db.expire_all()
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
        for notification_id, error in attempted_results:
            delivered_row = delivered_rows.get(notification_id)
            if delivered_row is None or delivered_row.status != "processing":
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
