from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.program import UserProgram, UserWorkout
from fitminiapp_api.schemas.invite import CoachInvitePreviewResponse, CoachInviteTokenRequest
from fitminiapp_api.schemas.user import (
    AccountDeleteRequest,
    TrainerResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
)
from fitminiapp_api.services.accounts import build_account_export, delete_user_cascade
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.coach_clients import (
    confirm_coach_invite_link,
    get_current_trainer,
    preview_coach_invite_link,
    remove_current_trainer,
)
from fitminiapp_api.services.nutrition import NutritionError, get_nutrition_target_for_user
from fitminiapp_api.services.profile import update_profile
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.security import get_current_user

router = APIRouter()


def _build_user_response(db: Session, user) -> UserResponse:
    kbju = get_nutrition_target_for_user(db, user)
    trainer = get_current_trainer(db, user)
    has_active_program = (
        db.query(UserProgram.id)
        .filter(UserProgram.user_id == user.id, UserProgram.is_active.is_(True))
        .first()
        is not None
    )
    has_workout_history = (
        db.query(UserWorkout.id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(UserProgram.user_id == user.id, UserWorkout.status == "completed")
        .first()
        is not None
    )
    return UserResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        photo_url=user.photo_url,
        is_coach=user.is_coach,
        is_admin=user.is_admin,
        has_active_program=has_active_program,
        has_workout_history=has_workout_history,
        profile=UserProfileResponse(
            full_name=user.profile.full_name if user.profile else None,
            goal=user.profile.goal if user.profile else None,
            level=user.profile.level if user.profile else None,
            height_cm=user.profile.height_cm if user.profile else None,
            weight_kg=user.profile.weight_kg if user.profile else None,
            workouts_per_week=user.profile.workouts_per_week if user.profile else None,
            cardio_trainings_per_week=(
                user.profile.cardio_trainings_per_week if user.profile else None
            ),
            timezone=user.profile.timezone if user.profile else "Europe/Moscow",
            kbju=kbju,
        )
        if user.profile or kbju
        else None,
        trainer=TrainerResponse(**trainer) if trainer else None,
    )


@router.get("", response_model=UserResponse)
def read_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_user_response(db, user)


@router.patch("/profile", response_model=UserResponse)
def patch_profile(
    payload: UserProfileUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    try:
        user = update_profile(db, user, payload)
    except NutritionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _build_user_response(db, user)


@router.get("/export")
def export_account_data(
    user=Depends(get_current_user), db: Session = Depends(get_db)
) -> JSONResponse:
    payload = jsonable_encoder(build_account_export(db, user))
    return JSONResponse(
        content=payload,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="fitmini-account-{user.id}.json"',
        },
    )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_account(
    payload: AccountDeleteRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    record_audit_event(
        db,
        action="account.self_deleted",
        resource_type="user",
        actor_user_id=user.id,
        target_user_id=user.id,
        resource_id=user.id,
    )
    db.flush()
    delete_user_cascade(db, user)
    db.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/api/v1/auth",
        secure=settings.app_env == "prod",
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.delete("/trainer", status_code=status.HTTP_204_NO_CONTENT)
def detach_trainer(db: Session = Depends(get_db), user=Depends(get_current_user)):
    remove_current_trainer(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/coach-invites/link/preview",
    response_model=CoachInvitePreviewResponse,
)
def preview_invite_link(
    payload: CoachInviteTokenRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> CoachInvitePreviewResponse:
    try:
        return CoachInvitePreviewResponse(**preview_coach_invite_link(db, user, payload.token))
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/coach-invites/link/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
def confirm_invite_link(
    payload: CoachInviteTokenRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Response:
    try:
        confirm_coach_invite_link(db, user, payload.token)
    except ProgramError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
