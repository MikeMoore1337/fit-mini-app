from typing import Literal

from pydantic import BaseModel, Field


class BotTimezoneUpdateRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1)
    timezone: str = Field(..., min_length=1, max_length=64)
    username: str | None = Field(default=None, max_length=64)
    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)


class BotTimezoneUpdateResponse(BaseModel):
    telegram_user_id: int
    timezone: str


class BotTelegramLinkRequest(BaseModel):
    token: str = Field(..., min_length=32, max_length=128)
    telegram_user_id: int = Field(..., ge=1)
    username: str | None = Field(default=None, max_length=64)
    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)


class BotTelegramLinkResponse(BaseModel):
    status: Literal["linked", "already_linked"]


class BotCoachRoleApplicationRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1)
    username: str | None = Field(default=None, max_length=64)
    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)


class BotCoachRoleApplicationResponse(BaseModel):
    status: Literal["pending", "already_pending", "already_coach"]
