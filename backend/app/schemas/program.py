from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.nutrition import NutritionTargetResponse


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
    is_example: bool = False
    is_assigned_to_current_user: bool = False
    is_active_for_current_user: bool = False
    assigned_by_user_id: int | None = None
    assigned_by_full_name: str | None = None
    days: list[ProgramTemplateDayResponse]


class ProgramTargetUserResponse(BaseModel):
    id: int
    telegram_user_id: int
    full_name: str | None = None


class ProgramTemplateCreateResponse(BaseModel):
    template: ProgramTemplateResponse
    assigned_program_id: int | None = None
    workouts_created: int = 0
    target_user: ProgramTargetUserResponse


class ProgramAssignmentResponse(BaseModel):
    user_program_id: int
    workouts_created: int


class CoachAssignedProgramResponse(BaseModel):
    id: int
    client_id: int
    client_telegram_user_id: int
    client_username: str | None = None
    client_full_name: str | None = None
    template_id: int | None = None
    title: str
    goal: str | None = None
    level: str | None = None
    assigned_at: datetime
    is_active: bool
    workouts_total: int
    workouts_completed: int
    workouts_planned: int
    next_workout_date: date | None = None


class AssignTemplateRequest(BaseModel):
    target_telegram_user_id: int = Field(ge=1)
    target_full_name: str | None = Field(default=None, max_length=128)


class AssignTemplateSelfRequest(BaseModel):
    start_date: date | None = None


class AssignTemplateToClientRequest(BaseModel):
    start_date: date | None = None


class CoachClientCreate(BaseModel):
    telegram_user_id: int | None = Field(default=None, ge=1)
    username: str | None = Field(default=None, max_length=64)
    client_code: str | None = Field(default=None, min_length=7, max_length=16)
    source: Literal["client_code", "username_search", "telegram_user_picker"] | None = None
    full_name: str | None = Field(default=None, max_length=128)


class ProgramAssignedResponse(BaseModel):
    program_id: int
    title: str
    workouts_created: int


class ExerciseGuideMuscle(BaseModel):
    name: str
    role: str
    function: str


class ExerciseGuideImage(BaseModel):
    phase: str
    url: str
    alt: str


class ExerciseGuide(BaseModel):
    technique_steps: list[str]
    breathing: str
    common_mistakes: list[str]
    muscles: list[ExerciseGuideMuscle]
    images: list[ExerciseGuideImage]
    source_name: str
    source_url: str
    source_license: str


class ExerciseCatalogItem(BaseModel):
    id: int
    title: str
    primary_muscle: str | None = None
    equipment: str | None = None
    difficulty_level: Literal["beginner", "intermediate", "advanced"]
    edit_target_id: int | None = None
    slug: str | None = None
    is_custom: bool = False
    is_personalized: bool = False
    created_by_user_id: int | None = None
    source_exercise_id: int | None = None
    guide: ExerciseGuide | None = None


class ExerciseCatalogCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    primary_muscle: str | None = Field(default=None, max_length=64)
    equipment: str | None = Field(default=None, max_length=64)
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    target_telegram_user_id: int | None = Field(default=None, ge=1)


class ExerciseCatalogCreateResponse(ExerciseCatalogItem):
    slug: str


class ClientResponse(BaseModel):
    id: int | None = None
    invite_id: int | None = None
    telegram_user_id: int | None = None
    username: str | None = None
    full_name: str | None = None
    goal: str | None = None
    level: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    workouts_per_week: int | None = None
    cardio_trainings_per_week: int | None = None
    kbju: NutritionTargetResponse | None = None
    status: Literal["active", "pending"]
