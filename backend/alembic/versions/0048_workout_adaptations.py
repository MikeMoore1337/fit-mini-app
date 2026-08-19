"""add deterministic workout adaptation audit

Revision ID: 0048_workout_adaptations
Revises: 0047_weekly_check_ins
Create Date: 2026-08-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0048_workout_adaptations"
down_revision = "0047_weekly_check_ins"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workout_adaptations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("preview_token", sa.String(length=64), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("original_snapshot", sa.JSON(), nullable=False),
        sa.Column("applied_diff", sa.JSON(), nullable=False),
        sa.Column("ruleset_version", sa.String(length=32), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "reason IN ('limited_time', 'unavailable_equipment', "
            "'replace_exercise', 'different_environment')",
            name="ck_workout_adaptations_reason",
        ),
        sa.ForeignKeyConstraint(["workout_id"], ["user_workouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("preview_token"),
    )
    op.create_index(
        "ix_workout_adaptations_workout_applied",
        "workout_adaptations",
        ["workout_id", "applied_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workout_adaptations_workout_applied",
        table_name="workout_adaptations",
    )
    op.drop_table("workout_adaptations")
