from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.billing import Payment, Plan
from app.models.notification import Notification
from app.models.program import ProgramTemplate
from app.models.user import User, UserProfile
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


def require_admin_or_coach(current_user: User = Depends(get_current_user)) -> User:
    if not (current_user.is_admin or current_user.is_coach):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return current_user


@router.get("/users")
def admin_users(
        db: Session = Depends(get_db),
        _: User = Depends(require_admin_or_coach),
) -> list[dict]:
    rows = (
        db.query(User, UserProfile)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .order_by(User.id.desc())
        .all()
    )

    result = []
    for user, profile in rows:
        result.append(
            {
                "id": user.id,
                "telegram_user_id": user.telegram_user_id,
                "is_coach": user.is_coach,
                "is_admin": user.is_admin,
                "full_name": profile.full_name if profile else None,
                "goal": profile.goal if profile else None,
                "level": profile.level if profile else None,
            }
        )
    return result


@router.get("/payments")
def admin_payments(
        db: Session = Depends(get_db),
        _: User = Depends(require_admin_or_coach),
) -> list[dict]:
    rows = (
        db.query(Payment, Plan)
        .outerjoin(Plan, Plan.code == Payment.plan_code)
        .order_by(Payment.id.desc())
        .all()
    )

    result = []
    for payment, plan in rows:
        result.append(
            {
                "id": payment.id,
                "telegram_user_id": payment.telegram_user_id,
                "plan_code": payment.plan_code,
                "plan_title": plan.title if plan else payment.plan_code,
                "status": payment.status,
                "amount": payment.amount,
                "currency": payment.currency,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
            }
        )
    return result


@router.get("/notifications")
def admin_notifications(
        db: Session = Depends(get_db),
        _: User = Depends(require_admin_or_coach),
) -> list[dict]:
    rows = db.query(Notification).order_by(Notification.id.desc()).limit(200).all()

    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "title": row.title,
            "body": row.body,
            "status": row.status,
            "scheduled_for": row.scheduled_for.isoformat() if row.scheduled_for else None,
            "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        }
        for row in rows
    ]


@router.get("/templates")
def admin_templates(
        db: Session = Depends(get_db),
        _: User = Depends(require_admin_or_coach),
) -> list[dict]:
    rows = db.query(ProgramTemplate).order_by(ProgramTemplate.id.desc()).all()

    return [
        {
            "id": row.id,
            "title": row.title,
            "goal": row.goal,
            "level": row.level,
            "owner_user_id": row.owner_user_id,
            "created_by_user_id": row.created_by_user_id,
            "is_public": row.is_public,
        }
        for row in rows
    ]
