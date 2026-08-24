from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import (
    get_user_timezone_name,
    local_naive_to_utc_naive,
    utc_naive_to_timezone_naive,
)
from fitminiapp_api.models.cardio import CardioSession, utc_now_naive
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.cardio import CardioSessionCreate, CardioSessionUpdate


class CardioSessionError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _utc_from_user_local(value: datetime, user: User) -> datetime:
    return local_naive_to_utc_naive(value, get_user_timezone_name(user))


def _validate_completion_time(status: str, scheduled_at_utc: datetime) -> None:
    if status == "completed" and scheduled_at_utc > utc_now_naive() + timedelta(minutes=5):
        raise CardioSessionError("Завершённую активность нельзя записать в будущем")


def _owned_session(db: Session, user: User, session_id: int) -> CardioSession:
    row = (
        db.query(CardioSession)
        .filter(CardioSession.id == session_id, CardioSession.user_id == user.id)
        .first()
    )
    if row is None:
        raise CardioSessionError("Кардио-запись не найдена", 404)
    return row


def serialize_cardio_session(row: CardioSession, user: User) -> dict:
    timezone_name = get_user_timezone_name(user)
    return {
        "id": row.id,
        "activity_type": row.activity_type,
        "duration_minutes": row.duration_minutes,
        "distance_km": float(row.distance_km) if row.distance_km is not None else None,
        "average_heart_rate_bpm": row.average_heart_rate_bpm,
        "heart_rate_zone": row.heart_rate_zone,
        "note": row.note,
        "scheduled_at": utc_naive_to_timezone_naive(row.scheduled_at, timezone_name),
        "status": row.status,
        "source": row.source,
        "completed_at": (
            utc_naive_to_timezone_naive(row.completed_at, timezone_name)
            if row.completed_at
            else None
        ),
        "created_at": utc_naive_to_timezone_naive(row.created_at, timezone_name),
        "updated_at": utc_naive_to_timezone_naive(row.updated_at, timezone_name),
    }


def list_cardio_sessions(
    db: Session,
    user: User,
    *,
    date_from: date | None,
    date_to: date | None,
    status: str | None,
    limit: int,
    offset: int,
) -> list[CardioSession]:
    query = db.query(CardioSession).filter(CardioSession.user_id == user.id)
    timezone_name = get_user_timezone_name(user)
    if date_from is not None:
        query = query.filter(
            CardioSession.scheduled_at
            >= local_naive_to_utc_naive(datetime.combine(date_from, time.min), timezone_name)
        )
    if date_to is not None:
        query = query.filter(
            CardioSession.scheduled_at
            < local_naive_to_utc_naive(
                datetime.combine(date_to + timedelta(days=1), time.min), timezone_name
            )
        )
    if status is not None:
        query = query.filter(CardioSession.status == status)
    return (
        query.order_by(CardioSession.scheduled_at.desc(), CardioSession.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_cardio_session(
    db: Session,
    user: User,
    payload: CardioSessionCreate,
) -> CardioSession:
    request_id = str(payload.client_request_id)
    existing = (
        db.query(CardioSession)
        .filter(
            CardioSession.user_id == user.id,
            CardioSession.client_request_id == request_id,
        )
        .first()
    )
    if existing is not None:
        return existing
    scheduled_at = _utc_from_user_local(payload.scheduled_at, user)
    _validate_completion_time(payload.status, scheduled_at)
    now = utc_now_naive()
    row = CardioSession(
        user_id=user.id,
        client_request_id=request_id,
        activity_type=payload.activity_type,
        duration_minutes=payload.duration_minutes,
        distance_km=(
            Decimal(str(payload.distance_km)) if payload.distance_km is not None else None
        ),
        average_heart_rate_bpm=payload.average_heart_rate_bpm,
        heart_rate_zone=payload.heart_rate_zone,
        note=payload.note,
        scheduled_at=scheduled_at,
        status=payload.status,
        source="manual",
        completed_at=now if payload.status == "completed" else None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(CardioSession)
            .filter(
                CardioSession.user_id == user.id,
                CardioSession.client_request_id == request_id,
            )
            .first()
        )
        if existing is not None:
            return existing
        raise
    db.refresh(row)
    return row


def update_cardio_session(
    db: Session,
    user: User,
    session_id: int,
    payload: CardioSessionUpdate,
) -> CardioSession:
    row = _owned_session(db, user, session_id)
    changes = payload.model_dump(exclude_unset=True)
    if "scheduled_at" in changes:
        changes["scheduled_at"] = _utc_from_user_local(changes["scheduled_at"], user)
    next_status = changes.get("status", row.status)
    next_scheduled_at = changes.get("scheduled_at", row.scheduled_at)
    _validate_completion_time(next_status, next_scheduled_at)
    for field, value in changes.items():
        if field == "distance_km" and value is not None:
            value = Decimal(str(value))
        setattr(row, field, value)
    if row.status == "completed" and row.completed_at is None:
        row.completed_at = utc_now_naive()
    elif row.status == "planned":
        row.completed_at = None
    row.updated_at = utc_now_naive()
    db.commit()
    db.refresh(row)
    return row


def complete_cardio_session(db: Session, user: User, session_id: int) -> CardioSession:
    row = _owned_session(db, user, session_id)
    if row.status == "completed":
        return row
    _validate_completion_time("completed", row.scheduled_at)
    row.status = "completed"
    row.completed_at = utc_now_naive()
    row.updated_at = row.completed_at
    db.commit()
    db.refresh(row)
    return row


def delete_cardio_session(db: Session, user: User, session_id: int) -> None:
    row = _owned_session(db, user, session_id)
    db.delete(row)
    db.commit()
