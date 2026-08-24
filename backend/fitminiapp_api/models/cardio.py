from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.db.base import Base


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class CardioSession(Base):
    __tablename__ = "cardio_sessions"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('walking', 'running', 'elliptical', 'stationary_bike', "
            "'cycling', 'rowing', 'stepper', 'swimming', 'other')",
            name="ck_cardio_sessions_activity_type",
        ),
        CheckConstraint(
            "duration_minutes BETWEEN 1 AND 600",
            name="ck_cardio_sessions_duration_minutes",
        ),
        CheckConstraint(
            "distance_km IS NULL OR (distance_km > 0 AND distance_km <= 1000)",
            name="ck_cardio_sessions_distance_km",
        ),
        CheckConstraint(
            "average_heart_rate_bpm IS NULL OR average_heart_rate_bpm BETWEEN 30 AND 250",
            name="ck_cardio_sessions_average_heart_rate",
        ),
        CheckConstraint(
            "heart_rate_zone IS NULL OR heart_rate_zone BETWEEN 1 AND 5",
            name="ck_cardio_sessions_heart_rate_zone",
        ),
        CheckConstraint(
            "status IN ('planned', 'completed')",
            name="ck_cardio_sessions_status",
        ),
        CheckConstraint("source = 'manual'", name="ck_cardio_sessions_source"),
        CheckConstraint("note IS NULL OR length(note) <= 500", name="ck_cardio_sessions_note"),
        UniqueConstraint("user_id", "client_request_id", name="uq_cardio_sessions_request"),
        Index("ix_cardio_sessions_user_scheduled", "user_id", "scheduled_at", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    average_heart_rate_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate_zone: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now_naive,
        onupdate=utc_now_naive,
    )
