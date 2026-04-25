"""add nutrition targets

Revision ID: 0007_add_nutrition_targets
Revises: 0006_add_coach_client_invites
Create Date: 2026-04-25
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_add_nutrition_targets"
down_revision = "0006_add_coach_client_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nutrition_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sex", sa.String(length=16), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("age", sa.Float(), nullable=False),
        sa.Column("strength_trainings_per_week", sa.Integer(), nullable=False),
        sa.Column("cardio_trainings_per_week", sa.Integer(), nullable=False),
        sa.Column("goal", sa.String(length=32), nullable=False),
        sa.Column("bmr", sa.Integer(), nullable=False),
        sa.Column("tdee", sa.Integer(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Integer(), nullable=False),
        sa.Column("fat_g", sa.Integer(), nullable=False),
        sa.Column("carbs_g", sa.Integer(), nullable=False),
        sa.Column("saved_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", name="uq_nutrition_targets_user_id"),
    )


def downgrade() -> None:
    op.drop_table("nutrition_targets")
