"""add local credentials and allow users without Telegram

Revision ID: 0030_local_credentials
Revises: 0029_auth_identities
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0030_local_credentials"
down_revision = "0029_auth_identities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "telegram_user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.create_table(
        "local_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username_normalized", sa.String(length=32), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "password_changed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_local_credentials_user_id", "local_credentials", ["user_id"], unique=True
    )
    op.create_index(
        "ix_local_credentials_username_normalized",
        "local_credentials",
        ["username_normalized"],
        unique=True,
    )
    op.create_table(
        "auth_action_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auth_action_tokens_expires_at", "auth_action_tokens", ["expires_at"], unique=False
    )
    op.create_index(
        "ix_auth_action_tokens_purpose", "auth_action_tokens", ["purpose"], unique=False
    )
    op.create_index(
        "ix_auth_action_tokens_token_hash", "auth_action_tokens", ["token_hash"], unique=True
    )
    op.create_index(
        "ix_auth_action_tokens_user_id", "auth_action_tokens", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_auth_action_tokens_user_id", table_name="auth_action_tokens")
    op.drop_index("ix_auth_action_tokens_token_hash", table_name="auth_action_tokens")
    op.drop_index("ix_auth_action_tokens_purpose", table_name="auth_action_tokens")
    op.drop_index("ix_auth_action_tokens_expires_at", table_name="auth_action_tokens")
    op.drop_table("auth_action_tokens")
    op.drop_index(
        "ix_local_credentials_username_normalized", table_name="local_credentials"
    )
    op.drop_index("ix_local_credentials_user_id", table_name="local_credentials")
    op.drop_table("local_credentials")
    op.alter_column(
        "users",
        "telegram_user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
