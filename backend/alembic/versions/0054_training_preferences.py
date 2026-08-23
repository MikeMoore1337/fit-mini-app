"""add non-medical training preferences

Revision ID: 0054_training_preferences
Revises: 0053_workout_completion_feedback
Create Date: 2026-08-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0054_training_preferences"
down_revision = "0053_workout_completion_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.add_column(
            sa.Column("preferred_workout_duration_min", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("preferred_workout_duration_max", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "preferred_training_weekdays",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("preferred_training_time", sa.Time(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "training_location_profiles",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "preferred_exercise_ids",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "avoided_exercises",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("training_preferences_note", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("training_preferences_updated_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("training_preferences_updated_by_user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_user_profiles_training_preferences_editor",
            "users",
            ["training_preferences_updated_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_check_constraint(
            "ck_user_profiles_preferred_duration_min",
            "preferred_workout_duration_min IS NULL OR "
            "preferred_workout_duration_min BETWEEN 10 AND 240",
        )
        batch_op.create_check_constraint(
            "ck_user_profiles_preferred_duration_max",
            "preferred_workout_duration_max IS NULL OR "
            "preferred_workout_duration_max BETWEEN 10 AND 240",
        )
        batch_op.create_check_constraint(
            "ck_user_profiles_preferred_duration_order",
            "preferred_workout_duration_min IS NULL OR "
            "preferred_workout_duration_max IS NULL OR "
            "preferred_workout_duration_min <= preferred_workout_duration_max",
        )
        batch_op.create_check_constraint(
            "ck_user_profiles_training_preferences_note_length",
            "training_preferences_note IS NULL OR length(training_preferences_note) <= 500",
        )


def downgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_constraint(
            "ck_user_profiles_training_preferences_note_length", type_="check"
        )
        batch_op.drop_constraint("ck_user_profiles_preferred_duration_order", type_="check")
        batch_op.drop_constraint("ck_user_profiles_preferred_duration_max", type_="check")
        batch_op.drop_constraint("ck_user_profiles_preferred_duration_min", type_="check")
        batch_op.drop_constraint(
            "fk_user_profiles_training_preferences_editor", type_="foreignkey"
        )
        batch_op.drop_column("training_preferences_updated_by_user_id")
        batch_op.drop_column("training_preferences_updated_at")
        batch_op.drop_column("training_preferences_note")
        batch_op.drop_column("avoided_exercises")
        batch_op.drop_column("preferred_exercise_ids")
        batch_op.drop_column("training_location_profiles")
        batch_op.drop_column("preferred_training_time")
        batch_op.drop_column("preferred_training_weekdays")
        batch_op.drop_column("preferred_workout_duration_max")
        batch_op.drop_column("preferred_workout_duration_min")
