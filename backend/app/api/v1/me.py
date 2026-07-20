from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import TrainerResponse, UserProfileResponse, UserProfileUpdate, UserResponse
from app.services.nutrition import get_nutrition_target_for_user
from app.services.profile import update_profile
from app.services.programs import (
    ProgramError,
    get_current_trainer,
    list_coach_invites_for_client,
    remove_current_trainer,
    respond_to_coach_invite,
)
from app.services.security import get_current_user

router = APIRouter()


def _build_user_response(db: Session, user) -> UserResponse:
    kbju = get_nutrition_target_for_user(db, user)
    trainer = get_current_trainer(db, user)
    return UserResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_coach=user.is_coach,
        is_admin=user.is_admin,
        profile=UserProfileResponse(
            full_name=user.profile.full_name if user.profile else None,
            goal=user.profile.goal if user.profile else None,
            level=user.profile.level if user.profile else None,
            height_cm=user.profile.height_cm if user.profile else None,
            weight_kg=user.profile.weight_kg if user.profile else None,
            workouts_per_week=user.profile.workouts_per_week if user.profile else None,
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
    user = update_profile(db, user, payload)
    return _build_user_response(db, user)


@router.delete("/trainer", status_code=status.HTTP_204_NO_CONTENT)
def detach_trainer(db: Session = Depends(get_db), user=Depends(get_current_user)):
    remove_current_trainer(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/coach-invites")
def coach_invites(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[dict]:
    return list_coach_invites_for_client(db, user)


@router.post("/coach-invites/{invite_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_coach_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Response:
    try:
        respond_to_coach_invite(db, user, invite_id, accept=True)
    except ProgramError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/coach-invites/{invite_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_coach_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Response:
    try:
        respond_to_coach_invite(db, user, invite_id, accept=False)
    except ProgramError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
