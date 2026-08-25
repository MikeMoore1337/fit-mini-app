from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.db.base import Base


class NewsSource(Base):
    __tablename__ = "news_sources"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('primary_research', 'systematic_review', 'official_organization', "
            "'official_product', 'reputable_secondary', 'yfc')",
            name="ck_news_sources_type",
        ),
        CheckConstraint(
            "fetch_kind IN ('rss', 'json_feed', 'html_metadata')",
            name="ck_news_sources_fetch_kind",
        ),
        CheckConstraint(
            "fetch_interval_minutes BETWEEN 15 AND 10080",
            name="ck_news_sources_fetch_interval",
        ),
        Index("ix_news_sources_due", "enabled", "next_fetch_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    fetch_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    feed_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    trust_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    licensing_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fetch_options: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    etag: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    consecutive_error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_fetch_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class NewsCluster(Base):
    __tablename__ = "news_clusters"
    __table_args__ = (
        CheckConstraint(
            "status IN ('clustered', 'rejected_by_rules', 'candidate', 'draft_ready', "
            "'awaiting_review', 'deferred', 'rejected', 'accepted_for_design')",
            name="ck_news_clusters_status",
        ),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_news_clusters_score"),
        CheckConstraint(
            "generation_attempt_count BETWEEN 0 AND 20",
            name="ck_news_clusters_generation_attempts",
        ),
        Index("ix_news_clusters_work_queue", "status", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    cluster_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="clustered")
    primary_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String(48), nullable=False, default="other")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_version: Mapped[str] = mapped_column(String(32), nullable=False, default="news-score-v1")
    score_reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conflict_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    merge_reason: Mapped[str] = mapped_column(String(160), nullable=False, default="new_event")
    latest_draft_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivery_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class NewsItem(Base):
    __tablename__ = "news_items"
    __table_args__ = (
        CheckConstraint(
            "status IN ('fetched', 'clustered', 'rejected_by_rules')",
            name="ck_news_items_status",
        ),
        UniqueConstraint(
            "source_id", "external_id_hash", "content_hash", name="uq_news_items_source_revision"
        ),
        Index("ix_news_items_url_hash", "canonical_url_hash"),
        Index("ix_news_items_doi", "doi"),
        Index("ix_news_items_cluster", "cluster_id", "published_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("news_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cluster_id: Mapped[str | None] = mapped_column(
        ForeignKey("news_clusters.id", ondelete="CASCADE"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="fetched")
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    external_id_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author: Mapped[str | None] = mapped_column(String(256), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(160), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merge_reason: Mapped[str] = mapped_column(String(64), nullable=False, default="new_event")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class NewsDraftRevision(Base):
    __tablename__ = "news_draft_revisions"
    __table_args__ = (
        UniqueConstraint("cluster_id", "revision", name="uq_news_draft_cluster_revision"),
        CheckConstraint("revision >= 1", name="ck_news_draft_revision_positive"),
        CheckConstraint("generation_latency_ms >= 0", name="ck_news_draft_latency"),
        Index("ix_news_drafts_cluster_created", "cluster_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    cluster_id: Mapped[str] = mapped_column(
        ForeignKey("news_clusters.id", ondelete="CASCADE"), nullable=False
    )
    primary_item_id: Mapped[int] = mapped_column(
        ForeignKey("news_items.id", ondelete="RESTRICT"), nullable=False
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_item_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    evidence_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    generation_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_cost_microunits: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class NewsReviewDelivery(Base):
    __tablename__ = "news_review_deliveries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'sent', 'failed', 'cancelled')",
            name="ck_news_review_deliveries_status",
        ),
        UniqueConstraint(
            "draft_id", "recipient_ref", "delivery_round", name="uq_news_review_delivery_round"
        ),
        Index(
            "ix_news_review_delivery_queue",
            "next_attempt_at",
            postgresql_where=text("status = 'queued'"),
            sqlite_where=text("status = 'queued'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[str] = mapped_column(
        ForeignKey("news_draft_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_ref: Mapped[str] = mapped_column(String(24), nullable=False)
    delivery_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class NewsEditorialAction(Base):
    __tablename__ = "news_editorial_actions"
    __table_args__ = (
        CheckConstraint(
            "action IN ('skip', 'defer', 'regenerate', 'accept_for_design')",
            name="ck_news_editorial_actions_action",
        ),
        UniqueConstraint(
            "draft_id", "actor_ref", "action", name="uq_news_editorial_action_idempotency"
        ),
        Index("ix_news_editorial_actions_cluster_created", "cluster_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[str] = mapped_column(
        ForeignKey("news_clusters.id", ondelete="CASCADE"), nullable=False
    )
    draft_id: Mapped[str] = mapped_column(
        ForeignKey("news_draft_revisions.id", ondelete="CASCADE"), nullable=False
    )
    actor_ref: Mapped[str] = mapped_column(String(24), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class NewsStateTransition(Base):
    __tablename__ = "news_state_transitions"
    __table_args__ = (
        Index("ix_news_state_transitions_cluster_created", "cluster_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[str] = mapped_column(
        ForeignKey("news_clusters.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_ref: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
