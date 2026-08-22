from fastapi import APIRouter, HTTPException

from fitminiapp_api.core.config import settings
from fitminiapp_api.schemas.public import PublicExerciseDetail, PublicExerciseSummary
from fitminiapp_api.services.public_exercises import public_exercise, public_exercises

router = APIRouter()


@router.get("/public/config")
def public_config() -> dict[str, str | bool | list[str]]:
    return {
        "app_env": settings.app_env,
        "enable_dev_auth": settings.enable_dev_auth,
        "enable_web_auth": settings.enable_web_auth,
        "enable_email_auth": settings.enable_email_auth,
        "telegram_bot_username": settings.telegram_bot_username,
        "oauth_providers": settings.oauth_provider_names if settings.enable_web_auth else [],
    }


@router.get("/public/exercises", response_model=list[PublicExerciseSummary])
def get_public_exercises() -> tuple[dict[str, object], ...]:
    return public_exercises()


@router.get("/public/exercises/{slug}", response_model=PublicExerciseDetail)
def get_public_exercise(slug: str) -> dict[str, object]:
    exercise = public_exercise(slug)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Упражнение не опубликовано")
    return exercise
