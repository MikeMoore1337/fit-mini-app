from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import (
    FoodBarcodeLookupResponse,
    FoodListResponse,
    FoodResponse,
    FoodSearchResponse,
    UserFoodCreate,
    UserFoodUpdate,
    validate_gtin,
)
from fitminiapp_api.schemas.food_diary import (
    FoodDiaryCopyDay,
    FoodDiaryCopyMeal,
    FoodDiaryCopyProduct,
    FoodDiaryCopyResponse,
    FoodDiaryDayResponse,
    FoodDiaryEntryCreate,
    FoodDiaryEntryResponse,
    FoodDiaryEntryUpdate,
)
from fitminiapp_api.schemas.nutrition import NutritionTargetResponse, NutritionTargetSave
from fitminiapp_api.schemas.recipe import (
    RecipeCreate,
    RecipeListResponse,
    RecipeResponse,
    RecipeUpdate,
)
from fitminiapp_api.services.food_catalog import (
    get_food_catalog_item_by_barcode,
    search_food_catalog,
)
from fitminiapp_api.services.food_diary import (
    FoodDiaryConflictError,
    FoodDiaryError,
    FoodDiaryNotFoundError,
    copy_diary_day,
    copy_diary_meal,
    copy_diary_product,
    create_food_diary_entry,
    delete_food_diary_entry,
    get_food_diary_day,
    update_food_diary_entry,
)
from fitminiapp_api.services.food_provider import FoodProvider, get_food_provider
from fitminiapp_api.services.foods import (
    FoodConflictError,
    FoodError,
    FoodNotFoundError,
    create_user_food_response,
    delete_user_food,
    get_food_response,
    list_favorite_foods,
    list_recent_foods,
    set_food_favorite,
    update_user_food,
)
from fitminiapp_api.services.nutrition import NutritionError, save_nutrition_target
from fitminiapp_api.services.recipes import (
    RecipeError,
    RecipeNotFoundError,
    create_recipe,
    delete_recipe,
    get_recipe_response,
    list_recipes,
    update_recipe,
)

router = APIRouter()


def _raise_food_http_error(exc: FoodError) -> None:
    if isinstance(exc, FoodNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, FoodConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise HTTPException(status_code=422, detail=str(exc)) from exc


def _raise_diary_http_error(exc: FoodDiaryError) -> None:
    if isinstance(exc, FoodDiaryNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, FoodDiaryConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise HTTPException(status_code=422, detail=str(exc)) from exc


def _raise_recipe_http_error(exc: RecipeError) -> None:
    if isinstance(exc, RecipeNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise HTTPException(status_code=422, detail=str(exc)) from exc


IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=8, max_length=128),
]


@router.post(
    "/foods",
    response_model=FoodResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_food(
    payload: UserFoodCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return create_user_food_response(db, current_user, payload)
    except FoodError as exc:
        _raise_food_http_error(exc)


@router.get("/foods/search", response_model=FoodSearchResponse)
def search_food_library(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10_000),
    include_external: bool = False,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    provider: FoodProvider | None = Depends(get_food_provider),
):
    try:
        return search_food_catalog(
            db,
            current_user,
            q,
            limit=limit,
            offset=offset,
            include_external=include_external,
            provider=provider,
        )
    except FoodError as exc:
        _raise_food_http_error(exc)


@router.get("/foods/barcode/{barcode}", response_model=FoodBarcodeLookupResponse)
def get_food_by_barcode(
    barcode: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    provider: FoodProvider | None = Depends(get_food_provider),
):
    try:
        normalized = validate_gtin(barcode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if normalized is None:
        raise HTTPException(status_code=422, detail="barcode is required")
    return get_food_catalog_item_by_barcode(
        db,
        current_user,
        normalized,
        provider=provider,
    )


@router.get("/foods/recent", response_model=FoodListResponse)
def get_recent_foods(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10_000),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return list_recent_foods(db, current_user, limit=limit, offset=offset)


@router.get("/foods/favorites", response_model=FoodListResponse)
def get_favorite_foods(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10_000),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return list_favorite_foods(db, current_user, limit=limit, offset=offset)


@router.get("/foods/{food_id}", response_model=FoodResponse)
def get_food(
    food_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return get_food_response(db, current_user, food_id)
    except FoodError as exc:
        _raise_food_http_error(exc)


@router.patch("/foods/{food_id}", response_model=FoodResponse)
def update_food(
    food_id: int,
    payload: UserFoodUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return update_user_food(db, current_user, food_id, payload)
    except FoodError as exc:
        _raise_food_http_error(exc)


@router.delete("/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(
    food_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        delete_user_food(db, current_user, food_id)
    except FoodError as exc:
        _raise_food_http_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/foods/{food_id}/favorite", response_model=FoodResponse)
def add_food_favorite(
    food_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return set_food_favorite(db, current_user, food_id, favorite=True)
    except FoodError as exc:
        _raise_food_http_error(exc)


@router.delete("/foods/{food_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def remove_food_favorite(
    food_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        set_food_favorite(db, current_user, food_id, favorite=False)
    except FoodError as exc:
        _raise_food_http_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/recipes",
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_recipe(
    payload: RecipeCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return create_recipe(db, current_user, payload)
    except RecipeError as exc:
        _raise_recipe_http_error(exc)


@router.get("/recipes", response_model=RecipeListResponse)
def get_recipes(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10_000),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return list_recipes(db, current_user, limit=limit, offset=offset)


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return get_recipe_response(db, current_user, recipe_id)
    except RecipeError as exc:
        _raise_recipe_http_error(exc)


@router.patch("/recipes/{recipe_id}", response_model=RecipeResponse)
def patch_recipe(
    recipe_id: int,
    payload: RecipeUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return update_recipe(db, current_user, recipe_id, payload)
    except RecipeError as exc:
        _raise_recipe_http_error(exc)


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recipe(
    recipe_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        delete_recipe(db, current_user, recipe_id)
    except RecipeError as exc:
        _raise_recipe_http_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/diary", response_model=FoodDiaryDayResponse)
def get_diary_day(
    diary_date: date | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return get_food_diary_day(db, current_user, diary_date)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)


@router.post(
    "/diary/entries",
    response_model=FoodDiaryEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_diary_entry(
    payload: FoodDiaryEntryCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return create_food_diary_entry(db, current_user, payload)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)


@router.patch("/diary/entries/{entry_id}", response_model=FoodDiaryEntryResponse)
def update_diary_entry(
    entry_id: int,
    payload: FoodDiaryEntryUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return update_food_diary_entry(db, current_user, entry_id, payload)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)


@router.delete("/diary/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diary_entry(
    entry_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        delete_food_diary_entry(db, current_user, entry_id)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/diary/copy/product",
    response_model=FoodDiaryCopyResponse,
    status_code=status.HTTP_201_CREATED,
)
def copy_product(
    payload: FoodDiaryCopyProduct,
    idempotency_key: IdempotencyKey,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return copy_diary_product(db, current_user, payload, idempotency_key)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)


@router.post(
    "/diary/copy/meal",
    response_model=FoodDiaryCopyResponse,
    status_code=status.HTTP_201_CREATED,
)
def copy_meal(
    payload: FoodDiaryCopyMeal,
    idempotency_key: IdempotencyKey,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return copy_diary_meal(db, current_user, payload, idempotency_key)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)


@router.post(
    "/diary/copy/day",
    response_model=FoodDiaryCopyResponse,
    status_code=status.HTTP_201_CREATED,
)
def copy_day(
    payload: FoodDiaryCopyDay,
    idempotency_key: IdempotencyKey,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return copy_diary_day(db, current_user, payload, idempotency_key)
    except FoodDiaryError as exc:
        _raise_diary_http_error(exc)


@router.post("/targets", response_model=NutritionTargetResponse)
def save_target(
    payload: NutritionTargetSave,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return save_nutrition_target(db, current_user, payload)
    except NutritionError as exc:
        detail = str(exc)
        if detail == "Target user not found":
            raise HTTPException(status_code=404, detail=detail)
        if detail == "No permission to manage this user":
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
