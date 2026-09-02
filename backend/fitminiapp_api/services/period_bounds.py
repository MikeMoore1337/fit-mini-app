from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from fitminiapp_api.core.timezone import today_for_user
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.progress import NutritionReportPeriod, ProgressPeriodDays

MAX_REPORT_DAYS = 366


class PeriodBoundsError(ValueError):
    """Raised when a requested reporting period cannot be evaluated safely."""


@dataclass(frozen=True)
class ReportBounds:
    period: NutritionReportPeriod
    start: date
    end: date


def resolve_report_bounds(
    user: User,
    period: NutritionReportPeriod,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReportBounds:
    """Resolve one timezone-aware, inclusive date range for every progress consumer."""
    today = today_for_user(user)
    period = NutritionReportPeriod(period)

    if period == NutritionReportPeriod.CUSTOM:
        if date_from is None or date_to is None:
            raise PeriodBoundsError("Для произвольного периода укажите обе даты")
        start, end = date_from, date_to
    else:
        if date_from is not None or date_to is not None:
            raise PeriodBoundsError("Даты можно передавать только для произвольного периода")
        if period == NutritionReportPeriod.DAYS_1:
            start, end = today, today
        elif period == NutritionReportPeriod.DAYS_7:
            start, end = today - timedelta(days=6), today
        elif period == NutritionReportPeriod.DAYS_30:
            start, end = today - timedelta(days=29), today
        elif period == NutritionReportPeriod.DAYS_90:
            start, end = today - timedelta(days=89), today
        elif period == NutritionReportPeriod.DAYS_365:
            start, end = today - timedelta(days=364), today
        elif period == NutritionReportPeriod.CURRENT_WEEK:
            start, end = today - timedelta(days=today.weekday()), today
        elif period == NutritionReportPeriod.CURRENT_MONTH:
            start, end = today.replace(day=1), today
        elif period == NutritionReportPeriod.PREVIOUS_MONTH:
            previous_end = today.replace(day=1) - timedelta(days=1)
            start = previous_end.replace(day=1)
            end = previous_end
        else:  # pragma: no cover - enum validation owns this boundary
            raise PeriodBoundsError("Неизвестный период отчёта")

    if end < start:
        raise PeriodBoundsError("Дата окончания не может быть раньше даты начала")
    if end > today:
        raise PeriodBoundsError("Отчёт нельзя построить за будущие даты")
    if (end - start).days + 1 > MAX_REPORT_DAYS:
        raise PeriodBoundsError(f"Период отчёта не может превышать {MAX_REPORT_DAYS} дней")
    return ReportBounds(period=period, start=start, end=end)


def progress_period_for_days(period_days: int) -> NutritionReportPeriod:
    try:
        progress_period = ProgressPeriodDays(period_days)
    except ValueError as exc:
        raise PeriodBoundsError("Период должен быть 1, 7, 30, 90 или 365 дней") from exc
    return {
        ProgressPeriodDays.DAYS_1: NutritionReportPeriod.DAYS_1,
        ProgressPeriodDays.DAYS_7: NutritionReportPeriod.DAYS_7,
        ProgressPeriodDays.DAYS_30: NutritionReportPeriod.DAYS_30,
        ProgressPeriodDays.DAYS_90: NutritionReportPeriod.DAYS_90,
        ProgressPeriodDays.DAYS_365: NutritionReportPeriod.DAYS_365,
    }[progress_period]


def resolve_progress_bounds(
    user: User,
    period_days: int | None = None,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReportBounds:
    if date_from is not None or date_to is not None:
        if period_days is not None:
            raise PeriodBoundsError(
                "Нельзя одновременно передавать количество дней и произвольные даты"
            )
        return resolve_report_bounds(
            user,
            NutritionReportPeriod.CUSTOM,
            date_from=date_from,
            date_to=date_to,
        )
    return resolve_report_bounds(
        user,
        progress_period_for_days(30 if period_days is None else int(period_days)),
    )
