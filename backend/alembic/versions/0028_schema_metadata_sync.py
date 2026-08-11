"""synchronize indexes and timestamp nullability with model metadata

Revision ID: 0028_schema_metadata_sync
Revises: 0027_nutrition_inputs
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0028_schema_metadata_sync"
down_revision = "0027_nutrition_inputs"
branch_labels = None
depends_on = None


_NON_NULL_TIMESTAMPS = (
    ("coach_client_invites", "created_at"),
    ("coach_clients", "created_at"),
    ("notifications", "created_at"),
    ("payments", "created_at"),
    ("program_templates", "created_at"),
    ("subscriptions", "created_at"),
    ("user_programs", "assigned_at"),
    ("users", "created_at"),
)

_INDEXES = (
    ("ix_notifications_scheduled_for", "notifications", ("scheduled_for",)),
    ("ix_notifications_user_id", "notifications", ("user_id",)),
    ("ix_payments_plan_id", "payments", ("plan_id",)),
    ("ix_payments_user_id", "payments", ("user_id",)),
    ("ix_program_template_days_program_id", "program_template_days", ("program_id",)),
    (
        "ix_program_template_exercises_day_id",
        "program_template_exercises",
        ("day_id",),
    ),
    (
        "ix_program_template_exercises_exercise_id",
        "program_template_exercises",
        ("exercise_id",),
    ),
    (
        "ix_program_templates_created_by_user_id",
        "program_templates",
        ("created_by_user_id",),
    ),
    (
        "ix_program_templates_owner_user_id",
        "program_templates",
        ("owner_user_id",),
    ),
    ("ix_subscriptions_plan_id", "subscriptions", ("plan_id",)),
    ("ix_subscriptions_user_id", "subscriptions", ("user_id",)),
    (
        "ix_user_programs_assigned_by_user_id",
        "user_programs",
        ("assigned_by_user_id",),
    ),
    ("ix_user_programs_template_id", "user_programs", ("template_id",)),
    ("ix_user_programs_user_id", "user_programs", ("user_id",)),
    (
        "ix_user_workout_exercises_exercise_id",
        "user_workout_exercises",
        ("exercise_id",),
    ),
    (
        "ix_user_workout_exercises_workout_id",
        "user_workout_exercises",
        ("workout_id",),
    ),
    (
        "ix_user_workout_sets_workout_exercise_id",
        "user_workout_sets",
        ("workout_exercise_id",),
    ),
    ("ix_user_workouts_scheduled_date", "user_workouts", ("scheduled_date",)),
    ("ix_user_workouts_user_program_id", "user_workouts", ("user_program_id",)),
)


def upgrade() -> None:
    for table_name, column_name in _NON_NULL_TIMESTAMPS:
        op.execute(
            sa.text(
                f'UPDATE "{table_name}" SET "{column_name}" = CURRENT_TIMESTAMP '
                f'WHERE "{column_name}" IS NULL'
            )
        )
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(),
            nullable=False,
        )

    op.drop_constraint(
        "notification_settings_user_id_key",
        "notification_settings",
        type_="unique",
    )
    op.create_index(
        "ix_notification_settings_user_id",
        "notification_settings",
        ["user_id"],
        unique=True,
    )

    for index_name, table_name, columns in _INDEXES:
        op.create_index(index_name, table_name, list(columns))


def downgrade() -> None:
    for index_name, table_name, _columns in reversed(_INDEXES):
        op.drop_index(index_name, table_name=table_name)

    op.drop_index(
        "ix_notification_settings_user_id",
        table_name="notification_settings",
    )
    op.create_unique_constraint(
        "notification_settings_user_id_key",
        "notification_settings",
        ["user_id"],
    )

    for table_name, column_name in reversed(_NON_NULL_TIMESTAMPS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(),
            nullable=True,
        )
