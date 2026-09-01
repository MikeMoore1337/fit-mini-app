from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class HydrationGoal(Base):
    __tablename__ = "hydration_goals"
    __table_args__ = (
        CheckConstraint("status IN ('enabled', 'disabled')", name="ck_hydration_goals_status"),
        CheckConstraint(
            "source IN ('national_academies_beverages', 'manual')",
            name="ck_hydration_goals_source",
        ),
        CheckConstraint(
            "(status = 'disabled' AND target_ml IS NULL) OR "
            "(status = 'enabled' AND target_ml BETWEEN 250 AND 10000)",
            name="ck_hydration_goals_target",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_hydration_goals_effective_period",
        ),
        Index(
            "uq_hydration_goals_active_user",
            "user_id",
            unique=True,
            postgresql_where=text("effective_to IS NULL"),
            sqlite_where=text("effective_to IS NULL"),
        ),
        Index("ix_hydration_goals_user_effective", "user_id", "effective_from"),
        UniqueConstraint("user_id", "request_key", name="uq_hydration_goals_request_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    target_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(48), nullable=False)
    method_version: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_scope: Mapped[str] = mapped_column(
        String(24), nullable=False, default="beverages", server_default="beverages"
    )
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    adult_confirmed: Mapped[bool | None] = mapped_column(nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    superseded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("hydration_goals.id", ondelete="SET NULL"), nullable=True
    )
    request_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)


class HydrationEntry(Base):
    __tablename__ = "hydration_entries"
    __table_args__ = (
        CheckConstraint("volume_ml BETWEEN 1 AND 5000", name="ck_hydration_entries_volume"),
        CheckConstraint(
            "beverage_type IN ('water', 'tea', 'coffee', 'milk', 'juice', 'other')",
            name="ck_hydration_entries_beverage_type",
        ),
        CheckConstraint(
            "source IN ('quick_preset', 'manual', 'history_edit')",
            name="ck_hydration_entries_source",
        ),
        UniqueConstraint("user_id", "request_key", name="uq_hydration_entries_request_key"),
        Index("ix_hydration_entries_user_day", "user_id", "diary_date", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    diary_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    beverage_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    request_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)


class HydrationPreset(Base):
    __tablename__ = "hydration_presets"
    __table_args__ = (
        CheckConstraint("volume_ml BETWEEN 1 AND 5000", name="ck_hydration_presets_volume"),
        CheckConstraint(
            "beverage_type IN ('water', 'tea', 'coffee', 'milk', 'juice', 'other')",
            name="ck_hydration_presets_beverage_type",
        ),
        CheckConstraint("length(label) BETWEEN 1 AND 40", name="ck_hydration_presets_label"),
        UniqueConstraint("user_id", "label", name="uq_hydration_presets_user_label"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    beverage_type: Mapped[str] = mapped_column(String(16), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
