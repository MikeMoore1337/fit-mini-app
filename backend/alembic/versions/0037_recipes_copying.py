"""add private recipes and idempotent diary copying

Revision ID: 0037_recipes_copying
Revises: 0036_food_library_search
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0037_recipes_copying"
down_revision = "0036_food_library_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("final_weight_g", sa.Numeric(precision=10, scale=3), nullable=True),
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
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_recipes_name_not_blank"),
        sa.CheckConstraint(
            "final_weight_g IS NULL OR final_weight_g > 0",
            name="ck_recipes_final_weight_positive",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name="recipes_owner_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="recipes_pkey"),
    )
    op.create_index(
        "ix_recipes_owner_updated",
        "recipes",
        ["owner_user_id", "updated_at", "id"],
    )
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(
            "position >= 0",
            name="ck_recipe_ingredients_position_non_negative",
        ),
        sa.CheckConstraint(
            "amount_unit IN ('g', 'serving')",
            name="ck_recipe_ingredients_amount_unit",
        ),
        sa.CheckConstraint("amount > 0", name="ck_recipe_ingredients_amount_positive"),
        sa.CheckConstraint("weight_g > 0", name="ck_recipe_ingredients_weight_positive"),
        sa.CheckConstraint(
            "amount_unit <> 'g' OR amount = weight_g",
            name="ck_recipe_ingredients_gram_amount_weight",
        ),
        sa.CheckConstraint(
            "serving_amount IS NULL AND serving_unit IS NULL AND serving_weight_g IS NULL OR "
            "serving_amount > 0 AND serving_unit IN ('g', 'ml', 'piece', 'serving') AND "
            "serving_weight_g > 0",
            name="ck_recipe_ingredients_serving_complete",
        ),
        sa.CheckConstraint(
            "energy_kcal_per_100g BETWEEN 0 AND 1000",
            name="ck_recipe_ingredients_energy_range",
        ),
        sa.CheckConstraint(
            "protein_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_protein_range",
        ),
        sa.CheckConstraint(
            "fat_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_fat_range",
        ),
        sa.CheckConstraint(
            "carbs_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_carbs_range",
        ),
        sa.CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_fiber_range",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name="recipe_ingredients_food_id_fkey",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name="recipe_ingredients_recipe_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="recipe_ingredients_pkey"),
        sa.UniqueConstraint(
            "recipe_id",
            "position",
            name="uq_recipe_ingredients_position",
        ),
    )
    op.create_index(
        "ix_recipe_ingredients_recipe_position",
        "recipe_ingredients",
        ["recipe_id", "position"],
    )
    op.create_table(
        "food_diary_copy_operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("copy_scope", sa.String(length=16), nullable=False),
        sa.Column("source_entry_id", sa.Integer(), nullable=True),
        sa.Column("source_date", sa.Date(), nullable=False),
        sa.Column("source_meal_type", sa.String(length=16), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("target_meal_type", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "copy_scope IN ('product', 'meal', 'day')",
            name="ck_food_diary_copy_operations_scope",
        ),
        sa.CheckConstraint(
            "source_meal_type IS NULL OR "
            "source_meal_type IN ('breakfast', 'lunch', 'dinner', 'snacks')",
            name="ck_food_diary_copy_operations_source_meal",
        ),
        sa.CheckConstraint(
            "target_meal_type IS NULL OR "
            "target_meal_type IN ('breakfast', 'lunch', 'dinner', 'snacks')",
            name="ck_food_diary_copy_operations_target_meal",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="food_diary_copy_operations_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="food_diary_copy_operations_pkey"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_food_diary_copy_operations_user_key",
        ),
    )
    with op.batch_alter_table("food_diary_entries") as batch_op:
        batch_op.add_column(sa.Column("recipe_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("copy_operation_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("copied_from_entry_id", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_food_diary_entries_single_source",
            "NOT (food_id IS NOT NULL AND recipe_id IS NOT NULL)",
        )
        batch_op.create_foreign_key(
            "food_diary_entries_recipe_id_fkey",
            "recipes",
            ["recipe_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "food_diary_entries_copy_operation_id_fkey",
            "food_diary_copy_operations",
            ["copy_operation_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "food_diary_entries_copied_from_entry_id_fkey",
            "food_diary_entries",
            ["copied_from_entry_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_food_diary_entries_copy_operation",
        "food_diary_entries",
        ["copy_operation_id", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_food_diary_entries_copy_operation", table_name="food_diary_entries")
    with op.batch_alter_table("food_diary_entries") as batch_op:
        batch_op.drop_constraint(
            "food_diary_entries_copied_from_entry_id_fkey",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "food_diary_entries_copy_operation_id_fkey",
            type_="foreignkey",
        )
        batch_op.drop_constraint("food_diary_entries_recipe_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("ck_food_diary_entries_single_source", type_="check")
        batch_op.drop_column("copied_from_entry_id")
        batch_op.drop_column("copy_operation_id")
        batch_op.drop_column("recipe_id")
    op.drop_table("food_diary_copy_operations")
    op.drop_index("ix_recipe_ingredients_recipe_position", table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_index("ix_recipes_owner_updated", table_name="recipes")
    op.drop_table("recipes")
