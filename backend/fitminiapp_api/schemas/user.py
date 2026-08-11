from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from fitminiapp_api.core.timezone import is_valid_timezone
from fitminiapp_api.schemas.nutrition import NutritionTargetResponse


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=128)
    birth_date: date | None = None
    goal: Literal["muscle_gain", "fat_loss", "maintenance", "recomposition"] | None = None
    level: Literal["beginner", "intermediate", "advanced"] | None = None
    height_cm: int | None = Field(default=None, ge=100, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=350, allow_inf_nan=False)
    workouts_per_week: int | None = Field(default=None, ge=0, le=14)
    cardio_trainings_per_week: int | None = Field(default=None, ge=0, le=14)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value and not is_valid_timezone(value):
            raise ValueError("Unsupported timezone")
        return value

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        if value is None:
            return value
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 10 or age > 100:
            raise ValueError("Age must be between 10 and 100 years")
        return value


class AccountDeleteRequest(BaseModel):
    confirmation: Literal["DELETE"]


class HeartRateZoneResponse(BaseModel):
    zone: int
    title: str
    min_bpm: int
    max_bpm: int


class UserProfileResponse(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    workouts_per_week: int | None = None
    cardio_trainings_per_week: int | None = None
    timezone: str = "Europe/Moscow"
    estimated_max_heart_rate: int | None = None
    heart_rate_zones: list[HeartRateZoneResponse] = Field(default_factory=list)
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
    photo_url: str | None = None
    is_coach: bool = False
    is_admin: bool = False
    has_active_program: bool = False
    has_workout_history: bool = False
    profile: UserProfileResponse | None = None
    trainer: TrainerResponse | None = None
