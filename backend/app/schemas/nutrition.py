from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NutritionTargetSave(BaseModel):
    target_telegram_user_id: int | None = Field(default=None, ge=1)
    sex: Literal["male", "female"]
    weight_kg: float = Field(ge=20, le=500, allow_inf_nan=False)
    height_cm: float = Field(ge=50, le=280, allow_inf_nan=False)
    age: float = Field(ge=12, le=120, allow_inf_nan=False)
    strength_trainings_per_week: int = Field(ge=0, le=14)
    cardio_trainings_per_week: int = Field(ge=0, le=14)
    goal: Literal["fat_loss", "muscle_gain", "maintenance", "recomposition"]


class NutritionAssignedByResponse(BaseModel):
    id: int
    telegram_user_id: int
    username: str | None = None
    full_name: str | None = None


class NutritionTargetResponse(BaseModel):
    user_id: int
    telegram_user_id: int
    sex: str
    weight_kg: float
    height_cm: float
    age: float
    strength_trainings_per_week: int
    cardio_trainings_per_week: int
    goal: str
    bmr: int
    tdee: int
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    saved_at: datetime
    assigned_by: NutritionAssignedByResponse | None = None
