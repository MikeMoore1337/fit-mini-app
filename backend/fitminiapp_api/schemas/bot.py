from datetime import datetime
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


class BotNewsModerationRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    action: Literal["skip", "defer", "regenerate", "accept_for_design"]


class BotNewsModerationResponse(BaseModel):
    status: Literal[
        "accepted",
        "queued",
        "deferred",
        "already_processed",
        "stale",
        "limit_reached",
        "unavailable",
    ]
    cluster_status: str | None = None


class BotNewsRevisionActionRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    action: Literal[
        "publish",
        "schedule",
        "regenerate_image",
        "remove_image",
    ]
    expected_image_revision: int = Field(..., ge=0, le=10_000)
    expected_artifact_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{16}$")
    scheduled_local: datetime | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    urgent_override: bool = False


class BotNewsTextEditRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    expected_image_revision: int = Field(..., ge=0, le=10_000)
    draft_text: str = Field(..., min_length=100, max_length=4000)


class BotNewsRevisionActionResponse(BaseModel):
    status: str
    cluster_status: str | None = None
    snapshot_id: str | None = None
    blockers: list[str] = Field(default_factory=list)


class BotNewsPostActionRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    action: Literal["edit", "delete"]
    text: str | None = Field(default=None, max_length=4096)


class BotNewsReconcileRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
    channel_message_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)


class BotNewsRetryRequest(BaseModel):
    admin_telegram_user_id: int = Field(..., ge=1, le=9_223_372_036_854_775_807)
