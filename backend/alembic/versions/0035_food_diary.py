"""add private food diary entries

Revision ID: 0035_food_diary
Revises: 0034_food_domain_foundation
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0035_food_diary"
down_revision = "0034_food_domain_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "food_diary_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=True),
        sa.Column("diary_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("amount_unit", sa.String(length=16), nullable=False),
        sa.Column("weight_g", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("food_name", sa.String(length=256), nullable=False),
        sa.Column("food_brand", sa.String(length=128), nullable=True),
        sa.Column("energy_kcal_per_100g", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("protein_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("fat_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("carbs_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("fiber_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("serving_amount", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("serving_unit", sa.String(length=16), nullable=True),
        sa.Column("serving_weight_g", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snacks')",
            name="ck_food_diary_entries_meal_type",
        ),
        sa.CheckConstraint(
            "amount_unit IN ('g', 'serving')",
            name="ck_food_diary_entries_amount_unit",
        ),
        sa.CheckConstraint("amount > 0", name="ck_food_diary_entries_amount_positive"),
        sa.CheckConstraint("weight_g > 0", name="ck_food_diary_entries_weight_positive"),
        sa.CheckConstraint(
            "amount_unit <> 'g' OR amount = weight_g",
            name="ck_food_diary_entries_gram_amount_weight",
        ),
        sa.CheckConstraint(
            "serving_amount IS NULL AND serving_unit IS NULL AND serving_weight_g IS NULL OR "
            "serving_amount > 0 AND serving_unit IN ('g', 'ml', 'piece', 'serving') AND "
            "serving_weight_g > 0",
            name="ck_food_diary_entries_serving_complete",
        ),
        sa.CheckConstraint(
            "energy_kcal_per_100g BETWEEN 0 AND 1000",
            name="ck_food_diary_entries_energy_range",
        ),
        sa.CheckConstraint(
            "protein_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_protein_range",
        ),
        sa.CheckConstraint(
            "fat_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_fat_range",
        ),
        sa.CheckConstraint(
            "carbs_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_carbs_range",
        ),
        sa.CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_fiber_range",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"], name="food_diary_entries_food_id_fkey", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="food_diary_entries_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="food_diary_entries_pkey"),
    )
    op.create_index(
        "ix_food_diary_entries_user_date_meal",
        "food_diary_entries",
        ["user_id", "diary_date", "meal_type", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_food_diary_entries_user_date_meal", table_name="food_diary_entries")
    op.drop_table("food_diary_entries")
