"""add user profile timezone

Revision ID: 0009_add_user_timezone
Revises: 0008_business_time_msk
Create Date: 2026-04-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_add_user_timezone"
down_revision = "0008_business_time_msk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="Europe/Moscow",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "timezone")
