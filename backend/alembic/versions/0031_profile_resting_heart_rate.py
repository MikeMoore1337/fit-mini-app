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
    op.add_column(
        "user_profiles",
        sa.Column("resting_heart_rate", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_user_profiles_resting_heart_rate_range",
        "user_profiles",
        "resting_heart_rate IS NULL OR resting_heart_rate BETWEEN 30 AND 120",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_profiles_resting_heart_rate_range",
        "user_profiles",
        type_="check",
    )
    op.drop_column("user_profiles", "resting_heart_rate")
