from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_recipes_name_not_blank"),
        CheckConstraint(
            "final_weight_g IS NULL OR final_weight_g > 0",
            name="ck_recipes_final_weight_positive",
        ),
        Index("ix_recipes_owner_updated", "owner_user_id", "updated_at", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    final_weight_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
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

    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.position",
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_recipe_ingredients_position_non_negative"),
        CheckConstraint(
            "amount_unit IN ('g', 'serving')",
            name="ck_recipe_ingredients_amount_unit",
        ),
        CheckConstraint("amount > 0", name="ck_recipe_ingredients_amount_positive"),
        CheckConstraint("weight_g > 0", name="ck_recipe_ingredients_weight_positive"),
        CheckConstraint(
            "amount_unit <> 'g' OR amount = weight_g",
            name="ck_recipe_ingredients_gram_amount_weight",
        ),
        CheckConstraint(
            "serving_amount IS NULL AND serving_unit IS NULL AND serving_weight_g IS NULL OR "
            "serving_amount > 0 AND serving_unit IN ('g', 'ml', 'piece', 'serving') AND "
            "serving_weight_g > 0",
            name="ck_recipe_ingredients_serving_complete",
        ),
        CheckConstraint(
            "energy_kcal_per_100g BETWEEN 0 AND 1000",
            name="ck_recipe_ingredients_energy_range",
        ),
        CheckConstraint(
            "protein_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_protein_range",
        ),
        CheckConstraint(
            "fat_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_fat_range",
        ),
        CheckConstraint(
            "carbs_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_carbs_range",
        ),
        CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g BETWEEN 0 AND 100",
            name="ck_recipe_ingredients_fiber_range",
        ),
        UniqueConstraint("recipe_id", "position", name="uq_recipe_ingredients_position"),
        Index("ix_recipe_ingredients_recipe_position", "recipe_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    food_id: Mapped[int | None] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL"), nullable=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

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

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
