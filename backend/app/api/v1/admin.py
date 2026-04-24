from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.models.billing import Payment, Plan
from app.models.notification import Notification
from app.models.program import ProgramTemplate
from app.models.user import User, UserProfile
from app.schemas.admin import AdminUserRoleUpdate

router = APIRouter()


def _role_from_user(user: User) -> str:
    if user.is_admin:
        return "admin"
    if user.is_coach:
        return "coach"
    return "client"


def _serialize_user_row(user: User, profile: UserProfile | None) -> dict:
    return {
        "id": user.id,
        "telegram_user_id": user.telegram_user_id,
        "username": user.username,
        "role": _role_from_user(user),
        "is_coach": user.is_coach,
        "is_admin": user.is_admin,
        "full_name": profile.full_name if profile else None,
        "goal": profile.goal if profile else None,
        "level": profile.level if profile else None,
    }


@router.get("/users")
def admin_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    rows = (
        db.query(User, UserProfile)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .order_by(User.id.desc())
        .all()
    )

    return [_serialize_user_row(user, profile) for user, profile in rows]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: AdminUserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.id == current_user.id and payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя снять роль администратора с текущего пользователя",
        )

    if payload.role == "client":
        user.is_coach = False
        user.is_admin = False
    elif payload.role == "coach":
        user.is_coach = True
        user.is_admin = False
    else:
        user.is_coach = True
        user.is_admin = True

    db.commit()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return _serialize_user_row(user, profile)


@router.get("/payments")
def admin_payments(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    rows = (
        db.query(Payment, Plan, User)
        .outerjoin(Plan, Plan.id == Payment.plan_id)
        .outerjoin(User, User.id == Payment.user_id)
        .order_by(Payment.id.desc())
        .all()
    )

    result = []
    for payment, plan, user in rows:
        plan_code = plan.code if plan else None
        result.append(
            {
                "id": payment.id,
                "telegram_user_id": user.telegram_user_id if user else None,
                "plan_code": plan_code,
                "plan_title": plan.title if plan else plan_code,
                "status": payment.status,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
            }
        )
    return result


@router.get("/notifications")
def admin_notifications(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
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
    _: User = Depends(require_admin),
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
