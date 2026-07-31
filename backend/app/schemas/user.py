from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.timezone import is_valid_timezone
from app.schemas.nutrition import NutritionTargetResponse


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=128)
    goal: Literal["muscle_gain", "fat_loss", "maintenance", "recomposition"] | None = None
    level: Literal["beginner", "intermediate", "advanced"] | None = None
    height_cm: int | None = Field(default=None, ge=50, le=280)
    weight_kg: int | None = Field(default=None, ge=20, le=500)
    workouts_per_week: int | None = Field(default=None, ge=0, le=14)
    cardio_trainings_per_week: int | None = Field(default=None, ge=0, le=14)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value and not is_valid_timezone(value):
            raise ValueError("Unsupported timezone")
        return value


class UserProfileResponse(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    workouts_per_week: int | None = None
    cardio_trainings_per_week: int | None = None
    timezone: str = "Europe/Moscow"
    kbju: NutritionTargetResponse | None = None


class TrainerResponse(BaseModel):
    id: int
    telegram_user_id: int
    username: str | None = None
    full_name: str | None = None
    can_open_chat: bool = False
    chat_url: str | None = None
    chat_unavailable_reason: str | None = None


class UserResponse(BaseModel):
    id: int
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_coach: bool = False
    is_admin: bool = False
    profile: UserProfileResponse | None = None
    trainer: TrainerResponse | None = None
