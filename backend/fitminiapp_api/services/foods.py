from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from fitminiapp_api.models.food import Food
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import FoodNutrientsInput, UserFoodCreate

ENERGY_QUANTUM = Decimal("0.01")
MACRO_QUANTUM = Decimal("0.001")
WEIGHT_QUANTUM = Decimal("0.001")


class FoodError(ValueError):
    pass


@dataclass(frozen=True)
class FoodNutrition:
    weight_g: Decimal
    energy_kcal: Decimal | None
    protein_g: Decimal | None
    fat_g: Decimal | None
    carbs_g: Decimal | None
    fiber_g: Decimal | None


def _scale(value: Decimal | None, factor: Decimal, quantum: Decimal) -> Decimal | None:
    if value is None:
        return None
    return (value * factor).quantize(quantum, rounding=ROUND_HALF_UP)


def calculate_food_nutrition(
    nutrients: FoodNutrientsInput,
    weight_g: Decimal,
) -> FoodNutrition:
    if not weight_g.is_finite() or weight_g <= 0:
        raise FoodError("weight_g must be a positive finite decimal")
    normalized_weight = weight_g.quantize(WEIGHT_QUANTUM, rounding=ROUND_HALF_UP)
    if normalized_weight <= 0:
        raise FoodError("weight_g is below the supported 0.001 g precision")
    factor = normalized_weight / Decimal(100)
    return FoodNutrition(
        weight_g=normalized_weight,
        energy_kcal=_scale(nutrients.energy_kcal_per_100g, factor, ENERGY_QUANTUM),
        protein_g=_scale(nutrients.protein_g_per_100g, factor, MACRO_QUANTUM),
        fat_g=_scale(nutrients.fat_g_per_100g, factor, MACRO_QUANTUM),
        carbs_g=_scale(nutrients.carbs_g_per_100g, factor, MACRO_QUANTUM),
        fiber_g=_scale(nutrients.fiber_g_per_100g, factor, MACRO_QUANTUM),
    )


def calculate_food_servings(food: Food, servings: Decimal) -> FoodNutrition:
    if food.standard_serving_weight_g is None:
        raise FoodError("food has no standard serving weight")
    if not servings.is_finite() or servings <= 0:
        raise FoodError("servings must be a positive finite decimal")
    nutrients = FoodNutrientsInput(
        energy_kcal_per_100g=food.energy_kcal_per_100g,
        protein_g_per_100g=food.protein_g_per_100g,
        fat_g_per_100g=food.fat_g_per_100g,
        carbs_g_per_100g=food.carbs_g_per_100g,
        fiber_g_per_100g=food.fiber_g_per_100g,
    )
    return calculate_food_nutrition(nutrients, food.standard_serving_weight_g * servings)


def create_user_food(db: Session, owner: User, payload: UserFoodCreate) -> Food:
    food = Food(
        **payload.model_dump(),
        food_type="user",
        owner_user_id=owner.id,
        provenance="user",
        trust_level="unverified",
        status="active",
    )
    db.add(food)
    db.flush()
    return food


def list_visible_foods(db: Session, current_user: User) -> list[Food]:
    return (
        db.query(Food)
        .filter(
            Food.status == "active",
            or_(Food.food_type != "user", Food.owner_user_id == current_user.id),
        )
        .order_by(Food.name.asc(), Food.id.asc())
        .all()
    )


def get_visible_food(db: Session, current_user: User, food_id: int) -> Food:
    food = (
        db.query(Food)
        .filter(
            Food.id == food_id,
            Food.status == "active",
            or_(Food.food_type != "user", Food.owner_user_id == current_user.id),
        )
        .first()
    )
    if food is None:
        raise FoodError("food not found")
    return food


def get_owned_user_food(db: Session, current_user: User, food_id: int) -> Food:
    food = (
        db.query(Food)
        .filter(
            Food.id == food_id,
            Food.food_type == "user",
            Food.owner_user_id == current_user.id,
        )
        .first()
    )
    if food is None:
        raise FoodError("user food not found")
    return food
