"""add effective nutrition target history

Revision ID: 0055_nutrition_target_history
Revises: 0054_training_preferences
Create Date: 2026-08-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0055_nutrition_target_history"
down_revision = "0054_training_preferences"
branch_labels = None
depends_on = None


LEGACY_OPTIONAL_COLUMNS = {
    "sex": sa.String(length=16),
    "weight_kg": sa.Float(),
    "height_cm": sa.Float(),
    "age": sa.Float(),
    "daily_activity_level": sa.String(length=16),
    "daily_routine": sa.String(length=24),
    "steps_range": sa.String(length=32),
    "strength_trainings_per_week": sa.Integer(),
    "strength_training_duration_minutes": sa.Integer(),
    "strength_training_type": sa.String(length=16),
    "cardio_trainings_per_week": sa.Integer(),
    "cardio_training_duration_minutes": sa.Integer(),
    "cardio_intensity": sa.String(length=16),
    "cardio_trainings": sa.JSON(),
    "goal": sa.String(length=32),
    "bmr": sa.Integer(),
    "tdee": sa.Integer(),
}


def upgrade() -> None:
    with op.batch_alter_table("nutrition_targets") as batch_op:
        batch_op.add_column(sa.Column("effective_from", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("effective_to", sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(length=16),
                nullable=False,
                server_default="calculated",
            )
        )
        batch_op.add_column(sa.Column("note", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("superseded_by_id", sa.Integer(), nullable=True))

    # saved_at is already the account-local creation time. Its calendar date is the
    # only honest effective boundary available for existing rows; no earlier backfill
    # is invented.
    op.execute("UPDATE nutrition_targets SET effective_from = DATE(saved_at)")

    with op.batch_alter_table("nutrition_targets") as batch_op:
        batch_op.alter_column("effective_from", existing_type=sa.Date(), nullable=False)
        batch_op.alter_column(
            "source",
            existing_type=sa.String(length=16),
            nullable=False,
            server_default=None,
        )
        batch_op.drop_constraint("uq_nutrition_targets_user_id", type_="unique")
        batch_op.create_foreign_key(
            "fk_nutrition_targets_superseded_by",
            "nutrition_targets",
            ["superseded_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_check_constraint(
            "ck_nutrition_targets_source",
            "source IN ('calculated', 'manual', 'trainer', 'adaptive')",
        )
        batch_op.create_check_constraint(
            "ck_nutrition_targets_effective_period",
            "effective_to IS NULL OR effective_to >= effective_from",
        )
        batch_op.create_check_constraint(
            "ck_nutrition_targets_calories_positive",
            "calories > 0",
        )
        batch_op.create_check_constraint(
            "ck_nutrition_targets_protein_nonnegative",
            "protein_g >= 0",
        )
        batch_op.create_check_constraint(
            "ck_nutrition_targets_fat_nonnegative",
            "fat_g >= 0",
        )
        batch_op.create_check_constraint(
            "ck_nutrition_targets_carbs_nonnegative",
            "carbs_g >= 0",
        )
        for column_name, column_type in LEGACY_OPTIONAL_COLUMNS.items():
            batch_op.alter_column(column_name, existing_type=column_type, nullable=True)

    op.create_index(
        "uq_nutrition_targets_active_user",
        "nutrition_targets",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("effective_to IS NULL"),
        sqlite_where=sa.text("effective_to IS NULL"),
    )
    op.create_index(
        "ix_nutrition_targets_user_effective",
        "nutrition_targets",
        ["user_id", "effective_from", "effective_to"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    missing_legacy_context = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM nutrition_targets WHERE effective_to IS NULL AND ("
            + " OR ".join(f"{column_name} IS NULL" for column_name in LEGACY_OPTIONAL_COLUMNS)
            + ")"
        )
    ).scalar_one()
    if missing_legacy_context:
        raise RuntimeError(
            "Cannot downgrade nutrition target history while a manual-only current target "
            "has no legacy calculator context"
        )

    op.drop_index("ix_nutrition_targets_user_effective", table_name="nutrition_targets")
    op.drop_index("uq_nutrition_targets_active_user", table_name="nutrition_targets")
    # The previous schema can retain only the current row. Historical rows are
    # removed only during an explicit downgrade, never during normal operation.
    op.execute("DELETE FROM nutrition_targets WHERE effective_to IS NOT NULL")
    with op.batch_alter_table("nutrition_targets") as batch_op:
        batch_op.drop_constraint("ck_nutrition_targets_carbs_nonnegative", type_="check")
        batch_op.drop_constraint("ck_nutrition_targets_fat_nonnegative", type_="check")
        batch_op.drop_constraint("ck_nutrition_targets_protein_nonnegative", type_="check")
        batch_op.drop_constraint("ck_nutrition_targets_calories_positive", type_="check")
        batch_op.drop_constraint("ck_nutrition_targets_effective_period", type_="check")
        batch_op.drop_constraint("ck_nutrition_targets_source", type_="check")
        batch_op.drop_constraint("fk_nutrition_targets_superseded_by", type_="foreignkey")
        batch_op.create_unique_constraint("uq_nutrition_targets_user_id", ["user_id"])
        for column_name, column_type in LEGACY_OPTIONAL_COLUMNS.items():
            batch_op.alter_column(column_name, existing_type=column_type, nullable=False)
        batch_op.drop_column("superseded_by_id")
        batch_op.drop_column("note")
        batch_op.drop_column("source")
        batch_op.drop_column("effective_to")
        batch_op.drop_column("effective_from")
