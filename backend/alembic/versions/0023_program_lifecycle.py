"""add recurring program lifecycle and workout instructions

Revision ID: 0023_program_lifecycle
Revises: 0022_secure_invites_nutrition
Create Date: 2026-08-02
"""

import sqlalchemy as sa

from alembic import op

revision = "0023_program_lifecycle"
down_revision = "0022_secure_invites_nutrition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_programs", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column(
        "user_programs",
        sa.Column("duration_weeks", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "user_programs",
        sa.Column("schedule_weekdays", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
    )
    op.add_column(
        "user_programs",
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
    )
    op.add_column("user_programs", sa.Column("completed_at", sa.DateTime(), nullable=True))
    op.add_column("user_programs", sa.Column("archived_at", sa.DateTime(), nullable=True))

    connection = op.get_bind()
    date_expression = (
        "CAST(user_programs.assigned_at AS DATE)"
        if connection.dialect.name == "postgresql"
        else "DATE(user_programs.assigned_at)"
    )
    connection.execute(
        sa.text(
            f"""
            UPDATE user_programs
            SET start_date = COALESCE(
                (SELECT MIN(user_workouts.scheduled_date)
                 FROM user_workouts
                 WHERE user_workouts.user_program_id = user_programs.id),
                {date_expression}
            ),
            status = CASE
                WHEN NOT is_active THEN 'archived'
                WHEN NOT EXISTS (
                    SELECT 1 FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                ) THEN 'archived'
                WHEN NOT EXISTS (
                    SELECT 1 FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                      AND user_workouts.status <> 'completed'
                ) THEN 'completed'
                ELSE 'active'
            END,
            is_active = CASE
                WHEN NOT is_active THEN false
                WHEN NOT EXISTS (
                    SELECT 1 FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                ) THEN false
                WHEN NOT EXISTS (
                    SELECT 1 FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                      AND user_workouts.status <> 'completed'
                ) THEN false
                ELSE true
            END,
            completed_at = CASE
                WHEN EXISTS (
                    SELECT 1 FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                ) AND NOT EXISTS (
                    SELECT 1 FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                      AND user_workouts.status <> 'completed'
                ) THEN (
                    SELECT MAX(user_workouts.completed_at)
                    FROM user_workouts
                    WHERE user_workouts.user_program_id = user_programs.id
                )
                ELSE NULL
            END
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE user_programs
            SET archived_at = assigned_at
            WHERE status = 'archived' AND archived_at IS NULL
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE user_workouts
            SET status = 'cancelled'
            WHERE status IN ('planned', 'in_progress')
              AND user_program_id IN (
                  SELECT id FROM user_programs WHERE status = 'archived'
              )
            """
        )
    )
    op.alter_column("user_programs", "start_date", nullable=False)
    op.create_check_constraint(
        "ck_user_programs_status",
        "user_programs",
        "status IN ('scheduled', 'active', 'completed', 'archived')",
    )
    op.create_check_constraint(
        "ck_user_programs_duration_weeks",
        "user_programs",
        "duration_weeks >= 1",
    )

    op.add_column(
        "user_workouts",
        sa.Column("week_number", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column("user_workout_exercises", sa.Column("notes", sa.Text(), nullable=True))
    connection.execute(
        sa.text(
            """
            UPDATE user_workout_exercises
            SET notes = (
                SELECT program_template_exercises.notes
                FROM user_workouts
                JOIN user_programs
                  ON user_programs.id = user_workouts.user_program_id
                JOIN program_template_days
                  ON program_template_days.program_id = user_programs.template_id
                 AND program_template_days.day_number = user_workouts.day_number
                JOIN program_template_exercises
                  ON program_template_exercises.day_id = program_template_days.id
                 AND program_template_exercises.exercise_id = user_workout_exercises.exercise_id
                 AND program_template_exercises.sort_order = user_workout_exercises.sort_order
                WHERE user_workouts.id = user_workout_exercises.workout_id
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM user_workouts
                JOIN user_programs
                  ON user_programs.id = user_workouts.user_program_id
                JOIN program_template_days
                  ON program_template_days.program_id = user_programs.template_id
                 AND program_template_days.day_number = user_workouts.day_number
                JOIN program_template_exercises
                  ON program_template_exercises.day_id = program_template_days.id
                 AND program_template_exercises.exercise_id = user_workout_exercises.exercise_id
                 AND program_template_exercises.sort_order = user_workout_exercises.sort_order
                WHERE user_workouts.id = user_workout_exercises.workout_id
                  AND program_template_exercises.notes IS NOT NULL
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("user_workout_exercises", "notes")
    op.drop_column("user_workouts", "week_number")
    op.drop_constraint("ck_user_programs_duration_weeks", "user_programs", type_="check")
    op.drop_constraint("ck_user_programs_status", "user_programs", type_="check")
    op.drop_column("user_programs", "archived_at")
    op.drop_column("user_programs", "completed_at")
    op.drop_column("user_programs", "status")
    op.drop_column("user_programs", "schedule_weekdays")
    op.drop_column("user_programs", "duration_weeks")
    op.drop_column("user_programs", "start_date")
