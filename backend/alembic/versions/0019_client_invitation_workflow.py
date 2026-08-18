"""add client codes, request lifecycle and relation history

Revision ID: 0019_client_invitation_workflow
Revises: 0018_exercise_difficulty
Create Date: 2026-07-31
"""

import secrets

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

    with op.batch_alter_table("coach_clients") as batch_op:
        batch_op.drop_constraint("uq_coach_client", type_="unique")
        batch_op.drop_constraint("uq_coach_clients_client_user_id", type_="unique")
        batch_op.add_column(
            sa.Column("status", sa.String(length=16), nullable=False, server_default="active")
        )
        batch_op.add_column(sa.Column("accepted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("ended_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("ended_reason", sa.String(length=64), nullable=True))
    connection.execute(
        sa.text("UPDATE coach_clients SET accepted_at = COALESCE(created_at, CURRENT_TIMESTAMP)")
    )
    op.create_index(
        "uq_coach_clients_one_active_per_client",
        "coach_clients",
        ["client_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )

    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.drop_constraint("uq_coach_client_invite_username", type_="unique")
        batch_op.drop_constraint("uq_coach_client_invite_telegram_id", type_="unique")
        batch_op.alter_column("username", existing_type=sa.String(length=64), nullable=True)
        batch_op.add_column(sa.Column("client_user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_coach_client_invites_client_user_id_users",
            "users",
            ["client_user_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_coach_client_invites_client_user_id",
            ["client_user_id"],
        )
        batch_op.add_column(sa.Column("token_hash", sa.String(length=64), nullable=True))
        batch_op.create_index(
            "ix_coach_client_invites_token_hash",
            ["token_hash"],
            unique=True,
        )
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(length=32),
                nullable=False,
                server_default="username_search",
            )
        )
        batch_op.add_column(
            sa.Column("status", sa.String(length=16), nullable=False, server_default="pending")
        )
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("accepted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("declined_at", sa.DateTime(), nullable=True))
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
    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.drop_column("declined_at")
        batch_op.drop_column("accepted_at")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("status")
        batch_op.drop_column("source")
        batch_op.drop_index("ix_coach_client_invites_token_hash")
        batch_op.drop_column("token_hash")
        batch_op.drop_index("ix_coach_client_invites_client_user_id")
        batch_op.drop_constraint(
            "fk_coach_client_invites_client_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("client_user_id")
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
    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.alter_column("username", existing_type=sa.String(length=64), nullable=False)
        batch_op.create_unique_constraint(
            "uq_coach_client_invite_telegram_id",
            ["coach_user_id", "telegram_user_id"],
        )
        batch_op.create_unique_constraint(
            "uq_coach_client_invite_username",
            ["coach_user_id", "username"],
        )

    op.drop_index("uq_coach_clients_one_active_per_client", table_name="coach_clients")
    with op.batch_alter_table("coach_clients") as batch_op:
        batch_op.drop_column("ended_reason")
        batch_op.drop_column("ended_at")
        batch_op.drop_column("accepted_at")
        batch_op.drop_column("status")
        batch_op.create_unique_constraint("uq_coach_clients_client_user_id", ["client_user_id"])
        batch_op.create_unique_constraint("uq_coach_client", ["coach_user_id", "client_user_id"])

    op.drop_index("ix_users_client_code", table_name="users")
    op.drop_column("users", "client_code")
    op.drop_column("users", "photo_url")
