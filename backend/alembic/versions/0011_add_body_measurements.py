"""add body measurements

Revision ID: 0011_add_body_measurements
Revises: 0010_optional_exercise_metadata
Create Date: 2026-05-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0011_add_body_measurements"
down_revision = "0010_optional_exercise_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "body_measurements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("measured_on", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("chest_cm", sa.Float(), nullable=True),
        sa.Column("waist_cm", sa.Float(), nullable=True),
        sa.Column("hips_cm", sa.Float(), nullable=True),
        sa.Column("biceps_cm", sa.Float(), nullable=True),
        sa.Column("thigh_cm", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "measured_on", name="uq_body_measurement_user_date"),
    )
    op.create_index("ix_body_measurements_user_id", "body_measurements", ["user_id"])
    op.create_index("ix_body_measurements_measured_on", "body_measurements", ["measured_on"])


def downgrade() -> None:
    op.drop_index("ix_body_measurements_measured_on", table_name="body_measurements")
    op.drop_index("ix_body_measurements_user_id", table_name="body_measurements")
    op.drop_table("body_measurements")
