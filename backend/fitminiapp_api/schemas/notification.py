from datetime import datetime, time

from pydantic import BaseModel, Field


class NotificationSettingUpdate(BaseModel):
    workout_reminders_enabled: bool | None = None
    weekly_check_in_reminders_enabled: bool | None = None
    measurement_reminders_enabled: bool | None = None
    telegram_enabled: bool | None = None
    reminder_hour: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class NotificationSettingResponse(BaseModel):
    workout_reminders_enabled: bool
    weekly_check_in_reminders_enabled: bool
    measurement_reminders_enabled: bool
    telegram_enabled: bool
    telegram_linked: bool
    reminder_hour: int
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class NotificationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    body: str = Field(min_length=1, max_length=2000)
    scheduled_for: datetime


class NotificationResponse(BaseModel):
    id: int
    category: str
    event_kind: str
    title: str
    body: str
    created_at: datetime
    scheduled_for: datetime
    status: str
    delivery_status: str
    sent_at: datetime | None = None
    read_at: datetime | None = None
    action_url: str | None = None


class NotificationOpenResponse(BaseModel):
    destination: str
    stale: bool
    message: str | None = None


class NotificationReadAllResponse(BaseModel):
    updated: int
