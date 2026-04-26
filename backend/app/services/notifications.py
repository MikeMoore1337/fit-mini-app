from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.timezone import (
    get_timezone,
    now_for_user_naive,
    now_in_timezone_naive,
    to_user_timezone_naive,
)
from app.models.notification import Notification, NotificationSetting
from app.models.user import User, UserProfile


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
        .filter(Notification.status == "queued")
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
