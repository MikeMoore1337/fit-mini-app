from datetime import datetime

from pydantic import BaseModel, Field


class NutritionTargetSave(BaseModel):
    target_telegram_user_id: int | None = Field(default=None, ge=1)
    sex: str
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    age: float = Field(gt=0)
    strength_trainings_per_week: int = Field(ge=0)
    cardio_trainings_per_week: int = Field(ge=0)
    goal: str


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
