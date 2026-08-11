from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DailyRoutine = Literal["mostly_sitting", "mixed", "mostly_on_feet", "physical_work"]
StepsRange = Literal[
    "up_to_4000",
    "from_4000_to_7000",
    "from_7000_to_10000",
    "from_10000_to_14000",
    "over_14000",
    "unknown",
]
StrengthTrainingType = Literal["calm", "regular", "heavy", "dense", "circuit"]
StrengthRest = Literal["under_60", "one_to_two", "two_to_three", "over_three", "varied"]
CardioKind = Literal[
    "walking",
    "running",
    "elliptical",
    "stationary_bike",
    "cycling",
    "rowing",
    "stepper",
    "swimming",
    "other",
]
CardioIntensity = Literal["very_light", "light", "moderate", "hard", "very_hard"]


class CardioTraining(BaseModel):
    kind: CardioKind
    trainings_per_week: int = Field(ge=1, le=14)
    duration_minutes: int = Field(ge=10, le=300)
    intensity: CardioIntensity


class NutritionTargetSave(BaseModel):
    target_telegram_user_id: int | None = Field(default=None, ge=1)
    sex: Literal["male", "female"]
    weight_kg: float = Field(ge=20, le=350, allow_inf_nan=False)
    height_cm: float = Field(ge=100, le=250, allow_inf_nan=False)
    age: float = Field(ge=18, le=100, allow_inf_nan=False)
    daily_routine: DailyRoutine | None = None
    steps_range: StepsRange | None = None
    strength_trainings_per_week: int = Field(ge=0, le=14)
    strength_training_duration_minutes: int = Field(default=60, ge=10, le=300)
    strength_training_type: StrengthTrainingType | None = None
    strength_rest: StrengthRest | None = None
    cardio_trainings: list[CardioTraining] | None = Field(default=None, max_length=10)
    goal: Literal["fat_loss", "muscle_gain", "maintenance", "recomposition"]

    # Transitional fields keep already deployed clients compatible while the
    # form migrates to the more expressive inputs above.
    daily_activity_level: Literal["sedentary", "low", "moderate", "high"] | None = "sedentary"
    cardio_trainings_per_week: int | None = Field(default=0, ge=0, le=14)
    cardio_training_duration_minutes: int | None = Field(default=30, ge=10, le=300)
    cardio_intensity: Literal["low", "moderate", "high"] | None = "moderate"

    @model_validator(mode="after")
    def validate_activity_details(self) -> NutritionTargetSave:
        has_new_daily_activity = self.daily_routine is not None or self.steps_range is not None
        if has_new_daily_activity and (self.daily_routine is None or self.steps_range is None):
            raise ValueError("daily_routine and steps_range must be provided together")
        if has_new_daily_activity:
            if self.strength_trainings_per_week > 0 and self.strength_training_type is None:
                raise ValueError("strength_training_type is required for strength trainings")
            if "cardio_trainings" not in self.model_fields_set:
                raise ValueError("cardio_trainings is required for detailed activity")
        if self.cardio_trainings is not None:
            legacy_cardio_fields = {
                "cardio_trainings_per_week",
                "cardio_training_duration_minutes",
                "cardio_intensity",
            }
            if self.model_fields_set & legacy_cardio_fields:
                raise ValueError("use cardio_trainings instead of legacy cardio fields")
        return self


class NutritionAssignedByResponse(BaseModel):
    id: int
    telegram_user_id: int | None = None
    username: str | None = None
    full_name: str | None = None


class NutritionTargetResponse(BaseModel):
    user_id: int
    telegram_user_id: int | None = None
    sex: str
    weight_kg: float
    height_cm: float
    age: float
    daily_routine: str
    steps_range: str
    strength_trainings_per_week: int
    strength_training_duration_minutes: int
    strength_training_type: str
    strength_rest: str | None
    cardio_trainings: list[CardioTraining]
    goal: str
    bmr: int
    tdee: int
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    saved_at: datetime
    assigned_by: NutritionAssignedByResponse | None = None

    # Returned during the transition so an older frontend can still render a
    # target saved by a newer server.
    daily_activity_level: str
    cardio_trainings_per_week: int
    cardio_training_duration_minutes: int
    cardio_intensity: str
