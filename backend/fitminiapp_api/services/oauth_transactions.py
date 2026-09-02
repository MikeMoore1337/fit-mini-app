from __future__ import annotations

import hashlib
import re
import secrets
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.oauth_transaction import OAuthTransaction
from fitminiapp_api.services.auth_redirects import OAUTH_PROVIDERS, safe_auth_next_path

OAUTH_BROWSER_MARKER_KEY = "oauth_browser_marker"
LEGACY_OAUTH_SESSION_KEYS = frozenset(
    {
        "oauth_next",
        "oauth_link_token",
        "oauth_link_provider",
        "oauth_link_family",
        "vk_oauth",
    }
)
OAUTH_STATE_RE = re.compile(r"[A-Za-z0-9._~-]{8,256}")
BROWSER_MARKER_RE = re.compile(r"[A-Za-z0-9_-]{32,128}")


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def transaction_hash_prefix(state: str) -> str:
    return hash_secret(state)[:12]


def new_browser_marker() -> str:
    return secrets.token_urlsafe(32)


def is_valid_browser_marker(value: object) -> bool:
    return isinstance(value, str) and BROWSER_MARKER_RE.fullmatch(value) is not None


def is_valid_oauth_state(value: object) -> bool:
    return isinstance(value, str) and OAUTH_STATE_RE.fullmatch(value) is not None


def scrub_legacy_oauth_session(session: MutableMapping[str, Any]) -> bool:
    removed = False
    for key in list(session.keys()):
        if key.startswith("_state_") or key in LEGACY_OAUTH_SESSION_KEYS:
            session.pop(key, None)
            removed = True
    return removed


def prepare_oauth_session(session: MutableMapping[str, Any]) -> str:
    scrub_legacy_oauth_session(session)
    marker: object = session.get(OAUTH_BROWSER_MARKER_KEY)
    if isinstance(marker, str) and is_valid_browser_marker(marker):
        return marker
    marker = new_browser_marker()
    session[OAUTH_BROWSER_MARKER_KEY] = marker
    return marker


def browser_marker_from_session(session: Mapping[str, Any]) -> str | None:
    marker: object = session.get(OAUTH_BROWSER_MARKER_KEY)
    return marker if isinstance(marker, str) and is_valid_browser_marker(marker) else None


def _transaction_expired(row: OAuthTransaction, now: datetime) -> bool:
    return row.expires_at <= now


@dataclass(frozen=True)
class OAuthTransactionClaim:
    transaction: OAuthTransaction | None
    reason: str | None


def _prune_terminal_transactions(db: Session, now: datetime) -> None:
    cutoff = now - timedelta(seconds=settings.oauth_transaction_ttl_seconds)
    db.query(OAuthTransaction).filter(
        OAuthTransaction.status == "pending",
        OAuthTransaction.expires_at <= now,
    ).update(
        {
            OAuthTransaction.status: "expired",
            OAuthTransaction.failure_reason: "expired_state",
            OAuthTransaction.completed_at: now,
        },
        synchronize_session=False,
    )
    db.query(OAuthTransaction).filter(
        OAuthTransaction.status == "processing",
        OAuthTransaction.claimed_at < cutoff,
    ).update(
        {
            OAuthTransaction.status: "failed",
            OAuthTransaction.failure_reason: "processing_timeout",
            OAuthTransaction.completed_at: now,
        },
        synchronize_session=False,
    )
    db.query(OAuthTransaction).filter(
        OAuthTransaction.status != "pending",
        or_(
            OAuthTransaction.completed_at < cutoff,
            OAuthTransaction.expires_at < cutoff,
        ),
    ).delete(synchronize_session=False)


def create_oauth_transaction(
    db: Session,
    *,
    browser_marker: str,
    provider: str,
    purpose: str,
    authorization_data: Mapping[str, Any],
    next_path: str | None = None,
    link_action_token_hash: str | None = None,
    link_user_id: int | None = None,
    session_family_id: str | None = None,
    now: datetime | None = None,
) -> OAuthTransaction:
    current = now or utcnow()
    state = authorization_data.get("state")
    redirect_uri = authorization_data.get("redirect_uri")
    if not is_valid_browser_marker(browser_marker):
        raise ValueError("OAuth browser marker is invalid")
    if provider not in OAUTH_PROVIDERS:
        raise ValueError("Unsupported OAuth provider")
    if purpose not in {"login", "link"}:
        raise ValueError("Unsupported OAuth purpose")
    if not is_valid_oauth_state(state) or not isinstance(redirect_uri, str) or not redirect_uri:
        raise ValueError("OAuth authorization data is invalid")
    safe_path = safe_auth_next_path(next_path)
    if next_path is not None and safe_path is None:
        raise ValueError("OAuth next path is invalid")

    _prune_terminal_transactions(db, current)
    row = OAuthTransaction(
        transaction_id=secrets.token_urlsafe(32),
        browser_marker_hash=hash_secret(browser_marker),
        provider=provider,
        purpose=purpose,
        state=state,
        redirect_uri=redirect_uri,
        next_path=safe_path,
        code_verifier=(
            authorization_data.get("code_verifier")
            if isinstance(authorization_data.get("code_verifier"), str)
            else None
        ),
        nonce=(
            authorization_data.get("nonce")
            if isinstance(authorization_data.get("nonce"), str)
            else None
        ),
        link_action_token_hash=link_action_token_hash,
        link_user_id=link_user_id,
        session_family_id=session_family_id,
        expires_at=current + timedelta(seconds=settings.oauth_transaction_ttl_seconds),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def claim_oauth_transaction(
    db: Session,
    *,
    browser_marker: str | None,
    provider: str,
    state: str | None,
    now: datetime | None = None,
) -> OAuthTransactionClaim:
    current = now or utcnow()
    if not browser_marker or not is_valid_browser_marker(browser_marker):
        return OAuthTransactionClaim(None, "invalid_state")
    if not is_valid_oauth_state(state):
        return OAuthTransactionClaim(None, "invalid_state")

    row = (
        db.query(OAuthTransaction)
        .filter(
            OAuthTransaction.browser_marker_hash == hash_secret(browser_marker),
            OAuthTransaction.provider == provider,
            OAuthTransaction.state == state,
        )
        .with_for_update()
        .first()
    )
    if row is None:
        return OAuthTransactionClaim(None, "invalid_state")
    if row.status != "pending":
        return OAuthTransactionClaim(
            row,
            "expired_state" if row.status == "expired" else "repeated_state",
        )
    if _transaction_expired(row, current):
        row.status = "expired"
        row.failure_reason = "expired_state"
        row.completed_at = current
        db.commit()
        return OAuthTransactionClaim(row, "expired_state")

    row.status = "processing"
    row.claimed_at = current
    db.commit()
    db.refresh(row)
    return OAuthTransactionClaim(row, None)


def has_pending_oauth_transactions(db: Session, browser_marker: str | None) -> bool:
    if not browser_marker or not is_valid_browser_marker(browser_marker):
        return False
    return (
        db.query(OAuthTransaction.transaction_id)
        .filter(
            OAuthTransaction.browser_marker_hash == hash_secret(browser_marker),
            OAuthTransaction.status == "pending",
            OAuthTransaction.expires_at > utcnow(),
        )
        .first()
        is not None
    )


def finish_oauth_transaction(
    db: Session,
    row: OAuthTransaction,
    *,
    failure_reason: str | None = None,
    commit: bool = True,
) -> None:
    if row.status != "processing":
        return
    row.status = "failed" if failure_reason else "completed"
    row.failure_reason = failure_reason
    row.completed_at = utcnow()
    if commit:
        db.commit()
    else:
        db.flush()


def authlib_state_data(row: OAuthTransaction) -> dict[str, str]:
    data = {"redirect_uri": row.redirect_uri}
    if row.code_verifier:
        data["code_verifier"] = row.code_verifier
    if row.nonce:
        data["nonce"] = row.nonce
    return data
