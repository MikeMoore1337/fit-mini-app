"""add created_by_user_id to exercises

Revision ID: 0003_add_created_by_user_id_to_exercises
Revises: 0002_add_refresh_tokens
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_add_created_by_user_id_to_exercises"
down_revision = "0002_add_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_exercises_created_by_user_id",
        "exercises",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_exercises_created_by_user_id_users",
        "exercises",
        "users",
        ["created_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_exercises_created_by_user_id_users", "exercises", type_="foreignkey")
    op.drop_index("ix_exercises_created_by_user_id", table_name="exercises")
    op.drop_column("exercises", "created_by_user_id")
