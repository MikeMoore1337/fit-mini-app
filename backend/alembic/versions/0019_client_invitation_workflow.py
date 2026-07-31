"""add client codes, request lifecycle and relation history

Revision ID: 0019_client_invitation_workflow
Revises: 0018_exercise_difficulty
Create Date: 2026-07-31
"""

import secrets
from datetime import datetime

import sqlalchemy as sa

from alembic import op

revision = "0019_client_invitation_workflow"
down_revision = "0018_exercise_difficulty"
branch_labels = None
depends_on = None

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _new_code(existing: set[str]) -> str:
    while True:
        raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(7))
        code = f"{raw[:4]}-{raw[4:]}"
        if code not in existing:
            existing.add(code)
            return code


def upgrade() -> None:
    op.add_column("users", sa.Column("photo_url", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("client_code", sa.String(length=8), nullable=True))
    existing: set[str] = set()
    connection = op.get_bind()
    for user_id in connection.execute(sa.text("SELECT id FROM users")).scalars():
        connection.execute(
            sa.text("UPDATE users SET client_code = :code WHERE id = :user_id"),
            {"code": _new_code(existing), "user_id": user_id},
        )
    op.create_index("ix_users_client_code", "users", ["client_code"], unique=True)

    op.drop_constraint("uq_coach_client", "coach_clients", type_="unique")
    op.drop_constraint("uq_coach_clients_client_user_id", "coach_clients", type_="unique")
    op.add_column(
        "coach_clients",
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
    )
    op.add_column("coach_clients", sa.Column("accepted_at", sa.DateTime(), nullable=True))
    op.add_column("coach_clients", sa.Column("ended_at", sa.DateTime(), nullable=True))
    op.add_column("coach_clients", sa.Column("ended_reason", sa.String(length=64), nullable=True))
    connection.execute(
        sa.text("UPDATE coach_clients SET accepted_at = COALESCE(created_at, :now)"),
        {"now": datetime.now()},
    )
    op.create_index(
        "uq_coach_clients_one_active_per_client",
        "coach_clients",
        ["client_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )

    op.drop_constraint("uq_coach_client_invite_username", "coach_client_invites", type_="unique")
    op.drop_constraint("uq_coach_client_invite_telegram_id", "coach_client_invites", type_="unique")
    op.alter_column(
        "coach_client_invites", "username", existing_type=sa.String(length=64), nullable=True
    )
    op.add_column(
        "coach_client_invites",
        sa.Column("client_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_coach_client_invites_client_user_id_users",
        "coach_client_invites",
        "users",
        ["client_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_coach_client_invites_client_user_id",
        "coach_client_invites",
        ["client_user_id"],
    )
    op.add_column(
        "coach_client_invites", sa.Column("token_hash", sa.String(length=64), nullable=True)
    )
    op.create_index(
        "ix_coach_client_invites_token_hash",
        "coach_client_invites",
        ["token_hash"],
        unique=True,
    )
    op.add_column(
        "coach_client_invites",
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="username_search",
        ),
    )
    op.add_column(
        "coach_client_invites",
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
    )
    op.add_column("coach_client_invites", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("coach_client_invites", sa.Column("accepted_at", sa.DateTime(), nullable=True))
    op.add_column("coach_client_invites", sa.Column("declined_at", sa.DateTime(), nullable=True))
    connection.execute(
        sa.text(
            """
            UPDATE coach_client_invites
            SET client_user_id = (
                SELECT users.id FROM users
                WHERE users.telegram_user_id = coach_client_invites.telegram_user_id
            )
            WHERE telegram_user_id IS NOT NULL
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE coach_client_invites
            SET status = 'revoked'
            WHERE client_user_id IS NOT NULL
              AND id NOT IN (
                  SELECT MAX(id)
                  FROM coach_client_invites
                  WHERE client_user_id IS NOT NULL
                  GROUP BY coach_user_id, client_user_id
              )
            """
        )
    )
    op.create_index(
        "uq_coach_client_invites_pending_pair",
        "coach_client_invites",
        ["coach_user_id", "client_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending' AND client_user_id IS NOT NULL"),
        sqlite_where=sa.text("status = 'pending' AND client_user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_coach_client_invites_pending_pair", table_name="coach_client_invites")
    op.drop_column("coach_client_invites", "declined_at")
    op.drop_column("coach_client_invites", "accepted_at")
    op.drop_column("coach_client_invites", "expires_at")
    op.drop_column("coach_client_invites", "status")
    op.drop_column("coach_client_invites", "source")
    op.drop_index("ix_coach_client_invites_token_hash", table_name="coach_client_invites")
    op.drop_column("coach_client_invites", "token_hash")
    op.drop_index("ix_coach_client_invites_client_user_id", table_name="coach_client_invites")
    op.drop_constraint(
        "fk_coach_client_invites_client_user_id_users",
        "coach_client_invites",
        type_="foreignkey",
    )
    op.drop_column("coach_client_invites", "client_user_id")
    op.execute("DELETE FROM coach_client_invites WHERE username IS NULL")
    op.execute(
        """
        DELETE FROM coach_client_invites
        WHERE id NOT IN (
            SELECT MAX(id) FROM coach_client_invites GROUP BY coach_user_id, username
        )
        """
    )
    op.execute(
        """
        DELETE FROM coach_client_invites
        WHERE telegram_user_id IS NOT NULL
          AND id NOT IN (
              SELECT MAX(id)
              FROM coach_client_invites
              WHERE telegram_user_id IS NOT NULL
              GROUP BY coach_user_id, telegram_user_id
          )
        """
    )
    op.alter_column(
        "coach_client_invites", "username", existing_type=sa.String(length=64), nullable=False
    )
    op.create_unique_constraint(
        "uq_coach_client_invite_telegram_id",
        "coach_client_invites",
        ["coach_user_id", "telegram_user_id"],
    )
    op.create_unique_constraint(
        "uq_coach_client_invite_username",
        "coach_client_invites",
        ["coach_user_id", "username"],
    )

    op.drop_index("uq_coach_clients_one_active_per_client", table_name="coach_clients")
    op.drop_column("coach_clients", "ended_reason")
    op.drop_column("coach_clients", "ended_at")
    op.drop_column("coach_clients", "accepted_at")
    op.drop_column("coach_clients", "status")
    op.create_unique_constraint(
        "uq_coach_clients_client_user_id", "coach_clients", ["client_user_id"]
    )
    op.create_unique_constraint(
        "uq_coach_client", "coach_clients", ["coach_user_id", "client_user_id"]
    )

    op.drop_index("ix_users_client_code", table_name="users")
    op.drop_column("users", "client_code")
    op.drop_column("users", "photo_url")
