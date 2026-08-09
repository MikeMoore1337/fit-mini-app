import hmac

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.timezone import is_valid_timezone
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.bot import BotTimezoneUpdateRequest, BotTimezoneUpdateResponse
from fitminiapp_api.services.telegram_auth import (
    get_or_insert_telegram_user,
    normalize_telegram_username,
)

router = APIRouter()


def _check_bot_token(x_bot_token: str | None) -> None:
    expected = settings.bot_internal_token
    if not expected:
        raise HTTPException(status_code=503, detail="Bot internal token is not configured")
    if not x_bot_token or not hmac.compare_digest(x_bot_token, expected):
        raise HTTPException(status_code=403, detail="Forbidden")


def _get_or_create_user(db: Session, payload: BotTimezoneUpdateRequest) -> User:
    username = normalize_telegram_username(payload.username)
    user = get_or_insert_telegram_user(
        db,
        telegram_user_id=payload.telegram_user_id,
        username=username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        photo_url=None,
    )
    user = db.query(User).filter(User.id == user.id).with_for_update().one()
    if payload.username is not None:
        user.username = username
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name

    return user


def _ensure_profile_and_settings(db: Session, user: User) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        full_name = (
            " ".join(part for part in [user.first_name, user.last_name] if part).strip()
            or user.username
            or f"User {user.telegram_user_id}"
        )
        profile = UserProfile(user_id=user.id, full_name=full_name)
        db.add(profile)
        db.flush()

    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    if not setting:
        db.add(NotificationSetting(user_id=user.id))

    return profile


@router.post("/timezone", response_model=BotTimezoneUpdateResponse)
def update_timezone_from_bot(
    payload: BotTimezoneUpdateRequest,
    x_bot_token: str | None = Header(default=None),
):
    _check_bot_token(x_bot_token)
    if not is_valid_timezone(payload.timezone):
        raise HTTPException(status_code=400, detail="Unsupported timezone")

    with get_session_context() as db:
        user = _get_or_create_user(db, payload)
        profile = _ensure_profile_and_settings(db, user)
        profile.timezone = payload.timezone
        db.flush()

        return BotTimezoneUpdateResponse(
            telegram_user_id=user.telegram_user_id,
            timezone=profile.timezone,
        )
