from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from fitminiapp_api.models.auth_identity import AuthActionToken, AuthIdentity, LocalCredential
from fitminiapp_api.models.user import User

password_hash = PasswordHash.recommended()
_DUMMY_HASH = password_hash.hash("dummy-password-used-only-for-timing")
_COMMON_PASSWORDS = {
    "123456789012",
    "password1234",
    "qwerty123456",
    "yourfitnesscoach",
}


class PasswordAuthError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def validate_password_strength(password: str) -> None:
    if len(password) < 12:
        raise PasswordAuthError("Пароль должен содержать не менее 12 символов")
    if len(password) > 128:
        raise PasswordAuthError("Пароль слишком длинный")
    if password.casefold() in _COMMON_PASSWORDS:
        raise PasswordAuthError("Выберите менее распространённый пароль")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    return password_hash.verify(password, encoded_hash or _DUMMY_HASH)


def local_identity_by_email(db: Session, email: str) -> AuthIdentity | None:
    return (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == "password", AuthIdentity.subject == email)
        .first()
    )


def authenticate_local_user(db: Session, email: str, password: str) -> User:
    identity = local_identity_by_email(db, email)
    credential = (
        db.query(LocalCredential).filter(LocalCredential.user_id == identity.user_id).first()
        if identity is not None
        else None
    )
    if not verify_password(password, credential.password_hash if credential else None):
        raise PasswordAuthError("Неверный email или пароль")
    if identity is None or credential is None:
        raise PasswordAuthError("Неверный email или пароль")
    if not identity.email_verified:
        raise PasswordAuthError("Подтвердите email перед входом")
    user = db.query(User).filter(User.id == identity.user_id).first()
    if user is None or not user.is_active:
        raise PasswordAuthError("Аккаунт недоступен")
    identity.last_login_at = utcnow()
    return user


def create_action_token(
    db: Session,
    user_id: int,
    *,
    purpose: str,
    lifetime: timedelta,
) -> str:
    now = utcnow()
    db.query(AuthActionToken).filter(
        AuthActionToken.user_id == user_id,
        AuthActionToken.purpose == purpose,
        AuthActionToken.consumed_at.is_(None),
    ).update({AuthActionToken.consumed_at: now}, synchronize_session=False)
    raw_token = secrets.token_urlsafe(32)
    db.add(
        AuthActionToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=now + lifetime,
        )
    )
    return raw_token


def consume_action_token(db: Session, raw_token: str, *, purpose: str) -> AuthActionToken:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    row = (
        db.query(AuthActionToken)
        .filter(
            AuthActionToken.token_hash == token_hash,
            AuthActionToken.purpose == purpose,
        )
        .with_for_update()
        .first()
    )
    now = utcnow()
    if row is None or row.consumed_at is not None or row.expires_at < now:
        raise PasswordAuthError("Ссылка недействительна или срок её действия истёк")
    row.consumed_at = now
    return row


def validate_action_token(db: Session, raw_token: str, *, purpose: str) -> AuthActionToken:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    row = (
        db.query(AuthActionToken)
        .filter(
            AuthActionToken.token_hash == token_hash,
            AuthActionToken.purpose == purpose,
        )
        .first()
    )
    now = utcnow()
    if row is None or row.consumed_at is not None or row.expires_at < now:
        raise PasswordAuthError("Ссылка недействительна или срок её действия истёк")
    return row
