"""Add nullable fields for type-aware workout logging.

Revision ID: 0064_workout_metric_fields
Revises: 0063_audit_retention_index
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0064_workout_metric_fields"
down_revision: str | None = "0063_audit_retention_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "expand"
online_rollout_notes = "Nullable scalar columns only; no table rewrite or constraint lock required."


def upgrade() -> None:
    op.add_column("exercises", sa.Column("metric_type", sa.String(length=16), nullable=True))
    op.add_column(
        "program_template_exercises",
        sa.Column("prescribed_duration_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_workout_exercises",
        sa.Column("prescribed_duration_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_workout_exercises", sa.Column("metric_type", sa.String(length=16), nullable=True)
    )
    op.add_column("user_workout_sets", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.add_column("user_workout_sets", sa.Column("distance_km", sa.Float(), nullable=True))
    op.add_column(
        "user_workout_sets",
        sa.Column("average_heart_rate_bpm", sa.Integer(), nullable=True),
    )
    op.add_column("user_workout_sets", sa.Column("heart_rate_zone", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_workout_sets", "heart_rate_zone")
    op.drop_column("user_workout_sets", "average_heart_rate_bpm")
    op.drop_column("user_workout_sets", "distance_km")
    op.drop_column("user_workout_sets", "duration_minutes")
    op.drop_column("user_workout_exercises", "metric_type")
    op.drop_column("user_workout_exercises", "prescribed_duration_minutes")
    op.drop_column("program_template_exercises", "prescribed_duration_minutes")
    op.drop_column("exercises", "metric_type")
