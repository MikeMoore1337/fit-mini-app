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
    with op.batch_alter_table("coach_clients") as batch_op:
        batch_op.create_unique_constraint(
            "uq_coach_clients_client_user_id",
            ["client_user_id"],
        )
    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.add_column(
            sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        )
        batch_op.create_index(
            "ix_coach_client_invites_telegram_user_id",
            ["telegram_user_id"],
        )
        batch_op.create_unique_constraint(
            "uq_coach_client_invite_telegram_id",
            ["coach_user_id", "telegram_user_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.drop_constraint(
            "uq_coach_client_invite_telegram_id",
            type_="unique",
        )
        batch_op.drop_index("ix_coach_client_invites_telegram_user_id")
        batch_op.drop_column("telegram_user_id")
    with op.batch_alter_table("coach_clients") as batch_op:
        batch_op.drop_constraint(
            "uq_coach_clients_client_user_id",
            type_="unique",
        )
