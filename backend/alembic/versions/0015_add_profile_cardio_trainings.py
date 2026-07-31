"""add cardio trainings to user profiles

Revision ID: 0015_profile_cardio
Revises: 0014_hardening_data_integrity
Create Date: 2026-07-31
"""

import sqlalchemy as sa

from alembic import op

revision = "0015_profile_cardio"
down_revision = "0014_hardening_data_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("cardio_trainings_per_week", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "cardio_trainings_per_week")
