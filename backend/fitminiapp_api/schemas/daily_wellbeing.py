from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

DailyWellbeingSource = Literal["manual", "future_import"]


class DailyWellbeingCheckInSaveRequest(BaseModel):
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    sleep_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    mood: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)


class DailyWellbeingCheckInResponse(BaseModel):
    id: int
    user_id: int
    local_date: date
    timezone_at_entry: str
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    sleep_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    mood: int | None = Field(default=None, ge=1, le=5)
    note: str | None = None
    source: DailyWellbeingSource
    created_at: datetime
    updated_at: datetime


class DailyWellbeingCurrentResponse(BaseModel):
    local_date: date
    today: date
    timezone: str
    record: DailyWellbeingCheckInResponse | None = None


class DailyWellbeingDistributionItem(BaseModel):
    value: int = Field(ge=1, le=5)
    count: int = Field(ge=0)


class DailyWellbeingMetric(BaseModel):
    recorded_days: int = Field(ge=0)
    distribution: list[DailyWellbeingDistributionItem]
    trend: Literal["improving", "declining", "stable", "insufficient_data"]


class DailyWellbeingPoint(BaseModel):
    local_date: date
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    sleep_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    mood: int | None = Field(default=None, ge=1, le=5)
    source: DailyWellbeingSource


class DailyWellbeingReport(BaseModel):
    period_start: date
    period_end: date
    eligible_days: int = Field(ge=1)
    recorded_days: int = Field(ge=0)
    coverage_percent: float = Field(ge=0, le=100)
    sleep: DailyWellbeingMetric
    mood: DailyWellbeingMetric
    daily: list[DailyWellbeingPoint]
