from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.billing import CheckoutRequest, CheckoutResponse, PlanResponse, SubscriptionResponse
from app.services.billing import BillingError, complete_mock_payment, create_checkout, get_active_subscription, list_plans
from app.services.security import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanResponse])
def plans(db: Session = Depends(get_db), user=Depends(get_current_user)):
    del user
    return [PlanResponse(id=p.id, code=p.code, title=p.title, price=float(p.price), currency=p.currency, period_days=p.period_days) for p in list_plans(db)]


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        payment = create_checkout(db, user, payload.plan_code)
    except BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CheckoutResponse(checkout_id=payment.provider_payment_id, checkout_url=payment.checkout_url or "", status=payment.status)


@router.post("/mock/complete/{checkout_id}")
def mock_complete(checkout_id: str, db: Session = Depends(get_db)):
    try:
        payment = complete_mock_payment(db, checkout_id)
    except BillingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": payment.status}


@router.get("/subscription", response_model=SubscriptionResponse | None)
def my_subscription(db: Session = Depends(get_db), user=Depends(get_current_user)):
    sub = get_active_subscription(db, user)
    if not sub:
        return None
    return SubscriptionResponse(
        id=sub.id,
        plan_code=sub.plan.code,
        plan_title=sub.plan.title,
        status=sub.status,
        starts_at=sub.starts_at,
        ends_at=sub.ends_at,
    )
