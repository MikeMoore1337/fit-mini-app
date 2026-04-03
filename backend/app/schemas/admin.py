from datetime import datetime

from pydantic import BaseModel


class AdminUserRow(BaseModel):
    id: int
    telegram_user_id: int
    name: str | None = None
    is_coach: bool
    is_admin: bool
    created_at: datetime


class AdminPaymentRow(BaseModel):
    provider_payment_id: str
    status: str
    amount: float
    currency: str
    created_at: datetime


class AdminNotificationRow(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    scheduled_for: datetime
    sent_at: datetime | None = None
