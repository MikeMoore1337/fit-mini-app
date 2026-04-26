from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.models.billing import Payment, Plan, Subscription
from app.models.exercise import Exercise
from app.models.notification import Notification, NotificationSetting
from app.models.program import (
    ProgramTemplate,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from app.models.token import RefreshToken
from app.models.user import CoachClient, CoachClientInvite, User, UserProfile
from app.schemas.admin import AdminUserRoleUpdate, AdminUserStatusUpdate
from app.services.programs import delete_template_cascade
from app.services.token_service import revoke_all_user_refresh_tokens

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


def _delete_user_programs(db: Session, user_program_ids: list[int]) -> None:
    if not user_program_ids:
        return

    workouts = db.query(UserWorkout).filter(UserWorkout.user_program_id.in_(user_program_ids)).all()
    workout_ids = [item.id for item in workouts]

    if workout_ids:
        workout_exercises = (
            db.query(UserWorkoutExercise)
            .filter(UserWorkoutExercise.workout_id.in_(workout_ids))
            .all()
        )
        workout_exercise_ids = [item.id for item in workout_exercises]

        if workout_exercise_ids:
            db.query(UserWorkoutSet).filter(
                UserWorkoutSet.workout_exercise_id.in_(workout_exercise_ids)
            ).delete(synchronize_session=False)
            db.query(UserWorkoutExercise).filter(
                UserWorkoutExercise.id.in_(workout_exercise_ids)
            ).delete(synchronize_session=False)

        db.query(UserWorkout).filter(UserWorkout.id.in_(workout_ids)).delete(
            synchronize_session=False
        )

    db.query(UserProgram).filter(UserProgram.id.in_(user_program_ids)).delete(
        synchronize_session=False
    )


def _delete_user_cascade(db: Session, user: User) -> None:
    owned_templates = (
        db.query(ProgramTemplate)
        .filter(
            or_(
                ProgramTemplate.owner_user_id == user.id,
                ProgramTemplate.created_by_user_id == user.id,
            )
        )
        .all()
    )
    for template in owned_templates:
        delete_template_cascade(db, template)
        db.flush()

    own_program_ids = [
        item.id for item in db.query(UserProgram.id).filter(UserProgram.user_id == user.id).all()
    ]
    _delete_user_programs(db, own_program_ids)

    db.query(UserProgram).filter(UserProgram.assigned_by_user_id == user.id).update(
        {"assigned_by_user_id": None},
        synchronize_session=False,
    )
    db.query(Exercise).filter(Exercise.created_by_user_id == user.id).update(
        {"created_by_user_id": None, "is_deleted": True},
        synchronize_session=False,
    )

    db.query(CoachClient).filter(
        or_(CoachClient.coach_user_id == user.id, CoachClient.client_user_id == user.id)
    ).delete(synchronize_session=False)

    db.query(CoachClientInvite).filter(
        or_(
            CoachClientInvite.coach_user_id == user.id,
            CoachClientInvite.username == user.username,
        )
    ).delete(synchronize_session=False)

    db.query(Notification).filter(Notification.user_id == user.id).delete(synchronize_session=False)
    db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Payment).filter(Payment.user_id == user.id).delete(synchronize_session=False)
    db.query(Subscription).filter(Subscription.user_id == user.id).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete(synchronize_session=False)
    db.query(UserProfile).filter(UserProfile.user_id == user.id).delete(synchronize_session=False)

    db.delete(user)


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


@router.patch("/users/{user_id}/status")
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
        revoke_all_user_refresh_tokens(db, user.id)

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

    _delete_user_cascade(db, user)
    db.commit()


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
    rows = (
        db.query(Notification, UserProfile.timezone)
        .outerjoin(UserProfile, UserProfile.user_id == Notification.user_id)
        .order_by(Notification.id.desc())
        .limit(200)
        .all()
    )

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
