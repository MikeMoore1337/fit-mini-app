"""Backfill deterministic exercise metric types.

Revision ID: 0065_exercise_metric_backfill
Revises: 0064_workout_metric_fields
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0065_exercise_metric_backfill"
down_revision: str | None = "0064_workout_metric_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "backfill"
online_rollout_notes = (
    "One idempotent bounded catalog update; exercise rows are a small seeded set."
)
online_rollout_batch_size = 1000
online_rollout_idempotent = True


def upgrade() -> None:
    op.execute(
        """UPDATE exercises
        SET metric_type = CASE
            WHEN id IN (
                SELECT exercise_muscles.exercise_id
                FROM exercise_muscles
                JOIN muscles ON muscles.id = exercise_muscles.muscle_id
                WHERE muscles.identifier = 'cardio'
            ) THEN 'cardio'
            ELSE 'strength'
        END
        WHERE metric_type IS NULL"""
    )


def downgrade() -> None:
    pass
