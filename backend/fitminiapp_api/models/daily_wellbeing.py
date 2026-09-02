from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class DailyWellbeingCheckIn(Base):
    __tablename__ = "daily_wellbeing_check_ins"
    __table_args__ = (
        UniqueConstraint("user_id", "local_date", name="uq_daily_wellbeing_user_date"),
        CheckConstraint(
            "sleep_quality IS NULL OR sleep_quality BETWEEN 1 AND 5",
            name="ck_daily_wellbeing_sleep_quality",
        ),
        CheckConstraint(
            "mood IS NULL OR mood BETWEEN 1 AND 5",
            name="ck_daily_wellbeing_mood",
        ),
        CheckConstraint(
            "sleep_duration_minutes IS NULL OR sleep_duration_minutes BETWEEN 1 AND 1440",
            name="ck_daily_wellbeing_sleep_duration",
        ),
        CheckConstraint(
            "sleep_quality IS NOT NULL OR sleep_duration_minutes IS NOT NULL OR mood IS NOT NULL",
            name="ck_daily_wellbeing_has_observation",
        ),
        CheckConstraint(
            "source IN ('manual', 'future_import')",
            name="ck_daily_wellbeing_source",
        ),
        CheckConstraint(
            "note IS NULL OR length(note) <= 500",
            name="ck_daily_wellbeing_note_length",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone_at_entry: Mapped[str] = mapped_column(String(64), nullable=False)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
