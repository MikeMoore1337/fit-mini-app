"""add telegram id to coach client invites

Revision ID: 0012_coach_invite_telegram_id
Revises: 0011_add_body_measurements
Create Date: 2026-07-20
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_coach_invite_telegram_id"
down_revision = "0011_add_body_measurements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM coach_clients WHERE id NOT IN "
        "(SELECT MAX(id) FROM coach_clients GROUP BY client_user_id)"
    )
    op.create_unique_constraint(
        "uq_coach_clients_client_user_id",
        "coach_clients",
        ["client_user_id"],
    )
    op.add_column(
        "coach_client_invites",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_coach_client_invites_telegram_user_id",
        "coach_client_invites",
        ["telegram_user_id"],
    )
    op.create_unique_constraint(
        "uq_coach_client_invite_telegram_id",
        "coach_client_invites",
        ["coach_user_id", "telegram_user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_coach_client_invite_telegram_id",
        "coach_client_invites",
        type_="unique",
    )
    op.drop_index(
        "ix_coach_client_invites_telegram_user_id",
        table_name="coach_client_invites",
    )
    op.drop_column("coach_client_invites", "telegram_user_id")
    op.drop_constraint(
        "uq_coach_clients_client_user_id",
        "coach_clients",
        type_="unique",
    )
