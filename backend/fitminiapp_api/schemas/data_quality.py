from typing import Literal

from pydantic import BaseModel

DataSufficiencyStatus = Literal["sufficient", "limited", "insufficient"]
DataSufficiencyReasonKey = Literal[
    "thresholds_met",
    "nutrition_access_not_granted",
    "no_logged_days",
    "below_required_coverage",
    "no_measurements",
    "no_anthropometry_measurements",
    "too_few_points",
    "timespan_too_short",
    "no_completed_workouts",
    "no_prescribed_sets",
    "no_logged_working_sets",
    "partial_workout_logging",
    "no_working_sets",
    "too_few_working_sets",
    "too_few_workout_sessions",
    "no_rir_observations",
    "too_few_rir_observations",
    "rir_coverage_too_low",
    "no_evaluable_planned_workouts",
    "too_few_evaluable_workouts",
]


class DataSufficiencySignal(BaseModel):
    status: DataSufficiencyStatus
    counters: dict[str, int | float]
    reason_keys: list[DataSufficiencyReasonKey]


class TrainingDataSufficiency(BaseModel):
    ruleset_version: Literal["data-sufficiency-v1"]
    workout_logging: DataSufficiencySignal
    working_sets: DataSufficiencySignal
    rir_coverage: DataSufficiencySignal


class ProgressDataSufficiency(TrainingDataSufficiency):
    nutrition_coverage: DataSufficiencySignal
    weight_trend: DataSufficiencySignal
    anthropometry: DataSufficiencySignal
    schedule_adherence: DataSufficiencySignal
