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
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("dedupe_key", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        )
        batch_op.add_column(sa.Column("next_attempt_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("processing_started_at", sa.DateTime(), nullable=True))
        batch_op.create_unique_constraint(
            "uq_notifications_dedupe_key",
            ["dedupe_key"],
        )
        batch_op.create_index("ix_notifications_next_attempt_at", ["next_attempt_at"])


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_index("ix_notifications_next_attempt_at")
        batch_op.drop_constraint("uq_notifications_dedupe_key", type_="unique")
        batch_op.drop_column("processing_started_at")
        batch_op.drop_column("next_attempt_at")
        batch_op.drop_column("attempt_count")
        batch_op.drop_column("dedupe_key")
