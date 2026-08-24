from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"
    __table_args__ = (
        CheckConstraint(
            "(quiet_hours_start IS NULL AND quiet_hours_end IS NULL) OR "
            "(quiet_hours_start IS NOT NULL AND quiet_hours_end IS NOT NULL)",
            name="ck_notification_settings_quiet_hours_pair",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    workout_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_check_in_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    measurement_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_hour: Mapped[int] = mapped_column(Integer, default=9)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_notifications_dedupe_key"),
        CheckConstraint(
            "action_url IS NULL OR action_url = '/app' OR action_url LIKE '/app?%'",
            name="ck_notifications_internal_action_url",
        ),
        CheckConstraint(
            "event_kind IN ('reminder', 'transactional', 'security')",
            name="ck_notifications_event_kind",
        ),
        Index(
            "ix_notifications_due_queue",
            "scheduled_for_utc",
            "next_attempt_at",
            postgresql_where=text("status = 'queued'"),
            sqlite_where=text("status = 'queued'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="telegram")
    category: Mapped[str] = mapped_column(String(48), default="custom_reminder")
    event_kind: Mapped[str] = mapped_column(String(24), default="reminder")
    title: Mapped[str] = mapped_column(String(128))
    body: Mapped[str] = mapped_column(Text)
    # scheduled_for остаётся локальным wall time для показа пользователю.
    # UTC-колонка используется worker-ом для индексируемого поиска срока доставки.
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, index=True)
    scheduled_for_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_msk_naive,
        server_default=func.now(),
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
