from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_coach_or_admin
from fitminiapp_api.core.timezone import now_for_user_naive, today_for_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.program import (
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import BodyMeasurement, CoachClient, User
from fitminiapp_api.schemas.invite import CoachInviteLinkResponse
from fitminiapp_api.schemas.program import (
    AssignTemplateToClientRequest,
    ClientResponse,
    CoachAssignedProgramResponse,
    CoachProgramExerciseAssignmentResponse,
    CoachProgramExerciseCreate,
    ProgramAssignmentResponse,
)
from fitminiapp_api.schemas.progress import (
    ProgressPeriodDays,
    ProgressSummaryResponse,
    TrainerClientProgressSummary,
)
from fitminiapp_api.schemas.user import UserProfileUpdate
from fitminiapp_api.schemas.workout import (
    BodyMeasurementResponse,
    BodyMeasurementSave,
    WorkoutProgressResponse,
    WorkoutRescheduleRequest,
    WorkoutScheduleItem,
    WorkoutTimelineItem,
)
from fitminiapp_api.services.analytics import build_user_progress, build_workout_timeline
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.coach_clients import (
    create_coach_invite_link,
    get_client_managed_by_coach,
    remove_client_for_coach,
    revoke_coach_invite,
)
from fitminiapp_api.services.exercise_catalog import _effective_exercise_id, list_exercises
from fitminiapp_api.services.notifications import queue_telegram_notification
from fitminiapp_api.services.nutrition import NutritionError, recalculate_nutrition_target
from fitminiapp_api.services.profile import update_profile
from fitminiapp_api.services.program_common import ProgramError, assignment_error_status
from fitminiapp_api.services.programs import (
    assign_template_to_user,
    get_template_for_user,
    list_clients,
    list_coach_assigned_programs,
)
from fitminiapp_api.services.progress import (
    build_progress_summary,
    build_trainer_client_summaries,
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


@router.get(
    "/clients/{client_id}/analytics",
    response_model=WorkoutProgressResponse,
)
def coach_client_analytics(
    client_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    return build_user_progress(db, client)


@router.get(
    "/clients/{client_id}/summary",
    response_model=ProgressSummaryResponse,
)
def coach_client_progress_summary(
    client_id: int,
    period_days: ProgressPeriodDays = ProgressPeriodDays.DAYS_30,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    return build_progress_summary(db, client, period_days)


@router.get(
    "/client-summaries",
    response_model=list[TrainerClientProgressSummary],
)
def coach_client_progress_summaries(
    period_days: ProgressPeriodDays = ProgressPeriodDays.DAYS_30,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    return build_trainer_client_summaries(db, current_user, period_days)


@router.get(
    "/clients/{client_id}/workouts",
    response_model=list[WorkoutTimelineItem],
)
def coach_client_workout_timeline(
    client_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    return build_workout_timeline(db, client, limit=limit)


@router.patch(
    "/clients/{client_id}/workouts/{workout_id}/schedule",
    response_model=WorkoutScheduleItem,
)
def coach_reschedule_client_workout(
    client_id: int,
    workout_id: int,
    payload: WorkoutRescheduleRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    managed_client = _managed_client(db, current_user, client_id)
    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserWorkout.id == workout_id,
            UserProgram.user_id == managed_client.id,
            UserProgram.is_active.is_(True),
        )
        .with_for_update()
        .first()
    )
    if workout is None:
        raise HTTPException(status_code=404, detail="Тренировка клиента не найдена")
    if workout.status != "planned":
        raise HTTPException(
            status_code=409,
            detail="Перенести можно только запланированную тренировку",
        )

    now = now_for_user_naive(managed_client)
    if payload.scheduled_date < now.date() or (
        payload.scheduled_date == now.date()
        and payload.scheduled_time is not None
        and payload.scheduled_time < now.time()
    ):
        raise HTTPException(status_code=422, detail="Нельзя назначить дату и время в прошлом")

    collision = (
        db.query(UserWorkout.id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == managed_client.id,
            UserProgram.is_active.is_(True),
            UserWorkout.id != workout.id,
            UserWorkout.scheduled_date == payload.scheduled_date,
            UserWorkout.status.notin_({"completed", "skipped", "cancelled"}),
        )
        .first()
    )
    if collision is not None:
        raise HTTPException(status_code=409, detail="На эту дату уже назначена тренировка")

    workout.scheduled_date = payload.scheduled_date
    workout.scheduled_time = payload.scheduled_time
    time_text = f" в {payload.scheduled_time.strftime('%H:%M')}" if payload.scheduled_time else ""
    queue_telegram_notification(
        db,
        managed_client,
        title="Тренер изменил тренировку",
        body=(
            f"Тренер перенёс тренировку «{workout.title}» на "
            f"{payload.scheduled_date:%d.%m.%Y}{time_text}."
        ),
    )
    db.commit()
    return {
        "id": workout.id,
        "scheduled_date": workout.scheduled_date,
        "scheduled_time": workout.scheduled_time,
        "title": workout.title,
        "status": workout.status,
        "day_number": workout.day_number,
        "week_number": workout.week_number,
    }


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
    """Add or update an exercise in future occurrences of one selected program day."""
    managed_client = _managed_client(db, current_user, client_id)
    program = (
        db.query(UserProgram)
        .filter(
            UserProgram.id == program_id,
            UserProgram.user_id == managed_client.id,
            UserProgram.assigned_by_user_id == current_user.id,
            UserProgram.is_active.is_(True),
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

    available_days = sorted(
        {
            workout.day_number
            for workout in program.workouts
            if workout.status == "planned"
            and workout.scheduled_date >= today_for_user(managed_client)
        }
    )
    selected_day = payload.day_number
    if selected_day is None:
        if len(available_days) != 1:
            raise HTTPException(
                status_code=422,
                detail="Выберите день программы для добавления упражнения",
            )
        selected_day = available_days[0]

    planned_workouts = [
        workout
        for workout in program.workouts
        if workout.status == "planned"
        and workout.day_number == selected_day
        and workout.scheduled_date >= today_for_user(managed_client)
    ]
    if not planned_workouts:
        raise HTTPException(
            status_code=409,
            detail="Для выбранного дня нет предстоящих тренировок",
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
                notes=payload.notes,
            )
            db.add(workout_exercise)
            db.flush()
        else:
            workout_exercise.prescribed_sets = payload.prescribed_sets
            workout_exercise.prescribed_reps = payload.prescribed_reps
            workout_exercise.rest_seconds = payload.rest_seconds
            workout_exercise.notes = payload.notes
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

    record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=managed_client.id,
        action="coach.program_exercise_upserted",
        resource_type="user_program",
        resource_id=program.id,
        details={
            "day_number": selected_day,
            "exercise_id": payload.exercise_id,
            "workouts_updated": len(planned_workouts),
        },
    )
    db.commit()
    return {"workouts_updated": len(planned_workouts)}


@router.post(
    "/invite-links",
    response_model=CoachInviteLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invite_link(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    return create_coach_invite_link(db, current_user)


@router.patch("/clients/{client_id}/profile", response_model=ClientResponse)
def update_coach_client_profile(
    client_id: int,
    payload: UserProfileUpdate,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    client = _managed_client(db, current_user, client_id)
    profile_changes = payload.model_dump(exclude_unset=True)
    changed_fields = sorted(profile_changes)
    if "full_name" in profile_changes:
        relation = (
            db.query(CoachClient)
            .filter(
                CoachClient.coach_user_id == current_user.id,
                CoachClient.client_user_id == client.id,
                CoachClient.status == "active",
            )
            .one()
        )
        private_name = profile_changes.pop("full_name")
        relation.private_name = (private_name.strip() or None) if private_name else None

    if profile_changes:
        update_profile(
            db,
            client,
            UserProfileUpdate.model_validate(profile_changes),
            changed_by=current_user,
            commit=False,
        )
    record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=client.id,
        action="coach.client_profile_updated",
        resource_type="user_profile",
        resource_id=client.profile.id if client.profile else None,
        details={"fields": changed_fields},
    )
    db.commit()
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
        try:
            recalculate_nutrition_target(
                db,
                client,
                {"weight_kg": changes["weight_kg"]},
                current_user,
            )
        except NutritionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.flush()
    record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=client.id,
        action="coach.measurement_saved",
        resource_type="body_measurement",
        resource_id=row.id,
        details={"measured_on": measured_on.isoformat(), "fields": sorted(changes)},
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
    record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=client.id,
        action="coach.measurement_deleted",
        resource_type="body_measurement",
        resource_id=row.id,
        details={"measured_on": row.measured_on.isoformat()},
    )
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
            duration_weeks=payload.duration_weeks if payload else 1,
            schedule_weekdays=payload.schedule_weekdays if payload else None,
            replace_active=payload.replace_active if payload else False,
        )
        record_audit_event(
            db,
            actor_user_id=current_user.id,
            target_user_id=client.id,
            action="coach.program_assigned",
            resource_type="user_program",
            resource_id=program.id,
            details={
                "template_id": template.id,
                "workouts_created": created,
                "duration_weeks": program.duration_weeks,
            },
        )
        db.commit()
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail) from exc
        error_status = assignment_error_status(detail)
        if error_status != 400:
            raise HTTPException(status_code=error_status, detail=detail) from exc
        raise HTTPException(status_code=403, detail=detail) from exc
    return {
        "user_program_id": program.id,
        "workouts_created": created,
        "status": program.status,
        "start_date": program.start_date,
        "duration_weeks": program.duration_weeks,
    }


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


@router.delete("/client-invites/id/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coach_client_invite_by_id(
    invite_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        revoke_coach_invite(db, current_user, invite_id)
    except ProgramError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
