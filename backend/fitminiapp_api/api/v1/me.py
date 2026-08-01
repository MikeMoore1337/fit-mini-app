from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.program import UserProgram, UserWorkout
from fitminiapp_api.schemas.user import (
    TrainerResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
)
from fitminiapp_api.services.client_codes import ensure_client_code, rotate_client_code
from fitminiapp_api.services.coach_clients import (
    claim_coach_invite_link,
    get_current_trainer,
    list_coach_invites_for_client,
    remove_current_trainer,
    respond_to_coach_invite,
)
from fitminiapp_api.services.nutrition import get_nutrition_target_for_user
from fitminiapp_api.services.profile import update_profile
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.security import get_current_user

router = APIRouter()


def _build_user_response(db: Session, user) -> UserResponse:
    if not user.client_code:
        ensure_client_code(db, user)
        db.commit()
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
        client_code=user.client_code,
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
    user = update_profile(db, user, payload)
    return _build_user_response(db, user)


@router.delete("/trainer", status_code=status.HTTP_204_NO_CONTENT)
def detach_trainer(db: Session = Depends(get_db), user=Depends(get_current_user)):
    remove_current_trainer(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/coach-invites")
def coach_invites(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[dict]:
    return list_coach_invites_for_client(db, user)


@router.post("/coach-invites/link/{token}/claim")
def claim_invite_link(
    token: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    try:
        return claim_coach_invite_link(db, user, token)
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/client-code/rotate")
def rotate_my_client_code(
    db: Session = Depends(get_db), user=Depends(get_current_user)
) -> dict[str, str]:
    return {"client_code": rotate_client_code(db, user)}


@router.get("/client-code/qr")
def client_code_qr(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        import qrcode
    except ImportError as exc:  # pragma: no cover - deployment dependency guard
        raise HTTPException(status_code=503, detail="Генератор QR-кода недоступен") from exc

    code = ensure_client_code(db, user)
    db.commit()
    image = qrcode.make(code)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


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
