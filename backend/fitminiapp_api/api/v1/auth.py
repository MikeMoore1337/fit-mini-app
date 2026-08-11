import logging
from datetime import timedelta

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from httpx import HTTPError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.rate_limit import limiter
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.auth_identity import AuthIdentity, LocalCredential
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.auth import (
    AuthTokenRequest,
    DevLoginRequest,
    EmailLoginRequest,
    EmailRegisterRequest,
    EmailRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    RefreshRequest,
    RegistrationResponse,
    TelegramInitRequest,
    TokenPairResponse,
)
from fitminiapp_api.services.auth_email import password_reset_email, verification_email
from fitminiapp_api.services.auth_identities import ensure_auth_identity, ensure_telegram_identity
from fitminiapp_api.services.jwt import (
    AuthError,
    build_access_token,
    build_refresh_token,
    decode_token,
)
from fitminiapp_api.services.oauth_login import (
    configured_oauth_client,
    get_or_create_oauth_user,
)
from fitminiapp_api.services.password_auth import (
    PasswordAuthError,
    authenticate_local_user,
    consume_action_token,
    create_action_token,
    hash_password,
    local_identity_by_email,
    utcnow,
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
logger = logging.getLogger(__name__)


def _require_web_auth() -> None:
    if not settings.enable_web_auth:
        raise HTTPException(status_code=404, detail="Web-авторизация отключена")


def _development_action_token(raw_token: str) -> str | None:
    return raw_token if settings.app_env in {"dev", "test"} else None


def _send_auth_message(sender, email: str, raw_token: str) -> None:
    try:
        delivered = sender(email, raw_token)
    except Exception as exc:
        logger.error("auth_email_delivery_failed", exc_info=exc)
        delivered = False
    if not delivered and settings.app_env == "prod":
        raise HTTPException(
            status_code=503,
            detail="Аккаунт сохранён, но письмо пока не отправлено. Повторите отправку позже.",
        )


def _oauth_callback_url(provider: str) -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/api/v1/auth/oauth/{provider}/callback"


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


@router.get("/oauth/{provider}/start")
@limiter.limit("20/minute")
async def oauth_start(request: Request, provider: str):
    _require_web_auth()
    client = configured_oauth_client(provider)
    if client is None:
        raise HTTPException(status_code=404, detail="Провайдер входа не настроен")
    return await client.authorize_redirect(request, _oauth_callback_url(provider))


async def _oauth_callback_impl(
    request: Request,
    provider: str,
    db: Session,
) -> Response:
    _require_web_auth()
    client = configured_oauth_client(provider)
    if client is None:
        raise HTTPException(status_code=404, detail="Провайдер входа не настроен")
    try:
        token = await client.authorize_access_token(request)
        if provider == "yandex":
            profile_response = await client.get("info?format=json", token=token)
            profile_response.raise_for_status()
            raw_claims = profile_response.json()
        else:
            raw_claims = dict(token.get("userinfo") or {})
        user = get_or_create_oauth_user(db, provider=provider, raw_claims=raw_claims)
    except (HTTPError, OAuthError, ValueError) as exc:
        logger.warning(
            "oauth_login_failed", extra={"provider": provider, "reason": type(exc).__name__}
        )
        return RedirectResponse(url="/app?auth_error=oauth", status_code=303)

    redirect = RedirectResponse(url="/app", status_code=303)
    issue_token_pair(db, user, redirect)
    return redirect


@router.get(
    "/oauth/{provider}/callback",
    operation_id="oauth_callback_get",
)
@limiter.limit("20/minute")
async def oauth_callback_get(
    request: Request,
    provider: str,
    db: Session = Depends(get_db),
) -> Response:
    return await _oauth_callback_impl(request, provider, db)


@router.post(
    "/oauth/{provider}/callback",
    operation_id="oauth_callback_post",
)
@limiter.limit("20/minute")
async def oauth_callback_post(
    request: Request,
    provider: str,
    db: Session = Depends(get_db),
) -> Response:
    return await _oauth_callback_impl(request, provider, db)


@router.post("/email/register", response_model=RegistrationResponse, status_code=201)
@limiter.limit("5/hour")
def email_register(
    request: Request,
    payload: EmailRegisterRequest,
    db: Session = Depends(get_db),
) -> RegistrationResponse:
    _require_web_auth()
    existing_email = local_identity_by_email(db, payload.email)
    existing_username = (
        db.query(LocalCredential)
        .filter(LocalCredential.username_normalized == payload.username)
        .first()
    )
    if existing_email is not None or existing_username is not None:
        raise HTTPException(status_code=409, detail="Email или имя пользователя уже заняты")

    try:
        user = User(
            telegram_user_id=None,
            username=payload.username,
            is_active=True,
        )
        db.add(user)
        db.flush()
        ensure_auth_identity(
            db,
            user,
            provider="password",
            subject=payload.email,
            email=payload.email,
            email_verified=False,
            mark_login=False,
        )
        db.add(
            LocalCredential(
                user_id=user.id,
                username_normalized=payload.username,
                password_hash=hash_password(payload.password),
            )
        )
        db.add(UserProfile(user_id=user.id, full_name=payload.username))
        db.add(NotificationSetting(user_id=user.id))
        raw_token = create_action_token(
            db,
            user.id,
            purpose="verify_email",
            lifetime=timedelta(hours=24),
        )
        db.commit()
    except PasswordAuthError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Email или имя пользователя уже заняты"
        ) from exc

    _send_auth_message(verification_email, payload.email, raw_token)
    return RegistrationResponse(verification_token=_development_action_token(raw_token))


@router.post("/email/verify", response_model=TokenPairResponse)
@limiter.limit("10/hour")
def verify_email(
    request: Request,
    response: Response,
    payload: AuthTokenRequest,
    db: Session = Depends(get_db),
) -> TokenPairResponse:
    _require_web_auth()
    try:
        token = consume_action_token(db, payload.token, purpose="verify_email")
    except PasswordAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    identity = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.user_id == token.user_id, AuthIdentity.provider == "password")
        .first()
    )
    user = db.query(User).filter(User.id == token.user_id).first()
    if identity is None or user is None or not user.is_active:
        db.rollback()
        raise HTTPException(status_code=400, detail="Аккаунт недоступен")
    identity.email_verified = True
    identity.last_login_at = utcnow()
    token_pair = issue_token_pair(db, user, response, commit=False)
    db.commit()
    return token_pair


@router.post("/email/login", response_model=TokenPairResponse)
@limiter.limit("10/minute")
def email_login(
    request: Request,
    response: Response,
    payload: EmailLoginRequest,
    db: Session = Depends(get_db),
) -> TokenPairResponse:
    _require_web_auth()
    try:
        user = authenticate_local_user(db, payload.email, payload.password)
    except PasswordAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return issue_token_pair(db, user, response)


@router.post("/email/verification/resend", response_model=MessageResponse)
@limiter.limit("3/hour")
def resend_verification(
    request: Request,
    payload: EmailRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    _require_web_auth()
    identity = local_identity_by_email(db, payload.email)
    raw_token: str | None = None
    if identity is not None and not identity.email_verified:
        raw_token = create_action_token(
            db,
            identity.user_id,
            purpose="verify_email",
            lifetime=timedelta(hours=24),
        )
        db.commit()
        _send_auth_message(verification_email, payload.email, raw_token)
    return MessageResponse(
        message="Если аккаунт существует, письмо с подтверждением отправлено",
        action_token=_development_action_token(raw_token) if raw_token else None,
    )


@router.post("/password/reset/request", response_model=MessageResponse)
@limiter.limit("3/hour")
def request_password_reset(
    request: Request,
    payload: EmailRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    _require_web_auth()
    identity = local_identity_by_email(db, payload.email)
    raw_token: str | None = None
    if identity is not None and identity.email_verified:
        raw_token = create_action_token(
            db,
            identity.user_id,
            purpose="reset_password",
            lifetime=timedelta(hours=1),
        )
        db.commit()
        _send_auth_message(password_reset_email, payload.email, raw_token)
    return MessageResponse(
        message="Если аккаунт существует, письмо для восстановления отправлено",
        action_token=_development_action_token(raw_token) if raw_token else None,
    )


@router.post("/password/reset/confirm", response_model=MessageResponse)
@limiter.limit("10/hour")
def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    _require_web_auth()
    try:
        token = consume_action_token(db, payload.token, purpose="reset_password")
        new_hash = hash_password(payload.password)
    except PasswordAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    credential = db.query(LocalCredential).filter(LocalCredential.user_id == token.user_id).first()
    if credential is None:
        db.rollback()
        raise HTTPException(status_code=400, detail="Аккаунт недоступен")
    credential.password_hash = new_hash
    credential.password_changed_at = utcnow()
    revoke_all_user_refresh_tokens(db, token.user_id, commit=False)
    db.commit()
    return MessageResponse(message="Пароль обновлён. Теперь можно войти.")


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

    ensure_telegram_identity(db, user)
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
