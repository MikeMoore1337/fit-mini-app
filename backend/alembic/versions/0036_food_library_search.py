"""add personal food favorites and library query indexes

Revision ID: 0036_food_library_search
Revises: 0035_food_diary
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0036_food_library_search"
down_revision = "0035_food_diary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "foods",
        sa.Column(
            "search_text",
            sa.String(length=1024),
            server_default="",
            nullable=False,
        ),
    )
    op.execute(
        sa.text("UPDATE foods SET search_text = lower(trim(name || ' ' || coalesce(brand, '')))")
    )
    op.create_table(
        "food_favorites",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name="food_favorites_food_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="food_favorites_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "food_id", name="food_favorites_pkey"),
    )
    op.create_index(
        "ix_food_favorites_user_created",
        "food_favorites",
        ["user_id", "created_at", "food_id"],
    )
    op.create_index(
        "ix_food_diary_entries_user_food_updated",
        "food_diary_entries",
        ["user_id", "food_id", "updated_at"],
    )
    op.create_index(
        "ix_foods_status_type_name",
        "foods",
        ["status", "food_type", "name"],
    )


def downgrade() -> None:
    op.drop_index("ix_foods_status_type_name", table_name="foods")
    op.drop_index(
        "ix_food_diary_entries_user_food_updated",
        table_name="food_diary_entries",
    )
    op.drop_index("ix_food_favorites_user_created", table_name="food_favorites")
    op.drop_table("food_favorites")
    op.drop_column("foods", "search_text")
