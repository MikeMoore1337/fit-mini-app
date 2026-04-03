from datetime import datetime

from pydantic import BaseModel


class NotificationSettingUpdate(BaseModel):
    workout_reminders_enabled: bool
    reminder_hour: int


class NotificationSettingResponse(BaseModel):
    workout_reminders_enabled: bool
    reminder_hour: int


class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str
    scheduled_for: datetime
    status: str
    sent_at: datetime | None = None
