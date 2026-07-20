from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.timezone import (
    get_timezone,
    now_for_user_naive,
    now_in_timezone_naive,
    to_user_timezone_naive,
)
from app.models.notification import Notification, NotificationSetting
from app.models.program import UserProgram, UserWorkout
from app.models.user import User, UserProfile

MAX_DELIVERY_ATTEMPTS = 5
PROCESSING_TIMEOUT = timedelta(minutes=5)


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def get_or_create_settings(db: Session, user: User) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
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


def get_due_notifications(db: Session, now: datetime | None = None) -> list[Notification]:
    rows = (
        db.query(Notification, UserProfile.timezone)
        .join(User, User.id == Notification.user_id)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .filter(
            Notification.status == "queued",
            or_(Notification.next_attempt_at.is_(None), Notification.next_attempt_at <= utcnow()),
        )
        .order_by(Notification.scheduled_for.asc(), Notification.id.asc())
        .all()
    )

    due = []
    for notification, timezone in rows:
        current_time = (
            now.astimezone(get_timezone(timezone)).replace(tzinfo=None)
            if now and now.tzinfo is not None
            else now or now_in_timezone_naive(timezone)
        )
        if notification.scheduled_for <= current_time:
            due.append(notification)
    return due


def sync_workout_reminders(db: Session) -> int:
    created = 0
    rows = (
        db.query(NotificationSetting, User)
        .join(User, User.id == NotificationSetting.user_id)
        .filter(User.is_active.is_(True))
        .all()
    )
    for setting, user in rows:
        reminder_prefix = "workout:"
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.dedupe_key.like(f"{reminder_prefix}%"),
                Notification.status == "queued",
            )
            .all()
        )
        existing_by_key = {row.dedupe_key: row for row in existing}

        if not setting.workout_reminders_enabled:
            for row in existing:
                row.status = "cancelled"
            continue

        today = now_for_user_naive(user).date()
        workouts = (
            db.query(UserWorkout)
            .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
            .filter(
                UserProgram.user_id == user.id,
                UserProgram.is_active.is_(True),
                UserWorkout.status == "planned",
                UserWorkout.scheduled_date >= today,
            )
            .all()
        )
        active_keys: set[str] = set()
        for workout in workouts:
            dedupe_key = f"workout:{workout.id}:reminder"
            active_keys.add(dedupe_key)
            scheduled_for = datetime.combine(
                workout.scheduled_date,
                time(hour=setting.reminder_hour),
            )
            notification = existing_by_key.get(dedupe_key)
            if notification:
                notification.scheduled_for = scheduled_for
                continue
            if db.query(Notification.id).filter(Notification.dedupe_key == dedupe_key).first():
                continue
            db.add(
                Notification(
                    user_id=user.id,
                    channel="telegram",
                    title="Тренировка сегодня",
                    body=f"По плану: {workout.title}",
                    scheduled_for=scheduled_for,
                    status="queued",
                    dedupe_key=dedupe_key,
                )
            )
            created += 1

        for key, notification in existing_by_key.items():
            if key not in active_keys:
                notification.status = "cancelled"

    db.commit()
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

    due = get_due_notifications(db)[:limit]
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


def mark_delivery_succeeded(db: Session, notification: Notification, user: User) -> None:
    notification.status = "sent"
    notification.sent_at = now_for_user_naive(user)
    notification.last_error = None
    notification.processing_started_at = None
    notification.next_attempt_at = None
    db.commit()


def mark_delivery_failed(db: Session, notification: Notification, error: Exception) -> None:
    notification.attempt_count += 1
    notification.last_error = str(error)[:2000]
    notification.processing_started_at = None
    if notification.attempt_count >= MAX_DELIVERY_ATTEMPTS:
        notification.status = "failed"
        notification.next_attempt_at = None
    else:
        notification.status = "queued"
        delay_minutes = min(60, 2 ** (notification.attempt_count - 1))
        notification.next_attempt_at = utcnow() + timedelta(minutes=delay_minutes)
    db.commit()


def mark_notification_sent(db: Session, notification: Notification) -> Notification:
    user = db.query(User).filter(User.id == notification.user_id).first()
    notification.status = "sent"
    notification.sent_at = now_for_user_naive(user)
    notification.last_error = None
    db.commit()
    db.refresh(notification)
    return notification


def mark_notification_failed(
    db: Session,
    notification: Notification,
    error_message: str,
) -> Notification:
    notification.status = "failed"
    notification.last_error = error_message[:2000] if error_message else "unknown error"
    db.commit()
    db.refresh(notification)
    return notification


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
        status="queued",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
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
