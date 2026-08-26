"""add opt-in moderated weekly Telegram digest

Revision ID: 0061_weekly_telegram_digest
Revises: 0060_telegram_news_publishing
Create Date: 2026-08-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0061_weekly_telegram_digest"
down_revision = "0060_telegram_news_publishing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_digest_issues",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("issue_key", sa.String(length=16), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("window_start_utc", sa.DateTime(), nullable=False),
        sa.Column("window_end_utc", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("intro", sa.Text(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("min_items", sa.Integer(), nullable=False),
        sa.Column("selection_version", sa.String(length=64), nullable=False),
        sa.Column("renderer_version", sa.String(length=64), nullable=False),
        sa.Column("parse_mode", sa.String(length=16), nullable=False),
        sa.Column("rendered_text", sa.Text(), nullable=False),
        sa.Column("channel_url", sa.String(length=512), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("approved_by_ref", sa.String(length=24), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("scheduled_for_utc", sa.DateTime(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("recipient_count", sa.Integer(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("revision >= 1", name="ck_weekly_digest_issue_revision_positive"),
        sa.CheckConstraint(
            "item_count BETWEEN 0 AND 5", name="ck_weekly_digest_issue_item_count"
        ),
        sa.CheckConstraint(
            "min_items BETWEEN 1 AND 5", name="ck_weekly_digest_issue_min_items"
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'scheduled', 'sending', 'sent', "
            "'superseded', 'cancelled', 'rejected')",
            name="ck_weekly_digest_issue_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_key", "revision", name="uq_weekly_digest_issue_revision"),
    )
    op.create_index(
        "uq_weekly_digest_issue_active",
        "weekly_digest_issues",
        ["issue_key"],
        unique=True,
        postgresql_where=sa.text("status IN ('approved', 'scheduled', 'sending', 'sent')"),
        sqlite_where=sa.text("status IN ('approved', 'scheduled', 'sending', 'sent')"),
    )
    op.create_index(
        "ix_weekly_digest_issue_schedule",
        "weekly_digest_issues",
        ["status", "scheduled_for_utc"],
    )

    op.create_table(
        "weekly_digest_issue_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.String(length=32), nullable=False),
        sa.Column("publication_snapshot_id", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("headline", sa.String(length=180), nullable=False),
        sa.Column("takeaway", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=48), nullable=False),
        sa.Column("channel_permalink", sa.String(length=512), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("requires_owner_review", sa.Boolean(), nullable=False),
        sa.Column("selection_reason", sa.String(length=160), nullable=False),
        sa.CheckConstraint("position BETWEEN 1 AND 5", name="ck_weekly_digest_item_position"),
        sa.ForeignKeyConstraint(
            ["issue_id"], ["weekly_digest_issues.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["publication_snapshot_id"],
            ["news_publication_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_id", "position", name="uq_weekly_digest_item_position"),
        sa.UniqueConstraint(
            "issue_id", "publication_snapshot_id", name="uq_weekly_digest_item_post"
        ),
    )
    op.create_index(
        "ix_weekly_digest_item_issue",
        "weekly_digest_issue_items",
        ["issue_id", "position"],
    )

    op.create_table(
        "weekly_digest_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("weekly_news_digest_enabled", sa.Boolean(), nullable=False),
        sa.Column("consent_version", sa.String(length=64), nullable=True),
        sa.Column("subscribed_at", sa.DateTime(), nullable=True),
        sa.Column("unsubscribed_at", sa.DateTime(), nullable=True),
        sa.Column("disabled_reason", sa.String(length=64), nullable=True),
        sa.Column("last_digest_issue_id", sa.String(length=32), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "NOT weekly_news_digest_enabled OR telegram_chat_id IS NOT NULL",
            name="ck_weekly_digest_enabled_chat",
        ),
        sa.ForeignKeyConstraint(
            ["last_digest_issue_id"], ["weekly_digest_issues.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_weekly_digest_preference_enabled",
        "weekly_digest_preferences",
        ["weekly_news_digest_enabled", "user_id"],
    )

    op.create_table(
        "weekly_digest_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'sent', 'failed', 'cancelled', 'uncertain')",
            name="ck_weekly_digest_delivery_status",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_weekly_digest_delivery_attempts"),
        sa.ForeignKeyConstraint(
            ["issue_id"], ["weekly_digest_issues.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_id", "user_id", name="uq_weekly_digest_delivery_recipient"),
    )
    op.create_index(
        "ix_weekly_digest_delivery_queue",
        "weekly_digest_deliveries",
        ["next_attempt_at"],
        postgresql_where=sa.text("status = 'queued'"),
        sqlite_where=sa.text("status = 'queued'"),
    )


def downgrade() -> None:
    op.drop_index("ix_weekly_digest_delivery_queue", table_name="weekly_digest_deliveries")
    op.drop_table("weekly_digest_deliveries")
    op.drop_index(
        "ix_weekly_digest_preference_enabled", table_name="weekly_digest_preferences"
    )
    op.drop_table("weekly_digest_preferences")
    op.drop_index("ix_weekly_digest_item_issue", table_name="weekly_digest_issue_items")
    op.drop_table("weekly_digest_issue_items")
    op.drop_index("ix_weekly_digest_issue_schedule", table_name="weekly_digest_issues")
    op.drop_index("uq_weekly_digest_issue_active", table_name="weekly_digest_issues")
    op.drop_table("weekly_digest_issues")
