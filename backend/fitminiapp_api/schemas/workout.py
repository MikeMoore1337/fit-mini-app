from datetime import date, datetime

from pydantic import BaseModel, Field


class WorkoutSetCreate(BaseModel):
    workout_exercise_id: int
    set_number: int
    actual_reps: int | None = None
    actual_weight: float | None = None
    is_completed: bool = True


class WorkoutSetUpdate(BaseModel):
    actual_reps: int | None = Field(default=None, ge=0)
    actual_weight: float | None = Field(default=None, ge=0)
    is_completed: bool | None = None


class LoggedSetItem(BaseModel):
    id: int
    set_number: int
    actual_reps: int | None = None
    actual_weight: float | None = None
    is_completed: bool = True


class WorkoutExerciseItem(BaseModel):
    id: int
    exercise_id: int
    exercise_title: str
    sort_order: int
    prescribed_sets: int
    prescribed_reps: str
    rest_seconds: int
    has_guide: bool = False
    sets: list[LoggedSetItem]


class WorkoutTodayResponse(BaseModel):
    id: int
    scheduled_date: date
    title: str
    status: str
    day_number: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exercises: list[WorkoutExerciseItem]


class WorkoutStatusResponse(BaseModel):
    id: int
    set_number: int
    actual_reps: int | None = None
    actual_weight: float | None = None
    is_completed: bool


class WorkoutScheduleItem(BaseModel):
    id: int
    scheduled_date: date
    title: str
    status: str
    day_number: int


class WorkoutHistoryItem(BaseModel):
    id: int
    scheduled_date: date
    title: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completed_sets: int
    volume_kg: float


class BodyMeasurementSave(BaseModel):
    measured_on: date | None = None
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    chest_cm: float | None = Field(default=None, ge=0, le=300)
    waist_cm: float | None = Field(default=None, ge=0, le=300)
    hips_cm: float | None = Field(default=None, ge=0, le=300)
    biceps_cm: float | None = Field(default=None, ge=0, le=150)
    thigh_cm: float | None = Field(default=None, ge=0, le=200)
    note: str | None = Field(default=None, max_length=500)


class BodyMeasurementResponse(BaseModel):
    id: int
    measured_on: date
    weight_kg: float | None = None
    chest_cm: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    biceps_cm: float | None = None
    thigh_cm: float | None = None
    note: str | None = None
    created_at: datetime | None = None
