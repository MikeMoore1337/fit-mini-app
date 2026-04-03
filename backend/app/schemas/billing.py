from datetime import datetime

from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: int
    code: str
    title: str
    price: float
    currency: str
    period_days: int


class CheckoutRequest(BaseModel):
    plan_code: str


class CheckoutResponse(BaseModel):
    checkout_id: str
    checkout_url: str
    status: str


class SubscriptionResponse(BaseModel):
    id: int
    plan_code: str
    plan_title: str
    status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
