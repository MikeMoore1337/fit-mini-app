from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import httpx
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import (
    local_naive_to_utc_naive,
    now_for_user_naive,
    now_msk_naive,
    to_user_timezone_naive,
    user_local_naive_to_utc_naive,
)
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.program import UserProgram, UserWorkout
from fitminiapp_api.models.user import CoachClientInvite, User, UserProfile

MAX_DELIVERY_ATTEMPTS = 5
PROCESSING_TIMEOUT = timedelta(minutes=5)
TERMINAL_RETENTION = timedelta(days=90)
RETENTION_BATCH_SIZE = 1000


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def safe_delivery_error(error: Exception) -> str:
    """Return a bounded diagnostic code without serializing request URLs or secrets."""
    if isinstance(error, httpx.HTTPStatusError):
        return f"http_status:{error.response.status_code}"
    if isinstance(error, httpx.TimeoutException):
        return "timeout"
    if isinstance(error, httpx.RequestError):
        return "transport_error"
    return f"unexpected:{type(error).__name__}"[:2000]


def get_or_create_settings(db: Session, user: User) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    if not setting:
        db.query(User).filter(User.id == user.id).with_for_update().one()
        setting = (
            db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
        )
        if not setting:
            setting = NotificationSetting(
                user_id=user.id,
                workout_reminders_enabled=True,
                reminder_hour=9,
            )
            db.add(setting)
            db.commit()
            db.refresh(setting)
    return setting


def list_my_notifications(db: Session, user: User, limit: int = 100) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.scheduled_for.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )


def prune_terminal_records(db: Session) -> int:
    """Bound terminal operational history while preserving relation/audit rows."""
    cutoff = now_msk_naive() - TERMINAL_RETENTION
    notification_ids = [
        row.id
        for row in db.query(Notification.id)
        .filter(
            Notification.status.in_(("sent", "cancelled", "failed")),
            Notification.created_at < cutoff,
        )
        .order_by(Notification.id.asc())
        .limit(RETENTION_BATCH_SIZE)
        .all()
    ]
    invite_ids = [
        row.id
        for row in db.query(CoachClientInvite.id)
        .filter(
            CoachClientInvite.status.in_(("expired", "revoked")),
            CoachClientInvite.created_at < cutoff,
        )
        .order_by(CoachClientInvite.id.asc())
        .limit(RETENTION_BATCH_SIZE)
        .all()
    ]
    if notification_ids:
        db.query(Notification).filter(Notification.id.in_(notification_ids)).delete(
            synchronize_session=False
        )
    if invite_ids:
        db.query(CoachClientInvite).filter(CoachClientInvite.id.in_(invite_ids)).delete(
            synchronize_session=False
        )
    deleted = len(notification_ids) + len(invite_ids)
    if deleted:
        db.commit()
    return deleted


def get_due_notifications(
    db: Session,
    now: datetime | None = None,
    limit: int = 100,
) -> list[Notification]:
    if now and now.tzinfo is not None:
        current_utc = now.astimezone(UTC).replace(tzinfo=None)
    else:
        current_utc = now or utcnow()
    return (
        db.query(Notification)
        .filter(
            Notification.status == "queued",
            Notification.scheduled_for_utc <= current_utc,
            or_(Notification.next_attempt_at.is_(None), Notification.next_attempt_at <= utcnow()),
        )
        .order_by(Notification.scheduled_for_utc.asc(), Notification.id.asc())
        .limit(limit)
        .all()
    )


def sync_workout_reminders(db: Session) -> int:
    prune_terminal_records(db)
    created = 0
    rows = (
        db.query(NotificationSetting, User, UserProfile.timezone)
        .join(User, User.id == NotificationSetting.user_id)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .filter(User.is_active.is_(True))
        .all()
    )
    if not rows:
        return 0

    user_ids = [user.id for _, user, _ in rows]
    settings_by_user = {user.id: (setting, user, timezone) for setting, user, timezone in rows}
    min_today = min(now_for_user_naive(user).date() for _, user, _ in rows)

    workouts = (
        db.query(UserWorkout, UserProgram.user_id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id.in_(user_ids),
            UserProgram.is_active.is_(True),
            UserWorkout.status == "planned",
            UserWorkout.scheduled_date >= min_today,
        )
        .all()
    )
    scheduled_workouts: list[tuple[UserWorkout, User, str | None, datetime]] = []
    active_keys: set[str] = set()
    for workout, user_id in workouts:
        setting, user, timezone = settings_by_user[user_id]
        if not setting.workout_reminders_enabled:
            continue
        if workout.scheduled_date < now_for_user_naive(user).date():
            continue
        dedupe_key = f"workout:{workout.id}:reminder"
        active_keys.add(dedupe_key)
        scheduled_workouts.append(
            (
                workout,
                user,
                timezone,
                datetime.combine(workout.scheduled_date, time(hour=setting.reminder_hour)),
            )
        )

    reminder_scope = [Notification.status == "queued"]
    if active_keys:
        reminder_scope.append(Notification.dedupe_key.in_(active_keys))
    reminders = (
        db.query(Notification)
        .filter(
            Notification.user_id.in_(user_ids),
            Notification.dedupe_key.like("workout:%"),
            or_(*reminder_scope),
        )
        .all()
    )
    reminders_by_key = {row.dedupe_key: row for row in reminders}
    queued_by_user: dict[int, list[Notification]] = {}
    for notification in reminders:
        if notification.status == "queued":
            queued_by_user.setdefault(notification.user_id, []).append(notification)

    for workout, user, timezone, scheduled_for in scheduled_workouts:
        dedupe_key = f"workout:{workout.id}:reminder"
        existing_notification = reminders_by_key.get(dedupe_key)
        if existing_notification:
            if existing_notification.status in {"queued", "cancelled"}:
                was_cancelled = existing_notification.status == "cancelled"
                existing_notification.status = "queued"
                existing_notification.scheduled_for = scheduled_for
                existing_notification.scheduled_for_utc = local_naive_to_utc_naive(
                    scheduled_for,
                    timezone,
                )
                if was_cancelled:
                    existing_notification.attempt_count = 0
                    existing_notification.last_error = None
                    existing_notification.next_attempt_at = None
                    existing_notification.processing_started_at = None
            continue
        notification = Notification(
            user_id=user.id,
            channel="telegram",
            title="Тренировка сегодня",
            body=f"По плану: {workout.title}",
            scheduled_for=scheduled_for,
            scheduled_for_utc=local_naive_to_utc_naive(scheduled_for, timezone),
            status="queued",
            dedupe_key=dedupe_key,
        )
        db.add(notification)
        reminders_by_key[dedupe_key] = notification
        created += 1

    for user_id, notifications in queued_by_user.items():
        setting, _, _ = settings_by_user[user_id]
        for notification in notifications:
            if not setting.workout_reminders_enabled or notification.dedupe_key not in active_keys:
                notification.status = "cancelled"

    try:
        db.commit()
    except IntegrityError:
        # Параллельный worker мог первым создать тот же dedupe_key.
        db.rollback()
        return 0
    return created


def claim_due_notifications(db: Session, limit: int = 100) -> list[Notification]:
    stale_before = utcnow() - PROCESSING_TIMEOUT
    db.query(Notification).filter(
        Notification.status == "processing",
        Notification.processing_started_at < stale_before,
        Notification.attempt_count < MAX_DELIVERY_ATTEMPTS,
    ).update(
        {
            Notification.status: "queued",
            Notification.processing_started_at: None,
        },
        synchronize_session=False,
    )
    db.commit()

    due = get_due_notifications(db, limit=limit)
    claimed_ids: list[int] = []
    started_at = utcnow()
    for notification in due:
        updated = (
            db.query(Notification)
            .filter(
                Notification.id == notification.id,
                Notification.status == "queued",
            )
            .update(
                {
                    Notification.status: "processing",
                    Notification.processing_started_at: started_at,
                },
                synchronize_session=False,
            )
        )
        if updated == 1:
            claimed_ids.append(notification.id)
    db.commit()
    if not claimed_ids:
        return []
    return db.query(Notification).filter(Notification.id.in_(claimed_ids)).all()


def mark_delivery_succeeded(
    db: Session,
    notification: Notification,
    user: User,
    *,
    commit: bool = True,
) -> None:
    notification.status = "sent"
    notification.sent_at = now_for_user_naive(user)
    notification.last_error = None
    notification.processing_started_at = None
    notification.next_attempt_at = None
    if commit:
        db.commit()


def mark_delivery_failed(
    db: Session,
    notification: Notification,
    error: Exception,
    *,
    commit: bool = True,
) -> None:
    notification.attempt_count += 1
    notification.last_error = safe_delivery_error(error)
    notification.processing_started_at = None
    if notification.attempt_count >= MAX_DELIVERY_ATTEMPTS:
        notification.status = "failed"
        notification.next_attempt_at = None
    else:
        notification.status = "queued"
        delay_minutes = min(60, 2 ** (notification.attempt_count - 1))
        notification.next_attempt_at = utcnow() + timedelta(minutes=delay_minutes)
    if commit:
        db.commit()


def create_manual_notification(
    db: Session,
    user: User,
    title: str,
    body: str,
    scheduled_for: datetime,
    channel: str = "app",
) -> Notification:
    notification = Notification(
        user_id=user.id,
        channel=channel,
        title=title.strip(),
        body=body.strip(),
        scheduled_for=to_user_timezone_naive(scheduled_for, user),
        scheduled_for_utc=(
            scheduled_for.astimezone(UTC).replace(tzinfo=None)
            if scheduled_for.tzinfo is not None
            else user_local_naive_to_utc_naive(scheduled_for, user)
        ),
        status="queued",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def queue_telegram_notification(
    db: Session,
    user: User,
    *,
    title: str,
    body: str,
    dedupe_key: str | None = None,
    action_url: str | None = None,
) -> Notification:
    """Add an immediate Telegram notification to the current transaction."""
    scheduled_for = now_for_user_naive(user)
    notification = Notification(
        user_id=user.id,
        channel="telegram",
        title=title.strip(),
        body=body.strip(),
        scheduled_for=scheduled_for,
        scheduled_for_utc=user_local_naive_to_utc_naive(scheduled_for, user),
        status="queued",
        dedupe_key=dedupe_key,
        action_url=action_url,
    )
    db.add(notification)
    return notification


def delete_notification_for_user(
    db: Session,
    user: User,
    notification_id: int,
) -> bool:
    row = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
        .first()
    )
    if not row:
        return False

    db.delete(row)
    db.commit()
    return True
