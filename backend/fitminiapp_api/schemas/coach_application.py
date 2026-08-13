from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CoachRoleApplicationResponse(BaseModel):
    id: int
    status: Literal["pending", "approved", "rejected", "cancelled"]
    source: Literal["web", "telegram"]
    created_at: datetime
    reviewed_at: datetime | None = None


class AdminCoachRoleApplicationRow(CoachRoleApplicationResponse):
    user_id: int
    username: str | None = None
    full_name: str | None = None


class AdminCoachRoleApplicationReview(BaseModel):
    status: Literal["approved", "rejected"]
