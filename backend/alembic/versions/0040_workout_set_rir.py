"""add optional RIR category to workout sets

Revision ID: 0040_workout_set_rir
Revises: 0039_exercise_domain
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0040_workout_set_rir"
down_revision = "0039_exercise_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_workout_sets") as batch_op:
        batch_op.add_column(sa.Column("rir", sa.String(length=2), nullable=True))
        batch_op.create_check_constraint(
            "ck_user_workout_sets_rir",
            "rir IS NULL OR rir IN ('0', '1', '2', '3', '4+')",
        )


def downgrade() -> None:
    with op.batch_alter_table("user_workout_sets") as batch_op:
        batch_op.drop_constraint("ck_user_workout_sets_rir", type_="check")
        batch_op.drop_column("rir")
