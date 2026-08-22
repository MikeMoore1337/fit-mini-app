"""add workout comment idempotency keys

Revision ID: 0050_comment_idempotency
Revises: 0049_offline_workout_sync
Create Date: 2026-08-22
"""

import sqlalchemy as sa

from alembic import op

revision = "0050_comment_idempotency"
down_revision = "0049_offline_workout_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workout_comments") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint(
            "uq_workout_comments_author_idempotency",
            ["trainer_author_id", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("workout_comments") as batch_op:
        batch_op.drop_constraint(
            "uq_workout_comments_author_idempotency",
            type_="unique",
        )
        batch_op.drop_column("idempotency_key")
