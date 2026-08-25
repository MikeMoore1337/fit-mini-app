from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AdminOperationReason = Literal[
    "security_incident",
    "abuse",
    "account_recovery",
    "support_request",
    "relationship_safety",
]


class AdminOperationRequest(BaseModel):
    reason: AdminOperationReason


class AdminUserStatusUpdate(AdminOperationRequest):
    is_active: bool


class AdminTrainerCapabilityUpdate(AdminOperationRequest):
    is_active: bool


class AdminUserSearchRow(BaseModel):
    id: int
    telegram_user_id: int | None = None
    username: str | None = None
    display_name: str
    is_active: bool
    is_trainer: bool
    is_root: bool
    created_at: datetime
    linked_providers: list[str] = Field(default_factory=list)


class AdminIdentityRow(BaseModel):
    provider: str
    identifier: str
    verified: bool
    last_login_at: datetime


class AdminRelationshipRow(BaseModel):
    id: int
    account_role: Literal["trainer", "client"]
    counterparty_user_id: int
    counterparty_name: str
    status: str
    created_at: datetime
    accepted_at: datetime | None = None
    ended_at: datetime | None = None
    ended_reason: str | None = None
    can_end: bool


class AdminJobRow(BaseModel):
    job_id: str
    kind: Literal["notification", "account_export"]
    user_id: int
    status: str
    created_at: datetime
    scheduled_for: datetime | None = None
    completed_at: datetime | None = None
    attempt_count: int | None = None
    error_code: str | None = None
    retry_allowed: bool


class AdminAuditRow(BaseModel):
    id: int
    action: str
    actor_user_id: int | None = None
    target_user_id: int | None = None
    resource_type: str
    resource_id: str | None = None
    reason: AdminOperationReason | None = None
    created_at: datetime


class AdminUserDetail(AdminUserSearchRow):
    identities: list[AdminIdentityRow] = Field(default_factory=list)
    relationships: list[AdminRelationshipRow] = Field(default_factory=list)
    jobs: list[AdminJobRow] = Field(default_factory=list)
    audit_history: list[AdminAuditRow] = Field(default_factory=list)


class AdminFunnelStage(BaseModel):
    key: Literal["registered", "profile_ready", "program_activated", "core_value_reached"]
    account_count: int
    cohort_rate_percent: float


class AdminFunnelResponse(BaseModel):
    period_days: int
    cohort_since: datetime
    analytics_provider_status: Literal["not_connected"]
    coverage_note: str
    stages: list[AdminFunnelStage]
