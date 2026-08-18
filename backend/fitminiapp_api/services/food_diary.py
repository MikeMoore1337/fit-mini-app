from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import get_user_timezone_name, today_for_user
from fitminiapp_api.models.food import Food
from fitminiapp_api.models.food_diary import FoodDiaryEntry
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import FoodNutrientsInput
from fitminiapp_api.schemas.food_diary import (
    DiaryAmountUnit,
    FoodDiaryDayResponse,
    FoodDiaryEntryCreate,
    FoodDiaryEntryResponse,
    FoodDiaryEntryUpdate,
    FoodDiaryMeal,
    FoodDiaryNutrition,
    FoodDiaryTargets,
    MealType,
)
from fitminiapp_api.services.foods import (
    FoodError,
    FoodNutrition,
    calculate_food_nutrition,
    calculate_food_servings,
    get_visible_food,
)
from fitminiapp_api.services.nutrition import get_nutrition_target_for_user

MEAL_TYPES: tuple[MealType, ...] = ("breakfast", "lunch", "dinner", "snacks")
ZERO = Decimal("0")


class FoodDiaryError(ValueError):
    pass


class FoodDiaryNotFoundError(FoodDiaryError):
    pass


def _validate_diary_date(user: User, value: date) -> None:
    if value > today_for_user(user):
        raise FoodDiaryError("future diary dates are not allowed")


def _visible_food(db: Session, user: User, food_id: int) -> Food:
    try:
        return get_visible_food(db, user, food_id)
    except FoodError as exc:
        raise FoodDiaryNotFoundError("food not found") from exc


def _calculate_amount(
    food: Food,
    amount: Decimal,
    amount_unit: DiaryAmountUnit,
) -> FoodNutrition:
    try:
        if amount_unit == "g":
            nutrients = FoodNutrientsInput(
                energy_kcal_per_100g=food.energy_kcal_per_100g,
                protein_g_per_100g=food.protein_g_per_100g,
                fat_g_per_100g=food.fat_g_per_100g,
                carbs_g_per_100g=food.carbs_g_per_100g,
                fiber_g_per_100g=food.fiber_g_per_100g,
            )
            return calculate_food_nutrition(nutrients, amount)
        return calculate_food_servings(food, amount)
    except FoodError as exc:
        raise FoodDiaryError(str(exc)) from exc


def _copy_food_snapshot(entry: FoodDiaryEntry, food: Food) -> None:
    entry.food_id = food.id
    entry.food_name = food.name
    entry.food_brand = food.brand
    entry.energy_kcal_per_100g = cast(Decimal, food.energy_kcal_per_100g)
    entry.protein_g_per_100g = cast(Decimal, food.protein_g_per_100g)
    entry.fat_g_per_100g = cast(Decimal, food.fat_g_per_100g)
    entry.carbs_g_per_100g = cast(Decimal, food.carbs_g_per_100g)
    entry.fiber_g_per_100g = food.fiber_g_per_100g
    entry.serving_amount = food.standard_serving_amount
    entry.serving_unit = food.standard_serving_unit
    entry.serving_weight_g = food.standard_serving_weight_g


def _entry_nutrition(entry: FoodDiaryEntry) -> FoodDiaryNutrition:
    calculated = calculate_food_nutrition(
        FoodNutrientsInput(
            energy_kcal_per_100g=entry.energy_kcal_per_100g,
            protein_g_per_100g=entry.protein_g_per_100g,
            fat_g_per_100g=entry.fat_g_per_100g,
            carbs_g_per_100g=entry.carbs_g_per_100g,
            fiber_g_per_100g=entry.fiber_g_per_100g,
        ),
        entry.weight_g,
    )
    return FoodDiaryNutrition(
        energy_kcal=cast(Decimal, calculated.energy_kcal),
        protein_g=cast(Decimal, calculated.protein_g),
        fat_g=cast(Decimal, calculated.fat_g),
        carbs_g=cast(Decimal, calculated.carbs_g),
        fiber_g=calculated.fiber_g,
    )


def _serialize_entry(entry: FoodDiaryEntry) -> FoodDiaryEntryResponse:
    return FoodDiaryEntryResponse(
        id=entry.id,
        diary_date=entry.diary_date,
        meal_type=cast(MealType, entry.meal_type),
        food_id=entry.food_id,
        food_name=entry.food_name,
        food_brand=entry.food_brand,
        amount=entry.amount,
        amount_unit=cast(DiaryAmountUnit, entry.amount_unit),
        weight_g=entry.weight_g,
        serving_amount=entry.serving_amount,
        serving_unit=entry.serving_unit,
        serving_weight_g=entry.serving_weight_g,
        nutrition=_entry_nutrition(entry),
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _sum_nutrition(values: list[FoodDiaryNutrition]) -> FoodDiaryNutrition:
    fiber_values = [value.fiber_g for value in values]
    fiber = ZERO if not fiber_values else None
    if fiber_values and all(value is not None for value in fiber_values):
        fiber = sum((value for value in fiber_values if value is not None), start=ZERO)
    return FoodDiaryNutrition(
        energy_kcal=sum((value.energy_kcal for value in values), start=ZERO),
        protein_g=sum((value.protein_g for value in values), start=ZERO),
        fat_g=sum((value.fat_g for value in values), start=ZERO),
        carbs_g=sum((value.carbs_g for value in values), start=ZERO),
        fiber_g=fiber,
    )


def create_food_diary_entry(
    db: Session,
    user: User,
    payload: FoodDiaryEntryCreate,
) -> FoodDiaryEntryResponse:
    _validate_diary_date(user, payload.diary_date)
    food = _visible_food(db, user, payload.food_id)
    calculation = _calculate_amount(food, payload.amount, payload.amount_unit)
    entry = FoodDiaryEntry(
        user_id=user.id,
        diary_date=payload.diary_date,
        meal_type=payload.meal_type,
        amount=payload.amount,
        amount_unit=payload.amount_unit,
        weight_g=calculation.weight_g,
    )
    _copy_food_snapshot(entry, food)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _serialize_entry(entry)


def update_food_diary_entry(
    db: Session,
    user: User,
    entry_id: int,
    payload: FoodDiaryEntryUpdate,
) -> FoodDiaryEntryResponse:
    entry = (
        db.query(FoodDiaryEntry)
        .filter(FoodDiaryEntry.id == entry_id, FoodDiaryEntry.user_id == user.id)
        .first()
    )
    if entry is None:
        raise FoodDiaryNotFoundError("diary entry not found")

    diary_date = payload.diary_date if payload.diary_date is not None else entry.diary_date
    _validate_diary_date(user, diary_date)
    food = _visible_food(db, user, payload.food_id) if payload.food_id is not None else None
    amount = payload.amount if payload.amount is not None else entry.amount
    amount_unit = (
        payload.amount_unit
        if payload.amount_unit is not None
        else cast(DiaryAmountUnit, entry.amount_unit)
    )

    calculation_food = food
    if calculation_food is None:
        calculation_food = Food(
            energy_kcal_per_100g=entry.energy_kcal_per_100g,
            protein_g_per_100g=entry.protein_g_per_100g,
            fat_g_per_100g=entry.fat_g_per_100g,
            carbs_g_per_100g=entry.carbs_g_per_100g,
            fiber_g_per_100g=entry.fiber_g_per_100g,
            standard_serving_weight_g=entry.serving_weight_g,
        )
    calculation = _calculate_amount(calculation_food, amount, amount_unit)

    if food is not None:
        _copy_food_snapshot(entry, food)
    entry.diary_date = diary_date
    if payload.meal_type is not None:
        entry.meal_type = payload.meal_type
    entry.amount = amount
    entry.amount_unit = amount_unit
    entry.weight_g = calculation.weight_g
    db.commit()
    db.refresh(entry)
    return _serialize_entry(entry)


def delete_food_diary_entry(db: Session, user: User, entry_id: int) -> None:
    entry = (
        db.query(FoodDiaryEntry)
        .filter(FoodDiaryEntry.id == entry_id, FoodDiaryEntry.user_id == user.id)
        .first()
    )
    if entry is None:
        raise FoodDiaryNotFoundError("diary entry not found")
    db.delete(entry)
    db.commit()


def get_food_diary_day(
    db: Session,
    user: User,
    diary_date: date | None,
) -> FoodDiaryDayResponse:
    selected_date = diary_date or today_for_user(user)
    _validate_diary_date(user, selected_date)
    entries = (
        db.query(FoodDiaryEntry)
        .filter(
            FoodDiaryEntry.user_id == user.id,
            FoodDiaryEntry.diary_date == selected_date,
        )
        .order_by(FoodDiaryEntry.meal_type.asc(), FoodDiaryEntry.id.asc())
        .all()
    )
    serialized = [_serialize_entry(entry) for entry in entries]
    meals = []
    for meal_type in MEAL_TYPES:
        meal_entries = [entry for entry in serialized if entry.meal_type == meal_type]
        meals.append(
            FoodDiaryMeal(
                meal_type=meal_type,
                entries=meal_entries,
                totals=_sum_nutrition([entry.nutrition for entry in meal_entries]),
            )
        )
    totals = _sum_nutrition([entry.nutrition for entry in serialized])

    nutrition_target = get_nutrition_target_for_user(db, user)
    targets = None
    remaining = None
    if nutrition_target is not None:
        targets = FoodDiaryTargets(
            energy_kcal=Decimal(nutrition_target.calories),
            protein_g=Decimal(nutrition_target.protein_g),
            fat_g=Decimal(nutrition_target.fat_g),
            carbs_g=Decimal(nutrition_target.carbs_g),
        )
        remaining = FoodDiaryTargets(
            energy_kcal=targets.energy_kcal - totals.energy_kcal,
            protein_g=targets.protein_g - totals.protein_g,
            fat_g=targets.fat_g - totals.fat_g,
            carbs_g=targets.carbs_g - totals.carbs_g,
        )

    return FoodDiaryDayResponse(
        diary_date=selected_date,
        timezone=get_user_timezone_name(user),
        meals=meals,
        totals=totals,
        targets=targets,
        remaining=remaining,
    )
