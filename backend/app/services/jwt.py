from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def utcnow() -> datetime:
    return datetime.now(UTC)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def build_access_token(user_id: int) -> tuple[str, str, datetime]:
    now = utcnow()
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = uuid4().hex

    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, jti, expires_at


def build_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    now = utcnow()
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    jti = uuid4().hex

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def extract_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix) :].strip()
