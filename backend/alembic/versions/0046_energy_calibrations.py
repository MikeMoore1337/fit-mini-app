"""add adaptive energy calibration history

Revision ID: 0046_energy_calibrations
Revises: 0045_body_priorities
Create Date: 2026-08-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0046_energy_calibrations"
down_revision = "0045_body_priorities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "energy_calibrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ruleset_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("sufficiency_status", sa.String(length=16), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("goal", sa.String(length=32), nullable=False),
        sa.Column("logged_day_count", sa.Integer(), nullable=False),
        sa.Column("eligible_day_count", sa.Integer(), nullable=False),
        sa.Column("weight_point_count", sa.Integer(), nullable=False),
        sa.Column("weight_span_days", sa.Integer(), nullable=False),
        sa.Column("average_intake_kcal", sa.Integer(), nullable=False),
        sa.Column("smoothed_start_weight_kg", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("smoothed_end_weight_kg", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("estimated_expenditure_kcal", sa.Integer(), nullable=False),
        sa.Column("estimate_low_kcal", sa.Integer(), nullable=False),
        sa.Column("estimate_high_kcal", sa.Integer(), nullable=False),
        sa.Column("previous_target_calories", sa.Integer(), nullable=False),
        sa.Column("previous_target_saved_at", sa.DateTime(), nullable=False),
        sa.Column("proposed_target_calories", sa.Integer(), nullable=True),
        sa.Column("sufficiency_counters", sa.JSON(), nullable=False),
        sa.Column("sufficiency_reason_keys", sa.JSON(), nullable=False),
        sa.Column("rationale_keys", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('limited', 'no_change', 'pending', 'accepted', 'rejected', "
            "'superseded')",
            name="ck_energy_calibrations_status",
        ),
        sa.CheckConstraint(
            "sufficiency_status IN ('limited', 'sufficient')",
            name="ck_energy_calibrations_sufficiency_status",
        ),
        sa.CheckConstraint(
            "period_end >= period_start",
            name="ck_energy_calibrations_period",
        ),
        sa.CheckConstraint(
            "estimate_low_kcal <= estimated_expenditure_kcal AND "
            "estimated_expenditure_kcal <= estimate_high_kcal",
            name="ck_energy_calibrations_estimate_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_energy_calibrations_user_created",
        "energy_calibrations",
        ["user_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_energy_calibrations_user_created", table_name="energy_calibrations")
    op.drop_table("energy_calibrations")
