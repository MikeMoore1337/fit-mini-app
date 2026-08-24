"""Add manual cardio session logging.

Revision ID: 0058_cardio_sessions
Revises: 0057_account_data_exports
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0058_cardio_sessions"
down_revision: str | None = "0057_account_data_exports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cardio_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_request_id", sa.String(length=36), nullable=False),
        sa.Column("activity_type", sa.String(length=32), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("distance_km", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("average_heart_rate_bpm", sa.Integer(), nullable=True),
        sa.Column("heart_rate_zone", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "activity_type IN ('walking', 'running', 'elliptical', 'stationary_bike', "
            "'cycling', 'rowing', 'stepper', 'swimming', 'other')",
            name="ck_cardio_sessions_activity_type",
        ),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 1 AND 600",
            name="ck_cardio_sessions_duration_minutes",
        ),
        sa.CheckConstraint(
            "distance_km IS NULL OR (distance_km > 0 AND distance_km <= 1000)",
            name="ck_cardio_sessions_distance_km",
        ),
        sa.CheckConstraint(
            "average_heart_rate_bpm IS NULL OR average_heart_rate_bpm BETWEEN 30 AND 250",
            name="ck_cardio_sessions_average_heart_rate",
        ),
        sa.CheckConstraint(
            "heart_rate_zone IS NULL OR heart_rate_zone BETWEEN 1 AND 5",
            name="ck_cardio_sessions_heart_rate_zone",
        ),
        sa.CheckConstraint(
            "status IN ('planned', 'completed')",
            name="ck_cardio_sessions_status",
        ),
        sa.CheckConstraint("source = 'manual'", name="ck_cardio_sessions_source"),
        sa.CheckConstraint("note IS NULL OR length(note) <= 500", name="ck_cardio_sessions_note"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "client_request_id", name="uq_cardio_sessions_request"),
    )
    op.create_index("ix_cardio_sessions_user_id", "cardio_sessions", ["user_id"], unique=False)
    op.create_index(
        "ix_cardio_sessions_user_scheduled",
        "cardio_sessions",
        ["user_id", "scheduled_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_cardio_sessions_user_scheduled", table_name="cardio_sessions")
    op.drop_index("ix_cardio_sessions_user_id", table_name="cardio_sessions")
    op.drop_table("cardio_sessions")
