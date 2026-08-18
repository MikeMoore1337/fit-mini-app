from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
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
        CheckConstraint(
            "NOT (food_id IS NOT NULL AND recipe_id IS NOT NULL)",
            name="ck_food_diary_entries_single_source",
        ),
        Index(
            "ix_food_diary_entries_user_date_meal",
            "user_id",
            "diary_date",
            "meal_type",
            "id",
        ),
        Index(
            "ix_food_diary_entries_user_food_updated",
            "user_id",
            "food_id",
            "updated_at",
        ),
        Index("ix_food_diary_entries_copy_operation", "copy_operation_id", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[int | None] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL"), nullable=True
    )
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    copy_operation_id: Mapped[int | None] = mapped_column(
        ForeignKey("food_diary_copy_operations.id", ondelete="SET NULL"), nullable=True
    )
    copied_from_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("food_diary_entries.id", ondelete="SET NULL"), nullable=True
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


class FoodDiaryCopyOperation(Base):
    __tablename__ = "food_diary_copy_operations"
    __table_args__ = (
        CheckConstraint(
            "copy_scope IN ('product', 'meal', 'day')",
            name="ck_food_diary_copy_operations_scope",
        ),
        CheckConstraint(
            "source_meal_type IS NULL OR "
            "source_meal_type IN ('breakfast', 'lunch', 'dinner', 'snacks')",
            name="ck_food_diary_copy_operations_source_meal",
        ),
        CheckConstraint(
            "target_meal_type IS NULL OR "
            "target_meal_type IN ('breakfast', 'lunch', 'dinner', 'snacks')",
            name="ck_food_diary_copy_operations_target_meal",
        ),
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_food_diary_copy_operations_user_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    copy_scope: Mapped[str] = mapped_column(String(16), nullable=False)
    source_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_meal_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_meal_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=now_msk_naive,
    )
