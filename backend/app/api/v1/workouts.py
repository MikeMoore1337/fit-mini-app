from datetime import date, datetime

from app.api.dependencies.auth import require_user
from app.db.session import get_db
from app.models.program import UserProgram, UserWorkout, UserWorkoutExercise, UserWorkoutSet
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

router = APIRouter()


def _get_user_workout_or_404(db: Session, current_user: User, workout_id: int) -> UserWorkout:
    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .options(
            joinedload(UserWorkout.exercises)
            .joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.exercises)
            .joinedload(UserWorkoutExercise.sets),
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


def _serialize_workout(workout: UserWorkout) -> dict:
    return {
        "id": workout.id,
        "scheduled_date": str(workout.scheduled_date),
        "day_number": workout.day_number,
        "title": workout.title,
        "status": workout.status,
        "started_at": workout.started_at.isoformat() if workout.started_at else None,
        "completed_at": workout.completed_at.isoformat() if workout.completed_at else None,
        "exercises": [
            {
                "id": item.id,
                "exercise_id": item.exercise_id,
                "exercise_title": item.exercise.title if item.exercise else f"Exercise {item.exercise_id}",
                "sort_order": item.sort_order,
                "prescribed_sets": item.prescribed_sets,
                "prescribed_reps": item.prescribed_reps,
                "rest_seconds": item.rest_seconds,
                "sets": [
                    {
                        "id": set_item.id,
                        "set_number": set_item.set_number,
                        "actual_reps": set_item.actual_reps,
                        "actual_weight": set_item.actual_weight,
                        "is_completed": set_item.is_completed,
                    }
                    for set_item in sorted(item.sets, key=lambda x: x.set_number)
                ],
            }
            for item in sorted(workout.exercises, key=lambda x: x.sort_order)
        ],
    }


@router.get("/today")
def get_today_workout(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    today = date.today()

    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .options(
            joinedload(UserWorkout.exercises)
            .joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.exercises)
            .joinedload(UserWorkoutExercise.sets),
        )
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.is_active.is_(True),
            UserWorkout.scheduled_date == today,
        )
        .order_by(UserWorkout.id.asc())
        .first()
    )

    if not workout:
        raise HTTPException(status_code=404, detail="На сегодня тренировка не назначена")

    return _serialize_workout(workout)


@router.post("/{workout_id}/start")
def start_workout(
    workout_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)

    if workout.status == "completed":
        raise HTTPException(status_code=400, detail="Тренировка уже завершена")

    if not workout.started_at:
        workout.started_at = datetime.utcnow()
    workout.status = "in_progress"
    db.commit()
    db.refresh(workout)

    workout = _get_user_workout_or_404(db, current_user, workout_id)
    return _serialize_workout(workout)


@router.post("/{workout_id}/finish")
def finish_workout(
    workout_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    workout = _get_user_workout_or_404(db, current_user, workout_id)

    if not workout.started_at:
        workout.started_at = datetime.utcnow()
    workout.completed_at = datetime.utcnow()
    workout.status = "completed"

    db.commit()
    db.refresh(workout)

    workout = _get_user_workout_or_404(db, current_user, workout_id)
    return _serialize_workout(workout)


@router.patch("/sets/{set_id}")
def update_workout_set(
    set_id: int,
    payload: dict,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    set_row = (
        db.query(UserWorkoutSet)
        .join(UserWorkoutExercise, UserWorkoutExercise.id == UserWorkoutSet.workout_exercise_id)
        .join(UserWorkout, UserWorkout.id == UserWorkoutExercise.workout_id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserWorkoutSet.id == set_id,
            UserProgram.user_id == current_user.id,
        )
        .first()
    )

    if not set_row:
        raise HTTPException(status_code=404, detail="Подход не найден")

    if "actual_reps" in payload:
        set_row.actual_reps = payload.get("actual_reps")
    if "actual_weight" in payload:
        set_row.actual_weight = payload.get("actual_weight")
    if "is_completed" in payload:
        set_row.is_completed = bool(payload.get("is_completed"))

    db.commit()
    db.refresh(set_row)

    return {
        "id": set_row.id,
        "set_number": set_row.set_number,
        "actual_reps": set_row.actual_reps,
        "actual_weight": set_row.actual_weight,
        "is_completed": set_row.is_completed,
    }


@router.get("/history")
def workout_history(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=4, ge=1, le=20),
):
    workouts = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(UserProgram.user_id == current_user.id)
        .order_by(UserWorkout.scheduled_date.desc(), UserWorkout.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": item.id,
            "scheduled_date": str(item.scheduled_date),
            "title": item.title,
            "status": item.status,
            "started_at": item.started_at.isoformat() if item.started_at else None,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        }
        for item in workouts
    ]
