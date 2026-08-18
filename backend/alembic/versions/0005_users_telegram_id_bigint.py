"""change telegram_user_id to bigint

Revision ID: 0005_users_telegram_id_bigint
Revises: 0004_exercise_personalization
Create Date: 2026-04-06
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_users_telegram_id_bigint"
down_revision = "0004_exercise_personalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "telegram_user_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "telegram_user_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
