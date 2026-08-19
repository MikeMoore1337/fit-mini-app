from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import today_for_user
from fitminiapp_api.models.user import BodyMeasurement, User
from fitminiapp_api.schemas.workout import BodyMeasurementSave
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.nutrition import NutritionError, recalculate_nutrition_target

MEASUREMENT_FIELDS = (
    "weight_kg",
    "chest_cm",
    "waist_cm",
    "hips_cm",
    "biceps_cm",
    "thigh_cm",
)


class MeasurementError(Exception):
    pass


class MeasurementNotFoundError(MeasurementError):
    pass


def serialize_measurement(row: BodyMeasurement) -> dict:
    return {
        "id": row.id,
        "measured_on": row.measured_on,
        "weight_kg": row.weight_kg,
        "chest_cm": row.chest_cm,
        "waist_cm": row.waist_cm,
        "hips_cm": row.hips_cm,
        "biceps_cm": row.biceps_cm,
        "thigh_cm": row.thigh_cm,
        "note": row.note,
        "created_at": row.created_at,
    }


def list_measurements(db: Session, owner: User, *, limit: int) -> list[BodyMeasurement]:
    """Return measurement history, including preserved legacy future-dated rows."""
    return (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == owner.id)
        .order_by(BodyMeasurement.measured_on.desc(), BodyMeasurement.id.desc())
        .limit(limit)
        .all()
    )


def latest_current_weight_measurement(
    db: Session,
    owner: User,
) -> BodyMeasurement | None:
    return (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.user_id == owner.id,
            BodyMeasurement.measured_on <= today_for_user(owner),
            BodyMeasurement.weight_kg.is_not(None),
        )
        .order_by(BodyMeasurement.measured_on.desc(), BodyMeasurement.id.desc())
        .first()
    )


def _lock_owner_measurements(db: Session, owner_user_id: int) -> None:
    """Serialize the owner's chronology mutation and derived-state reconciliation."""
    db.query(User.id).filter(User.id == owner_user_id).with_for_update().one()


def reconcile_current_measurement_state(
    db: Session,
    owner: User,
    *,
    changed_by: User,
) -> bool:
    """Recalculate current derived state from chronology, falling back to profile weight."""
    db.flush()
    latest = latest_current_weight_measurement(db, owner)
    weight_kg = latest.weight_kg if latest is not None else None
    if weight_kg is None and owner.profile is not None:
        weight_kg = owner.profile.weight_kg
    if weight_kg is None:
        return False
    return recalculate_nutrition_target(
        db,
        owner,
        {"weight_kg": weight_kg},
        changed_by,
    )


def _measurement_changes(payload: BodyMeasurementSave) -> dict[str, object]:
    changes = payload.model_dump(exclude_unset=True, exclude={"measured_on"})
    note = changes.get("note")
    if isinstance(note, str):
        changes["note"] = note.strip() or None
    if not changes.get("note") and not any(
        changes.get(field) is not None for field in MEASUREMENT_FIELDS
    ):
        raise MeasurementError("Укажите вес, замер или заметку")
    return changes


def _upsert_measurement(
    db: Session,
    *,
    owner_user_id: int,
    measured_on: date,
    changes: dict[str, object],
) -> BodyMeasurement:
    values = {"user_id": owner_user_id, "measured_on": measured_on, **changes}
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        postgresql_statement = postgresql_insert(BodyMeasurement).values(**values)
        postgresql_statement = postgresql_statement.on_conflict_do_update(
            constraint="uq_body_measurement_user_date",
            set_={field: getattr(postgresql_statement.excluded, field) for field in changes},
        )
        measurement_id = db.execute(postgresql_statement.returning(BodyMeasurement.id)).scalar_one()
    elif dialect == "sqlite":
        sqlite_statement = sqlite_insert(BodyMeasurement).values(**values)
        sqlite_statement = sqlite_statement.on_conflict_do_update(
            index_elements=[BodyMeasurement.user_id, BodyMeasurement.measured_on],
            set_={field: getattr(sqlite_statement.excluded, field) for field in changes},
        )
        measurement_id = db.execute(sqlite_statement.returning(BodyMeasurement.id)).scalar_one()
    else:
        raise RuntimeError(f"Unsupported measurement upsert dialect: {dialect}")

    return db.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.id == measurement_id)
        .execution_options(populate_existing=True)
    ).scalar_one()


def save_measurement(
    db: Session,
    owner: User,
    payload: BodyMeasurementSave,
    *,
    changed_by: User,
) -> BodyMeasurement:
    owner_today = today_for_user(owner)
    measured_on = payload.measured_on or owner_today
    if measured_on > owner_today:
        raise MeasurementError("Дата замера не может быть в будущем")
    changes = _measurement_changes(payload)

    try:
        _lock_owner_measurements(db, owner.id)
        row = _upsert_measurement(
            db,
            owner_user_id=owner.id,
            measured_on=measured_on,
            changes=changes,
        )
        reconcile_current_measurement_state(db, owner, changed_by=changed_by)
        if changed_by.id != owner.id:
            record_audit_event(
                db,
                actor_user_id=changed_by.id,
                target_user_id=owner.id,
                action="coach.measurement_saved",
                resource_type="body_measurement",
                resource_id=row.id,
                details={"measured_on": measured_on.isoformat(), "fields": sorted(changes)},
            )
        db.commit()
    except NutritionError as exc:
        db.rollback()
        raise MeasurementError(str(exc)) from exc
    db.refresh(row)
    return row


def delete_measurement(
    db: Session,
    owner: User,
    measurement_id: int,
    *,
    changed_by: User,
) -> None:
    _lock_owner_measurements(db, owner.id)
    row = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.id == measurement_id,
            BodyMeasurement.user_id == owner.id,
        )
        .first()
    )
    if row is None:
        raise MeasurementNotFoundError("Запись дневника не найдена")

    measured_on = row.measured_on
    try:
        db.delete(row)
        reconcile_current_measurement_state(db, owner, changed_by=changed_by)
        if changed_by.id != owner.id:
            record_audit_event(
                db,
                actor_user_id=changed_by.id,
                target_user_id=owner.id,
                action="coach.measurement_deleted",
                resource_type="body_measurement",
                resource_id=measurement_id,
                details={"measured_on": measured_on.isoformat()},
            )
        db.commit()
    except NutritionError as exc:
        db.rollback()
        raise MeasurementError(str(exc)) from exc
