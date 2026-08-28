from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from fitminiapp_api.models.audit import AuditEvent

AUDIT_RETENTION_BATCH_SIZE = 500


def record_audit_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    resource_id: int | str | None = None,
    details: Mapping[str, object] | None = None,
) -> AuditEvent:
    """Stage an append-only event in the caller's current transaction."""

    event = AuditEvent(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=dict(details or {}),
    )
    db.add(event)
    return event


def prune_audit_events(
    db: Session,
    *,
    retention_days: int,
    now: datetime | None = None,
    batch_size: int = AUDIT_RETENTION_BATCH_SIZE,
) -> int:
    """Delete one bounded batch of expired pseudonymous audit history."""

    current = now or datetime.now(UTC).replace(tzinfo=None)
    cutoff = current - timedelta(days=retention_days)
    event_ids = [
        event_id
        for (event_id,) in (
            db.query(AuditEvent.id)
            .filter(AuditEvent.created_at < cutoff)
            .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
            .limit(batch_size)
            .all()
        )
    ]
    if not event_ids:
        return 0
    return int(
        db.query(AuditEvent).filter(AuditEvent.id.in_(event_ids)).delete(synchronize_session=False)
    )
