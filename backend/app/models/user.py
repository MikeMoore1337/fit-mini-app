from datetime import date, datetime

from sqlalchemy import (
    BIGINT,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timezone import DEFAULT_TIMEZONE, now_msk_naive
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BIGINT, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    client_code: Mapped[str | None] = mapped_column(
        String(8), unique=True, index=True, nullable=True
    )
    is_coach: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)

    profile = relationship("UserProfile", back_populates="user", uselist=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    goal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workouts_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cardio_trainings_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=DEFAULT_TIMEZONE,
        server_default=DEFAULT_TIMEZONE,
    )

    user = relationship("User", back_populates="profile")


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"
    __table_args__ = (
        UniqueConstraint("user_id", "measured_on", name="uq_body_measurement_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    measured_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    biceps_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    thigh_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)


class CoachClient(Base):
    __tablename__ = "coach_clients"
    __table_args__ = (
        Index(
            "uq_coach_clients_one_active_per_client",
            "client_user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
        Index("ix_coach_clients_coach_status", "coach_user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coach_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=now_msk_naive
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CoachClientInvite(Base):
    __tablename__ = "coach_client_invites"
    __table_args__ = (
        Index(
            "uq_coach_client_invites_pending_pair",
            "coach_user_id",
            "client_user_id",
            unique=True,
            postgresql_where=text("status = 'pending' AND client_user_id IS NOT NULL"),
            sqlite_where=text("status = 'pending' AND client_user_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coach_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    telegram_user_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    token_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    source: Mapped[str] = mapped_column(
        String(32), nullable=False, default="username_search", server_default="username_search"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", server_default="pending"
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    declined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
