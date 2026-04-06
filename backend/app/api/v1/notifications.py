from datetime import datetime

from app.api.dependencies.auth import require_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdate,
)
from app.services.notifications import get_or_create_settings, list_my_notifications
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/settings", response_model=NotificationSettingResponse)
def get_notification_settings(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    settings = get_or_create_settings(db, current_user)
    return NotificationSettingResponse(
        workout_reminders_enabled=settings.workout_reminders_enabled,
        reminder_hour=settings.reminder_hour,
    )


@router.patch("/settings", response_model=NotificationSettingResponse)
def update_notification_settings(
    payload: NotificationSettingUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if payload.reminder_hour < 0 or payload.reminder_hour > 23:
        raise HTTPException(status_code=400, detail="reminder_hour должен быть от 0 до 23")

    settings = get_or_create_settings(db, current_user)
    settings.workout_reminders_enabled = payload.workout_reminders_enabled
    settings.reminder_hour = payload.reminder_hour
    db.commit()
    db.refresh(settings)

    return NotificationSettingResponse(
        workout_reminders_enabled=settings.workout_reminders_enabled,
        reminder_hour=settings.reminder_hour,
    )


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    rows = list_my_notifications(db, current_user)
    return [
        NotificationResponse(
            id=row.id,
            title=row.title,
            body=row.body,
            scheduled_for=row.scheduled_for,
            status=row.status,
            sent_at=row.sent_at,
        )
        for row in rows
    ]


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: dict,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    title = (payload.get("title") or "").strip()
    body = (payload.get("body") or "").strip()
    scheduled_for_raw = payload.get("scheduled_for")

    if not title:
        raise HTTPException(status_code=400, detail="title обязателен")
    if not body:
        raise HTTPException(status_code=400, detail="body обязателен")
    if not scheduled_for_raw:
        raise HTTPException(status_code=400, detail="scheduled_for обязателен")

    try:
        scheduled_for = datetime.fromisoformat(str(scheduled_for_raw).replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный формат scheduled_for")

    if scheduled_for.tzinfo is not None:
        scheduled_for = scheduled_for.astimezone().replace(tzinfo=None)

    row = Notification(
        user_id=current_user.id,
        channel="app",
        title=title,
        body=body,
        scheduled_for=scheduled_for,
        status="queued",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return NotificationResponse(
        id=row.id,
        title=row.title,
        body=row.body,
        scheduled_for=row.scheduled_for,
        status=row.status,
        sent_at=row.sent_at,
    )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")

    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
