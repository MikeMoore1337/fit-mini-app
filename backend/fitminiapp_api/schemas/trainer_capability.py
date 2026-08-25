from typing import Literal

from pydantic import BaseModel


class TrainerCapabilityActivateRequest(BaseModel):
    accepted_terms: Literal[True]


class TrainerCapabilityResponse(BaseModel):
    is_active: bool
    activated_now: bool = False
    active_client_count: int
    pending_invite_count: int
    can_disable: bool
    terms_version: str
