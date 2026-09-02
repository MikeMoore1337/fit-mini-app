from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal
from urllib.parse import quote

from sqlalchemy.orm import Session

from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.user import User
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.auth_identities import ensure_auth_identity, ensure_telegram_identity
from fitminiapp_api.services.oauth_login import normalize_oauth_claims
from fitminiapp_api.services.password_auth import (
    consume_action_token,
    consume_action_token_hash,
    create_action_token,
)
from fitminiapp_api.services.root_admin import is_root_telegram_user_id
from fitminiapp_api.services.telegram_auth import normalize_telegram_username
from fitminiapp_api.services.token_service import is_refresh_token_family_active

TELEGRAM_LINK_PURPOSE = "link_telegram"
TELEGRAM_LINK_LIFETIME = timedelta(minutes=10)
OAUTH_LINK_LIFETIME = timedelta(minutes=10)
OAUTH_LINK_PROVIDERS = frozenset({"google", "yandex", "vk", "apple"})


class TelegramLinkError(RuntimeError):
    pass


class TelegramLinkConflictError(TelegramLinkError):
    pass


class OAuthLinkError(RuntimeError):
    pass


class OAuthLinkConflictError(OAuthLinkError):
    pass


@dataclass(frozen=True)
class TelegramLinkResult:
    user_id: int
    status: Literal["linked", "already_linked"]


def oauth_link_purpose(provider: str) -> str:
    normalized_provider = provider.strip().lower()
    if normalized_provider not in OAUTH_LINK_PROVIDERS:
        raise OAuthLinkError("Этот способ входа нельзя привязать")
    return f"link_oauth_{normalized_provider}"


def create_oauth_link_url(
    db: Session,
    user: User,
    provider: str,
    *,
    session_family_id: str,
) -> tuple[str, int]:
    normalized_provider = provider.strip().lower()
    purpose = oauth_link_purpose(normalized_provider)
    existing_provider = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.user_id == user.id, AuthIdentity.provider == normalized_provider)
        .first()
    )
    if existing_provider is not None:
        raise OAuthLinkConflictError("Этот способ входа уже привязан")

    raw_token = create_action_token(
        db,
        user.id,
        purpose=purpose,
        lifetime=OAUTH_LINK_LIFETIME,
        session_family_id=session_family_id,
    )
    encoded_token = quote(raw_token, safe="_-~")
    return (
        f"/api/v1/auth/oauth/{normalized_provider}/link/start?token={encoded_token}",
        int(OAUTH_LINK_LIFETIME.total_seconds()),
    )


def link_oauth_account(
    db: Session,
    *,
    raw_token: str | None = None,
    action_token_hash: str | None = None,
    provider: str,
    raw_claims: dict[str, object],
    expected_session_family_id: str | None = None,
) -> User:
    normalized_provider = provider.strip().lower()
    if action_token_hash:
        token = consume_action_token_hash(
            db,
            action_token_hash,
            purpose=oauth_link_purpose(normalized_provider),
        )
    elif raw_token:
        token = consume_action_token(
            db,
            raw_token,
            purpose=oauth_link_purpose(normalized_provider),
        )
    else:
        raise OAuthLinkError("Ссылка привязки недействительна")
    if expected_session_family_id is not None:
        family_id = expected_session_family_id
        if token.session_family_id != family_id:
            raise OAuthLinkError("Сессия привязки недействительна")
        if not is_refresh_token_family_active(db, token.user_id, family_id):
            raise OAuthLinkError("Сессия привязки недействительна")
    target = db.query(User).filter(User.id == token.user_id).with_for_update().first()
    if target is None or not target.is_active:
        raise OAuthLinkError("Аккаунт для привязки недоступен")

    claims = normalize_oauth_claims(normalized_provider, raw_claims)
    subject = claims["subject"]
    if not subject:
        raise OAuthLinkError("Провайдер не вернул устойчивый идентификатор")

    identity = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.provider == normalized_provider,
            AuthIdentity.subject == subject,
        )
        .with_for_update()
        .first()
    )
    target_provider = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.user_id == target.id,
            AuthIdentity.provider == normalized_provider,
        )
        .with_for_update()
        .first()
    )
    if (identity is not None and identity.user_id != target.id) or (
        target_provider is not None and target_provider.subject != subject
    ):
        record_audit_event(
            db,
            action="account.oauth_link_conflict",
            resource_type="user",
            target_user_id=target.id,
            resource_id=target.id,
            details={"provider": normalized_provider},
        )
        raise OAuthLinkConflictError("Этот способ входа уже связан с другим аккаунтом")

    ensure_auth_identity(
        db,
        target,
        provider=normalized_provider,
        subject=subject,
        email=claims["email"],
        email_verified=claims["email_verified"],
    )
    record_audit_event(
        db,
        action="account.oauth_linked",
        resource_type="user",
        actor_user_id=target.id,
        target_user_id=target.id,
        resource_id=target.id,
        details={"provider": normalized_provider},
    )
    return target


def create_telegram_link_url(
    db: Session,
    user: User,
    bot_username: str,
    *,
    session_family_id: str,
) -> tuple[str, int]:
    if user.telegram_user_id is not None:
        raise TelegramLinkConflictError("Telegram уже привязан к этому аккаунту")
    normalized_bot_username = bot_username.strip().lstrip("@")
    if not normalized_bot_username:
        raise TelegramLinkError("Telegram-бот не настроен")

    raw_token = create_action_token(
        db,
        user.id,
        purpose=TELEGRAM_LINK_PURPOSE,
        lifetime=TELEGRAM_LINK_LIFETIME,
        session_family_id=session_family_id,
    )
    start_payload = quote(f"link_{raw_token}", safe="_-~")
    return (
        f"https://t.me/{normalized_bot_username}?start={start_payload}",
        int(TELEGRAM_LINK_LIFETIME.total_seconds()),
    )


def link_telegram_account(
    db: Session,
    *,
    raw_token: str,
    telegram_user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> TelegramLinkResult:
    token = consume_action_token(db, raw_token, purpose=TELEGRAM_LINK_PURPOSE)
    target = db.query(User).filter(User.id == token.user_id).with_for_update().first()
    if target is None or not target.is_active:
        raise TelegramLinkError("Аккаунт для привязки недоступен")
    if token.session_family_id is None or not is_refresh_token_family_active(
        db, target.id, token.session_family_id
    ):
        raise TelegramLinkError("Сессия привязки недействительна")

    if is_root_telegram_user_id(telegram_user_id):
        record_audit_event(
            db,
            action="account.root_telegram_link_rejected",
            resource_type="user",
            target_user_id=target.id,
            resource_id=target.id,
        )
        raise TelegramLinkConflictError("Root Telegram нельзя привязать к другому аккаунту")

    telegram_subject = str(telegram_user_id)
    existing_identity = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.provider == "telegram",
            AuthIdentity.subject == telegram_subject,
        )
        .with_for_update()
        .first()
    )
    existing_user = (
        db.query(User).filter(User.telegram_user_id == telegram_user_id).with_for_update().first()
    )

    conflicting_user_id = None
    if existing_identity is not None and existing_identity.user_id != target.id:
        conflicting_user_id = existing_identity.user_id
    elif existing_user is not None and existing_user.id != target.id:
        conflicting_user_id = existing_user.id
    elif target.telegram_user_id not in (None, telegram_user_id):
        conflicting_user_id = target.id

    if conflicting_user_id is not None:
        record_audit_event(
            db,
            action="account.telegram_link_conflict",
            resource_type="user",
            target_user_id=target.id,
            resource_id=target.id,
        )
        raise TelegramLinkConflictError("Этот Telegram уже связан с другим аккаунтом")

    normalized_username = normalize_telegram_username(username)
    target.telegram_user_id = telegram_user_id
    target.username = normalized_username
    target.first_name = first_name
    target.last_name = last_name
    ensure_telegram_identity(db, target)
    record_audit_event(
        db,
        action="account.telegram_linked",
        resource_type="user",
        actor_user_id=target.id,
        target_user_id=target.id,
        resource_id=target.id,
    )
    return TelegramLinkResult(
        user_id=target.id,
        status="already_linked" if existing_user is not None else "linked",
    )
