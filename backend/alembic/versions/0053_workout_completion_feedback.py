"""add workout completion feedback

Revision ID: 0053_workout_completion_feedback
Revises: 0052_fast_nutrition_logging
Create Date: 2026-08-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0053_workout_completion_feedback"
down_revision = "0052_fast_nutrition_logging"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_workouts") as batch_op:
        batch_op.add_column(sa.Column("completion_feedback", sa.String(length=24), nullable=True))
        batch_op.add_column(sa.Column("completion_note", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("completion_feedback_updated_at", sa.DateTime(), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_user_workouts_completion_feedback",
            "completion_feedback IS NULL OR completion_feedback IN "
            "('easier_than_expected', 'as_expected', 'harder_than_expected')",
        )
        batch_op.create_check_constraint(
            "ck_user_workouts_completion_note_length",
            "completion_note IS NULL OR length(completion_note) <= 500",
        )


def downgrade() -> None:
    with op.batch_alter_table("user_workouts") as batch_op:
        batch_op.drop_constraint("ck_user_workouts_completion_note_length", type_="check")
        batch_op.drop_constraint("ck_user_workouts_completion_feedback", type_="check")
        batch_op.drop_column("completion_feedback_updated_at")
        batch_op.drop_column("completion_note")
        batch_op.drop_column("completion_feedback")
