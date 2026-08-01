"""add private coach-side client name

Revision ID: 0021_coach_client_private_name
Revises: 0020_query_performance_indexes
Create Date: 2026-08-01
"""

import sqlalchemy as sa

from alembic import op

revision = "0021_coach_client_private_name"
down_revision = "0020_query_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "coach_clients",
        sa.Column("private_name", sa.String(length=128), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE coach_clients
            SET private_name = (
                SELECT user_profiles.full_name
                FROM user_profiles
                WHERE user_profiles.user_id = coach_clients.client_user_id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("coach_clients", "private_name")
