from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.api.dependencies.auth import require_user
from fitminiapp_api.core.timezone import now_for_user_naive, today_for_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.feedback import WorkoutComment, WorkoutCommentRevision
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.program import (
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
    WorkoutAdaptation,
)
from fitminiapp_api.models.user import BodyMeasurement, User
from fitminiapp_api.schemas.feedback import WorkoutCommentResponse
from fitminiapp_api.schemas.program import EquipmentIdentifier
from fitminiapp_api.schemas.progress import ProgressPeriodDays, ProgressSummaryResponse
from fitminiapp_api.schemas.workout import (
    BodyMeasurementResponse,
    BodyMeasurementSave,
    TrainingAnalyticsResponse,
    WorkoutAdaptationApplyRequest,
    WorkoutAdaptationApplyResponse,
    WorkoutAdaptationPreviewResponse,
    WorkoutAdaptationRequest,
    WorkoutAlternativeItem,
    WorkoutFinishRequest,
    WorkoutHistoryItem,
    WorkoutHistorySummary,
    WorkoutProgressResponse,
    WorkoutRescheduleRequest,
    WorkoutScheduleItem,
    WorkoutSetUpdate,
    WorkoutStatusResponse,
    WorkoutTodayResponse,
)
from fitminiapp_api.services.analytics import build_training_analytics, build_user_progress
from fitminiapp_api.services.exercise_catalog import get_visible_exercise_display_map
from fitminiapp_api.services.exercise_guides import get_exercise_guide
from fitminiapp_api.services.notifications import queue_telegram_notification
from fitminiapp_api.services.nutrition import NutritionError, recalculate_nutrition_target
from fitminiapp_api.services.progress import build_progress_summary
from fitminiapp_api.services.workout_adaptation import (
    WorkoutAdaptationError,
    apply_adaptation,
    build_adaptation_preview,
    list_compatible_alternatives,
)
from fitminiapp_api.services.workout_comments import (
    WorkoutCommentError,
    list_client_workout_comments,
    serialize_workout_comment,
)
from fitminiapp_api.services.workout_sync import (
    WorkoutSetSyncError,
    apply_workout_set_update,
    replayed_workout_set,
    serialize_workout_set,
)
from fitminiapp_api.services.workouts import (
    counts_toward_working_volume,
    working_volume_set_filter,
)

router = APIRouter()


@router.get("/{workout_id}/comments", response_model=list[WorkoutCommentResponse])
def get_my_workout_comments(
    workout_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        comments = list_client_workout_comments(db, current_user, workout_id)
    except WorkoutCommentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return [serialize_workout_comment(comment) for comment in comments]


def _get_user_workout_or_404(db: Session, current_user: User, workout_id: int) -> UserWorkout:
    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .options(
            joinedload(UserWorkout.user_program),
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.sets),
            joinedload(UserWorkout.adaptations),
        )
        .filter(
            UserWorkout.id == workout_id,
            UserProgram.user_id == current_user.id,
        )
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    return workout


def _lock_program(db: Session, program_id: int) -> UserProgram:
    return (
        db.query(UserProgram)
        .filter(UserProgram.id == program_id)
        .populate_existing()
        .with_for_update()
        .one()
    )


def _require_active_program(program: UserProgram) -> None:
    if not program.is_active:
        raise HTTPException(status_code=409, detail="Программа уже завершена или архивирована")


def _reconcile_program_completion(db: Session, program: UserProgram, current_user: User) -> None:
    db.flush()
    remaining_workout = (
        db.query(UserWorkout.id)
        .filter(
            UserWorkout.user_program_id == program.id,
            UserWorkout.status.notin_({"completed", "skipped", "cancelled"}),
        )
        .first()
    )
    if remaining_workout is None:
        program.status = "completed"
        program.is_active = False
        program.completed_at = now_for_user_naive(current_user)


def _delete_workouts(db: Session, workout_ids: list[int]) -> int:
    if not workout_ids:
        return 0

    db.query(WorkoutAdaptation).filter(WorkoutAdaptation.workout_id.in_(workout_ids)).delete(
        synchronize_session=False
    )

    comment_ids = [
        item.id
        for item in db.query(WorkoutComment.id)
        .filter(WorkoutComment.workout_id.in_(workout_ids))
        .all()
    ]
    if comment_ids:
        db.query(Notification).filter(
            Notification.dedupe_key.in_(
                [f"trainer_feedback:{comment_id}" for comment_id in comment_ids]
            )
        ).delete(synchronize_session=False)
        db.query(WorkoutCommentRevision).filter(
            WorkoutCommentRevision.comment_id.in_(comment_ids)
        ).delete(synchronize_session=False)
        db.query(WorkoutComment).filter(WorkoutComment.id.in_(comment_ids)).delete(
            synchronize_session=False
        )

    workout_exercise_ids = [
        item.id
        for item in db.query(UserWorkoutExercise.id)
        .filter(UserWorkoutExercise.workout_id.in_(workout_ids))
        .all()
    ]

    if workout_exercise_ids:
        db.query(UserWorkoutSet).filter(
            UserWorkoutSet.workout_exercise_id.in_(workout_exercise_ids)
        ).delete(synchronize_session=False)

        db.query(UserWorkoutExercise).filter(
            UserWorkoutExercise.id.in_(workout_exercise_ids)
        ).delete(synchronize_session=False)

    deleted = (
        db.query(UserWorkout)
        .filter(UserWorkout.id.in_(workout_ids))
        .delete(synchronize_session=False)
    )
    return deleted


def _serialize_workout(workout: UserWorkout, db: Session, current_user: User) -> dict:
    visible_map = get_visible_exercise_display_map(db, current_user)

    return {
        "id": workout.id,
        "scheduled_date": str(workout.scheduled_date),
        "scheduled_time": workout.scheduled_time,
        "day_number": workout.day_number,
        "week_number": workout.week_number,
        "title": workout.title,
        "status": workout.status,
        "started_at": workout.started_at.isoformat() if workout.started_at else None,
        "completed_at": workout.completed_at.isoformat() if workout.completed_at else None,
        "exercises": [
            {
                "id": item.id,
                "exercise_id": item.exercise_id,
                "exercise_title": (
                    visible_map[item.exercise_id].title
                    if item.exercise_id in visible_map
                    else (
                        item.exercise.title if item.exercise else f"Упражнение {item.exercise_id}"
                    )
                ),
                "sort_order": item.sort_order,
                "prescribed_sets": item.prescribed_sets,
                "prescribed_reps": item.prescribed_reps,
                "rest_seconds": item.rest_seconds,
                "notes": item.notes,
                "superset_group": item.superset_group,
                "superset_order": item.superset_order,
                "has_guide": bool(
                    (visible_map.get(item.exercise_id) or item.exercise)
                    and get_exercise_guide(visible_map.get(item.exercise_id) or item.exercise)
                ),
                "sets": [
                    {
                        "id": set_item.id,
                        "set_number": set_item.set_number,
                        "actual_reps": set_item.actual_reps,
                        "actual_weight": set_item.actual_weight,
                        "rir": set_item.rir,
                        "set_kind": set_item.set_kind,
                        "reached_failure": set_item.reached_failure,
                        "is_completed": set_item.is_completed,
                        "version": set_item.version,
                    }
                    for set_item in sorted(item.sets, key=lambda x: x.set_number)
                ],
            }
            for item in sorted(workout.exercises, key=lambda x: x.sort_order)
        ],
    }


def _serialize_body_measurement(row: BodyMeasurement) -> dict:
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


@router.get("/today", response_model=WorkoutTodayResponse)
def get_today_workout(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    today = today_for_user(current_user)

    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .options(
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.sets),
        )
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.is_active.is_(True),
            UserWorkout.scheduled_date == today,
            UserWorkout.status.in_({"planned", "in_progress"}),
        )
        .order_by(UserWorkout.id.asc())
        .first()
    )

    if not workout:
        raise HTTPException(status_code=404, detail="На сегодня тренировка не назначена")

    return _serialize_workout(workout, db, current_user)


@router.get(
    "/{workout_id}/exercises/{workout_exercise_id}/alternatives",
    response_model=list[WorkoutAlternativeItem],
)
def workout_exercise_alternatives(
    workout_id: int,
    workout_exercise_id: int,
    available_equipment_ids: list[EquipmentIdentifier] | None = Query(default=None),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if available_equipment_ids is not None and (
        len(available_equipment_ids) > 9
        or len(set(available_equipment_ids)) != len(available_equipment_ids)
    ):
        raise HTTPException(
            status_code=422,
            detail="Укажите не больше девяти уникальных видов оборудования",
        )
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    try:
        return list_compatible_alternatives(
            db,
            current_user,
            workout,
            workout_exercise_id,
            set(available_equipment_ids or []),
        )
    except WorkoutAdaptationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post(
    "/{workout_id}/adaptations/preview",
    response_model=WorkoutAdaptationPreviewResponse,
)
def preview_workout_adaptation(
    workout_id: int,
    payload: WorkoutAdaptationRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    try:
        return build_adaptation_preview(db, current_user, workout, payload)
    except WorkoutAdaptationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post(
    "/{workout_id}/adaptations/apply",
    response_model=WorkoutAdaptationApplyResponse,
)
def apply_workout_adaptation(
    workout_id: int,
    payload: WorkoutAdaptationApplyRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    _lock_program(db, workout.user_program_id)
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    try:
        adaptation = apply_adaptation(
            db,
            current_user,
            workout,
            payload,
            payload.preview_token,
        )
    except WorkoutAdaptationError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    updated = _get_user_workout_or_404(db, current_user, workout_id)
    return {
        "adaptation_id": adaptation.id,
        "applied_at": adaptation.applied_at,
        "workout": _serialize_workout(updated, db, current_user),
    }


@router.get("/week", response_model=list[WorkoutScheduleItem])
def get_week_schedule(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    today = today_for_user(current_user)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    workouts = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.is_active.is_(True),
            UserWorkout.scheduled_date.between(week_start, week_end),
        )
        .order_by(UserWorkout.scheduled_date.asc(), UserWorkout.id.asc())
        .all()
    )
    return [
        {
            "id": workout.id,
            "scheduled_date": str(workout.scheduled_date),
            "scheduled_time": workout.scheduled_time,
            "title": workout.title,
            "status": workout.status,
            "day_number": workout.day_number,
            "week_number": workout.week_number,
        }
        for workout in workouts
    ]


@router.get("/schedule", response_model=list[WorkoutScheduleItem])
def get_schedule(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    start = date_from or today_for_user(current_user)
    end = date_to or (start + timedelta(days=55))
    if end < start:
        raise HTTPException(status_code=422, detail="date_to must not be before date_from")
    if (end - start).days > 92:
        raise HTTPException(
            status_code=422, detail="Диапазон расписания не может быть больше 93 дней"
        )

    workouts = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.is_active.is_(True),
            UserWorkout.scheduled_date.between(start, end),
        )
        .order_by(UserWorkout.scheduled_date.asc(), UserWorkout.id.asc())
        .all()
    )
    return [
        {
            "id": workout.id,
            "scheduled_date": workout.scheduled_date,
            "scheduled_time": workout.scheduled_time,
            "title": workout.title,
            "status": workout.status,
            "day_number": workout.day_number,
            "week_number": workout.week_number,
        }
        for workout in workouts
    ]


@router.get("/progress", response_model=WorkoutProgressResponse)
def workout_progress(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return build_user_progress(db, current_user)


@router.get("/progress/summary", response_model=ProgressSummaryResponse)
def workout_progress_summary(
    period_days: ProgressPeriodDays = ProgressPeriodDays.DAYS_30,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return build_progress_summary(db, current_user, period_days)


@router.get("/progress/training-analytics", response_model=TrainingAnalyticsResponse)
def workout_training_analytics(
    period_days: ProgressPeriodDays = ProgressPeriodDays.DAYS_30,
    exercise_history_limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return build_training_analytics(
        db,
        current_user,
        period_days,
        exercise_history_limit=exercise_history_limit,
    )


@router.delete("/today", status_code=status.HTTP_204_NO_CONTENT)
def delete_today_workout(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    today = today_for_user(current_user)

    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.is_active.is_(True),
            UserWorkout.scheduled_date == today,
            UserWorkout.status.in_({"planned", "in_progress"}),
        )
        .order_by(UserWorkout.id.asc())
        .first()
    )

    if not workout:
        raise HTTPException(status_code=404, detail="На сегодня тренировка не назначена")

    program = _lock_program(db, workout.user_program_id)
    db.refresh(workout)
    _require_active_program(program)
    if workout.status == "in_progress":
        raise HTTPException(
            status_code=409,
            detail="Начатую тренировку нельзя удалить — сначала завершите её",
        )
    if workout.status != "planned":
        raise HTTPException(status_code=409, detail="Недопустимое состояние тренировки")
    workout.status = "skipped"
    _reconcile_program_completion(db, program, current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{workout_id}/start", response_model=WorkoutTodayResponse)
def start_workout(
    workout_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    program = _lock_program(db, workout.user_program_id)
    db.refresh(workout)

    if workout.scheduled_date != today_for_user(current_user):
        raise HTTPException(status_code=409, detail="Можно начать только тренировку на сегодня")
    if workout.status == "completed":
        raise HTTPException(status_code=409, detail="Тренировка уже завершена")
    _require_active_program(program)
    if workout.status not in {"planned", "in_progress"}:
        raise HTTPException(status_code=409, detail="Недопустимое состояние тренировки")

    if not workout.started_at:
        workout.started_at = now_for_user_naive(current_user)
    workout.status = "in_progress"
    if program.status == "scheduled":
        program.status = "active"
    db.commit()
    db.refresh(workout)

    workout = _get_user_workout_or_404(db, current_user, workout_id)
    return _serialize_workout(workout, db, current_user)


@router.post("/{workout_id}/finish", response_model=WorkoutTodayResponse)
def finish_workout(
    workout_id: int,
    payload: WorkoutFinishRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    program = _lock_program(db, workout.user_program_id)
    db.refresh(workout)

    if workout.scheduled_date != today_for_user(current_user):
        raise HTTPException(status_code=409, detail="Можно завершить только тренировку на сегодня")
    if workout.status == "completed":
        raise HTTPException(status_code=409, detail="Тренировка уже завершена")
    _require_active_program(program)
    if workout.status != "in_progress":
        raise HTTPException(status_code=409, detail="Сначала начните тренировку")

    all_sets = (
        db.query(UserWorkoutSet)
        .join(
            UserWorkoutExercise,
            UserWorkoutExercise.id == UserWorkoutSet.workout_exercise_id,
        )
        .filter(
            UserWorkoutExercise.workout_id == workout.id,
        )
        .all()
    )
    completed_sets = [row for row in all_sets if row.is_completed]
    if not completed_sets:
        raise HTTPException(
            status_code=409,
            detail="Отметьте хотя бы один выполненный подход",
        )
    if len(completed_sets) < len(all_sets) and not (payload and payload.confirm_incomplete):
        raise HTTPException(
            status_code=409,
            detail="Есть незаполненные подходы. Подтвердите досрочное завершение",
        )

    workout.completed_at = now_for_user_naive(current_user)
    workout.status = "completed"

    _reconcile_program_completion(db, program, current_user)

    db.commit()
    db.refresh(workout)
    return _serialize_workout(workout, db, current_user)


@router.patch("/sets/{set_id}", response_model=WorkoutStatusResponse)
def update_workout_set(
    set_id: int,
    payload: WorkoutSetUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    result = (
        db.query(UserWorkoutSet, UserWorkout, UserProgram)
        .join(UserWorkoutExercise, UserWorkoutExercise.id == UserWorkoutSet.workout_exercise_id)
        .join(UserWorkout, UserWorkout.id == UserWorkoutExercise.workout_id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserWorkoutSet.id == set_id,
            UserProgram.user_id == current_user.id,
        )
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Подход не найден")

    set_row, workout, _ = result
    program = _lock_program(db, workout.user_program_id)
    db.refresh(workout)
    db.refresh(set_row)
    changes = payload.model_dump(exclude_unset=True)
    expected_version = changes.pop("expected_version", None)
    mutation_id = changes.pop("mutation_id", None)

    try:
        replayed = replayed_workout_set(db, set_row, mutation_id, changes)
        if replayed is not None:
            return serialize_workout_set(replayed)
        if mutation_id is None and workout.status != "in_progress":
            raise HTTPException(
                status_code=409,
                detail="Подходы можно изменять только во время тренировки",
            )
        if workout.status == "in_progress":
            _require_active_program(program)
        apply_workout_set_update(
            db,
            set_row,
            workout,
            changes,
            expected_version=expected_version,
            mutation_id=mutation_id,
        )
    except WorkoutSetSyncError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    db.commit()
    db.refresh(set_row)
    return serialize_workout_set(set_row)


@router.patch("/{workout_id}/schedule", response_model=WorkoutScheduleItem)
def reschedule_workout(
    workout_id: int,
    payload: WorkoutRescheduleRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    program = _lock_program(db, workout.user_program_id)
    db.refresh(workout)
    _require_active_program(program)
    if workout.status != "planned":
        raise HTTPException(
            status_code=409,
            detail="Перенести можно только запланированную тренировку",
        )
    if payload.scheduled_date < today_for_user(current_user):
        raise HTTPException(status_code=422, detail="Нельзя перенести тренировку в прошлое")
    now = now_for_user_naive(current_user)
    if (
        payload.scheduled_date == now.date()
        and payload.scheduled_time is not None
        and payload.scheduled_time < now.time()
    ):
        raise HTTPException(status_code=422, detail="Нельзя назначить время в прошлом")

    collision = (
        db.query(UserWorkout.id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == current_user.id,
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
    if program.assigned_by_user_id and program.assigned_by_user_id != current_user.id:
        trainer = db.query(User).filter(User.id == program.assigned_by_user_id).first()
        if trainer is not None and trainer.is_active:
            time_text = (
                f" в {payload.scheduled_time.strftime('%H:%M')}" if payload.scheduled_time else ""
            )
            queue_telegram_notification(
                db,
                trainer,
                title="Клиент изменил тренировку",
                body=(
                    f"Клиент перенёс тренировку «{workout.title}» на "
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


@router.post("/{workout_id}/skip", response_model=WorkoutScheduleItem)
def skip_workout(
    workout_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)
    program = _lock_program(db, workout.user_program_id)
    db.refresh(workout)
    _require_active_program(program)
    if workout.status != "planned":
        raise HTTPException(
            status_code=409,
            detail="Пропустить можно только запланированную тренировку",
        )
    workout.status = "skipped"

    _reconcile_program_completion(db, program, current_user)

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


@router.get("/history", response_model=list[WorkoutHistoryItem])
def workout_history(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=4, ge=1, le=20),
):
    workouts = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .options(
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.sets),
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.adaptations),
        )
        .filter(
            UserProgram.user_id == current_user.id,
            UserWorkout.status == "completed",
        )
        .order_by(UserWorkout.scheduled_date.desc(), UserWorkout.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    rows = []
    for item in workouts:
        sets = [set_row for exercise in item.exercises for set_row in exercise.sets]
        completed_sets = [set_row for set_row in sets if set_row.is_completed]
        volume_kg = sum(
            (set_row.actual_weight or 0) * (set_row.actual_reps or 0)
            for set_row in completed_sets
            if counts_toward_working_volume(set_row)
        )
        rows.append(
            {
                "id": item.id,
                "scheduled_date": str(item.scheduled_date),
                "scheduled_time": item.scheduled_time,
                "title": item.title,
                "status": item.status,
                "started_at": item.started_at.isoformat() if item.started_at else None,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                "completed_sets": len(completed_sets),
                "volume_kg": round(volume_kg, 1),
                "exercises": [
                    {
                        "workout_exercise_id": exercise.id,
                        "exercise_id": exercise.exercise_id,
                        "title": exercise.exercise.title,
                        "prescribed_sets": exercise.prescribed_sets,
                        "prescribed_reps": exercise.prescribed_reps,
                        "sort_order": exercise.sort_order,
                    }
                    for exercise in sorted(
                        item.exercises,
                        key=lambda exercise: (exercise.sort_order, exercise.id),
                    )
                ],
                "adaptations": [
                    {
                        "id": adaptation.id,
                        "reason": adaptation.reason,
                        "ruleset_version": adaptation.ruleset_version,
                        "applied_at": adaptation.applied_at,
                        "changes": adaptation.applied_diff,
                    }
                    for adaptation in item.adaptations
                ],
            }
        )

    return rows


@router.get("/history/summary", response_model=WorkoutHistorySummary)
def workout_history_summary(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(
            func.count(func.distinct(UserWorkout.id)),
            func.count(UserWorkoutSet.id).filter(UserWorkoutSet.is_completed.is_(True)),
            func.coalesce(
                func.sum(
                    func.coalesce(UserWorkoutSet.actual_reps, 0)
                    * func.coalesce(UserWorkoutSet.actual_weight, 0)
                ).filter(
                    UserWorkoutSet.is_completed.is_(True),
                    working_volume_set_filter(),
                ),
                0,
            ),
        )
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .outerjoin(UserWorkoutExercise, UserWorkoutExercise.workout_id == UserWorkout.id)
        .outerjoin(
            UserWorkoutSet,
            UserWorkoutSet.workout_exercise_id == UserWorkoutExercise.id,
        )
        .filter(
            UserProgram.user_id == current_user.id,
            UserWorkout.status == "completed",
        )
        .one()
    )
    return {
        "workouts_completed": int(row[0] or 0),
        "completed_sets": int(row[1] or 0),
        "volume_kg": round(float(row[2] or 0), 2),
    }


@router.get("/diary", response_model=list[BodyMeasurementResponse])
def body_measurements(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=12, ge=1, le=60),
):
    rows = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == current_user.id)
        .order_by(BodyMeasurement.measured_on.desc(), BodyMeasurement.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_body_measurement(row) for row in rows]


@router.post("/diary", response_model=BodyMeasurementResponse)
def save_body_measurement(
    payload: BodyMeasurementSave,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    changes = payload.model_dump(exclude_unset=True)
    note = changes.get("note")
    if isinstance(note, str):
        changes["note"] = note.strip() or None

    measurement_keys = [
        "weight_kg",
        "chest_cm",
        "waist_cm",
        "hips_cm",
        "biceps_cm",
        "thigh_cm",
    ]
    has_measurement = any(changes.get(key) is not None for key in measurement_keys)
    if not changes.get("note") and not has_measurement:
        raise HTTPException(status_code=400, detail="Укажите вес, замер или заметку")

    measured_on = payload.measured_on or today_for_user(current_user)
    row = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.user_id == current_user.id,
            BodyMeasurement.measured_on == measured_on,
        )
        .first()
    )

    if row is None:
        row = BodyMeasurement(user_id=current_user.id, measured_on=measured_on)
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
                current_user,
                {"weight_kg": changes["weight_kg"]},
                current_user,
            )
        except NutritionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    db.refresh(row)
    return _serialize_body_measurement(row)


@router.delete("/diary/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_body_measurement(
    measurement_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.id == measurement_id,
            BodyMeasurement.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Запись дневника не найдена")

    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_workout_history(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout_ids = [
        item.id
        for item in db.query(UserWorkout.id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserWorkout.status == "completed",
        )
        .all()
    ]
    _delete_workouts(db, workout_ids)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
