"""add coach role applications

Revision ID: 0032_coach_role_applications
Revises: 0031_profile_resting_heart_rate
Create Date: 2026-08-13
"""

import sqlalchemy as sa

from alembic import op

revision = "0032_coach_role_applications"
down_revision = "0031_profile_resting_heart_rate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coach_role_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("source", sa.String(length=16), server_default="web", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "source IN ('web', 'telegram')",
            name="ck_coach_role_applications_source",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="ck_coach_role_applications_status",
        ),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coach_role_applications_user_id",
        "coach_role_applications",
        ["user_id"],
    )
    op.create_index(
        "uq_coach_role_applications_pending_user",
        "coach_role_applications",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_coach_role_applications_pending_user",
        table_name="coach_role_applications",
    )
    op.drop_index("ix_coach_role_applications_user_id", table_name="coach_role_applications")
    op.drop_table("coach_role_applications")
