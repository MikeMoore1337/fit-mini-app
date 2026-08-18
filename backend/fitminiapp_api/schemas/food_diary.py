from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

MealType = Literal["breakfast", "lunch", "dinner", "snacks"]
DiaryAmountUnit = Literal["g", "serving"]


class FoodDiaryEntryCreate(BaseModel):
    food_id: int | None = Field(default=None, gt=0)
    recipe_id: int | None = Field(default=None, gt=0)
    diary_date: date
    meal_type: MealType
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3, allow_inf_nan=False)
    amount_unit: DiaryAmountUnit = "g"

    @model_validator(mode="after")
    def require_single_source(self) -> FoodDiaryEntryCreate:
        if (self.food_id is None) == (self.recipe_id is None):
            raise ValueError("exactly one of food_id or recipe_id must be provided")
        if self.recipe_id is not None and self.amount_unit != "g":
            raise ValueError("recipe diary entries must use grams")
        return self


class FoodDiaryEntryUpdate(BaseModel):
    food_id: int | None = Field(default=None, gt=0)
    recipe_id: int | None = Field(default=None, gt=0)
    diary_date: date | None = None
    meal_type: MealType | None = None
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=3,
        allow_inf_nan=False,
    )
    amount_unit: DiaryAmountUnit | None = None

    @model_validator(mode="after")
    def require_change(self) -> FoodDiaryEntryUpdate:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("updated fields must not be null")
        if "food_id" in self.model_fields_set and "recipe_id" in self.model_fields_set:
            raise ValueError("food_id and recipe_id cannot be updated together")
        if self.recipe_id is not None and self.amount_unit == "serving":
            raise ValueError("recipe diary entries must use grams")
        return self


class FoodDiaryNutrition(BaseModel):
    energy_kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbs_g: Decimal
    fiber_g: Decimal | None


class FoodDiaryEntryResponse(BaseModel):
    id: int
    diary_date: date
    meal_type: MealType
    food_id: int | None
    recipe_id: int | None
    food_name: str
    food_brand: str | None
    amount: Decimal
    amount_unit: DiaryAmountUnit
    weight_g: Decimal
    serving_amount: Decimal | None
    serving_unit: str | None
    serving_weight_g: Decimal | None
    nutrition: FoodDiaryNutrition
    created_at: datetime
    updated_at: datetime


class FoodDiaryMeal(BaseModel):
    meal_type: MealType
    entries: list[FoodDiaryEntryResponse]
    totals: FoodDiaryNutrition


class FoodDiaryTargets(BaseModel):
    energy_kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbs_g: Decimal


class FoodDiaryDayResponse(BaseModel):
    diary_date: date
    timezone: str
    meals: list[FoodDiaryMeal]
    totals: FoodDiaryNutrition
    targets: FoodDiaryTargets | None
    remaining: FoodDiaryTargets | None


class FoodDiaryCopyProduct(BaseModel):
    source_entry_id: int = Field(gt=0)
    source_date: date
    source_meal_type: MealType
    target_date: date
    target_meal_type: MealType


class FoodDiaryCopyMeal(BaseModel):
    source_date: date
    source_meal_type: MealType
    target_date: date
    target_meal_type: MealType


class FoodDiaryCopyDay(BaseModel):
    source_date: date
    target_date: date


class FoodDiaryCopyResponse(BaseModel):
    copy_scope: Literal["product", "meal", "day"]
    source_date: date
    source_meal_type: MealType | None
    target_date: date
    target_meal_type: MealType | None
    entries: list[FoodDiaryEntryResponse]
    replayed: bool
