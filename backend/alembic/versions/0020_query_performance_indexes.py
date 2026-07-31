"""add indexes for common queue, coach and workout lookups

Revision ID: 0020_query_performance_indexes
Revises: 0019_client_invitation_workflow
Create Date: 2026-08-01
"""

import sqlalchemy as sa

from alembic import op

revision = "0020_query_performance_indexes"
down_revision = "0019_client_invitation_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_coach_clients_coach_status",
        "coach_clients",
        ["coach_user_id", "status"],
    )
    op.create_index(
        "ix_user_workouts_program_date_status",
        "user_workouts",
        ["user_program_id", "scheduled_date", "status"],
    )
    op.create_index(
        "ix_notifications_due_queue",
        "notifications",
        ["scheduled_for_utc", "next_attempt_at"],
        postgresql_where=sa.text("status = 'queued'"),
        sqlite_where=sa.text("status = 'queued'"),
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_due_queue", table_name="notifications")
    op.drop_index("ix_user_workouts_program_date_status", table_name="user_workouts")
    op.drop_index("ix_coach_clients_coach_status", table_name="coach_clients")
