from datetime import UTC, datetime

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User, UserProfile
from app.schemas.auth import RefreshRequest
from app.schemas.telegram_auth import TelegramInitRequest, TokenPairResponse
from app.services.jwt import build_access_token, build_refresh_token, decode_token
from app.services.telegram_auth import validate_init_data
from app.services.token_service import (
    get_refresh_token_by_jti,
    is_refresh_token_valid,
    mark_refresh_token_used,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    save_refresh_token,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

router = APIRouter()


def utcnow() -> datetime:
    return datetime.now(UTC)


def issue_token_pair(db: Session, user: User) -> TokenPairResponse:
    access_token, _, _ = build_access_token(user.id)
    refresh_token, refresh_jti, refresh_expires_at = build_refresh_token(user.id)

    save_refresh_token(
        db,
        user_id=user.id,
        jti=refresh_jti,
        raw_token=refresh_token,
        expires_at=refresh_expires_at,
    )

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/telegram/init", response_model=TokenPairResponse)
@limiter.limit("20/minute")
def telegram_init_auth(
    request: Request,
    payload: TelegramInitRequest,
    db: Session = Depends(get_db),
):
    if not settings.telegram_bot_token or settings.telegram_bot_token == "replace-me":
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN не настроен")

    try:
        parsed = validate_init_data(payload.init_data, settings.telegram_bot_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    tg_user = parsed["user"]
    telegram_user_id = tg_user["id"]
    username = tg_user.get("username")
    first_name = tg_user.get("first_name")
    last_name = tg_user.get("last_name")
    full_name = " ".join(part for part in [first_name, last_name] if part).strip() or username or str(telegram_user_id)

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            is_coach=False,
            is_admin=False,
        )
        db.add(user)
        db.flush()

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
        )
        db.add(profile)
    else:
        if not profile.full_name:
            profile.full_name = full_name

    # если у тебя в модели UserProfile есть username - раскомментируй
    # if hasattr(profile, "username"):
    #     profile.username = username

    db.commit()
    db.refresh(user)

    return issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPairResponse)
@limiter.limit("10/minute")
def refresh_tokens(
    request: Request,
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Невалидный refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Неверный тип токена")

    jti = token_payload.get("jti")
    user_id = int(token_payload.get("sub"))

    row = get_refresh_token_by_jti(db, jti)
    if not row:
        raise HTTPException(status_code=401, detail="Refresh token не найден")

    if row.is_used:
        revoke_all_user_refresh_tokens(db, user_id)
        raise HTTPException(status_code=401, detail="Refresh token уже использован")

    if not is_refresh_token_valid(row, payload.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token недействителен")

    mark_refresh_token_used(db, row)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return issue_token_pair(db, user)


@router.post("/logout")
def logout(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        return {"status": "ok"}

    jti = token_payload.get("jti")
    row = get_refresh_token_by_jti(db, jti)
    if row:
        revoke_refresh_token(db, row)

    return {"status": "ok"}
