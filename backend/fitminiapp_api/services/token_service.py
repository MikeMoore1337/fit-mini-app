from __future__ import annotations

import hmac
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from fitminiapp_api.models.token import RefreshToken
from fitminiapp_api.services.jwt import hash_token


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def save_refresh_token(
    db: Session,
    *,
    user_id: int,
    jti: str,
    family_id: str,
    raw_token: str,
    expires_at: datetime,
    commit: bool = True,
) -> RefreshToken:
    row = RefreshToken(
        user_id=user_id,
        jti=jti,
        family_id=family_id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def get_refresh_token_by_jti(db: Session, jti: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()


def is_refresh_token_family_active(db: Session, user_id: int, family_id: str) -> bool:
    now = utcnow()
    return (
        db.query(RefreshToken.id)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.family_id == family_id,
            RefreshToken.is_revoked.is_(False),
            RefreshToken.is_used.is_(False),
            RefreshToken.expires_at >= now,
        )
        .first()
        is not None
    )


def revoke_refresh_token_family(
    db: Session,
    user_id: int,
    family_id: str,
    *,
    commit: bool = True,
) -> None:
    now = utcnow()
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.family_id == family_id,
        RefreshToken.is_revoked.is_(False),
    ).update(
        {
            RefreshToken.is_revoked: True,
            RefreshToken.revoked_at: now,
        },
        synchronize_session=False,
    )
    if commit:
        db.commit()
    else:
        db.flush()


def consume_refresh_token(db: Session, row: RefreshToken, *, commit: bool = True) -> bool:
    now = utcnow()
    updated = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == row.id,
            RefreshToken.is_used.is_(False),
            RefreshToken.is_revoked.is_(False),
            RefreshToken.expires_at >= now,
        )
        .update(
            {
                RefreshToken.is_used: True,
                RefreshToken.used_at: now,
            },
            synchronize_session=False,
        )
    )
    if commit:
        db.commit()
    return updated == 1


def is_refresh_token_valid(row: RefreshToken, raw_token: str) -> bool:
    if row.is_revoked or row.is_used:
        return False
    if row.expires_at < utcnow():
        return False
    return hmac.compare_digest(row.token_hash, hash_token(raw_token))


def revoke_all_user_refresh_tokens(
    db: Session,
    user_id: int,
    *,
    commit: bool = True,
) -> None:
    rows = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        )
        .all()
    )
    now = utcnow()
    for row in rows:
        row.is_revoked = True
        row.revoked_at = now
        db.add(row)
    if commit:
        db.commit()
    else:
        db.flush()
