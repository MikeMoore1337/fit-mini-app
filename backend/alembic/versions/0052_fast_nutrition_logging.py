"""add fast nutrition logging and explicit diary completeness

Revision ID: 0052_fast_nutrition_logging
Revises: 0051_bot_support_cases
Create Date: 2026-08-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0052_fast_nutrition_logging"
down_revision = "0051_bot_support_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("food_diary_entries") as batch_op:
        batch_op.add_column(sa.Column("logged_at", sa.Time(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "entry_kind",
                sa.String(length=16),
                nullable=False,
                server_default="food",
            )
        )
        batch_op.add_column(
            sa.Column("quick_energy_kcal", sa.Numeric(precision=10, scale=2), nullable=True)
        )
        batch_op.add_column(
            sa.Column("quick_protein_g", sa.Numeric(precision=8, scale=3), nullable=True)
        )
        batch_op.add_column(
            sa.Column("quick_fat_g", sa.Numeric(precision=8, scale=3), nullable=True)
        )
        batch_op.add_column(
            sa.Column("quick_carbs_g", sa.Numeric(precision=8, scale=3), nullable=True)
        )
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("request_fingerprint", sa.String(length=64), nullable=True))
        batch_op.create_check_constraint(
            "ck_food_diary_entries_kind",
            "entry_kind IN ('food', 'recipe', 'quick_add')",
        )
        batch_op.create_check_constraint(
            "ck_food_diary_entries_quick_source",
            "entry_kind <> 'quick_add' OR (food_id IS NULL AND recipe_id IS NULL)",
        )
        batch_op.create_check_constraint(
            "ck_food_diary_entries_quick_nutrition",
            "(entry_kind = 'quick_add' AND quick_energy_kcal IS NOT NULL) OR "
            "(entry_kind <> 'quick_add' AND quick_energy_kcal IS NULL AND "
            "quick_protein_g IS NULL AND quick_fat_g IS NULL AND quick_carbs_g IS NULL)",
        )
        batch_op.create_check_constraint(
            "ck_food_diary_entries_quick_macros_complete",
            "(quick_protein_g IS NULL AND quick_fat_g IS NULL AND quick_carbs_g IS NULL) OR "
            "(quick_protein_g IS NOT NULL AND quick_fat_g IS NOT NULL AND "
            "quick_carbs_g IS NOT NULL)",
        )
        for name, column, maximum in (
            ("energy", "quick_energy_kcal", 10000),
            ("protein", "quick_protein_g", 1000),
            ("fat", "quick_fat_g", 1000),
            ("carbs", "quick_carbs_g", 1000),
        ):
            batch_op.create_check_constraint(
                f"ck_food_diary_entries_quick_{name}_range",
                (
                    f"{column} IS NULL OR {column} > 0 AND {column} <= {maximum}"
                    if name == "energy"
                    else f"{column} IS NULL OR {column} BETWEEN 0 AND {maximum}"
                ),
            )
        batch_op.create_check_constraint(
            "ck_food_diary_entries_idempotency_pair",
            "(idempotency_key IS NULL AND request_fingerprint IS NULL) OR "
            "(idempotency_key IS NOT NULL AND request_fingerprint IS NOT NULL)",
        )
        batch_op.create_unique_constraint(
            "uq_food_diary_entries_user_idempotency",
            ["user_id", "idempotency_key"],
        )
    op.execute("UPDATE food_diary_entries SET entry_kind = 'recipe' WHERE recipe_id IS NOT NULL")
    with op.batch_alter_table("food_diary_entries") as batch_op:
        batch_op.alter_column("entry_kind", server_default=None)

    op.create_table(
        "food_diary_day_statuses",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("diary_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('complete', 'incomplete', 'fasted')",
            name="ck_food_diary_day_statuses_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "diary_date"),
    )
    op.create_index(
        "ix_food_diary_day_statuses_user_status_date",
        "food_diary_day_statuses",
        ["user_id", "status", "diary_date"],
    )

    # Existing searchable rows are normalized without inventing new catalog records.
    op.execute("UPDATE foods SET search_text = replace(search_text, 'ё', 'е')")


def downgrade() -> None:
    op.drop_index(
        "ix_food_diary_day_statuses_user_status_date",
        table_name="food_diary_day_statuses",
    )
    op.drop_table("food_diary_day_statuses")
    with op.batch_alter_table("food_diary_entries") as batch_op:
        batch_op.drop_constraint(
            "uq_food_diary_entries_user_idempotency",
            type_="unique",
        )
        batch_op.drop_constraint(
            "ck_food_diary_entries_idempotency_pair",
            type_="check",
        )
        for name in ("carbs", "fat", "protein", "energy"):
            batch_op.drop_constraint(
                f"ck_food_diary_entries_quick_{name}_range",
                type_="check",
            )
        batch_op.drop_constraint("ck_food_diary_entries_quick_nutrition", type_="check")
        batch_op.drop_constraint(
            "ck_food_diary_entries_quick_macros_complete",
            type_="check",
        )
        batch_op.drop_constraint("ck_food_diary_entries_quick_source", type_="check")
        batch_op.drop_constraint("ck_food_diary_entries_kind", type_="check")
        batch_op.drop_column("request_fingerprint")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("quick_carbs_g")
        batch_op.drop_column("quick_fat_g")
        batch_op.drop_column("quick_protein_g")
        batch_op.drop_column("quick_energy_kcal")
        batch_op.drop_column("entry_kind")
        batch_op.drop_column("logged_at")
