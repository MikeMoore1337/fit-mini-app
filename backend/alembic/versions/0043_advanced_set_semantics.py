"""add advanced workout set semantics and superset grouping

Revision ID: 0043_set_semantics
Revises: 0042_workout_comments
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0043_set_semantics"
down_revision = "0042_workout_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("program_template_exercises") as batch_op:
        batch_op.add_column(sa.Column("superset_group", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("superset_order", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_program_template_exercises_superset",
            "(superset_group IS NULL AND superset_order IS NULL) OR "
            "(superset_group IS NOT NULL AND superset_order IS NOT NULL AND "
            "superset_group >= 1 AND superset_order IN (1, 2))",
        )
        batch_op.create_unique_constraint(
            "uq_program_template_exercises_superset_order",
            ["day_id", "superset_group", "superset_order"],
        )

    with op.batch_alter_table("user_workout_exercises") as batch_op:
        batch_op.add_column(sa.Column("superset_group", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("superset_order", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_user_workout_exercises_superset",
            "(superset_group IS NULL AND superset_order IS NULL) OR "
            "(superset_group IS NOT NULL AND superset_order IS NOT NULL AND "
            "superset_group >= 1 AND superset_order IN (1, 2))",
        )
        batch_op.create_unique_constraint(
            "uq_user_workout_exercises_superset_order",
            ["workout_id", "superset_group", "superset_order"],
        )

    with op.batch_alter_table("user_workout_sets") as batch_op:
        batch_op.add_column(sa.Column("set_kind", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("reached_failure", sa.Boolean(), nullable=True))
        batch_op.create_check_constraint(
            "ck_user_workout_sets_kind",
            "set_kind IS NULL OR set_kind IN ('warmup', 'working', 'drop')",
        )


def downgrade() -> None:
    with op.batch_alter_table("user_workout_sets") as batch_op:
        batch_op.drop_constraint("ck_user_workout_sets_kind", type_="check")
        batch_op.drop_column("reached_failure")
        batch_op.drop_column("set_kind")

    with op.batch_alter_table("user_workout_exercises") as batch_op:
        batch_op.drop_constraint(
            "uq_user_workout_exercises_superset_order", type_="unique"
        )
        batch_op.drop_constraint("ck_user_workout_exercises_superset", type_="check")
        batch_op.drop_column("superset_order")
        batch_op.drop_column("superset_group")

    with op.batch_alter_table("program_template_exercises") as batch_op:
        batch_op.drop_constraint(
            "uq_program_template_exercises_superset_order", type_="unique"
        )
        batch_op.drop_constraint("ck_program_template_exercises_superset", type_="check")
        batch_op.drop_column("superset_order")
        batch_op.drop_column("superset_group")
