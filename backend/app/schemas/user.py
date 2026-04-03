from pydantic import BaseModel


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    workouts_per_week: int | None = None


class UserProfileResponse(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    workouts_per_week: int | None = None


class UserResponse(BaseModel):
    id: int
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_coach: bool = False
    is_admin: bool = False
    profile: UserProfileResponse | None = None
