"""establish normalized food domain foundation

Revision ID: 0034_food_domain_foundation
Revises: 0033_auth_session_families
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0034_food_domain_foundation"
down_revision = "0033_auth_session_families"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("brand", sa.String(length=128), nullable=True),
        sa.Column("barcode", sa.String(length=14), nullable=True),
        sa.Column("energy_kcal_per_100g", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("protein_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("fat_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("carbs_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("fiber_g_per_100g", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("standard_serving_amount", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("standard_serving_unit", sa.String(length=16), nullable=True),
        sa.Column("standard_serving_weight_g", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("food_type", sa.String(length=16), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("provenance", sa.String(length=16), nullable=False),
        sa.Column("source_name", sa.String(length=64), nullable=True),
        sa.Column("source_version", sa.String(length=64), nullable=True),
        sa.Column("source_license", sa.String(length=128), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_license_url", sa.Text(), nullable=True),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("trust_level", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
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
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_foods_name_not_blank"),
        sa.CheckConstraint(
            "food_type IN ('system', 'branded', 'user')",
            name="ck_foods_food_type",
        ),
        sa.CheckConstraint(
            "provenance IN ('internal', 'external', 'user')",
            name="ck_foods_provenance",
        ),
        sa.CheckConstraint(
            "trust_level IN ('verified', 'unverified')",
            name="ck_foods_trust_level",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'disabled')",
            name="ck_foods_status",
        ),
        sa.CheckConstraint(
            "(food_type = 'user' AND owner_user_id IS NOT NULL AND provenance = 'user') "
            "OR (food_type <> 'user' AND owner_user_id IS NULL AND provenance <> 'user')",
            name="ck_foods_owner_scope",
        ),
        sa.CheckConstraint(
            "food_type = 'user' OR "
            "(source_name IS NOT NULL AND length(trim(source_name)) > 0)",
            name="ck_foods_catalog_source",
        ),
        sa.CheckConstraint(
            "provenance <> 'external' OR "
            "(source_name IS NOT NULL AND length(trim(source_name)) > 0 "
            "AND external_id IS NOT NULL AND length(trim(external_id)) > 0 "
            "AND source_license IS NOT NULL AND length(trim(source_license)) > 0 "
            "AND source_url IS NOT NULL AND length(trim(source_url)) > 0 "
            "AND source_license_url IS NOT NULL AND length(trim(source_license_url)) > 0)",
            name="ck_foods_external_source",
        ),
        sa.CheckConstraint(
            "barcode IS NULL OR length(barcode) IN (8, 12, 13, 14)",
            name="ck_foods_barcode_length",
        ),
        sa.CheckConstraint(
            "standard_serving_amount IS NULL AND standard_serving_unit IS NULL "
            "AND standard_serving_weight_g IS NULL OR "
            "standard_serving_amount > 0 AND "
            "standard_serving_unit IN ('g', 'ml', 'piece', 'serving') AND "
            "standard_serving_weight_g > 0",
            name="ck_foods_standard_serving_complete",
        ),
        sa.CheckConstraint(
            "standard_serving_unit IS NULL OR standard_serving_unit <> 'g' "
            "OR standard_serving_amount = standard_serving_weight_g",
            name="ck_foods_gram_serving_weight",
        ),
        sa.CheckConstraint(
            "energy_kcal_per_100g IS NULL OR energy_kcal_per_100g BETWEEN 0 AND 1000",
            name="ck_foods_energy_non_negative",
        ),
        sa.CheckConstraint(
            "protein_g_per_100g IS NULL OR protein_g_per_100g BETWEEN 0 AND 100",
            name="ck_foods_protein_range",
        ),
        sa.CheckConstraint(
            "fat_g_per_100g IS NULL OR fat_g_per_100g BETWEEN 0 AND 100",
            name="ck_foods_fat_range",
        ),
        sa.CheckConstraint(
            "carbs_g_per_100g IS NULL OR carbs_g_per_100g BETWEEN 0 AND 100",
            name="ck_foods_carbs_range",
        ),
        sa.CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g BETWEEN 0 AND 100",
            name="ck_foods_fiber_range",
        ),
        sa.CheckConstraint(
            "status <> 'active' OR (energy_kcal_per_100g IS NOT NULL "
            "AND protein_g_per_100g IS NOT NULL AND fat_g_per_100g IS NOT NULL "
            "AND carbs_g_per_100g IS NOT NULL)",
            name="ck_foods_active_nutrients",
        ),
        sa.CheckConstraint(
            "food_type = 'user' OR status <> 'active' OR trust_level = 'verified'",
            name="ck_foods_active_catalog_trust",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name="foods_owner_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="foods_pkey"),
    )
    op.create_index("ix_foods_owner_status", "foods", ["owner_user_id", "status"])
    op.create_index(
        "uq_foods_catalog_barcode",
        "foods",
        ["barcode"],
        unique=True,
        postgresql_where=sa.text("barcode IS NOT NULL AND food_type <> 'user'"),
        sqlite_where=sa.text("barcode IS NOT NULL AND food_type <> 'user'"),
    )
    op.create_index(
        "uq_foods_user_barcode",
        "foods",
        ["owner_user_id", "barcode"],
        unique=True,
        postgresql_where=sa.text("barcode IS NOT NULL AND food_type = 'user'"),
        sqlite_where=sa.text("barcode IS NOT NULL AND food_type = 'user'"),
    )
    op.create_index(
        "uq_foods_external_source_id",
        "foods",
        ["source_name", "external_id"],
        unique=True,
        postgresql_where=sa.text("provenance = 'external'"),
        sqlite_where=sa.text("provenance = 'external'"),
    )


def downgrade() -> None:
    op.drop_index("uq_foods_external_source_id", table_name="foods")
    op.drop_index("uq_foods_user_barcode", table_name="foods")
    op.drop_index("uq_foods_catalog_barcode", table_name="foods")
    op.drop_index("ix_foods_owner_status", table_name="foods")
    op.drop_table("foods")
