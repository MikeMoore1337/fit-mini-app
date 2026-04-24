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
    set_number: int
    actual_reps: int | None = None
    actual_weight: float | None = None
    is_completed: bool = True


class WorkoutProgressSnapshot(BaseModel):
    previous_workout_title: str | None = None
    previous_workout_date: str | None = None
    previous_volume: float | None = None
    current_volume: float | None = None
    volume_delta: float | None = None
    previous_top_weight: float | None = None
    current_top_weight: float | None = None
    top_weight_delta: float | None = None


class WorkoutExerciseItem(BaseModel):
    id: int
    title: str
    prescribed_sets: int
    prescribed_reps: str
    rest_seconds: int
    completed_sets: int
    remaining_sets: int
    logged_sets: list[LoggedSetItem]
    previous_logged_sets: list[LoggedSetItem]
    progress: WorkoutProgressSnapshot | None = None


class WorkoutTodayResponse(BaseModel):
    id: int
    title: str
    status: str
    day_number: int
    can_start: bool
    can_complete: bool
    can_log_sets: bool
    exercises: list[WorkoutExerciseItem]


class WorkoutStatusResponse(BaseModel):
    id: int
    status: str
