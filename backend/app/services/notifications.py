from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationSetting
from app.models.user import User


def get_or_create_settings(db: Session, user: User) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    if not setting:
        setting = NotificationSetting(user_id=user.id)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def list_my_notifications(db: Session, user: User) -> list[Notification]:
    return db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.id.desc()).limit(50).all()


def get_due_notifications(db: Session) -> list[Notification]:
    now = datetime.now(UTC).replace(tzinfo=None)
    return db.query(Notification).filter(Notification.status == "queued", Notification.scheduled_for <= now).order_by(Notification.scheduled_for.asc()).all()
