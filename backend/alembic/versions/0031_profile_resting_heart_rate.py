"""add resting heart rate to user profiles

Revision ID: 0031_profile_resting_heart_rate
Revises: 0030_local_credentials
Create Date: 2026-08-12
"""

import sqlalchemy as sa

from alembic import op

revision = "0031_profile_resting_heart_rate"
down_revision = "0030_local_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.add_column(
            sa.Column("resting_heart_rate", sa.Integer(), nullable=True),
        )
        batch_op.create_check_constraint(
            "ck_user_profiles_resting_heart_rate_range",
            "resting_heart_rate IS NULL OR resting_heart_rate BETWEEN 30 AND 120",
        )


def downgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_constraint(
            "ck_user_profiles_resting_heart_rate_range",
            type_="check",
        )
        batch_op.drop_column("resting_heart_rate")
