from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class NutritionTarget(Base):
    __tablename__ = "nutrition_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    age: Mapped[float] = mapped_column(Float, nullable=False)
    daily_activity_level: Mapped[str] = mapped_column(
        String(16), nullable=False, default="sedentary"
    )
    daily_routine: Mapped[str] = mapped_column(String(24), nullable=False, default="mostly_sitting")
    steps_range: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    strength_trainings_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_training_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    strength_training_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="regular"
    )
    strength_rest: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cardio_trainings_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    cardio_training_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    cardio_intensity: Mapped[str] = mapped_column(String(16), nullable=False, default="moderate")
    cardio_trainings: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    goal: Mapped[str] = mapped_column(String(32), nullable=False)

    bmr: Mapped[int] = mapped_column(Integer, nullable=False)
    tdee: Mapped[int] = mapped_column(Integer, nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_g: Mapped[int] = mapped_column(Integer, nullable=False)
    fat_g: Mapped[int] = mapped_column(Integer, nullable=False)
    carbs_g: Mapped[int] = mapped_column(Integer, nullable=False)

    saved_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=now_msk_naive,
    )


class EnergyCalibration(Base):
    __tablename__ = "energy_calibrations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('limited', 'no_change', 'pending', 'accepted', 'rejected', 'superseded')",
            name="ck_energy_calibrations_status",
        ),
        CheckConstraint(
            "sufficiency_status IN ('limited', 'sufficient')",
            name="ck_energy_calibrations_sufficiency_status",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_energy_calibrations_period",
        ),
        CheckConstraint(
            "estimate_low_kcal <= estimated_expenditure_kcal AND "
            "estimated_expenditure_kcal <= estimate_high_kcal",
            name="ck_energy_calibrations_estimate_range",
        ),
        Index(
            "ix_energy_calibrations_user_created",
            "user_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    sufficiency_status: Mapped[str] = mapped_column(String(16), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    goal: Mapped[str] = mapped_column(String(32), nullable=False)
    logged_day_count: Mapped[int] = mapped_column(Integer, nullable=False)
    eligible_day_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_point_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_span_days: Mapped[int] = mapped_column(Integer, nullable=False)
    average_intake_kcal: Mapped[int] = mapped_column(Integer, nullable=False)
    smoothed_start_weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    smoothed_end_weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    estimated_expenditure_kcal: Mapped[int] = mapped_column(Integer, nullable=False)
    estimate_low_kcal: Mapped[int] = mapped_column(Integer, nullable=False)
    estimate_high_kcal: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_target_calories: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_target_saved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    proposed_target_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sufficiency_counters: Mapped[dict[str, int | float]] = mapped_column(JSON, nullable=False)
    sufficiency_reason_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rationale_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=now_msk_naive,
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
