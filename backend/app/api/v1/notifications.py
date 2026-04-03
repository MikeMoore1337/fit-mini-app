from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notification import NotificationResponse, NotificationSettingResponse, NotificationSettingUpdate
from app.services.notifications import get_or_create_settings, list_my_notifications
from app.services.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingResponse)
def get_settings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    setting = get_or_create_settings(db, user)
    return NotificationSettingResponse(
        workout_reminders_enabled=setting.workout_reminders_enabled,
        reminder_hour=setting.reminder_hour,
    )


@router.patch("/settings", response_model=NotificationSettingResponse)
def patch_settings(payload: NotificationSettingUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    setting = get_or_create_settings(db, user)
    setting.workout_reminders_enabled = payload.workout_reminders_enabled
    setting.reminder_hour = payload.reminder_hour
    db.commit()
    db.refresh(setting)
    return NotificationSettingResponse(
        workout_reminders_enabled=setting.workout_reminders_enabled,
        reminder_hour=setting.reminder_hour,
    )


@router.get("", response_model=list[NotificationResponse])
def my_notifications(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [
        NotificationResponse(
            id=n.id,
            title=n.title,
            body=n.body,
            scheduled_for=n.scheduled_for,
            status=n.status,
            sent_at=n.sent_at,
        )
        for n in list_my_notifications(db, user)
    ]
