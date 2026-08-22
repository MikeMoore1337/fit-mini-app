"""add minimal Telegram bot support case routing metadata

Revision ID: 0051_bot_support_cases
Revises: 0050_comment_idempotency
Create Date: 2026-08-22
"""

import sqlalchemy as sa

from alembic import op

revision = "0051_bot_support_cases"
down_revision = "0050_comment_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bot_support_cases",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("request_message_id", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("reply_admin_telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("reply_message_id", sa.BigInteger(), nullable=True),
        sa.Column("reply_claimed_at", sa.DateTime(), nullable=True),
        sa.Column("replied_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "category IN ('bug', 'account', 'idea', 'contact', 'other')",
            name="ck_bot_support_cases_category",
        ),
        sa.CheckConstraint(
            "status IN ('pending_relay', 'open', 'replying', 'replied', "
            "'relay_failed', 'undeliverable', 'expired')",
            name="ck_bot_support_cases_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_user_id",
            "request_message_id",
            name="uq_bot_support_cases_user_message",
        ),
    )
    op.create_index(
        "ix_bot_support_cases_rate_limit",
        "bot_support_cases",
        ["telegram_user_id", "category", "created_at"],
    )
    op.create_index(
        "ix_bot_support_cases_status_expires",
        "bot_support_cases",
        ["status", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_bot_support_cases_status_expires", table_name="bot_support_cases")
    op.drop_index("ix_bot_support_cases_rate_limit", table_name="bot_support_cases")
    op.drop_table("bot_support_cases")
