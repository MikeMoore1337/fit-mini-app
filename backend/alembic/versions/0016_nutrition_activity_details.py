"""add nutrition activity details

Revision ID: 0016_nutrition_activity
Revises: 0015_profile_cardio
Create Date: 2026-07-31
"""

import sqlalchemy as sa

from alembic import op

revision = "0016_nutrition_activity"
down_revision = "0015_profile_cardio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "nutrition_targets",
        sa.Column(
            "daily_activity_level", sa.String(length=16), nullable=False, server_default="sedentary"
        ),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column(
            "strength_training_duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column(
            "cardio_training_duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column(
            "cardio_intensity", sa.String(length=16), nullable=False, server_default="moderate"
        ),
    )


def downgrade() -> None:
    op.drop_column("nutrition_targets", "cardio_intensity")
    op.drop_column("nutrition_targets", "cardio_training_duration_minutes")
    op.drop_column("nutrition_targets", "strength_training_duration_minutes")
    op.drop_column("nutrition_targets", "daily_activity_level")
