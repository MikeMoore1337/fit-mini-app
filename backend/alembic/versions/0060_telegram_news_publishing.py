"""add revision-bound Telegram news images and publishing

Revision ID: 0060_telegram_news_publishing
Revises: 0059_telegram_news_editorial
Create Date: 2026-08-25
"""

import sqlalchemy as sa

from alembic import op

revision = "0060_telegram_news_publishing"
down_revision = "0059_telegram_news_editorial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("news_clusters") as batch_op:
        batch_op.add_column(
            sa.Column("latest_image_revision", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column("current_image_revision", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.drop_constraint("ck_news_clusters_status", type_="check")
        batch_op.create_check_constraint(
            "ck_news_clusters_status",
            "status IN ('clustered', 'rejected_by_rules', 'candidate', 'draft_ready', "
            "'image_pending', 'awaiting_review', 'deferred', 'rejected', "
            "'accepted_for_design', 'publication_approved', 'publication_scheduled', "
            "'publication_failed', 'published')",
        )

    op.create_table(
        "news_image_revisions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=False),
        sa.Column("text_revision_id", sa.String(length=32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_digest", sa.String(length=64), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("safety_status", sa.String(length=32), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("generation_latency_ms", sa.Integer(), nullable=False),
        sa.Column("generation_input_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_output_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_cost_microunits", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("revision >= 1", name="ck_news_image_revision_positive"),
        sa.CheckConstraint(
            "kind IN ('generated', 'template', 'uploaded')", name="ck_news_image_kind"
        ),
        sa.CheckConstraint(
            "safety_status IN ('generated_pending_review', 'owner_uploaded', 'template')",
            name="ck_news_image_safety_status",
        ),
        sa.CheckConstraint("byte_size > 0", name="ck_news_image_byte_size"),
        sa.CheckConstraint("width > 0 AND height > 0", name="ck_news_image_dimensions"),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["text_revision_id"], ["news_draft_revisions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_id", "revision", name="uq_news_image_cluster_revision"),
    )
    op.create_index(
        "ix_news_images_cluster_created", "news_image_revisions", ["cluster_id", "created_at"]
    )

    op.create_table(
        "news_review_decisions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=False),
        sa.Column("text_revision_id", sa.String(length=32), nullable=False),
        sa.Column("image_revision_id", sa.String(length=32), nullable=True),
        sa.Column("explicit_no_image", sa.Boolean(), nullable=False),
        sa.Column("target_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("publication_mode", sa.String(length=16), nullable=False),
        sa.Column("scheduled_for_utc", sa.DateTime(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("reviewer_ref", sa.String(length=24), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revocation_reason", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "publication_mode IN ('immediate', 'scheduled')",
            name="ck_news_review_publication_mode",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'revoked', 'consumed', 'cancelled')",
            name="ck_news_review_decision_status",
        ),
        sa.CheckConstraint(
            "(image_revision_id IS NULL AND explicit_no_image) OR "
            "(image_revision_id IS NOT NULL AND NOT explicit_no_image)",
            name="ck_news_review_exact_image",
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["text_revision_id"], ["news_draft_revisions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["image_revision_id"], ["news_image_revisions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_news_review_decisions_cluster", "news_review_decisions", ["cluster_id", "approved_at"]
    )

    op.create_table(
        "news_publication_snapshots",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("decision_id", sa.String(length=32), nullable=False),
        sa.Column("cluster_id", sa.String(length=32), nullable=False),
        sa.Column("text_revision_id", sa.String(length=32), nullable=False),
        sa.Column("image_revision_id", sa.String(length=32), nullable=True),
        sa.Column("target_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("target_channel_username", sa.String(length=32), nullable=False),
        sa.Column("publication_mode", sa.String(length=16), nullable=False),
        sa.Column("scheduled_for_utc", sa.DateTime(), nullable=False),
        sa.Column("publication_local_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("reviewer_ref", sa.String(length=24), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("urgent_override", sa.Boolean(), nullable=False),
        sa.Column("publication_text", sa.Text(), nullable=False),
        sa.Column("renderer_version", sa.String(length=64), nullable=False),
        sa.Column("transport", sa.String(length=16), nullable=False),
        sa.Column("parse_mode", sa.String(length=16), nullable=True),
        sa.Column("link_preview_disabled", sa.Boolean(), nullable=False),
        sa.Column("image_sha256", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("processing_started_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_message_date", sa.DateTime(), nullable=True),
        sa.Column("telegram_permalink", sa.String(length=512), nullable=True),
        sa.Column("telegram_edited_at", sa.DateTime(), nullable=True),
        sa.Column("telegram_deleted_at", sa.DateTime(), nullable=True),
        sa.Column("post_edit_content_hash", sa.String(length=64), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "publication_mode IN ('immediate', 'scheduled')", name="ck_news_publication_mode"
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'scheduled', 'processing', 'published', 'failed', "
            "'uncertain', 'cancelled')",
            name="ck_news_publication_status",
        ),
        sa.CheckConstraint(
            "transport IN ('message', 'photo')", name="ck_news_publication_transport"
        ),
        sa.CheckConstraint(
            "parse_mode IS NULL OR parse_mode IN ('HTML')",
            name="ck_news_publication_parse_mode",
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["news_review_decisions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["text_revision_id"], ["news_draft_revisions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["image_revision_id"], ["news_image_revisions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_id", name="uq_news_publication_decision"),
        sa.UniqueConstraint("idempotency_key", name="uq_news_publication_idempotency"),
    )
    op.create_index(
        "ix_news_publication_queue",
        "news_publication_snapshots",
        ["next_attempt_at"],
        postgresql_where=sa.text("status IN ('queued', 'scheduled')"),
        sqlite_where=sa.text("status IN ('queued', 'scheduled')"),
    )
    op.create_index(
        "ix_news_publication_channel_day",
        "news_publication_snapshots",
        ["target_channel_id", "publication_local_date", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_news_publication_channel_day", table_name="news_publication_snapshots")
    op.drop_index("ix_news_publication_queue", table_name="news_publication_snapshots")
    op.drop_table("news_publication_snapshots")
    op.drop_index("ix_news_review_decisions_cluster", table_name="news_review_decisions")
    op.drop_table("news_review_decisions")
    op.drop_index("ix_news_images_cluster_created", table_name="news_image_revisions")
    op.drop_table("news_image_revisions")
    op.execute(
        "UPDATE news_clusters SET status = 'accepted_for_design' "
        "WHERE status IN ('image_pending', 'publication_approved', 'publication_scheduled', "
        "'publication_failed', 'published')"
    )
    with op.batch_alter_table("news_clusters") as batch_op:
        batch_op.drop_constraint("ck_news_clusters_status", type_="check")
        batch_op.create_check_constraint(
            "ck_news_clusters_status",
            "status IN ('clustered', 'rejected_by_rules', 'candidate', 'draft_ready', "
            "'awaiting_review', 'deferred', 'rejected', 'accepted_for_design')",
        )
        batch_op.drop_column("current_image_revision")
        batch_op.drop_column("latest_image_revision")
