from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workout import (
    LoggedSetItem,
    WorkoutExerciseItem,
    WorkoutProgressSnapshot,
    WorkoutSetCreate,
    WorkoutStatusResponse,
    WorkoutTodayResponse,
)
from app.services.security import get_current_user
from app.services.workouts import (
    WorkoutStateError,
    WorkoutValidationError,
    _sets_volume,
    _top_weight,
    add_or_update_set,
    complete_workout,
    delete_last_set,
    get_previous_completed_exercise,
    get_today_workout,
    start_workout,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/today", response_model=WorkoutTodayResponse | None)
def today(db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = get_today_workout(db, user)
    if workout is None:
        return None
    exercise_rows: list[WorkoutExerciseItem] = []
    for exercise in workout.exercises:
        completed_sets = [row for row in exercise.sets if row.is_completed]
        previous_exercise = get_previous_completed_exercise(db, user, workout, exercise)
        previous_sets = [row for row in (previous_exercise.sets if previous_exercise else []) if row.is_completed]
        current_volume = _sets_volume(completed_sets)
        previous_volume = _sets_volume(previous_sets) if previous_sets else None
        current_top_weight = _top_weight(completed_sets)
        previous_top_weight = _top_weight(previous_sets) if previous_sets else None

        progress = None
        if previous_exercise:
            progress = WorkoutProgressSnapshot(
                previous_workout_title=previous_exercise.workout.title if previous_exercise.workout else None,
                previous_workout_date=previous_exercise.workout.scheduled_date.isoformat() if previous_exercise.workout else None,
                previous_volume=previous_volume,
                current_volume=current_volume,
                volume_delta=(current_volume - previous_volume) if previous_volume is not None else None,
                previous_top_weight=previous_top_weight,
                current_top_weight=current_top_weight,
                top_weight_delta=(current_top_weight - previous_top_weight) if current_top_weight is not None and previous_top_weight is not None else None,
            )

        exercise_rows.append(
            WorkoutExerciseItem(
                id=exercise.id,
                title=exercise.exercise.title,
                prescribed_sets=exercise.prescribed_sets,
                prescribed_reps=exercise.prescribed_reps,
                rest_seconds=exercise.rest_seconds,
                completed_sets=len(completed_sets),
                remaining_sets=max(exercise.prescribed_sets - len(completed_sets), 0),
                logged_sets=[
                    LoggedSetItem(
                        set_number=row.set_number,
                        actual_reps=row.actual_reps,
                        actual_weight=row.actual_weight,
                        is_completed=row.is_completed,
                    )
                    for row in sorted(completed_sets, key=lambda x: x.set_number)
                ],
                previous_logged_sets=[
                    LoggedSetItem(
                        set_number=row.set_number,
                        actual_reps=row.actual_reps,
                        actual_weight=row.actual_weight,
                        is_completed=row.is_completed,
                    )
                    for row in sorted(previous_sets, key=lambda x: x.set_number)
                ],
                progress=progress,
            )
        )

    return WorkoutTodayResponse(
        id=workout.id,
        title=workout.title,
        status=workout.status,
        day_number=workout.day_number,
        can_start=workout.status == "planned",
        can_complete=workout.status in {"planned", "in_progress"},
        can_log_sets=workout.status in {"planned", "in_progress"},
        exercises=exercise_rows,
    )


@router.post("/{workout_id}/start", response_model=WorkoutStatusResponse)
def start(workout_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = get_today_workout(db, user)
    if workout is None or workout.id != workout_id:
        raise HTTPException(status_code=404, detail="Workout not found")
    try:
        workout = start_workout(db, workout)
    except WorkoutStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return WorkoutStatusResponse(id=workout.id, status=workout.status)


@router.post("/{workout_id}/sets")
def add_set(workout_id: int, payload: WorkoutSetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = get_today_workout(db, user)
    if workout is None or workout.id != workout_id:
        raise HTTPException(status_code=404, detail="Workout not found")
    try:
        row = add_or_update_set(db, workout, payload)
    except WorkoutStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WorkoutValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": row.id, "is_completed": row.is_completed}


@router.delete("/{workout_id}/exercises/{workout_exercise_id}/last-set")
def remove_last_set(workout_id: int, workout_exercise_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = get_today_workout(db, user)
    if workout is None or workout.id != workout_id:
        raise HTTPException(status_code=404, detail="Workout not found")
    try:
        delete_last_set(db, workout, workout_exercise_id)
    except WorkoutStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WorkoutValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/{workout_id}/complete", response_model=WorkoutStatusResponse)
def complete(workout_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    workout = get_today_workout(db, user)
    if workout is None or workout.id != workout_id:
        raise HTTPException(status_code=404, detail="Workout not found")
    workout = complete_workout(db, workout)
    return WorkoutStatusResponse(id=workout.id, status=workout.status)
