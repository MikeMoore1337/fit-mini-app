from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.rate_limit import limiter
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.auth import (
    DevLoginRequest,
    RefreshRequest,
    TelegramInitRequest,
    TokenPairResponse,
)
from fitminiapp_api.services.client_codes import ensure_client_code
from fitminiapp_api.services.jwt import (
    AuthError,
    build_access_token,
    build_refresh_token,
    decode_token,
)
from fitminiapp_api.services.telegram_auth import (
    get_or_create_user_from_init_data,
    normalize_telegram_username,
    validate_telegram_init_data,
)
from fitminiapp_api.services.token_service import (
    consume_refresh_token,
    get_refresh_token_by_jti,
    is_refresh_token_valid,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    save_refresh_token,
)

router = APIRouter()


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
        secure=settings.app_env == "prod",
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/api/v1/auth",
        secure=settings.app_env == "prod",
        httponly=True,
        samesite="strict",
    )


def issue_token_pair(
    db: Session,
    user: User,
    response: Response,
    *,
    commit: bool = True,
) -> TokenPairResponse:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")

    access_token, _, _ = build_access_token(user.id)
    refresh_token, refresh_jti, refresh_expires_at = build_refresh_token(user.id)

    save_refresh_token(
        db,
        user_id=user.id,
        jti=refresh_jti,
        raw_token=refresh_token,
        expires_at=refresh_expires_at,
        commit=commit,
    )
    _set_refresh_cookie(response, refresh_token)

    return TokenPairResponse(
        access_token=access_token,
    )


@router.post("/telegram/init", response_model=TokenPairResponse)
@limiter.limit("20/minute")
def telegram_init_auth(
    request: Request,
    response: Response,
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
    return issue_token_pair(db, user, response)


@router.post("/dev-login", response_model=TokenPairResponse)
@limiter.limit("30/minute")
def dev_login(
    request: Request,
    response: Response,
    payload: DevLoginRequest,
    db: Session = Depends(get_db),
):
    if not settings.enable_dev_auth:
        raise HTTPException(status_code=403, detail="Dev-вход отключён")

    username = normalize_telegram_username(payload.username) if payload.username else None
    user = db.query(User).filter(User.telegram_user_id == payload.telegram_user_id).first()
    if not user:
        user = User(
            telegram_user_id=payload.telegram_user_id,
            username=username
            if payload.username is not None
            else f"dev_{payload.telegram_user_id}",
            is_coach=payload.is_coach,
            is_admin=payload.is_admin,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(
            UserProfile(
                user_id=user.id,
                full_name=payload.full_name,
            )
        )
        db.add(NotificationSetting(user_id=user.id))
        ensure_client_code(db, user)
    else:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Пользователь заблокирован")

        user.is_coach = payload.is_coach
        user.is_admin = payload.is_admin
        if payload.username is not None:
            user.username = username
        if payload.full_name is not None:
            profile = user.profile
            if profile:
                profile.full_name = payload.full_name
            else:
                db.add(UserProfile(user_id=user.id, full_name=payload.full_name))
        ensure_client_code(db, user)

    db.commit()
    db.refresh(user)
    return issue_token_pair(db, user, response)


@router.post("/refresh", response_model=TokenPairResponse)
@limiter.limit("10/minute")
def refresh_tokens(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    raw_refresh_token = (
        payload.refresh_token
        if payload is not None and payload.refresh_token
        else request.cookies.get(settings.refresh_cookie_name, "")
    )
    if not raw_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token отсутствует")
    try:
        token_payload = decode_token(raw_refresh_token, expected_type="refresh")
    except AuthError:
        raise HTTPException(status_code=401, detail="Невалидный refresh token")

    jti = token_payload.get("jti")
    sub = token_payload.get("sub")
    if not jti or not sub:
        raise HTTPException(status_code=401, detail="Невалидный refresh token")

    try:
        user_id = int(sub)
    except TypeError, ValueError:
        raise HTTPException(status_code=401, detail="Невалидный refresh token")

    row = get_refresh_token_by_jti(db, jti)
    if not row:
        raise HTTPException(status_code=401, detail="Refresh token не найден")

    if row.is_used:
        revoke_all_user_refresh_tokens(db, user_id)
        raise HTTPException(status_code=401, detail="Refresh token уже использован")

    if not is_refresh_token_valid(row, raw_refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token недействителен")

    if not consume_refresh_token(db, row, commit=False):
        db.rollback()
        revoke_all_user_refresh_tokens(db, user_id)
        raise HTTPException(status_code=401, detail="Refresh token уже использован")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    token_pair = issue_token_pair(db, user, response, commit=False)
    db.commit()
    return token_pair


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    raw_refresh_token = (
        payload.refresh_token
        if payload is not None and payload.refresh_token
        else request.cookies.get(settings.refresh_cookie_name, "")
    )
    _clear_refresh_cookie(response)
    if not raw_refresh_token:
        return {"status": "ok"}
    try:
        token_payload = decode_token(raw_refresh_token, expected_type="refresh")
    except AuthError:
        return {"status": "ok"}

    jti = token_payload.get("jti")
    row = get_refresh_token_by_jti(db, jti) if isinstance(jti, str) else None
    if row:
        revoke_refresh_token(db, row)

    return {"status": "ok"}
