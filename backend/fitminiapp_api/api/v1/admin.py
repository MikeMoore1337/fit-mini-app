from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_admin, require_root_admin
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.program import ProgramTemplate
from fitminiapp_api.models.user import CoachRoleApplication, User, UserProfile
from fitminiapp_api.schemas.admin import (
    AdminNotificationRow,
    AdminTemplateRow,
    AdminUserAdminCapabilityUpdate,
    AdminUserRoleUpdate,
    AdminUserRow,
    AdminUserStatusUpdate,
)
from fitminiapp_api.schemas.coach_application import (
    AdminCoachRoleApplicationReview,
    AdminCoachRoleApplicationRow,
)
from fitminiapp_api.services.accounts import delete_user_cascade
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.coach_applications import (
    approve_pending_coach_applications,
    review_coach_application,
)
from fitminiapp_api.services.coach_clients import close_user_coaching_relationships
from fitminiapp_api.services.programs import delete_template_cascade
from fitminiapp_api.services.root_admin import is_root_user
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


def _require_mutable_target(user: User) -> None:
    if is_root_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Операции с Root-аккаунтом запрещены",
        )


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
    _require_mutable_target(user)

    if payload.role == "client":
        close_user_coaching_relationships(
            db,
            user,
            include_as_client=False,
            reason="coach_role_removed",
            actor_user_id=current_user.id,
        )
        user.is_coach = False
    else:
        user.is_coach = True
        approve_pending_coach_applications(db, user, current_user)

    record_audit_event(
        db,
        action="admin.user_trainer_capability_updated",
        resource_type="user",
        actor_user_id=current_user.id,
        target_user_id=user.id,
        resource_id=user.id,
        details={"is_coach": user.is_coach},
    )

    db.commit()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return _serialize_user_row(user, profile)


@router.patch("/users/{user_id}/admin-capability", response_model=AdminUserRow)
def update_user_admin_capability(
    user_id: int,
    payload: AdminUserAdminCapabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_admin),
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    _require_mutable_target(user)

    user.is_admin = payload.is_admin
    record_audit_event(
        db,
        action="root.user_admin_capability_updated",
        resource_type="user",
        actor_user_id=current_user.id,
        target_user_id=user.id,
        resource_id=user.id,
        details={"is_admin": user.is_admin},
    )
    db.commit()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return _serialize_user_row(user, profile)


@router.get("/coach-applications", response_model=list[AdminCoachRoleApplicationRow])
def admin_coach_applications(
    response: Response,
    application_status: str | None = Query(
        default="pending",
        alias="status",
        pattern="^(pending|approved|rejected|cancelled)$",
    ),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    query = (
        db.query(CoachRoleApplication, User, UserProfile)
        .join(User, User.id == CoachRoleApplication.user_id)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
    )
    if application_status:
        query = query.filter(CoachRoleApplication.status == application_status)
    response.headers["X-Total-Count"] = str(query.count())
    rows = (
        query.order_by(CoachRoleApplication.created_at.desc(), CoachRoleApplication.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": application.id,
            "user_id": user.id,
            "username": user.username,
            "full_name": profile.full_name if profile else None,
            "status": application.status,
            "source": application.source,
            "created_at": application.created_at,
            "reviewed_at": application.reviewed_at,
        }
        for application, user, profile in rows
    ]


@router.patch(
    "/coach-applications/{application_id}",
    response_model=AdminCoachRoleApplicationRow,
)
def update_coach_application(
    application_id: int,
    payload: AdminCoachRoleApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    application = (
        db.query(CoachRoleApplication).filter(CoachRoleApplication.id == application_id).first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    application = review_coach_application(db, application, current_user, payload.status)
    applicant = db.query(User).filter(User.id == application.user_id).one()
    profile = db.query(UserProfile).filter(UserProfile.user_id == applicant.id).first()
    return {
        "id": application.id,
        "user_id": applicant.id,
        "username": applicant.username,
        "full_name": profile.full_name if profile else None,
        "status": application.status,
        "source": application.source,
        "created_at": application.created_at,
        "reviewed_at": application.reviewed_at,
    }


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
    _require_mutable_target(user)
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
    _require_mutable_target(user)
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить текущего администратора",
        )

    delete_user_cascade(db, user)
    db.commit()


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
    query = db.query(ProgramTemplate).filter(ProgramTemplate.is_public.is_(True))
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
    if not template.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    delete_template_cascade(db, template)
    db.commit()
