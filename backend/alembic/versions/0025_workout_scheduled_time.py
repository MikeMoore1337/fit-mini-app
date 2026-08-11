"""add optional workout scheduled time

Revision ID: 0025_workout_scheduled_time
Revises: 0024_audit_events
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0025_workout_scheduled_time"
down_revision = "0024_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_workouts", sa.Column("scheduled_time", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_workouts", "scheduled_time")
