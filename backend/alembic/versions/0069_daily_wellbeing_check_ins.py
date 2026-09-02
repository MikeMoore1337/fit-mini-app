"""Add optional daily sleep and mood check-ins.

Revision ID: 0069_daily_wellbeing_check_ins
Revises: 0068_hydration_tracking
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0069_daily_wellbeing_check_ins"
down_revision: str | None = "0068_hydration_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "expand"
online_rollout_notes = (
    "Adds an empty user-owned daily wellbeing table with bounded observations and no data rewrite."
)


def upgrade() -> None:
    op.create_table(
        "daily_wellbeing_check_ins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("timezone_at_entry", sa.String(length=64), nullable=False),
        sa.Column("sleep_quality", sa.Integer(), nullable=True),
        sa.Column("sleep_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "local_date", name="uq_daily_wellbeing_user_date"),
        sa.CheckConstraint(
            "sleep_quality IS NULL OR sleep_quality BETWEEN 1 AND 5",
            name="ck_daily_wellbeing_sleep_quality",
        ),
        sa.CheckConstraint(
            "mood IS NULL OR mood BETWEEN 1 AND 5",
            name="ck_daily_wellbeing_mood",
        ),
        sa.CheckConstraint(
            "sleep_duration_minutes IS NULL OR sleep_duration_minutes BETWEEN 1 AND 1440",
            name="ck_daily_wellbeing_sleep_duration",
        ),
        sa.CheckConstraint(
            "sleep_quality IS NOT NULL OR sleep_duration_minutes IS NOT NULL OR mood IS NOT NULL",
            name="ck_daily_wellbeing_has_observation",
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'future_import')",
            name="ck_daily_wellbeing_source",
        ),
        sa.CheckConstraint(
            "note IS NULL OR length(note) <= 500",
            name="ck_daily_wellbeing_note_length",
        ),
    )


def downgrade() -> None:
    op.drop_table("daily_wellbeing_check_ins")
