"""add coach client invites

Revision ID: 0006_add_coach_client_invites
Revises: 0005_users_telegram_id_bigint
Create Date: 2026-04-24
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_add_coach_client_invites"
down_revision = "0005_users_telegram_id_bigint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coach_client_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("coach_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint(
            "coach_user_id",
            "username",
            name="uq_coach_client_invite_username",
        ),
    )


def downgrade() -> None:
    op.drop_table("coach_client_invites")
