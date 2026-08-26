from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
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


class WeeklyDigestIssue(Base):
    __tablename__ = "weekly_digest_issues"
    __table_args__ = (
        UniqueConstraint("issue_key", "revision", name="uq_weekly_digest_issue_revision"),
        CheckConstraint("revision >= 1", name="ck_weekly_digest_issue_revision_positive"),
        CheckConstraint("item_count BETWEEN 0 AND 5", name="ck_weekly_digest_issue_item_count"),
        CheckConstraint("min_items BETWEEN 1 AND 5", name="ck_weekly_digest_issue_min_items"),
        CheckConstraint(
            "status IN ('draft', 'approved', 'scheduled', 'sending', 'sent', "
            "'superseded', 'cancelled', 'rejected')",
            name="ck_weekly_digest_issue_status",
        ),
        Index(
            "uq_weekly_digest_issue_active",
            "issue_key",
            unique=True,
            postgresql_where=text("status IN ('approved', 'scheduled', 'sending', 'sent')"),
            sqlite_where=text("status IN ('approved', 'scheduled', 'sending', 'sent')"),
        ),
        Index("ix_weekly_digest_issue_schedule", "status", "scheduled_for_utc"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    issue_key: Mapped[str] = mapped_column(String(16), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    window_start_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    intro: Mapped[str] = mapped_column(Text, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    min_items: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_version: Mapped[str] = mapped_column(String(64), nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    parse_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="HTML")
    rendered_text: Mapped[str] = mapped_column(Text, nullable=False)
    channel_url: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_by_ref: Mapped[str | None] = mapped_column(String(24), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scheduled_for_utc: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class WeeklyDigestIssueItem(Base):
    __tablename__ = "weekly_digest_issue_items"
    __table_args__ = (
        UniqueConstraint("issue_id", "position", name="uq_weekly_digest_item_position"),
        UniqueConstraint("issue_id", "publication_snapshot_id", name="uq_weekly_digest_item_post"),
        CheckConstraint("position BETWEEN 1 AND 5", name="ck_weekly_digest_item_position"),
        Index("ix_weekly_digest_item_issue", "issue_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[str] = mapped_column(
        ForeignKey("weekly_digest_issues.id", ondelete="CASCADE"), nullable=False
    )
    publication_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("news_publication_snapshots.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    headline: Mapped[str] = mapped_column(String(180), nullable=False)
    takeaway: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    channel_permalink: Mapped[str] = mapped_column(String(512), nullable=False)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    requires_owner_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selection_reason: Mapped[str] = mapped_column(String(160), nullable=False)


class WeeklyDigestPreference(Base):
    __tablename__ = "weekly_digest_preferences"
    __table_args__ = (
        CheckConstraint(
            "NOT weekly_news_digest_enabled OR telegram_chat_id IS NOT NULL",
            name="ck_weekly_digest_enabled_chat",
        ),
        Index("ix_weekly_digest_preference_enabled", "weekly_news_digest_enabled", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    weekly_news_digest_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subscribed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    disabled_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_digest_issue_id: Mapped[str | None] = mapped_column(
        ForeignKey("weekly_digest_issues.id", ondelete="SET NULL"), nullable=True
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class WeeklyDigestDelivery(Base):
    __tablename__ = "weekly_digest_deliveries"
    __table_args__ = (
        UniqueConstraint("issue_id", "user_id", name="uq_weekly_digest_delivery_recipient"),
        CheckConstraint(
            "status IN ('queued', 'processing', 'sent', 'failed', 'cancelled', 'uncertain')",
            name="ck_weekly_digest_delivery_status",
        ),
        CheckConstraint("attempt_count >= 0", name="ck_weekly_digest_delivery_attempts"),
        Index(
            "ix_weekly_digest_delivery_queue",
            "next_attempt_at",
            postgresql_where=text("status = 'queued'"),
            sqlite_where=text("status = 'queued'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[str] = mapped_column(
        ForeignKey("weekly_digest_issues.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
