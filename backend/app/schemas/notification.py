from datetime import datetime

from pydantic import BaseModel, Field


class NotificationSettingUpdate(BaseModel):
    workout_reminders_enabled: bool
    reminder_hour: int = Field(ge=0, le=23)


class NotificationSettingResponse(BaseModel):
    workout_reminders_enabled: bool
    reminder_hour: int


class NotificationCreateRequest(BaseModel):
    title: str
    body: str
    scheduled_for: datetime


class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str
    scheduled_for: datetime
    status: str
    sent_at: datetime | None = None
