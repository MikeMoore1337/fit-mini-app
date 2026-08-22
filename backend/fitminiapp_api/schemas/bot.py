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


BotSupportCategory = Literal["bug", "account", "idea", "contact", "other"]
BotSupportCaseStatus = Literal[
    "pending_relay",
    "open",
    "replying",
    "replied",
    "relay_failed",
    "undeliverable",
    "expired",
]


class BotSupportCaseCreateRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    request_message_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    category: BotSupportCategory


class BotSupportCaseCreateResponse(BaseModel):
    case_id: str
    status: Literal["created", "duplicate"]
    case_status: BotSupportCaseStatus


class BotSupportRelayResultRequest(BaseModel):
    delivered: bool


class BotSupportReplyClaimRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    reply_message_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)


class BotSupportReplyClaimResponse(BaseModel):
    status: Literal["claimed", "already_processed", "unavailable", "expired"]
    telegram_user_id: int | None = None


class BotSupportReplyResultRequest(BotSupportReplyClaimRequest):
    outcome: Literal["delivered", "blocked", "failed"]


class BotSupportReplyResultResponse(BaseModel):
    status: Literal["recorded"]
