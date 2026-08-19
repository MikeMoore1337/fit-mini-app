"""add structured body development priorities

Revision ID: 0045_body_priorities
Revises: 0044_program_versions
Create Date: 2026-08-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0045_body_priorities"
down_revision = "0044_program_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.add_column(sa.Column("body_priority_mode", sa.String(length=16), nullable=True))
        batch_op.create_check_constraint(
            "ck_user_profiles_body_priority_mode",
            "body_priority_mode IS NULL OR body_priority_mode IN ('balanced', 'muscle_groups')",
        )

    op.create_table(
        "user_profile_priority_muscles",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "position >= 0",
            name="ck_user_profile_priority_muscle_position",
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_id"], ["muscles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint(
            "profile_id",
            "muscle_id",
            name="user_profile_priority_muscles_pkey",
        ),
        sa.UniqueConstraint(
            "profile_id",
            "position",
            name="uq_user_profile_priority_muscle_position",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_profile_priority_muscles")
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_constraint("ck_user_profiles_body_priority_mode", type_="check")
        batch_op.drop_column("body_priority_mode")
