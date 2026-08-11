"""add approachable nutrition activity inputs

Revision ID: 0027_nutrition_inputs
Revises: 0026_profile_birth_date
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0027_nutrition_inputs"
down_revision = "0026_profile_birth_date"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "nutrition_targets",
        sa.Column(
            "daily_routine",
            sa.String(length=24),
            nullable=False,
            server_default="mostly_sitting",
        ),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column("steps_range", sa.String(length=32), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column(
            "strength_training_type",
            sa.String(length=16),
            nullable=False,
            server_default="regular",
        ),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column("strength_rest", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "nutrition_targets",
        sa.Column("cardio_trainings", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE nutrition_targets
            SET daily_routine = CASE daily_activity_level
                    WHEN 'low' THEN 'mixed'
                    WHEN 'moderate' THEN 'mostly_on_feet'
                    WHEN 'high' THEN 'physical_work'
                    ELSE 'mostly_sitting'
                END,
                strength_training_type = 'regular',
                strength_rest = 'varied'
            """
        )
    )
    if connection.dialect.name == "postgresql":
        connection.execute(
            sa.text(
                """
                UPDATE nutrition_targets
                SET cardio_trainings = json_build_array(json_build_object(
                    'kind', 'other',
                    'trainings_per_week', cardio_trainings_per_week,
                    'duration_minutes', cardio_training_duration_minutes,
                    'intensity', CASE cardio_intensity
                        WHEN 'low' THEN 'light'
                        WHEN 'high' THEN 'hard'
                        ELSE 'moderate'
                    END
                ))
                WHERE cardio_trainings_per_week > 0
                """
            )
        )


def downgrade() -> None:
    op.drop_column("nutrition_targets", "cardio_trainings")
    op.drop_column("nutrition_targets", "strength_rest")
    op.drop_column("nutrition_targets", "strength_training_type")
    op.drop_column("nutrition_targets", "steps_range")
    op.drop_column("nutrition_targets", "daily_routine")
