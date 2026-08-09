from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AdminUserRow(BaseModel):
    id: int
    telegram_user_id: int
    username: str | None = None
    role: Literal["client", "coach", "admin"]
    is_coach: bool
    is_admin: bool
    is_active: bool
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None


class AdminNotificationRow(BaseModel):
    id: int
    user_id: int
    timezone: str
    title: str
    body: str
    status: str
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None


class AdminTemplateRow(BaseModel):
    id: int
    title: str
    goal: str
    level: str
    owner_user_id: int | None = None
    created_by_user_id: int | None = None
    is_public: bool


class AdminUserRoleUpdate(BaseModel):
    role: Literal["client", "coach", "admin"]


class AdminUserStatusUpdate(BaseModel):
    is_active: bool
