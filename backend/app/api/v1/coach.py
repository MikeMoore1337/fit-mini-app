from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_coach_or_admin
from app.core.timezone import today_for_user
from app.db.session import get_db
from app.models.user import BodyMeasurement, CoachClientInvite, User
from app.schemas.program import (
    AssignTemplateToClientRequest,
    ClientResponse,
    CoachAssignedProgramResponse,
    CoachClientCreate,
    ProgramAssignmentResponse,
)
from app.schemas.user import UserProfileUpdate
from app.schemas.workout import BodyMeasurementResponse, BodyMeasurementSave
from app.services.profile import update_profile
from app.services.programs import (
    ProgramError,
    _effective_exercise_id,
    add_client_for_coach,
    assign_template_to_user,
    get_client_managed_by_coach,
    get_template_for_user,
    list_clients,
    list_coach_assigned_programs,
    list_exercises,
    remove_client_for_coach,
    remove_pending_client_invite,
)

router = APIRouter()


def _serialize_measurement(row: BodyMeasurement) -> dict:
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


def _managed_client(db: Session, coach: User, client_id: int) -> User:
    try:
        return get_client_managed_by_coach(db, coach, client_id)
    except ProgramError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _client_list_entry(db: Session, coach: User, client_id: int) -> dict:
    return next(row for row in list_clients(db, coach) if row["id"] == client_id)


@router.get("/clients", response_model=list[ClientResponse])
def coach_clients(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    return list_clients(db, current_user)


@router.get(
    "/assigned-programs",
    response_model=list[CoachAssignedProgramResponse],
)
def coach_assigned_programs(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    return list_coach_assigned_programs(db, current_user)


@router.post(
    "/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_coach_client(
    payload: CoachClientCreate,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        return add_client_for_coach(
            db=db,
            coach=current_user,
            telegram_user_id=payload.telegram_user_id,
            username=payload.username,
            full_name=payload.full_name,
        )
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/clients/{client_id}/profile", response_model=ClientResponse)
def update_coach_client_profile(
    client_id: int,
    payload: UserProfileUpdate,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    update_profile(db, client, payload)
    return _client_list_entry(db, current_user, client_id)


@router.get(
    "/clients/{client_id}/measurements",
    response_model=list[BodyMeasurementResponse],
)
def coach_client_measurements(
    client_id: int,
    limit: int = Query(default=12, ge=1, le=60),
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    rows = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == client.id)
        .order_by(BodyMeasurement.measured_on.desc(), BodyMeasurement.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_measurement(row) for row in rows]


@router.post(
    "/clients/{client_id}/measurements",
    response_model=BodyMeasurementResponse,
)
def save_coach_client_measurement(
    client_id: int,
    payload: BodyMeasurementSave,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    changes = payload.model_dump(exclude_unset=True)
    note = changes.get("note")
    if isinstance(note, str):
        changes["note"] = note.strip() or None

    measurement_keys = (
        "weight_kg",
        "chest_cm",
        "waist_cm",
        "hips_cm",
        "biceps_cm",
        "thigh_cm",
    )
    if not changes.get("note") and not any(
        changes.get(key) is not None for key in measurement_keys
    ):
        raise HTTPException(status_code=400, detail="Укажите вес, замер или заметку")

    measured_on = payload.measured_on or today_for_user(client)
    row = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.user_id == client.id,
            BodyMeasurement.measured_on == measured_on,
        )
        .first()
    )
    if row is None:
        row = BodyMeasurement(user_id=client.id, measured_on=measured_on)
        db.add(row)

    for key in measurement_keys:
        if key in changes:
            setattr(row, key, changes[key])
    if "note" in changes:
        row.note = changes["note"]

    db.commit()
    db.refresh(row)
    return _serialize_measurement(row)


@router.delete(
    "/clients/{client_id}/measurements/{measurement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_coach_client_measurement(
    client_id: int,
    measurement_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    row = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.id == measurement_id,
            BodyMeasurement.user_id == client.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Запись дневника не найдена")
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/clients/{client_id}/templates/{template_id}/assign",
    response_model=ProgramAssignmentResponse,
)
def assign_template_to_coach_client(
    client_id: int,
    template_id: int,
    payload: AssignTemplateToClientRequest | None = None,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    try:
        template = get_template_for_user(db, current_user, template_id)
        visible_exercise_ids = {
            _effective_exercise_id(exercise) for exercise in list_exercises(db, client)
        }
        template_exercise_ids = {
            exercise.exercise_id for day in template.days for exercise in day.exercises
        }
        if not template_exercise_ids.issubset(visible_exercise_ids):
            raise ProgramError("Template contains exercises unavailable to client")
        program, created = assign_template_to_user(
            db,
            template,
            client,
            current_user,
            start_date=payload.start_date if payload else None,
        )
        db.commit()
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=403, detail=detail) from exc
    return {"user_program_id": program.id, "workouts_created": created}


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coach_client(
    client_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        remove_client_for_coach(db, current_user, client_id)
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Client link not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)


@router.delete("/client-invites/{username}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coach_client_invite(
    username: str,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        remove_pending_client_invite(db, current_user, username)
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Client invite not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)


@router.delete("/client-invites/id/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coach_client_invite_by_id(
    invite_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    invite = (
        db.query(CoachClientInvite)
        .filter(
            CoachClientInvite.id == invite_id,
            CoachClientInvite.coach_user_id == current_user.id,
        )
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Client invite not found")
    db.delete(invite)
    db.commit()
