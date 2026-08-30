from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import cast

from sqlalchemy import and_, case, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

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


def _edit_distance_at_most_one(left: str, right: str) -> bool:
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    if len(left) > len(right):
        left, right = right, left
    left_index = right_index = differences = 0
    while left_index < len(left) and right_index < len(right):
        if left[left_index] == right[right_index]:
            left_index += 1
            right_index += 1
            continue
        differences += 1
        if differences > 1:
            return False
        if len(left) == len(right):
            left_index += 1
        right_index += 1
    return True


def _simple_typo_match(search_text: str, normalized_query: str) -> bool:
    query_tokens = normalized_query.split()
    candidate_tokens = search_text.split()
    return all(
        any(
            query_token in candidate_token
            or (len(query_token) >= 4 and _edit_distance_at_most_one(query_token, candidate_token))
            for candidate_token in candidate_tokens
        )
        for query_token in query_tokens
    )


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
    external_source = payload.external_source
    values = payload.model_dump(exclude={"external_source"})
    food = Food(
        **values,
        food_type="user",
        owner_user_id=owner.id,
        provenance="user",
        source_name=external_source.provider if external_source is not None else None,
        source_license=external_source.license if external_source is not None else None,
        source_url=str(external_source.source_url) if external_source is not None else None,
        source_license_url=(
            str(external_source.license_url) if external_source is not None else None
        ),
        external_id=external_source.external_id if external_source is not None else None,
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


def get_food_by_barcode_response(
    db: Session,
    current_user: User,
    barcode: str,
) -> FoodResponse | None:
    query, _, _ = _food_metadata_query(db, current_user)
    row = (
        query.filter(Food.barcode == barcode)
        .order_by(
            case((Food.food_type == "user", 0), else_=1).asc(),
            Food.id.asc(),
        )
        .first()
    )
    if row is None:
        return None
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

    editable_fields = set(UserFoodCreate.model_fields) - {"external_source"}
    merged = {field: getattr(food, field) for field in editable_fields}
    merged.update(changes)
    try:
        validated = UserFoodCreate.model_validate(merged)
    except ValueError as exc:
        raise FoodError(str(exc)) from exc

    for field, value in validated.model_dump(exclude={"external_source"}).items():
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
    normalized = " ".join(query_text.split()).casefold().replace("ё", "е")
    if len(normalized) < 2:
        raise FoodError("query must contain at least 2 non-whitespace characters")

    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    exact = escaped
    prefix = f"{escaped}%"
    contains = f"%{escaped}%"
    query, favorites, recent = _food_metadata_query(db, current_user)
    is_postgresql = db.get_bind().dialect.name == "postgresql"
    similarity = func.similarity(Food.search_text, normalized)
    match_condition: ColumnElement[bool] = Food.search_text.like(contains, escape="\\")
    if is_postgresql:
        match_condition = or_(match_condition, Food.search_text.op("%")(normalized))
    filtered = query.filter(match_condition)
    total = filtered.count()
    if total == 0 and not is_postgresql:
        candidates = query.all()
        fuzzy_rows = [
            row for row in candidates if _simple_typo_match(row[0].search_text, normalized)
        ]

        def fuzzy_order(row):
            food, favorite_food_id, favorite_created_at, last_used_at = row
            category = (
                0
                if last_used_at is not None
                else 1
                if favorite_food_id is not None
                else 2
                if food.food_type == "user"
                else 3
                if food.food_type == "system"
                else 4
            )
            return (
                category,
                -(last_used_at.timestamp() if last_used_at is not None else 0),
                -(favorite_created_at.timestamp() if favorite_created_at is not None else 0),
                food.name,
                food.id,
            )

        fuzzy_rows.sort(key=fuzzy_order)
        return FoodListResponse(
            items=_serialize_rows(fuzzy_rows[offset : offset + limit]),
            total=len(fuzzy_rows),
            limit=limit,
            offset=offset,
        )
    exact_name = Food.name.ilike(exact, escape="\\")
    priority_rank = case(
        (and_(Food.food_type == "user", exact_name), 0),
        (recent.c.last_used_at.is_not(None), 1),
        (favorites.c.food_id.is_not(None), 2),
        (exact_name, 3),
        (Food.search_text.like(prefix, escape="\\"), 4),
        (Food.food_type == "user", 5),
        (Food.food_type == "system", 6),
        else_=7,
    )
    rows = (
        filtered.order_by(
            priority_rank.asc(),
            recent.c.last_used_at.desc(),
            favorites.c.favorite_created_at.desc(),
            *((similarity.desc(),) if is_postgresql else ()),
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
