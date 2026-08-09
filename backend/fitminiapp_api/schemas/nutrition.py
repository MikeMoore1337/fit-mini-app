from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NutritionTargetSave(BaseModel):
    target_telegram_user_id: int | None = Field(default=None, ge=1)
    sex: Literal["male", "female"]
    weight_kg: float = Field(ge=20, le=350, allow_inf_nan=False)
    height_cm: float = Field(ge=100, le=250, allow_inf_nan=False)
    age: float = Field(ge=18, le=100, allow_inf_nan=False)
    daily_activity_level: Literal["sedentary", "low", "moderate", "high"] = "sedentary"
    strength_trainings_per_week: int = Field(ge=0, le=14)
    strength_training_duration_minutes: int = Field(default=60, ge=10, le=300)
    cardio_trainings_per_week: int = Field(ge=0, le=14)
    cardio_training_duration_minutes: int = Field(default=30, ge=10, le=300)
    cardio_intensity: Literal["low", "moderate", "high"] = "moderate"
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
    daily_activity_level: str
    strength_trainings_per_week: int
    strength_training_duration_minutes: int
    cardio_trainings_per_week: int
    cardio_training_duration_minutes: int
    cardio_intensity: str
    goal: str
    bmr: int
    tdee: int
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    saved_at: datetime
    assigned_by: NutritionAssignedByResponse | None = None
