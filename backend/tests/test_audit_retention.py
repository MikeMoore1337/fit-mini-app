from datetime import UTC, datetime, timedelta

from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.services.audit import prune_audit_events


def _audit(created_at: datetime, resource_id: str) -> AuditEvent:
    return AuditEvent(
        action="test.retention",
        resource_type="test",
        resource_id=resource_id,
        details={},
        created_at=created_at,
    )


def test_audit_retention_prunes_only_one_bounded_expired_batch() -> None:
    now = datetime(2030, 1, 1, tzinfo=UTC).replace(tzinfo=None)
    with get_session_context() as db:
        db.add_all(
            (
                _audit(now - timedelta(days=367), "oldest"),
                _audit(now - timedelta(days=366), "older"),
                _audit(now - timedelta(days=365), "boundary"),
                _audit(now - timedelta(days=1), "current"),
            )
        )

    with get_session_context() as db:
        assert prune_audit_events(db, retention_days=365, now=now, batch_size=1) == 1

    with get_session_context() as db:
        remaining = [
            row.resource_id
            for row in db.query(AuditEvent).order_by(AuditEvent.created_at.asc()).all()
            if row.action == "test.retention"
        ]
        assert remaining == ["older", "boundary", "current"]
        assert prune_audit_events(db, retention_days=365, now=now, batch_size=10) == 1

    with get_session_context() as db:
        remaining = {
            row.resource_id
            for row in db.query(AuditEvent).filter(AuditEvent.action == "test.retention").all()
        }
        assert remaining == {"boundary", "current"}
