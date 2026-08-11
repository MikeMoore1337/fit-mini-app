from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal
from urllib.parse import quote

from sqlalchemy.orm import Session

from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.user import User
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.auth_identities import ensure_telegram_identity
from fitminiapp_api.services.password_auth import consume_action_token, create_action_token
from fitminiapp_api.services.telegram_auth import normalize_telegram_username

TELEGRAM_LINK_PURPOSE = "link_telegram"
TELEGRAM_LINK_LIFETIME = timedelta(minutes=10)


class TelegramLinkError(RuntimeError):
    pass


class TelegramLinkConflictError(TelegramLinkError):
    pass


@dataclass(frozen=True)
class TelegramLinkResult:
    user_id: int
    status: Literal["linked", "already_linked"]


def create_telegram_link_url(db: Session, user: User, bot_username: str) -> tuple[str, int]:
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
