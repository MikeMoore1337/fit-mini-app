from app.api.dependencies.auth import require_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationCreateRequest,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdate,
)
from app.services.notifications import (
    create_notification,
    delete_notification,
    get_or_create_settings,
    list_my_notifications,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/settings", response_model=NotificationSettingResponse)
def get_settings(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    settings = get_or_create_settings(db, current_user)
    return NotificationSettingResponse(
        workout_reminders_enabled=settings.workout_reminders_enabled,
        reminder_hour=settings.reminder_hour,
    )


@router.patch("/settings", response_model=NotificationSettingResponse)
def patch_settings(
    payload: NotificationSettingUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
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
    items = list_my_notifications(db, current_user)
    return [
        NotificationResponse(
            id=item.id,
            title=item.title,
            body=item.body,
            scheduled_for=item.scheduled_for,
            status=item.status,
            sent_at=item.sent_at,
        )
        for item in items
    ]


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_manual_notification(
    payload: NotificationCreateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    item = create_notification(
        db=db,
        user=current_user,
        title=payload.title,
        body=payload.body,
        scheduled_for=payload.scheduled_for,
    )
    return NotificationResponse(
        id=item.id,
        title=item.title,
        body=item.body,
        scheduled_for=item.scheduled_for,
        status=item.status,
        sent_at=item.sent_at,
    )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_notification(
    notification_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        delete_notification(db, current_user, notification_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
