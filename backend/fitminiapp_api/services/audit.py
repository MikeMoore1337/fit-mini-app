from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.orm import Session

from fitminiapp_api.models.audit import AuditEvent


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
