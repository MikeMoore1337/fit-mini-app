"""exercise personalization

Revision ID: 0004_exercise_personalization
Revises: 0003_exercise_owner
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_exercise_personalization"
down_revision = "0003_exercise_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("source_exercise_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "exercises",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_index(
        "ix_exercises_source_exercise_id",
        "exercises",
        ["source_exercise_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_exercises_source_exercise_id_exercises",
        "exercises",
        "exercises",
        ["source_exercise_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_exercises_source_exercise_id_exercises",
        "exercises",
        type_="foreignkey",
    )
    op.drop_index("ix_exercises_source_exercise_id", table_name="exercises")
    op.drop_column("exercises", "is_deleted")
    op.drop_column("exercises", "source_exercise_id")
