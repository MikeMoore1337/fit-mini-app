from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

MealType = Literal["breakfast", "lunch", "dinner", "snacks"]
DiaryAmountUnit = Literal["g", "serving"]


class FoodDiaryEntryCreate(BaseModel):
    food_id: int = Field(gt=0)
    diary_date: date
    meal_type: MealType
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3, allow_inf_nan=False)
    amount_unit: DiaryAmountUnit = "g"


class FoodDiaryEntryUpdate(BaseModel):
    food_id: int | None = Field(default=None, gt=0)
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
