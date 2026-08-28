"""Index audit event retention cleanup.

Revision ID: 0063_audit_retention_index
Revises: 0062_anonymize_delete_audit
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0063_audit_retention_index"
down_revision: str | None = "0062_anonymize_delete_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
