from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.admin import AdminNotificationRow, AdminPaymentRow, AdminUserRow
from app.services.admin import admin_notifications, admin_payments, admin_templates, admin_users
from app.services.security import require_coach

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserRow])
def users(db: Session = Depends(get_db), user=Depends(require_coach)):
    del user
    return [
        AdminUserRow(
            id=row.id,
            telegram_user_id=row.telegram_user_id,
            name=row.profile.full_name if row.profile else None,
            is_coach=row.is_coach,
            is_admin=row.is_admin,
            created_at=row.created_at,
        )
        for row in admin_users(db)
    ]


@router.get("/payments", response_model=list[AdminPaymentRow])
def payments(db: Session = Depends(get_db), user=Depends(require_coach)):
    del user
    return [
        AdminPaymentRow(
            provider_payment_id=row.provider_payment_id,
            status=row.status,
            amount=float(row.amount),
            currency=row.currency,
            created_at=row.created_at,
        )
        for row in admin_payments(db)
    ]


@router.get("/notifications", response_model=list[AdminNotificationRow])
def notifications(db: Session = Depends(get_db), user=Depends(require_coach)):
    del user
    return [
        AdminNotificationRow(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            status=row.status,
            scheduled_for=row.scheduled_for,
            sent_at=row.sent_at,
        )
        for row in admin_notifications(db)
    ]


@router.get("/templates")
def templates(db: Session = Depends(get_db), user=Depends(require_coach)):
    del user
    return [
        {"id": row.id, "title": row.title, "goal": row.goal, "level": row.level, "is_public": row.is_public}
        for row in admin_templates(db)
    ]
