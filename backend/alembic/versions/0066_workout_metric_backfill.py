"""Backfill stable metric snapshots for existing workout exercises.

Revision ID: 0066_workout_metric_backfill
Revises: 0065_exercise_metric_backfill
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0066_workout_metric_backfill"
down_revision: str | None = "0065_exercise_metric_backfill"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "backfill"
online_rollout_notes = "One idempotent bounded historical-workout update."
online_rollout_batch_size = 1000
online_rollout_idempotent = True


def upgrade() -> None:
    op.execute(
        """UPDATE user_workout_exercises
        SET metric_type = COALESCE(
            (SELECT exercises.metric_type
             FROM exercises
             WHERE exercises.id = user_workout_exercises.exercise_id),
            'strength'
        )
        WHERE metric_type IS NULL"""
    )


def downgrade() -> None:
    pass
