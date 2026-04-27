"""make exercise metadata optional

Revision ID: 0010_optional_exercise_metadata
Revises: 0009_add_user_timezone
Create Date: 2026-04-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0010_optional_exercise_metadata"
down_revision = "0009_add_user_timezone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.alter_column(
            "primary_muscle",
            existing_type=sa.String(length=64),
            nullable=True,
        )
        batch_op.alter_column(
            "equipment",
            existing_type=sa.String(length=64),
            nullable=True,
        )


def downgrade() -> None:
    op.execute("UPDATE exercises SET primary_muscle = '' WHERE primary_muscle IS NULL")
    op.execute("UPDATE exercises SET equipment = '' WHERE equipment IS NULL")
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.alter_column(
            "primary_muscle",
            existing_type=sa.String(length=64),
            nullable=False,
        )
        batch_op.alter_column(
            "equipment",
            existing_type=sa.String(length=64),
            nullable=False,
        )
