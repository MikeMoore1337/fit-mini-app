from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.billing import Payment, Plan, Subscription
from app.models.user import User


class BillingError(ValueError):
    pass


def list_plans(db: Session) -> list[Plan]:
    return db.query(Plan).order_by(Plan.price.asc()).all()


def get_active_subscription(db: Session, user: User) -> Subscription | None:
    return (
        db.query(Subscription)
        .join(Plan, Subscription.plan_id == Plan.id)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.id.desc())
        .first()
    )


def create_checkout(db: Session, user: User, plan_code: str) -> Payment:
    plan = db.query(Plan).filter(Plan.code == plan_code).first()
    if not plan:
        raise BillingError("Plan not found")
    provider_payment_id = uuid4().hex
    checkout_url = f"{settings.payment_public_url}/app?checkout_id={provider_payment_id}"
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        provider=settings.payment_provider,
        provider_payment_id=provider_payment_id,
        amount=float(plan.price),
        currency=plan.currency,
        status="created",
        checkout_url=checkout_url,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def complete_mock_payment(db: Session, checkout_id: str) -> Payment:
    payment = db.query(Payment).filter(Payment.provider_payment_id == checkout_id).first()
    if not payment:
        raise BillingError("Payment not found")
    if payment.status == "paid":
        return payment

    payment.status = "paid"
    payment.paid_at = datetime.now(UTC).replace(tzinfo=None)

    plan = db.query(Plan).filter(Plan.id == payment.plan_id).first()
    db.query(Subscription).filter(Subscription.user_id == payment.user_id, Subscription.status == "active").update({"status": "replaced"})
    sub = Subscription(
        user_id=payment.user_id,
        plan_id=payment.plan_id,
        status="active",
        starts_at=datetime.now(UTC).replace(tzinfo=None),
        ends_at=(datetime.now(UTC) + timedelta(days=plan.period_days)).replace(tzinfo=None),
    )
    db.add(sub)
    db.commit()
    db.refresh(payment)
    return payment
