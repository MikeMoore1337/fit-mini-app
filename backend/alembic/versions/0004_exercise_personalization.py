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
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.add_column(
            sa.Column("source_exercise_id", sa.Integer(), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
        batch_op.create_index(
            "ix_exercises_source_exercise_id",
            ["source_exercise_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_exercises_source_exercise_id_exercises",
            "exercises",
            ["source_exercise_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.drop_constraint(
            "fk_exercises_source_exercise_id_exercises",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_exercises_source_exercise_id")
        batch_op.drop_column("is_deleted")
        batch_op.drop_column("source_exercise_id")
