from pydantic import BaseModel

from app.schemas.nutrition import NutritionTargetResponse


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    workouts_per_week: int | None = None
    timezone: str | None = None


class UserProfileResponse(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    workouts_per_week: int | None = None
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
