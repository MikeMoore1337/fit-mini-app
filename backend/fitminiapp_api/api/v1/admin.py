from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_admin
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.billing import Payment, Plan
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.program import ProgramTemplate
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.admin import (
    AdminNotificationRow,
    AdminPaymentRow,
    AdminTemplateRow,
    AdminUserRoleUpdate,
    AdminUserRow,
    AdminUserStatusUpdate,
)
from fitminiapp_api.services.accounts import delete_user_cascade
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.coach_clients import close_user_coaching_relationships
from fitminiapp_api.services.programs import delete_template_cascade
from fitminiapp_api.services.token_service import revoke_all_user_refresh_tokens

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
        "is_active": user.is_active,
        "full_name": profile.full_name if profile else None,
        "goal": profile.goal if profile else None,
        "level": profile.level if profile else None,
    }


@router.get("/users", response_model=list[AdminUserRow])
def admin_users(
    response: Response,
    search: str | None = Query(default=None, max_length=128),
    role: str | None = Query(default=None, pattern="^(client|coach|admin)$"),
    active: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    query = db.query(User, UserProfile).outerjoin(UserProfile, UserProfile.user_id == User.id)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(func.coalesce(UserProfile.full_name, "")).like(pattern),
                func.lower(func.coalesce(User.username, "")).like(pattern),
                cast(User.telegram_user_id, String).like(pattern),
            )
        )
    if role == "admin":
        query = query.filter(User.is_admin.is_(True))
    elif role == "coach":
        query = query.filter(User.is_coach.is_(True), User.is_admin.is_(False))
    elif role == "client":
        query = query.filter(User.is_coach.is_(False), User.is_admin.is_(False))
    if active is not None:
        query = query.filter(User.is_active.is_(active))
    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    rows = query.order_by(User.id.desc()).offset(offset).limit(limit).all()

    return [_serialize_user_row(user, profile) for user, profile in rows]


@router.patch("/users/{user_id}/role", response_model=AdminUserRow)
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
        close_user_coaching_relationships(
            db,
            user,
            include_as_client=False,
            reason="coach_role_removed",
            actor_user_id=current_user.id,
        )
        user.is_coach = False
        user.is_admin = False
    elif payload.role == "coach":
        user.is_coach = True
        user.is_admin = False
    else:
        user.is_coach = True
        user.is_admin = True

    record_audit_event(
        db,
        action="admin.user_role_updated",
        resource_type="user",
        actor_user_id=current_user.id,
        target_user_id=user.id,
        resource_id=user.id,
        details={"role": payload.role},
    )

    db.commit()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return _serialize_user_row(user, profile)


@router.patch("/users/{user_id}/status", response_model=AdminUserRow)
def update_user_status(
    user_id: int,
    payload: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать текущего администратора",
        )

    user.is_active = payload.is_active
    if not user.is_active:
        revoke_all_user_refresh_tokens(db, user.id, commit=False)
        close_user_coaching_relationships(
            db,
            user,
            include_as_client=True,
            reason="user_deactivated",
            actor_user_id=current_user.id,
        )

    record_audit_event(
        db,
        action="admin.user_status_updated",
        resource_type="user",
        actor_user_id=current_user.id,
        target_user_id=user.id,
        resource_id=user.id,
        details={
            "status": "active" if user.is_active else "inactive",
            "reason": "admin_update",
        },
    )

    db.commit()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return _serialize_user_row(user, profile)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить текущего администратора",
        )

    delete_user_cascade(db, user)
    db.commit()


@router.get("/payments", response_model=list[AdminPaymentRow])
def admin_payments(
    response: Response,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    query = (
        db.query(Payment, Plan, User)
        .outerjoin(Plan, Plan.id == Payment.plan_id)
        .outerjoin(User, User.id == Payment.user_id)
    )
    response.headers["X-Total-Count"] = str(query.count())
    rows = query.order_by(Payment.id.desc()).offset(offset).limit(limit).all()

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


@router.get("/notifications", response_model=list[AdminNotificationRow])
def admin_notifications(
    response: Response,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    query = db.query(Notification, UserProfile.timezone).outerjoin(
        UserProfile, UserProfile.user_id == Notification.user_id
    )
    response.headers["X-Total-Count"] = str(query.count())
    rows = query.order_by(Notification.id.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "timezone": timezone or "Europe/Moscow",
            "title": row.title,
            "body": row.body,
            "status": row.status,
            "scheduled_for": row.scheduled_for.isoformat() if row.scheduled_for else None,
            "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        }
        for row, timezone in rows
    ]


@router.get("/templates", response_model=list[AdminTemplateRow])
def admin_templates(
    response: Response,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    query = db.query(ProgramTemplate)
    response.headers["X-Total-Count"] = str(query.count())
    rows = query.order_by(ProgramTemplate.id.desc()).offset(offset).limit(limit).all()

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


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    template = db.query(ProgramTemplate).filter(ProgramTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")

    delete_template_cascade(db, template)
    db.commit()
