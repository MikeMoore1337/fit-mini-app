from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.models.user import CoachRoleApplication, User
from fitminiapp_api.services.audit import record_audit_event


def submit_coach_application(
    db: Session, user: User, *, source: str = "web"
) -> CoachRoleApplication:
    if user.is_coach or user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Кабинет тренера уже подключён",
        )
    pending = (
        db.query(CoachRoleApplication)
        .filter(
            CoachRoleApplication.user_id == user.id,
            CoachRoleApplication.status == "pending",
        )
        .first()
    )
    if pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Заявка тренера уже находится на рассмотрении",
        )

    application = CoachRoleApplication(user_id=user.id, source=source)
    db.add(application)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Заявка тренера уже находится на рассмотрении",
        ) from exc
    record_audit_event(
        db,
        action="coach_application.submitted",
        resource_type="coach_role_application",
        actor_user_id=user.id,
        target_user_id=user.id,
        resource_id=application.id,
        details={"source": application.source},
    )
    db.commit()
    db.refresh(application)
    return application


def cancel_coach_application(db: Session, user: User) -> None:
    application = (
        db.query(CoachRoleApplication)
        .filter(
            CoachRoleApplication.user_id == user.id,
            CoachRoleApplication.status == "pending",
        )
        .order_by(CoachRoleApplication.id.desc())
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активная заявка тренера не найдена",
        )
    application.status = "cancelled"
    application.reviewed_at = now_msk_naive()
    record_audit_event(
        db,
        action="coach_application.cancelled",
        resource_type="coach_role_application",
        actor_user_id=user.id,
        target_user_id=user.id,
        resource_id=application.id,
    )
    db.commit()


def review_coach_application(
    db: Session,
    application: CoachRoleApplication,
    reviewer: User,
    decision: str,
) -> CoachRoleApplication:
    if application.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Заявка уже рассмотрена",
        )
    applicant = db.query(User).filter(User.id == application.user_id).first()
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if decision == "approved" and not applicant.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нельзя одобрить заявку заблокированного пользователя",
        )

    application.status = decision
    application.reviewed_at = now_msk_naive()
    application.reviewed_by_user_id = reviewer.id
    if decision == "approved":
        applicant.is_coach = True

    record_audit_event(
        db,
        action=f"coach_application.{decision}",
        resource_type="coach_role_application",
        actor_user_id=reviewer.id,
        target_user_id=applicant.id,
        resource_id=application.id,
    )
    db.commit()
    db.refresh(application)
    return application


def approve_pending_coach_applications(db: Session, user: User, reviewer: User) -> None:
    applications = (
        db.query(CoachRoleApplication)
        .filter(
            CoachRoleApplication.user_id == user.id,
            CoachRoleApplication.status == "pending",
        )
        .all()
    )
    for application in applications:
        application.status = "approved"
        application.reviewed_at = now_msk_naive()
        application.reviewed_by_user_id = reviewer.id
        record_audit_event(
            db,
            action="coach_application.approved",
            resource_type="coach_role_application",
            actor_user_id=reviewer.id,
            target_user_id=user.id,
            resource_id=application.id,
            details={"via": "direct_role_change"},
        )
