from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ProgramTemplateExerciseCreate(BaseModel):
    exercise_id: int = Field(ge=1)
    prescribed_sets: int = Field(ge=1, le=12)
    prescribed_reps: str = Field(min_length=1, max_length=32)
    rest_seconds: int = Field(default=90, ge=15, le=600)
    notes: str | None = Field(default=None, max_length=2000)


class ProgramTemplateDayCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    exercises: list[ProgramTemplateExerciseCreate] = Field(min_length=1, max_length=30)


class ProgramTemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    goal: Literal["muscle_gain", "fat_loss", "maintenance", "recomposition"]
    level: Literal["beginner", "intermediate", "advanced"]
    mode: Literal["self", "coach"] = "self"
    target_telegram_user_id: int | None = Field(default=None, ge=1)
    target_full_name: str | None = Field(default=None, max_length=128)
    days: list[ProgramTemplateDayCreate] = Field(min_length=1, max_length=14)
    assign_after_create: bool = True


class ProgramTemplateExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_title: str
    prescribed_sets: int
    prescribed_reps: str
    rest_seconds: int
    notes: str | None = None


class ProgramTemplateDayResponse(BaseModel):
    id: int
    day_number: int
    title: str
    exercises: list[ProgramTemplateExerciseResponse]


class ProgramTemplateResponse(BaseModel):
    id: int
    title: str
    slug: str
    goal: str
    level: str
    owner_user_id: int | None = None
    owner_telegram_user_id: int | None = None
    owner_full_name: str | None = None
    created_by_user_id: int | None = None
    is_public: bool = False
    days: list[ProgramTemplateDayResponse]


class ProgramTemplateCreateResponse(BaseModel):
    template: ProgramTemplateResponse
    assigned_program_id: int | None = None
    assigned_to_telegram_user_id: int | None = None
    assigned_to_name: str | None = None
    workouts_created: int = 0


class AssignTemplateRequest(BaseModel):
    target_telegram_user_id: int = Field(ge=1)
    target_full_name: str | None = Field(default=None, max_length=128)


class AssignTemplateSelfRequest(BaseModel):
    start_date: date | None = None


class CoachClientCreate(BaseModel):
    telegram_user_id: int | None = Field(default=None, ge=1)
    username: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, max_length=128)


class ProgramAssignedResponse(BaseModel):
    program_id: int
    title: str
    workouts_created: int


class ExerciseCatalogItem(BaseModel):
    id: int
    title: str
    primary_muscle: str | None = None
    equipment: str | None = None


class ExerciseCatalogCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    primary_muscle: str | None = Field(default=None, max_length=64)
    equipment: str | None = Field(default=None, max_length=64)
    target_telegram_user_id: int | None = Field(default=None, ge=1)


class ExerciseCatalogCreateResponse(ExerciseCatalogItem):
    slug: str


class ClientResponse(BaseModel):
    user_id: int
    telegram_user_id: int
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    is_coach: bool = False
