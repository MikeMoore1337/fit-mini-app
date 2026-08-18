from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class FoodDiaryEntry(Base):
    __tablename__ = "food_diary_entries"
    __table_args__ = (
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snacks')",
            name="ck_food_diary_entries_meal_type",
        ),
        CheckConstraint(
            "amount_unit IN ('g', 'serving')",
            name="ck_food_diary_entries_amount_unit",
        ),
        CheckConstraint("amount > 0", name="ck_food_diary_entries_amount_positive"),
        CheckConstraint("weight_g > 0", name="ck_food_diary_entries_weight_positive"),
        CheckConstraint(
            "amount_unit <> 'g' OR amount = weight_g",
            name="ck_food_diary_entries_gram_amount_weight",
        ),
        CheckConstraint(
            "serving_amount IS NULL AND serving_unit IS NULL AND serving_weight_g IS NULL OR "
            "serving_amount > 0 AND serving_unit IN ('g', 'ml', 'piece', 'serving') AND "
            "serving_weight_g > 0",
            name="ck_food_diary_entries_serving_complete",
        ),
        CheckConstraint(
            "energy_kcal_per_100g BETWEEN 0 AND 1000",
            name="ck_food_diary_entries_energy_range",
        ),
        CheckConstraint(
            "protein_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_protein_range",
        ),
        CheckConstraint(
            "fat_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_fat_range",
        ),
        CheckConstraint(
            "carbs_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_carbs_range",
        ),
        CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g BETWEEN 0 AND 100",
            name="ck_food_diary_entries_fiber_range",
        ),
        Index(
            "ix_food_diary_entries_user_date_meal",
            "user_id",
            "diary_date",
            "meal_type",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[int | None] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL"), nullable=True
    )
    diary_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(16), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    amount_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    weight_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    food_name: Mapped[str] = mapped_column(String(256), nullable=False)
    food_brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    energy_kcal_per_100g: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    protein_g_per_100g: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    fat_g_per_100g: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    carbs_g_per_100g: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    fiber_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)

    serving_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    serving_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    serving_weight_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=now_msk_naive,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=now_msk_naive,
        onupdate=now_msk_naive,
    )
