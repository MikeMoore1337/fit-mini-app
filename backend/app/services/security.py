from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserProfile


class AuthError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "telegram_user_id": user.telegram_user_id,
        "type": "access",
        "exp": _now() + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "telegram_user_id": user.telegram_user_id,
        "type": "refresh",
        "exp": _now() + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid token") from exc
    if payload.get("type") != expected_type:
        raise AuthError("Invalid token type")
    return payload


def verify_telegram_init_data(init_data: str) -> dict[str, Any]:
    pairs = parse_qsl(init_data, keep_blank_values=True)
    parsed = dict(pairs)
    provided_hash = parsed.pop("hash", None)
    if not provided_hash:
        raise AuthError("Missing Telegram hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, provided_hash):
        raise AuthError("Telegram initData signature mismatch")

    if "user" not in parsed:
        raise AuthError("Missing Telegram user")
    user_payload = json.loads(parsed["user"])
    return user_payload


def get_or_create_user_from_telegram(db: Session, user_payload: dict[str, Any]) -> User:
    telegram_user_id = int(user_payload["id"])
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            username=user_payload.get("username"),
            first_name=user_payload.get("first_name"),
            last_name=user_payload.get("last_name"),
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, full_name=(user_payload.get("first_name") or "Пользователь")))
    else:
        user.username = user_payload.get("username") or user.username
        user.first_name = user_payload.get("first_name") or user.first_name
        user.last_name = user_payload.get("last_name") or user.last_name
    db.commit()
    db.refresh(user)
    return user


def get_or_create_debug_user(db: Session, telegram_user_id: int, full_name: str | None = None, is_coach: bool = False) -> User:
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            username=f"debug_{telegram_user_id}",
            first_name=full_name,
            is_coach=is_coach,
            is_admin=is_coach,
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, full_name=full_name or f"Пользователь {telegram_user_id}"))
        db.commit()
        db.refresh(user)
    return user


def issue_token_pair(user: User) -> dict[str, str]:
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "token_type": "bearer",
    }


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_debug_user: str | None = Header(default=None, alias="X-Debug-User"),
) -> User:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token, expected_type="access")
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    if settings.enable_dev_auth:
        try:
            debug_id = int(x_debug_user or settings.dev_default_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid X-Debug-User header") from exc
        return get_or_create_debug_user(db, debug_id)

    raise HTTPException(status_code=401, detail="Authorization required")


def require_coach(user: User = Depends(get_current_user)) -> User:
    if not (user.is_coach or user.is_admin):
        raise HTTPException(status_code=403, detail="Coach role required")
    return user
