from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import (
    FoodListResponse,
    FoodResponse,
    UserFoodCreate,
    UserFoodUpdate,
)
from fitminiapp_api.schemas.food_diary import (
    FoodDiaryDayResponse,
    FoodDiaryEntryCreate,
    FoodDiaryEntryResponse,
    FoodDiaryEntryUpdate,
)
from fitminiapp_api.schemas.nutrition import NutritionTargetResponse, NutritionTargetSave
from fitminiapp_api.services.food_diary import (
    FoodDiaryError,
    FoodDiaryNotFoundError,
    create_food_diary_entry,
    delete_food_diary_entry,
    get_food_diary_day,
    update_food_diary_entry,
)
from fitminiapp_api.services.foods import (
    FoodConflictError,
    FoodError,
    FoodNotFoundError,
    create_user_food_response,
    delete_user_food,
    get_food_response,
    list_favorite_foods,
    list_recent_foods,
    search_foods,
    set_food_favorite,
    update_user_food,
)
from fitminiapp_api.services.nutrition import NutritionError, save_nutrition_target

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
    raise HTTPException(status_code=422, detail=str(exc)) from exc


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


@router.get("/foods/search", response_model=FoodListResponse)
def search_food_library(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10_000),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return search_foods(db, current_user, q, limit=limit, offset=offset)
    except FoodError as exc:
        _raise_food_http_error(exc)


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
