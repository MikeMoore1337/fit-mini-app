"""add moderated Telegram news ingestion and editorial drafts

Revision ID: 0059_telegram_news_editorial
Revises: 0058_cardio_sessions
Create Date: 2026-08-25
"""

import sqlalchemy as sa

from alembic import op

revision = "0059_telegram_news_editorial"
down_revision = "0058_cardio_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_sources",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("fetch_kind", sa.String(length=24), nullable=False),
        sa.Column("feed_url", sa.String(length=2048), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("trust_notes", sa.Text(), nullable=False),
        sa.Column("licensing_notes", sa.Text(), nullable=False),
        sa.Column("fetch_options", sa.JSON(), nullable=False),
        sa.Column("etag", sa.String(length=512), nullable=True),
        sa.Column("last_modified", sa.String(length=512), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_at", sa.DateTime(), nullable=True),
        sa.Column("consecutive_error_count", sa.Integer(), nullable=False),
        sa.Column("next_fetch_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "source_type IN ('primary_research', 'systematic_review', 'official_organization', "
            "'official_product', 'reputable_secondary', 'yfc')",
            name="ck_news_sources_type",
        ),
        sa.CheckConstraint(
            "fetch_kind IN ('rss', 'json_feed', 'html_metadata')",
            name="ck_news_sources_fetch_kind",
        ),
        sa.CheckConstraint(
            "fetch_interval_minutes BETWEEN 15 AND 10080",
            name="ck_news_sources_fetch_interval",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_news_sources_due", "news_sources", ["enabled", "next_fetch_at"])

    op.create_table(
        "news_clusters",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("cluster_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("primary_item_id", sa.Integer(), nullable=True),
        sa.Column("topic", sa.String(length=48), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("score_version", sa.String(length=32), nullable=False),
        sa.Column("score_reasons", sa.JSON(), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=False),
        sa.Column("conflict_notes", sa.JSON(), nullable=False),
        sa.Column("merge_reason", sa.String(length=160), nullable=False),
        sa.Column("latest_draft_revision", sa.Integer(), nullable=False),
        sa.Column("generation_attempt_count", sa.Integer(), nullable=False),
        sa.Column("delivery_round", sa.Integer(), nullable=False),
        sa.Column("deferred_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('clustered', 'rejected_by_rules', 'candidate', 'draft_ready', "
            "'awaiting_review', 'deferred', 'rejected', 'accepted_for_design')",
            name="ck_news_clusters_status",
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_news_clusters_score"),
        sa.CheckConstraint(
            "generation_attempt_count BETWEEN 0 AND 20",
            name="ck_news_clusters_generation_attempts",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_key"),
    )
    op.create_index("ix_news_clusters_primary_item_id", "news_clusters", ["primary_item_id"])
    op.create_index("ix_news_clusters_work_queue", "news_clusters", ["status", "updated_at"])
    op.create_index("ix_news_clusters_deferred_until", "news_clusters", ["deferred_until"])

    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("external_id_hash", sa.String(length=64), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("canonical_url_hash", sa.String(length=64), nullable=False),
        sa.Column("primary_url", sa.String(length=2048), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=256), nullable=True),
        sa.Column("publisher", sa.String(length=160), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        sa.Column("doi", sa.String(length=255), nullable=True),
        sa.Column("merge_reason", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_snapshot", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('fetched', 'clustered', 'rejected_by_rules')",
            name="ck_news_items_status",
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id", "external_id_hash", "content_hash", name="uq_news_items_source_revision"
        ),
    )
    op.create_index("ix_news_items_source_id", "news_items", ["source_id"])
    op.create_index("ix_news_items_url_hash", "news_items", ["canonical_url_hash"])
    op.create_index("ix_news_items_doi", "news_items", ["doi"])
    op.create_index("ix_news_items_cluster", "news_items", ["cluster_id", "published_at"])

    op.create_table(
        "news_draft_revisions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=False),
        sa.Column("primary_item_id", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("source_digest", sa.String(length=64), nullable=False),
        sa.Column("evidence_item_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_metadata", sa.JSON(), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("generation_latency_ms", sa.Integer(), nullable=False),
        sa.Column("generation_input_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_output_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_cost_microunits", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("generation_latency_ms >= 0", name="ck_news_draft_latency"),
        sa.CheckConstraint("revision >= 1", name="ck_news_draft_revision_positive"),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_item_id"], ["news_items.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_id", "revision", name="uq_news_draft_cluster_revision"),
    )
    op.create_index(
        "ix_news_drafts_cluster_created", "news_draft_revisions", ["cluster_id", "created_at"]
    )

    op.create_table(
        "news_review_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("draft_id", sa.String(length=32), nullable=False),
        sa.Column("recipient_ref", sa.String(length=24), nullable=False),
        sa.Column("delivery_round", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'sent', 'failed', 'cancelled')",
            name="ck_news_review_deliveries_status",
        ),
        sa.ForeignKeyConstraint(["draft_id"], ["news_draft_revisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "draft_id", "recipient_ref", "delivery_round", name="uq_news_review_delivery_round"
        ),
    )
    op.create_index("ix_news_review_deliveries_draft_id", "news_review_deliveries", ["draft_id"])
    op.create_index(
        "ix_news_review_delivery_queue",
        "news_review_deliveries",
        ["next_attempt_at"],
        postgresql_where=sa.text("status = 'queued'"),
        sqlite_where=sa.text("status = 'queued'"),
    )

    op.create_table(
        "news_editorial_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=False),
        sa.Column("draft_id", sa.String(length=32), nullable=False),
        sa.Column("actor_ref", sa.String(length=24), nullable=False),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "action IN ('skip', 'defer', 'regenerate', 'accept_for_design')",
            name="ck_news_editorial_actions_action",
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["draft_id"], ["news_draft_revisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "draft_id", "actor_ref", "action", name="uq_news_editorial_action_idempotency"
        ),
    )
    op.create_index(
        "ix_news_editorial_actions_cluster_created",
        "news_editorial_actions",
        ["cluster_id", "created_at"],
    )

    op.create_table(
        "news_state_transitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("actor_ref", sa.String(length=24), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_news_state_transitions_cluster_created",
        "news_state_transitions",
        ["cluster_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_news_state_transitions_cluster_created", table_name="news_state_transitions")
    op.drop_table("news_state_transitions")
    op.drop_index("ix_news_editorial_actions_cluster_created", table_name="news_editorial_actions")
    op.drop_table("news_editorial_actions")
    op.drop_index("ix_news_review_delivery_queue", table_name="news_review_deliveries")
    op.drop_index("ix_news_review_deliveries_draft_id", table_name="news_review_deliveries")
    op.drop_table("news_review_deliveries")
    op.drop_index("ix_news_drafts_cluster_created", table_name="news_draft_revisions")
    op.drop_table("news_draft_revisions")
    op.drop_index("ix_news_items_cluster", table_name="news_items")
    op.drop_index("ix_news_items_doi", table_name="news_items")
    op.drop_index("ix_news_items_url_hash", table_name="news_items")
    op.drop_index("ix_news_items_source_id", table_name="news_items")
    op.drop_table("news_items")
    op.drop_index("ix_news_clusters_deferred_until", table_name="news_clusters")
    op.drop_index("ix_news_clusters_work_queue", table_name="news_clusters")
    op.drop_index("ix_news_clusters_primary_item_id", table_name="news_clusters")
    op.drop_table("news_clusters")
    op.drop_index("ix_news_sources_due", table_name="news_sources")
    op.drop_table("news_sources")
