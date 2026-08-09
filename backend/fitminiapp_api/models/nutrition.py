from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
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
    strength_trainings_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_training_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    cardio_trainings_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    cardio_training_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    cardio_intensity: Mapped[str] = mapped_column(String(16), nullable=False, default="moderate")
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
