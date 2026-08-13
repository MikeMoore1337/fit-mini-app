from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.nutrition import NutritionTarget
from fitminiapp_api.models.program import UserProgram, UserWorkout
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.invite import CoachInvitePreviewResponse, CoachInviteTokenRequest
from fitminiapp_api.schemas.user import (
    AccountDeleteRequest,
    HeartRatePreviewRequest,
    HeartRatePreviewResponse,
    HeartRateRangeResponse,
    HeartRateZoneResponse,
    OAuthLinkCreateResponse,
    TelegramLinkCreateResponse,
    TrainerResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
)
from fitminiapp_api.services.account_linking import (
    OAUTH_LINK_PROVIDERS,
    OAuthLinkConflictError,
    OAuthLinkError,
    TelegramLinkConflictError,
    TelegramLinkError,
    create_oauth_link_url,
    create_telegram_link_url,
)
from fitminiapp_api.services.accounts import build_account_export, delete_user_cascade
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.coach_clients import (
    confirm_coach_invite_link,
    get_current_trainer,
    preview_coach_invite_link,
    remove_current_trainer,
)
from fitminiapp_api.services.nutrition import (
    NutritionError,
    build_nutrition_target_response_for_user,
)
from fitminiapp_api.services.profile import (
    ProfileError,
    calculate_profile_heart_rates,
    update_profile,
)
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.security import get_current_user

router = APIRouter()


def _heart_rate_response(heart_rates) -> HeartRatePreviewResponse:
    return HeartRatePreviewResponse(
        estimated_max_heart_rate=heart_rates.maximum,
        heart_rate_reserve=heart_rates.reserve,
        heart_rate_calculation_method=(
            "heart_rate_reserve" if heart_rates.is_personalized else "percent_maximum"
        ),
        heart_rate_zones=[HeartRateZoneResponse(**vars(zone)) for zone in heart_rates.zones],
        recommended_cardio_range=(
            HeartRateRangeResponse(**vars(heart_rates.recommended_cardio_range))
            if heart_rates.recommended_cardio_range
            else None
        ),
    )


def _build_user_response(db: Session, user) -> UserResponse:
    active_program_exists = db.query(UserProgram.id).filter(
        UserProgram.user_id == user.id,
        UserProgram.is_active.is_(True),
    )
    workout_history_exists = (
        db.query(UserWorkout.id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(UserProgram.user_id == user.id, UserWorkout.status == "completed")
    )
    target, has_active_program, has_workout_history = (
        db.query(
            NutritionTarget,
            active_program_exists.exists(),
            workout_history_exists.exists(),
        )
        .select_from(User)
        .outerjoin(NutritionTarget, NutritionTarget.user_id == User.id)
        .filter(User.id == user.id)
        .one()
    )
    kbju = build_nutrition_target_response_for_user(db, target, user)
    trainer = get_current_trainer(db, user)
    heart_rates = calculate_profile_heart_rates(
        user.profile.birth_date if user.profile else None,
        user.profile.resting_heart_rate if user.profile else None,
        user.profile.goal if user.profile else None,
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
        auth_providers=sorted(identity.provider for identity in user.auth_identities),
        profile=UserProfileResponse(
            full_name=user.profile.full_name if user.profile else None,
            birth_date=user.profile.birth_date if user.profile else None,
            goal=user.profile.goal if user.profile else None,
            level=user.profile.level if user.profile else None,
            height_cm=user.profile.height_cm if user.profile else None,
            weight_kg=user.profile.weight_kg if user.profile else None,
            workouts_per_week=user.profile.workouts_per_week if user.profile else None,
            cardio_trainings_per_week=(
                user.profile.cardio_trainings_per_week if user.profile else None
            ),
            resting_heart_rate=user.profile.resting_heart_rate if user.profile else None,
            timezone=user.profile.timezone if user.profile else "Europe/Moscow",
            estimated_max_heart_rate=heart_rates.maximum if heart_rates else None,
            heart_rate_reserve=heart_rates.reserve if heart_rates else None,
            heart_rate_calculation_method=(
                "heart_rate_reserve"
                if heart_rates and heart_rates.is_personalized
                else "percent_maximum"
                if heart_rates
                else None
            ),
            heart_rate_zones=(
                [HeartRateZoneResponse(**vars(zone)) for zone in heart_rates.zones]
                if heart_rates
                else []
            ),
            recommended_cardio_range=(
                HeartRateRangeResponse(**vars(heart_rates.recommended_cardio_range))
                if heart_rates and heart_rates.recommended_cardio_range
                else None
            ),
            kbju=kbju,
        )
        if user.profile or kbju
        else None,
        trainer=TrainerResponse(**trainer) if trainer else None,
    )


@router.get("", response_model=UserResponse)
def read_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_user_response(db, user)


@router.post("/auth/telegram-link", response_model=TelegramLinkCreateResponse)
def create_telegram_link(
    user=Depends(get_current_user), db: Session = Depends(get_db)
) -> TelegramLinkCreateResponse:
    try:
        telegram_url, expires_in_seconds = create_telegram_link_url(
            db,
            user,
            settings.telegram_bot_username,
        )
    except TelegramLinkConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except TelegramLinkError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    db.commit()
    return TelegramLinkCreateResponse(
        telegram_url=telegram_url,
        expires_in_seconds=expires_in_seconds,
    )


@router.post("/auth/oauth-link/{provider}", response_model=OAuthLinkCreateResponse)
def create_oauth_link(
    provider: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OAuthLinkCreateResponse:
    normalized_provider = provider.strip().lower()
    if (
        not settings.enable_web_auth
        or normalized_provider not in OAUTH_LINK_PROVIDERS
        or normalized_provider not in settings.oauth_provider_names
    ):
        raise HTTPException(status_code=404, detail="Провайдер входа не настроен")
    try:
        oauth_url, expires_in_seconds = create_oauth_link_url(db, user, normalized_provider)
    except OAuthLinkConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OAuthLinkError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return OAuthLinkCreateResponse(
        oauth_url=oauth_url,
        expires_in_seconds=expires_in_seconds,
    )


@router.patch("/profile", response_model=UserResponse)
def patch_profile(
    payload: UserProfileUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    try:
        user = update_profile(db, user, payload)
    except (NutritionError, ProfileError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _build_user_response(db, user)


@router.post("/profile/heart-rates/preview", response_model=HeartRatePreviewResponse)
def preview_heart_rates(
    payload: HeartRatePreviewRequest,
    _user=Depends(get_current_user),
) -> HeartRatePreviewResponse:
    try:
        heart_rates = calculate_profile_heart_rates(
            payload.birth_date,
            payload.resting_heart_rate,
            payload.goal,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if heart_rates is None:  # The request schema requires birth_date.
        raise HTTPException(status_code=422, detail="Birth date is required")
    return _heart_rate_response(heart_rates)


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
