from datetime import date, time
from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field

from fitminiapp_api.schemas.data_quality import ProgressDataSufficiency
from fitminiapp_api.schemas.user import BodyPriorityPreference


class ProgressPeriodDays(IntEnum):
    DAYS_7 = 7
    DAYS_30 = 30
    DAYS_90 = 90


AdherenceStatus = Literal["available", "not_applicable", "insufficient_data", "unsupported"]


class AdherenceComponent(BaseModel):
    status: AdherenceStatus
    percent: float | None = None
    achieved: int = 0
    evaluated: int = 0
    weight: float
    reason: str | None = None


class AdherenceSummary(BaseModel):
    formula_version: str
    overall_percent: float | None = None
    included_components: list[str]
    workouts: AdherenceComponent
    cardio: AdherenceComponent
    calories: AdherenceComponent
    protein: AdherenceComponent


class NextWorkoutSummary(BaseModel):
    id: int
    scheduled_date: date
    scheduled_time: time | None = None
    title: str
    status: str


class TrainingPeriodSummary(BaseModel):
    planned_workouts: int
    completed_workouts: int
    frequency_per_week: float
    volume_kg: float
    new_personal_records: int
    last_completed_workout_on: date | None = None
    next_workout: NextWorkoutSummary | None = None


class NutritionPeriodSummary(BaseModel):
    visible: bool
    logged_days: int = 0
    complete_days: int = 0
    incomplete_days: int = 0
    fasted_days: int = 0
    unlogged_days: int = 0
    adherence_evaluated_days: int = 0
    average_calories: float | None = None
    target_calories: int | None = None
    average_protein_g: float | None = None
    target_protein_g: int | None = None
    target_effective_on: date | None = None


class BodyMetricPoint(BaseModel):
    measured_on: date
    value: float


class BodyMetricTrend(BaseModel):
    metric: Literal["weight_kg", "chest_cm", "waist_cm", "hips_cm", "biceps_cm", "thigh_cm"]
    first_value: float
    latest_value: float
    change: float | None = None
    first_measured_on: date
    latest_measured_on: date
    point_count: int = Field(ge=1)
    span_days: int = Field(ge=0)
    interpretation_status: Literal[
        "single_point", "insufficient_points", "insufficient_period", "available"
    ]
    points: list[BodyMetricPoint]


class LatestBodyMeasurement(BaseModel):
    measured_on: date
    weight_kg: float | None = None
    chest_cm: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    biceps_cm: float | None = None
    thigh_cm: float | None = None


class BodyMeasurementGuidance(BaseModel):
    comparison_basis: Literal["self"] = "self"
    minimum_points_for_interpretation: int = Field(ge=2)
    minimum_span_days_for_interpretation: int = Field(ge=1)
    consistency_tips: list[str]
    circumference_limitations: list[str]


class BodyPeriodSummary(BaseModel):
    latest_measurement: LatestBodyMeasurement | None = None
    trends: list[BodyMetricTrend]
    priority: BodyPriorityPreference | None = None
    guidance: BodyMeasurementGuidance


class ProgressSummaryResponse(BaseModel):
    user_id: int
    period_days: ProgressPeriodDays
    period_start: date
    period_end: date
    training: TrainingPeriodSummary
    nutrition: NutritionPeriodSummary
    body: BodyPeriodSummary
    adherence: AdherenceSummary
    data_sufficiency: ProgressDataSufficiency


class TrainerClientProgressSummary(ProgressSummaryResponse):
    client_name: str | None = None


class TrainerClientProgressListResponse(BaseModel):
    items: list[TrainerClientProgressSummary]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
