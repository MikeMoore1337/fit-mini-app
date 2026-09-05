"""Backfill default-off contextual reminder flags.

Revision ID: 0075_contextual_template_flags
Revises: 0074_contextual_templates
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0075_contextual_template_flags"
down_revision: str | None = "0074_contextual_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "backfill"
online_rollout_notes = (
    "One idempotent bounded update fills NULL contextual reminder flags with FALSE; no user "
    "category is enabled by the backfill."
)
online_rollout_batch_size = 1000
online_rollout_idempotent = True


def upgrade() -> None:
    op.execute(
        """UPDATE notification_settings
        SET meal_reminders_enabled = FALSE,
            hydration_reminders_enabled = FALSE,
            movement_reminders_enabled = FALSE
        WHERE meal_reminders_enabled IS NULL
           OR hydration_reminders_enabled IS NULL
           OR movement_reminders_enabled IS NULL"""
    )


def downgrade() -> None:
    pass
