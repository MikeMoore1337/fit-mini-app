from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import cast

from sqlalchemy import and_, case, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.models.food import Food, FoodFavorite
from fitminiapp_api.models.food_diary import FoodDiaryEntry
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import (
    FoodListResponse,
    FoodNutrientsInput,
    FoodResponse,
    FoodType,
    ServingUnit,
    UserFoodCreate,
    UserFoodUpdate,
)

ENERGY_QUANTUM = Decimal("0.01")
MACRO_QUANTUM = Decimal("0.001")
WEIGHT_QUANTUM = Decimal("0.001")


class FoodError(ValueError):
    pass


class FoodNotFoundError(FoodError):
    pass


class FoodConflictError(FoodError):
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
        raise FoodNotFoundError("food not found")
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
        raise FoodNotFoundError("user food not found")
    return food


def _serialize_food(
    food: Food,
    *,
    is_favorite: bool = False,
    last_used_at: datetime | None = None,
) -> FoodResponse:
    return FoodResponse(
        id=food.id,
        name=food.name,
        brand=food.brand,
        barcode=food.barcode,
        energy_kcal_per_100g=cast(Decimal, food.energy_kcal_per_100g),
        protein_g_per_100g=cast(Decimal, food.protein_g_per_100g),
        fat_g_per_100g=cast(Decimal, food.fat_g_per_100g),
        carbs_g_per_100g=cast(Decimal, food.carbs_g_per_100g),
        fiber_g_per_100g=food.fiber_g_per_100g,
        standard_serving_amount=food.standard_serving_amount,
        standard_serving_unit=cast(ServingUnit | None, food.standard_serving_unit),
        standard_serving_weight_g=food.standard_serving_weight_g,
        food_type=cast(FoodType, food.food_type),
        is_favorite=is_favorite,
        last_used_at=last_used_at,
        created_at=food.created_at,
        updated_at=food.updated_at,
    )


def _visible_food_condition(current_user: User):
    return and_(
        Food.status == "active",
        or_(Food.food_type != "user", Food.owner_user_id == current_user.id),
    )


def _food_metadata_query(db: Session, current_user: User):
    recent = (
        db.query(
            FoodDiaryEntry.food_id.label("food_id"),
            func.max(FoodDiaryEntry.updated_at).label("last_used_at"),
        )
        .filter(
            FoodDiaryEntry.user_id == current_user.id,
            FoodDiaryEntry.food_id.is_not(None),
        )
        .group_by(FoodDiaryEntry.food_id)
        .subquery()
    )
    favorites = (
        db.query(
            FoodFavorite.food_id.label("food_id"),
            FoodFavorite.created_at.label("favorite_created_at"),
        )
        .filter(FoodFavorite.user_id == current_user.id)
        .subquery()
    )
    query = (
        db.query(
            Food,
            favorites.c.food_id.label("favorite_food_id"),
            favorites.c.favorite_created_at,
            recent.c.last_used_at,
        )
        .outerjoin(favorites, favorites.c.food_id == Food.id)
        .outerjoin(recent, recent.c.food_id == Food.id)
        .filter(_visible_food_condition(current_user))
    )
    return query, favorites, recent


def _serialize_rows(
    rows: Sequence[tuple[Food, int | None, datetime | None, datetime | None]],
) -> list[FoodResponse]:
    return [
        _serialize_food(
            food,
            is_favorite=favorite_food_id is not None,
            last_used_at=last_used_at,
        )
        for food, favorite_food_id, _favorite_created_at, last_used_at in rows
    ]


def create_user_food_response(
    db: Session,
    owner: User,
    payload: UserFoodCreate,
) -> FoodResponse:
    try:
        food = create_user_food(db, owner, payload)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FoodConflictError("a personal food with this barcode already exists") from exc
    db.refresh(food)
    return _serialize_food(food)


def get_food_response(db: Session, current_user: User, food_id: int) -> FoodResponse:
    query, _, _ = _food_metadata_query(db, current_user)
    row = query.filter(Food.id == food_id).first()
    if row is None:
        raise FoodNotFoundError("food not found")
    return _serialize_rows([row])[0]


def update_user_food(
    db: Session,
    current_user: User,
    food_id: int,
    payload: UserFoodUpdate,
) -> FoodResponse:
    food = get_owned_user_food(db, current_user, food_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise FoodError("at least one field must be provided")

    editable_fields = UserFoodCreate.model_fields
    merged = {field: getattr(food, field) for field in editable_fields}
    merged.update(changes)
    try:
        validated = UserFoodCreate.model_validate(merged)
    except ValueError as exc:
        raise FoodError(str(exc)) from exc

    for field, value in validated.model_dump().items():
        setattr(food, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FoodConflictError("a personal food with this barcode already exists") from exc
    db.refresh(food)
    return get_food_response(db, current_user, food.id)


def delete_user_food(db: Session, current_user: User, food_id: int) -> None:
    food = get_owned_user_food(db, current_user, food_id)
    db.delete(food)
    db.commit()


def set_food_favorite(
    db: Session,
    current_user: User,
    food_id: int,
    *,
    favorite: bool,
) -> FoodResponse | None:
    get_visible_food(db, current_user, food_id)
    stored = db.get(FoodFavorite, (current_user.id, food_id))
    if favorite and stored is None:
        db.add(FoodFavorite(user_id=current_user.id, food_id=food_id))
    elif not favorite and stored is not None:
        db.delete(stored)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if not favorite or db.get(FoodFavorite, (current_user.id, food_id)) is None:
            raise FoodConflictError("could not update food favorite") from exc
    if not favorite:
        return None
    return get_food_response(db, current_user, food_id)


def list_favorite_foods(
    db: Session,
    current_user: User,
    *,
    limit: int,
    offset: int,
) -> FoodListResponse:
    query, favorites, _ = _food_metadata_query(db, current_user)
    filtered = query.filter(favorites.c.food_id.is_not(None))
    total = filtered.count()
    rows = (
        filtered.order_by(
            favorites.c.favorite_created_at.desc(),
            Food.name.asc(),
            Food.id.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return FoodListResponse(
        items=_serialize_rows(rows),
        total=total,
        limit=limit,
        offset=offset,
    )


def list_recent_foods(
    db: Session,
    current_user: User,
    *,
    limit: int,
    offset: int,
) -> FoodListResponse:
    query, _, recent = _food_metadata_query(db, current_user)
    filtered = query.filter(recent.c.last_used_at.is_not(None))
    total = filtered.count()
    rows = (
        filtered.order_by(recent.c.last_used_at.desc(), Food.name.asc(), Food.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return FoodListResponse(
        items=_serialize_rows(rows),
        total=total,
        limit=limit,
        offset=offset,
    )


def search_foods(
    db: Session,
    current_user: User,
    query_text: str,
    *,
    limit: int,
    offset: int,
) -> FoodListResponse:
    normalized = " ".join(query_text.split()).casefold()
    if len(normalized) < 2:
        raise FoodError("query must contain at least 2 non-whitespace characters")

    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    exact = escaped
    prefix = f"{escaped}%"
    contains = f"%{escaped}%"
    query, favorites, recent = _food_metadata_query(db, current_user)
    filtered = query.filter(Food.search_text.like(contains, escape="\\"))
    total = filtered.count()
    category_rank = case(
        (recent.c.last_used_at.is_not(None), 0),
        (favorites.c.food_id.is_not(None), 1),
        (Food.food_type == "user", 2),
        (Food.food_type == "system", 3),
        else_=4,
    )
    match_rank = case(
        (Food.search_text == exact, 0),
        (Food.search_text.like(prefix, escape="\\"), 1),
        else_=2,
    )
    rows = (
        filtered.order_by(
            category_rank.asc(),
            recent.c.last_used_at.desc(),
            favorites.c.favorite_created_at.desc(),
            match_rank.asc(),
            Food.name.asc(),
            Food.id.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return FoodListResponse(
        items=_serialize_rows(rows),
        total=total,
        limit=limit,
        offset=offset,
    )
