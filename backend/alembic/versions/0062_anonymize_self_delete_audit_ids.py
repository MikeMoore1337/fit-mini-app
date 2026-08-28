"""Anonymize historical self-delete audit resource identifiers.

Revision ID: 0062_anonymize_delete_audit
Revises: 0061_weekly_telegram_digest
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0062_anonymize_delete_audit"
down_revision: str | None = "0061_weekly_telegram_digest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE audit_events SET resource_id = NULL WHERE action = 'account.self_deleted'")
    )


def downgrade() -> None:
    # Deleted account identifiers cannot and must not be reconstructed.
    pass
