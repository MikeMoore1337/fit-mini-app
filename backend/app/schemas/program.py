from pydantic import BaseModel, Field


class ProgramTemplateExerciseCreate(BaseModel):
    exercise_id: int
    prescribed_sets: int = Field(ge=1, le=12)
    prescribed_reps: str
    rest_seconds: int = Field(default=90, ge=15, le=600)
    notes: str | None = None


class ProgramTemplateDayCreate(BaseModel):
    title: str
    exercises: list[ProgramTemplateExerciseCreate]


class ProgramTemplateCreate(BaseModel):
    title: str
    goal: str
    level: str
    mode: str = "self"
    target_telegram_user_id: int | None = None
    target_full_name: str | None = None
    days: list[ProgramTemplateDayCreate]
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
    target_telegram_user_id: int
    target_full_name: str | None = None


class CoachClientCreate(BaseModel):
    telegram_user_id: int | None = Field(default=None, ge=1)
    username: str | None = None
    full_name: str | None = None


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
    title: str
    primary_muscle: str | None = None
    equipment: str | None = None
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
