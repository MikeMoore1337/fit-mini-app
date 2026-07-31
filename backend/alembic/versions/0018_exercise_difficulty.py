"""add exercise difficulty level

Revision ID: 0018_exercise_difficulty
Revises: 0017_hidden_templates
Create Date: 2026-07-31
"""

import sqlalchemy as sa

from alembic import op

revision = "0018_exercise_difficulty"
down_revision = "0017_hidden_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.add_column(
            sa.Column(
                "difficulty_level",
                sa.String(length=16),
                nullable=False,
                server_default="intermediate",
            )
        )
        batch_op.create_check_constraint(
            "ck_exercises_difficulty_level",
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
        )


def downgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.drop_constraint(
            "ck_exercises_difficulty_level",
            type_="check",
        )
        batch_op.drop_column("difficulty_level")
