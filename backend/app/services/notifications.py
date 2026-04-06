from __future__ import annotations

from datetime import UTC, datetime

from app.models.notification import Notification, NotificationSetting
from app.models.user import User
from sqlalchemy.orm import Session


def get_or_create_settings(db: Session, user: User) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    if not setting:
        setting = NotificationSetting(user_id=user.id)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def list_my_notifications(db: Session, user: User) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.scheduled_for.desc(), Notification.id.desc())
        .limit(100)
        .all()
    )


def create_notification(
    db: Session,
    user: User,
    title: str,
    body: str,
    scheduled_for: datetime,
) -> Notification:
    notification = Notification(
        user_id=user.id,
        title=title.strip(),
        body=body.strip(),
        scheduled_for=scheduled_for.astimezone(UTC).replace(tzinfo=None) if scheduled_for.tzinfo else scheduled_for,
        status="queued",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(
    db: Session,
    user: User,
    notification_id: int,
) -> None:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
        .first()
    )
    if not notification:
        raise ValueError("Notification not found")

    db.delete(notification)
    db.commit()


def get_due_notifications(db: Session) -> list[Notification]:
    now = datetime.now(UTC).replace(tzinfo=None)
    return (
        db.query(Notification)
        .filter(
            Notification.status == "queued",
            Notification.scheduled_for <= now,
        )
        .order_by(Notification.scheduled_for.asc())
        .all()
    )
