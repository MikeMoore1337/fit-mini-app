"""add notification delivery state

Revision ID: 0013_notification_delivery_state
Revises: 0012_coach_invite_telegram_id
Create Date: 2026-07-20
"""

import sqlalchemy as sa

from alembic import op

revision = "0013_notification_delivery_state"
down_revision = "0012_coach_invite_telegram_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("dedupe_key", sa.String(length=128), nullable=True))
    op.add_column(
        "notifications",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("notifications", sa.Column("next_attempt_at", sa.DateTime(), nullable=True))
    op.add_column("notifications", sa.Column("processing_started_at", sa.DateTime(), nullable=True))
    op.create_unique_constraint(
        "uq_notifications_dedupe_key",
        "notifications",
        ["dedupe_key"],
    )
    op.create_index("ix_notifications_next_attempt_at", "notifications", ["next_attempt_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_next_attempt_at", table_name="notifications")
    op.drop_constraint("uq_notifications_dedupe_key", "notifications", type_="unique")
    op.drop_column("notifications", "processing_started_at")
    op.drop_column("notifications", "next_attempt_at")
    op.drop_column("notifications", "attempt_count")
    op.drop_column("notifications", "dedupe_key")
