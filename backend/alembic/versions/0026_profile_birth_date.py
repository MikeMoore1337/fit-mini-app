"""add profile birth date for heart rate zones

Revision ID: 0026_profile_birth_date
Revises: 0025_workout_scheduled_time
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0026_profile_birth_date"
down_revision = "0025_workout_scheduled_time"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("birth_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "birth_date")
