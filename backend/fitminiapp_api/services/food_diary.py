from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Literal, cast

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import get_user_timezone_name, today_for_user
from fitminiapp_api.models.food import Food
from fitminiapp_api.models.food_diary import FoodDiaryCopyOperation, FoodDiaryEntry
from fitminiapp_api.models.recipe import Recipe
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import FoodNutrientsInput
from fitminiapp_api.schemas.food_diary import (
    DiaryAmountUnit,
    FoodDiaryCopyDay,
    FoodDiaryCopyMeal,
    FoodDiaryCopyProduct,
    FoodDiaryCopyResponse,
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
from fitminiapp_api.services.recipes import (
    RecipeCalculation,
    RecipeError,
    RecipeNotFoundError,
    calculate_recipe,
    get_owned_recipe,
)

MEAL_TYPES: tuple[MealType, ...] = ("breakfast", "lunch", "dinner", "snacks")
ZERO = Decimal("0")
CopyScope = Literal["product", "meal", "day"]


class FoodDiaryError(ValueError):
    pass


class FoodDiaryNotFoundError(FoodDiaryError):
    pass


class FoodDiaryConflictError(FoodDiaryError):
    pass


def _validate_diary_date(user: User, value: date) -> None:
    if value > today_for_user(user):
        raise FoodDiaryError("future diary dates are not allowed")


def _visible_food(db: Session, user: User, food_id: int) -> Food:
    try:
        return get_visible_food(db, user, food_id)
    except FoodError as exc:
        raise FoodDiaryNotFoundError("food not found") from exc


def _owned_recipe(db: Session, user: User, recipe_id: int) -> Recipe:
    try:
        return get_owned_recipe(db, user, recipe_id)
    except RecipeNotFoundError as exc:
        raise FoodDiaryNotFoundError("recipe not found") from exc


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


def _recipe_as_food(calculation: RecipeCalculation) -> Food:
    nutrients = calculation.nutrients_per_100g
    return Food(
        energy_kcal_per_100g=nutrients.energy_kcal_per_100g,
        protein_g_per_100g=nutrients.protein_g_per_100g,
        fat_g_per_100g=nutrients.fat_g_per_100g,
        carbs_g_per_100g=nutrients.carbs_g_per_100g,
        fiber_g_per_100g=nutrients.fiber_g_per_100g,
    )


def _entry_snapshot_as_food(entry: FoodDiaryEntry) -> Food:
    return Food(
        energy_kcal_per_100g=entry.energy_kcal_per_100g,
        protein_g_per_100g=entry.protein_g_per_100g,
        fat_g_per_100g=entry.fat_g_per_100g,
        carbs_g_per_100g=entry.carbs_g_per_100g,
        fiber_g_per_100g=entry.fiber_g_per_100g,
        standard_serving_weight_g=entry.serving_weight_g,
    )


def _copy_food_snapshot(entry: FoodDiaryEntry, food: Food) -> None:
    entry.food_id = food.id
    entry.recipe_id = None
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


def _copy_recipe_snapshot(
    entry: FoodDiaryEntry,
    recipe: Recipe,
    calculation: RecipeCalculation,
) -> None:
    nutrients = calculation.nutrients_per_100g
    entry.food_id = None
    entry.recipe_id = recipe.id
    entry.food_name = recipe.name
    entry.food_brand = None
    entry.energy_kcal_per_100g = nutrients.energy_kcal_per_100g
    entry.protein_g_per_100g = nutrients.protein_g_per_100g
    entry.fat_g_per_100g = nutrients.fat_g_per_100g
    entry.carbs_g_per_100g = nutrients.carbs_g_per_100g
    entry.fiber_g_per_100g = nutrients.fiber_g_per_100g
    entry.serving_amount = None
    entry.serving_unit = None
    entry.serving_weight_g = None


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
        recipe_id=entry.recipe_id,
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
    entry = FoodDiaryEntry(
        user_id=user.id,
        diary_date=payload.diary_date,
        meal_type=payload.meal_type,
        amount=payload.amount,
        amount_unit=payload.amount_unit,
    )
    if payload.food_id is not None:
        food = _visible_food(db, user, payload.food_id)
        calculation = _calculate_amount(food, payload.amount, payload.amount_unit)
        _copy_food_snapshot(entry, food)
    else:
        recipe = _owned_recipe(db, user, cast(int, payload.recipe_id))
        try:
            recipe_calculation = calculate_recipe(recipe)
        except RecipeError as exc:
            raise FoodDiaryError(str(exc)) from exc
        calculation = _calculate_amount(_recipe_as_food(recipe_calculation), payload.amount, "g")
        _copy_recipe_snapshot(entry, recipe, recipe_calculation)
    entry.weight_g = calculation.weight_g
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
    recipe = _owned_recipe(db, user, payload.recipe_id) if payload.recipe_id is not None else None
    amount = payload.amount if payload.amount is not None else entry.amount
    amount_unit = (
        payload.amount_unit
        if payload.amount_unit is not None
        else cast(DiaryAmountUnit, entry.amount_unit)
    )

    if (
        recipe is not None or (food is None and entry.recipe_id is not None)
    ) and amount_unit != "g":
        raise FoodDiaryError("recipe diary entries must use grams")
    if food is not None:
        calculation_food = food
    elif recipe is not None:
        try:
            recipe_calculation = calculate_recipe(recipe)
        except RecipeError as exc:
            raise FoodDiaryError(str(exc)) from exc
        calculation_food = _recipe_as_food(recipe_calculation)
    else:
        calculation_food = _entry_snapshot_as_food(entry)
    calculation = _calculate_amount(calculation_food, amount, amount_unit)

    if food is not None:
        _copy_food_snapshot(entry, food)
    elif recipe is not None:
        _copy_recipe_snapshot(entry, recipe, recipe_calculation)
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


def _request_fingerprint(scope: CopyScope, payload: BaseModel) -> str:
    canonical = json.dumps(
        {"copy_scope": scope, **payload.model_dump(mode="json")},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _normalize_idempotency_key(value: str) -> str:
    normalized = value.strip()
    if len(normalized) < 8 or len(normalized) > 128:
        raise FoodDiaryError("Idempotency-Key must contain 8 to 128 characters")
    return normalized


def _copy_response(
    db: Session,
    operation: FoodDiaryCopyOperation,
    *,
    replayed: bool,
) -> FoodDiaryCopyResponse:
    entries = (
        db.query(FoodDiaryEntry)
        .filter(FoodDiaryEntry.copy_operation_id == operation.id)
        .order_by(FoodDiaryEntry.id.asc())
        .all()
    )
    return FoodDiaryCopyResponse(
        copy_scope=cast(CopyScope, operation.copy_scope),
        source_date=operation.source_date,
        source_meal_type=cast(MealType | None, operation.source_meal_type),
        target_date=operation.target_date,
        target_meal_type=cast(MealType | None, operation.target_meal_type),
        entries=[_serialize_entry(entry) for entry in entries],
        replayed=replayed,
    )


def _existing_copy_operation(
    db: Session,
    user: User,
    idempotency_key: str,
    fingerprint: str,
) -> FoodDiaryCopyResponse | None:
    operation = (
        db.query(FoodDiaryCopyOperation)
        .filter(
            FoodDiaryCopyOperation.user_id == user.id,
            FoodDiaryCopyOperation.idempotency_key == idempotency_key,
        )
        .first()
    )
    if operation is None:
        return None
    if operation.request_fingerprint != fingerprint:
        raise FoodDiaryConflictError("Idempotency-Key was already used for another request")
    return _copy_response(db, operation, replayed=True)


def _clone_entry(
    source: FoodDiaryEntry,
    *,
    target_date: date,
    target_meal_type: MealType,
    operation_id: int,
) -> FoodDiaryEntry:
    return FoodDiaryEntry(
        user_id=source.user_id,
        food_id=source.food_id,
        recipe_id=source.recipe_id,
        copy_operation_id=operation_id,
        copied_from_entry_id=source.id,
        diary_date=target_date,
        meal_type=target_meal_type,
        amount=source.amount,
        amount_unit=source.amount_unit,
        weight_g=source.weight_g,
        food_name=source.food_name,
        food_brand=source.food_brand,
        energy_kcal_per_100g=source.energy_kcal_per_100g,
        protein_g_per_100g=source.protein_g_per_100g,
        fat_g_per_100g=source.fat_g_per_100g,
        carbs_g_per_100g=source.carbs_g_per_100g,
        fiber_g_per_100g=source.fiber_g_per_100g,
        serving_amount=source.serving_amount,
        serving_unit=source.serving_unit,
        serving_weight_g=source.serving_weight_g,
    )


def _perform_copy(
    db: Session,
    user: User,
    *,
    scope: CopyScope,
    payload: BaseModel,
    idempotency_key: str,
    source_entry_id: int | None,
    source_date: date,
    source_meal_type: MealType | None,
    target_date: date,
    target_meal_type: MealType | None,
) -> FoodDiaryCopyResponse:
    key = _normalize_idempotency_key(idempotency_key)
    fingerprint = _request_fingerprint(scope, payload)
    replay = _existing_copy_operation(db, user, key, fingerprint)
    if replay is not None:
        return replay

    _validate_diary_date(user, source_date)
    _validate_diary_date(user, target_date)
    if scope == "meal" and (source_date, source_meal_type) == (
        target_date,
        target_meal_type,
    ):
        raise FoodDiaryError("source and target meal must differ")
    if scope == "day" and source_date == target_date:
        raise FoodDiaryError("source and target day must differ")

    source_query = db.query(FoodDiaryEntry).filter(
        FoodDiaryEntry.user_id == user.id,
        FoodDiaryEntry.diary_date == source_date,
    )
    if scope == "product":
        source_query = source_query.filter(
            FoodDiaryEntry.id == source_entry_id,
            FoodDiaryEntry.meal_type == source_meal_type,
        )
    elif scope == "meal":
        source_query = source_query.filter(FoodDiaryEntry.meal_type == source_meal_type)
    source_entries = source_query.order_by(FoodDiaryEntry.id.asc()).all()
    if not source_entries:
        if scope == "product":
            raise FoodDiaryNotFoundError("source diary entry not found")
        raise FoodDiaryError(f"source {scope} is empty")

    operation = FoodDiaryCopyOperation(
        user_id=user.id,
        idempotency_key=key,
        request_fingerprint=fingerprint,
        copy_scope=scope,
        source_entry_id=source_entry_id,
        source_date=source_date,
        source_meal_type=source_meal_type,
        target_date=target_date,
        target_meal_type=target_meal_type,
    )
    db.add(operation)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        replay = _existing_copy_operation(db, user, key, fingerprint)
        if replay is None:
            raise FoodDiaryConflictError("copy request could not be completed")
        return replay

    for source in source_entries:
        destination_meal = (
            cast(MealType, source.meal_type) if scope == "day" else cast(MealType, target_meal_type)
        )
        db.add(
            _clone_entry(
                source,
                target_date=target_date,
                target_meal_type=destination_meal,
                operation_id=operation.id,
            )
        )
    db.commit()
    return _copy_response(db, operation, replayed=False)


def copy_diary_product(
    db: Session,
    user: User,
    payload: FoodDiaryCopyProduct,
    idempotency_key: str,
) -> FoodDiaryCopyResponse:
    return _perform_copy(
        db,
        user,
        scope="product",
        payload=payload,
        idempotency_key=idempotency_key,
        source_entry_id=payload.source_entry_id,
        source_date=payload.source_date,
        source_meal_type=payload.source_meal_type,
        target_date=payload.target_date,
        target_meal_type=payload.target_meal_type,
    )


def copy_diary_meal(
    db: Session,
    user: User,
    payload: FoodDiaryCopyMeal,
    idempotency_key: str,
) -> FoodDiaryCopyResponse:
    return _perform_copy(
        db,
        user,
        scope="meal",
        payload=payload,
        idempotency_key=idempotency_key,
        source_entry_id=None,
        source_date=payload.source_date,
        source_meal_type=payload.source_meal_type,
        target_date=payload.target_date,
        target_meal_type=payload.target_meal_type,
    )


def copy_diary_day(
    db: Session,
    user: User,
    payload: FoodDiaryCopyDay,
    idempotency_key: str,
) -> FoodDiaryCopyResponse:
    return _perform_copy(
        db,
        user,
        scope="day",
        payload=payload,
        idempotency_key=idempotency_key,
        source_entry_id=None,
        source_date=payload.source_date,
        source_meal_type=None,
        target_date=payload.target_date,
        target_meal_type=None,
    )
