from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RefreshRequest, TelegramInitRequest, TokenPairResponse
from app.services.jwt import build_access_token, build_refresh_token, decode_token
from app.services.telegram_auth import (
    get_or_create_user_from_init_data,
    validate_telegram_init_data,
)
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
    init_data = payload.init_data.strip()
    if not init_data:
        raise HTTPException(status_code=400, detail="init_data is required")

    bot_token = settings.telegram_bot_token
    if not bot_token or bot_token == "replace-me":
        raise HTTPException(status_code=500, detail="Telegram bot token is not configured")

    try:
        validated_init_data = validate_telegram_init_data(init_data, bot_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    user = get_or_create_user_from_init_data(db, validated_init_data)
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
