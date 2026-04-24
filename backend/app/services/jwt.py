from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt

from app.core.config import settings

ALGORITHM = "HS256"


class AuthError(Exception):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def build_access_token(user_id: int) -> tuple[str, str, datetime]:
    now_aware = datetime.now(UTC)
    expires_at_aware = now_aware + timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = expires_at_aware.replace(tzinfo=None)
    jti = uuid4().hex

    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": jti,
        "iat": int(now_aware.timestamp()),
        "exp": int(expires_at_aware.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, jti, expires_at


def build_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    now_aware = datetime.now(UTC)
    expires_at_aware = now_aware + timedelta(days=settings.refresh_token_expire_days)
    expires_at = expires_at_aware.replace(tzinfo=None)
    jti = uuid4().hex

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": int(now_aware.timestamp()),
        "exp": int(expires_at_aware.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid token") from exc

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise AuthError("Invalid token type")

    return payload


def extract_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix) :].strip()
