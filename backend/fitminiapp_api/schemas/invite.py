from datetime import datetime

from pydantic import BaseModel, Field

from fitminiapp_api.schemas.user import TrainerResponse


class CoachInviteLinkResponse(BaseModel):
    invite_id: int
    code: str
    start_param: str
    url: str | None = None
    expires_at: datetime


class CoachInviteTokenRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class CoachInvitePreviewResponse(BaseModel):
    invite_id: int
    coach: TrainerResponse
    created_at: datetime
    expires_at: datetime | None = None
    requires_trainer_change: bool = False
    already_current_trainer: bool = False
    current_trainer: TrainerResponse | None = None
