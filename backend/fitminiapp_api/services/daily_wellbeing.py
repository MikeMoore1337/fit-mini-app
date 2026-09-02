from __future__ import annotations

from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import get_user_timezone_name, now_for_user_naive, today_for_user
from fitminiapp_api.models.daily_wellbeing import DailyWellbeingCheckIn
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.daily_wellbeing import (
    DailyWellbeingCheckInSaveRequest,
    DailyWellbeingReport,
)

MIN_TREND_POINTS = 3
TREND_DELTA_THRESHOLD = 0.75


class DailyWellbeingValidationError(ValueError):
    pass


class DailyWellbeingConflictError(ValueError):
    pass


def validate_local_date(user: User, local_date: date) -> None:
    if local_date > today_for_user(user):
        raise DailyWellbeingValidationError("Нельзя сохранить отметку на будущую дату")


def serialize_daily_wellbeing(row: DailyWellbeingCheckIn) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "local_date": row.local_date,
        "timezone_at_entry": row.timezone_at_entry,
        "sleep_quality": row.sleep_quality,
        "sleep_duration_minutes": row.sleep_duration_minutes,
        "mood": row.mood,
        "note": row.note,
        "source": row.source,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def get_daily_wellbeing(
    db: Session,
    user: User,
    local_date: date,
) -> dict:
    row = (
        db.query(DailyWellbeingCheckIn)
        .filter(
            DailyWellbeingCheckIn.user_id == user.id,
            DailyWellbeingCheckIn.local_date == local_date,
        )
        .one_or_none()
    )
    # Reads may inspect an empty future calendar date, especially immediately
    # after the account timezone changes; only writes reject future dates.
    return {
        "local_date": local_date,
        "today": today_for_user(user),
        "timezone": get_user_timezone_name(user),
        "record": serialize_daily_wellbeing(row) if row else None,
    }


def save_daily_wellbeing(
    db: Session,
    user: User,
    local_date: date,
    payload: DailyWellbeingCheckInSaveRequest,
) -> DailyWellbeingCheckIn:
    if (
        payload.sleep_quality is None
        and payload.sleep_duration_minutes is None
        and payload.mood is None
    ):
        raise DailyWellbeingValidationError("Выберите хотя бы один показатель сна или настроения")

    db.query(User).filter(User.id == user.id).with_for_update().one()
    row = (
        db.query(DailyWellbeingCheckIn)
        .filter(
            DailyWellbeingCheckIn.user_id == user.id,
            DailyWellbeingCheckIn.local_date == local_date,
        )
        .one_or_none()
    )
    # A timezone change must not turn an already valid check-in into a future
    # date while the user is editing it. New rows still cannot be future-dated.
    if row is None:
        validate_local_date(user, local_date)
    now = now_for_user_naive(user)
    values = {
        "sleep_quality": payload.sleep_quality,
        "sleep_duration_minutes": payload.sleep_duration_minutes,
        "mood": payload.mood,
        "note": payload.note.strip() if payload.note else None,
        "timezone_at_entry": row.timezone_at_entry if row else get_user_timezone_name(user),
        "updated_at": now,
    }
    if row is None:
        row = DailyWellbeingCheckIn(
            user_id=user.id,
            local_date=local_date,
            source="manual",
            created_at=now,
            **values,
        )
        db.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DailyWellbeingConflictError("Отметка за эту дату уже сохраняется") from exc
    db.refresh(row)
    return row


def delete_daily_wellbeing(db: Session, user: User, local_date: date) -> None:
    row = (
        db.query(DailyWellbeingCheckIn)
        .filter(
            DailyWellbeingCheckIn.user_id == user.id,
            DailyWellbeingCheckIn.local_date == local_date,
        )
        .one_or_none()
    )
    if row is None:
        validate_local_date(user, local_date)
    else:
        db.delete(row)
    db.commit()


def _trend(values: list[int]) -> str:
    if len(values) < MIN_TREND_POINTS:
        return "insufficient_data"
    window_size = min(MIN_TREND_POINTS, max(1, len(values) // 2))
    first_window = values[:window_size]
    last_window = values[-window_size:]
    delta = sum(last_window) / len(last_window) - sum(first_window) / len(first_window)
    if delta >= TREND_DELTA_THRESHOLD:
        return "improving"
    if delta <= -TREND_DELTA_THRESHOLD:
        return "declining"
    return "stable"


def _metric(values: list[int]) -> dict:
    return {
        "recorded_days": len(values),
        "distribution": [{"value": value, "count": values.count(value)} for value in range(1, 6)],
        "trend": _trend(values),
    }


def build_daily_wellbeing_report(
    db: Session,
    user: User,
    *,
    period_start: date,
    period_end: date,
) -> dict | None:
    eligible_days = (period_end - period_start).days + 1
    rows = (
        db.query(DailyWellbeingCheckIn)
        .filter(
            DailyWellbeingCheckIn.user_id == user.id,
            DailyWellbeingCheckIn.local_date.between(period_start, period_end),
        )
        .order_by(DailyWellbeingCheckIn.local_date.asc(), DailyWellbeingCheckIn.id.asc())
        .all()
    )
    if not rows:
        return None
    sleep_values = [row.sleep_quality for row in rows if row.sleep_quality is not None]
    mood_values = [row.mood for row in rows if row.mood is not None]
    payload = {
        "period_start": period_start,
        "period_end": period_end,
        "eligible_days": eligible_days,
        "recorded_days": len(rows),
        "coverage_percent": round(len(rows) * 100 / eligible_days, 1),
        "sleep": _metric(sleep_values),
        "mood": _metric(mood_values),
        "daily": [
            {
                "local_date": row.local_date,
                "sleep_quality": row.sleep_quality,
                "sleep_duration_minutes": row.sleep_duration_minutes,
                "mood": row.mood,
                "source": row.source,
            }
            for row in rows
        ],
    }
    return DailyWellbeingReport.model_validate(payload).model_dump(mode="json")
