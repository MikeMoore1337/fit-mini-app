"""add created_by_user_id to exercises

Revision ID: 0003_exercise_owner
Revises: 0002_add_refresh_tokens
Create Date: 2026-04-04
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_exercise_owner"
down_revision = "0002_add_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.add_column(
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        )
        batch_op.create_index(
            "ix_exercises_created_by_user_id",
            ["created_by_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_exercises_created_by_user_id_users",
            "users",
            ["created_by_user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.drop_constraint(
            "fk_exercises_created_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_exercises_created_by_user_id")
        batch_op.drop_column("created_by_user_id")
