"""Add server-side browser OAuth transactions.

Revision ID: 0070_browser_oauth_transactions
Revises: 0069_daily_wellbeing_check_ins
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0070_browser_oauth_transactions"
down_revision: str | None = "0069_daily_wellbeing_check_ins"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "expand"
online_rollout_notes = "Adds a short-lived server-side OAuth transaction table; existing browser sessions remain valid."


def upgrade() -> None:
    op.create_table(
        "oauth_transactions",
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("browser_marker_hash", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("purpose", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=256), nullable=False),
        sa.Column("redirect_uri", sa.String(length=512), nullable=False),
        sa.Column("next_path", sa.String(length=256), nullable=True),
        sa.Column("code_verifier", sa.String(length=256), nullable=True),
        sa.Column("nonce", sa.String(length=256), nullable=True),
        sa.Column("link_action_token_hash", sa.String(length=64), nullable=True),
        sa.Column("link_user_id", sa.Integer(), nullable=True),
        sa.Column("session_family_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.String(length=32), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('login', 'link')",
            name="ck_oauth_transactions_purpose",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'expired')",
            name="ck_oauth_transactions_status",
        ),
        sa.ForeignKeyConstraint(["link_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(
        "ix_oauth_transactions_browser_marker_hash",
        "oauth_transactions",
        ["browser_marker_hash"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_transactions_provider",
        "oauth_transactions",
        ["provider"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_transactions_state",
        "oauth_transactions",
        ["state"],
        unique=True,
    )
    op.create_index(
        "ix_oauth_transactions_link_user_id",
        "oauth_transactions",
        ["link_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_transactions_session_family_id",
        "oauth_transactions",
        ["session_family_id"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_transactions_expires_at",
        "oauth_transactions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_transactions_browser_provider",
        "oauth_transactions",
        ["browser_marker_hash", "provider", "purpose"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_transactions_expiry_status",
        "oauth_transactions",
        ["expires_at", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_oauth_transactions_expiry_status", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_browser_provider", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_expires_at", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_session_family_id", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_link_user_id", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_state", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_provider", table_name="oauth_transactions")
    op.drop_index("ix_oauth_transactions_browser_marker_hash", table_name="oauth_transactions")
    op.drop_table("oauth_transactions")
