from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_coach_or_admin
from fitminiapp_api.core.timezone import today_for_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.program import (
    UserProgram,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import BodyMeasurement, CoachClientInvite, User
from fitminiapp_api.schemas.program import (
    AssignTemplateToClientRequest,
    ClientResponse,
    CoachAssignedProgramResponse,
    CoachClientCreate,
    CoachProgramExerciseAssignmentResponse,
    CoachProgramExerciseCreate,
    ProgramAssignmentResponse,
)
from fitminiapp_api.schemas.user import UserProfileUpdate
from fitminiapp_api.schemas.workout import BodyMeasurementResponse, BodyMeasurementSave
from fitminiapp_api.services.coach_clients import (
    add_client_for_coach,
    cancel_client_request_notification,
    create_coach_invite_link,
    get_client_managed_by_coach,
    remove_client_for_coach,
    remove_pending_client_invite,
)
from fitminiapp_api.services.exercise_catalog import _effective_exercise_id, list_exercises
from fitminiapp_api.services.nutrition import recalculate_nutrition_target
from fitminiapp_api.services.profile import update_profile
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.programs import (
    assign_template_to_user,
    get_template_for_user,
    list_clients,
    list_coach_assigned_programs,
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
    "/clients/{client_id}/programs/{program_id}/exercises",
    response_model=CoachProgramExerciseAssignmentResponse,
)
def add_exercise_to_client_program(
    client_id: int,
    program_id: int,
    payload: CoachProgramExerciseCreate,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """Add or update an exercise in every planned workout of a coach-owned assignment."""
    managed_client = _managed_client(db, current_user, client_id)
    program = (
        db.query(UserProgram)
        .filter(
            UserProgram.id == program_id,
            UserProgram.user_id == managed_client.id,
            UserProgram.assigned_by_user_id == current_user.id,
        )
        .first()
    )
    if not program:
        raise HTTPException(status_code=404, detail="Программа клиента не найдена")

    visible_exercise_ids = {
        _effective_exercise_id(exercise) for exercise in list_exercises(db, managed_client)
    }
    if payload.exercise_id not in visible_exercise_ids:
        raise HTTPException(status_code=404, detail="Упражнение недоступно клиенту")

    planned_workouts = [workout for workout in program.workouts if workout.status == "planned"]
    if not planned_workouts:
        raise HTTPException(
            status_code=409,
            detail="В программе нет предстоящих тренировок",
        )

    for workout in planned_workouts:
        workout_exercise = next(
            (row for row in workout.exercises if row.exercise_id == payload.exercise_id),
            None,
        )
        if workout_exercise is None:
            workout_exercise = UserWorkoutExercise(
                workout_id=workout.id,
                exercise_id=payload.exercise_id,
                sort_order=max((row.sort_order for row in workout.exercises), default=0) + 1,
                prescribed_sets=payload.prescribed_sets,
                prescribed_reps=payload.prescribed_reps,
                rest_seconds=payload.rest_seconds,
            )
            db.add(workout_exercise)
            db.flush()
        else:
            workout_exercise.prescribed_sets = payload.prescribed_sets
            workout_exercise.prescribed_reps = payload.prescribed_reps
            workout_exercise.rest_seconds = payload.rest_seconds
            db.query(UserWorkoutSet).filter(
                UserWorkoutSet.workout_exercise_id == workout_exercise.id
            ).delete(synchronize_session=False)

        for set_number in range(1, payload.prescribed_sets + 1):
            db.add(
                UserWorkoutSet(
                    workout_exercise_id=workout_exercise.id,
                    set_number=set_number,
                    actual_reps=None,
                    actual_weight=None,
                    is_completed=False,
                )
            )

    db.commit()
    return {"workouts_updated": len(planned_workouts)}


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
            client_code=payload.client_code,
            source=payload.source,
            full_name=payload.full_name,
            allow_unregistered_username=False,
        )
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/invite-links", status_code=status.HTTP_201_CREATED)
def create_invite_link(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    return create_coach_invite_link(db, current_user)


@router.get("/client-search")
def search_registered_client(
    username: str = Query(min_length=1, max_length=64),
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    from fitminiapp_api.services.telegram_auth import normalize_telegram_username

    normalized = normalize_telegram_username(username)
    client = db.query(User).filter(User.username == normalized, User.is_active.is_(True)).first()
    if not client or client.id == current_user.id:
        raise HTTPException(status_code=404, detail="Пользователь не найден в приложении")
    return {
        "username": client.username,
        "full_name": client.profile.full_name if client.profile else None,
        "photo_url": client.photo_url,
    }


@router.patch("/clients/{client_id}/profile", response_model=ClientResponse)
def update_coach_client_profile(
    client_id: int,
    payload: UserProfileUpdate,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    update_profile(db, client, payload, changed_by=current_user)
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

    if changes.get("weight_kg") is not None:
        recalculate_nutrition_target(
            db,
            client,
            {"weight_kg": changes["weight_kg"]},
            current_user,
        )

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
    invite.status = "revoked"
    cancel_client_request_notification(db, invite.id)
    db.commit()
