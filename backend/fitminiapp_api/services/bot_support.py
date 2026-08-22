from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from fitminiapp_api.models.support import BotSupportCase
from fitminiapp_api.services.audit import record_audit_event

SUPPORT_CASE_TTL = timedelta(days=7)
SUPPORT_CASE_RETENTION = timedelta(days=30)
SUPPORT_RATE_LIMIT_WINDOW = timedelta(hours=1)
SUPPORT_RATE_LIMIT_PER_CATEGORY = 3
SUPPORT_RETENTION_BATCH_SIZE = 500

SupportCategory = Literal["bug", "account", "idea", "contact", "other"]
ReplyOutcome = Literal["delivered", "blocked", "failed"]


class SupportRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupportCaseCreation:
    case: BotSupportCase
    created: bool


@dataclass(frozen=True)
class SupportReplyClaim:
    status: Literal["claimed", "already_processed", "unavailable", "expired"]
    telegram_user_id: int | None = None


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def prune_support_cases(db: Session, *, now: datetime | None = None) -> int:
    cutoff = (now or utcnow()) - SUPPORT_CASE_RETENTION
    case_ids = [
        row.id
        for row in db.query(BotSupportCase.id)
        .filter(BotSupportCase.created_at < cutoff)
        .order_by(BotSupportCase.created_at.asc(), BotSupportCase.id.asc())
        .limit(SUPPORT_RETENTION_BATCH_SIZE)
        .all()
    ]
    if case_ids:
        db.query(BotSupportCase).filter(BotSupportCase.id.in_(case_ids)).delete(
            synchronize_session=False
        )
    return len(case_ids)


def create_support_case(
    db: Session,
    *,
    telegram_user_id: int,
    request_message_id: int,
    category: SupportCategory,
    now: datetime | None = None,
) -> SupportCaseCreation:
    current = now or utcnow()
    prune_support_cases(db, now=current)

    existing = (
        db.query(BotSupportCase)
        .filter(
            BotSupportCase.telegram_user_id == telegram_user_id,
            BotSupportCase.request_message_id == request_message_id,
        )
        .first()
    )
    if existing is not None:
        return SupportCaseCreation(case=existing, created=False)

    recent_count = (
        db.query(BotSupportCase.id)
        .filter(
            BotSupportCase.telegram_user_id == telegram_user_id,
            BotSupportCase.category == category,
            BotSupportCase.created_at >= current - SUPPORT_RATE_LIMIT_WINDOW,
        )
        .count()
    )
    if recent_count >= SUPPORT_RATE_LIMIT_PER_CATEGORY:
        raise SupportRateLimitError("support_rate_limit_exceeded")

    case = BotSupportCase(
        id=secrets.token_hex(16),
        telegram_user_id=telegram_user_id,
        request_message_id=request_message_id,
        category=category,
        status="pending_relay",
        created_at=current,
        expires_at=current + SUPPORT_CASE_TTL,
    )
    db.add(case)
    db.flush()
    record_audit_event(
        db,
        action="support.case_created",
        resource_type="bot_support_case",
        resource_id=case.id,
        details={"category": category},
    )
    return SupportCaseCreation(case=case, created=True)


def record_support_relay_result(
    db: Session,
    *,
    case_id: str,
    delivered: bool,
) -> BotSupportCase | None:
    case = db.query(BotSupportCase).filter(BotSupportCase.id == case_id).with_for_update().first()
    if case is None:
        return None
    target_status = "open" if delivered else "relay_failed"
    if case.status == "pending_relay":
        case.status = target_status
        record_audit_event(
            db,
            action="support.relay_succeeded" if delivered else "support.relay_failed",
            resource_type="bot_support_case",
            resource_id=case.id,
            details={"category": case.category},
        )
    return case


def claim_support_reply(
    db: Session,
    *,
    case_id: str,
    admin_telegram_user_id: int,
    reply_message_id: int,
    now: datetime | None = None,
) -> SupportReplyClaim:
    current = now or utcnow()
    case = db.query(BotSupportCase).filter(BotSupportCase.id == case_id).with_for_update().first()
    if case is None:
        return SupportReplyClaim(status="unavailable")

    same_reply = (
        case.reply_admin_telegram_user_id == admin_telegram_user_id
        and case.reply_message_id == reply_message_id
    )
    if same_reply:
        return SupportReplyClaim(status="already_processed")
    if case.status in {"pending_relay", "open"} and case.expires_at <= current:
        case.status = "expired"
        record_audit_event(
            db,
            action="support.case_expired",
            resource_type="bot_support_case",
            resource_id=case.id,
            details={"category": case.category},
        )
        return SupportReplyClaim(status="expired")
    if case.status not in {"pending_relay", "open"}:
        return SupportReplyClaim(status="unavailable")

    case.status = "replying"
    case.reply_admin_telegram_user_id = admin_telegram_user_id
    case.reply_message_id = reply_message_id
    case.reply_claimed_at = current
    record_audit_event(
        db,
        action="support.reply_claimed",
        resource_type="bot_support_case",
        resource_id=case.id,
        details={"category": case.category},
    )
    return SupportReplyClaim(status="claimed", telegram_user_id=case.telegram_user_id)


def complete_support_reply(
    db: Session,
    *,
    case_id: str,
    admin_telegram_user_id: int,
    reply_message_id: int,
    outcome: ReplyOutcome,
    now: datetime | None = None,
) -> bool:
    current = now or utcnow()
    case = db.query(BotSupportCase).filter(BotSupportCase.id == case_id).with_for_update().first()
    if case is None:
        return False
    if (
        case.reply_admin_telegram_user_id != admin_telegram_user_id
        or case.reply_message_id != reply_message_id
    ):
        return False
    if case.status != "replying":
        return True

    action = "support.reply_failed"
    if outcome == "delivered":
        case.status = "replied"
        case.replied_at = current
        action = "support.reply_delivered"
    elif outcome == "blocked":
        case.status = "undeliverable"
        action = "support.reply_undeliverable"
    else:
        case.status = "open"

    record_audit_event(
        db,
        action=action,
        resource_type="bot_support_case",
        resource_id=case.id,
        details={"category": case.category},
    )
    return True
