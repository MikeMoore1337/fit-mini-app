from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.program import UserProgram, UserWorkout, UserWorkoutExercise, UserWorkoutSet
from app.models.user import User
from app.schemas.workout import WorkoutSetCreate


class WorkoutStateError(ValueError):
    pass


class WorkoutValidationError(ValueError):
    pass


def get_today_workout(db: Session, user: User) -> UserWorkout | None:
    return (
        db.query(UserWorkout)
        .join(UserProgram, UserWorkout.user_program_id == UserProgram.id)
        .options(
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.sets),
        )
        .filter(
            UserProgram.user_id == user.id,
            UserProgram.is_active.is_(True),
            UserWorkout.scheduled_date == date.today(),
        )
        .first()
    )


def start_workout(db: Session, workout: UserWorkout) -> UserWorkout:
    if workout.status == "completed":
        raise WorkoutStateError("Workout already completed")
    if workout.status == "planned":
        workout.status = "in_progress"
        workout.started_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        db.refresh(workout)
    return workout


def add_or_update_set(
    db: Session, workout: UserWorkout, payload: WorkoutSetCreate
) -> UserWorkoutSet:
    if workout.status == "completed":
        raise WorkoutStateError("Cannot log sets for completed workout")
    if workout.status == "planned":
        workout.status = "in_progress"
        workout.started_at = datetime.now(UTC).replace(tzinfo=None)

    exercise = next(
        (row for row in workout.exercises if row.id == payload.workout_exercise_id), None
    )
    if exercise is None:
        raise WorkoutValidationError("Exercise does not belong to workout")
    if payload.set_number < 1:
        raise WorkoutValidationError("set_number must be >= 1")
    if payload.set_number > exercise.prescribed_sets:
        raise WorkoutValidationError("set_number exceeds prescribed_sets")

    row = (
        db.query(UserWorkoutSet)
        .filter(
            UserWorkoutSet.workout_exercise_id == payload.workout_exercise_id,
            UserWorkoutSet.set_number == payload.set_number,
        )
        .first()
    )
    if row is None:
        row = UserWorkoutSet(
            workout_exercise_id=payload.workout_exercise_id, set_number=payload.set_number
        )
        db.add(row)

    row.actual_reps = payload.actual_reps
    row.actual_weight = payload.actual_weight
    row.is_completed = payload.is_completed
    db.commit()
    db.refresh(row)
    return row


def delete_last_set(db: Session, workout: UserWorkout, workout_exercise_id: int) -> None:
    if workout.status == "completed":
        raise WorkoutStateError("Cannot modify sets for completed workout")
    exercise = next((row for row in workout.exercises if row.id == workout_exercise_id), None)
    if exercise is None:
        raise WorkoutValidationError("Exercise does not belong to workout")
    last_set = (
        db.query(UserWorkoutSet)
        .filter(UserWorkoutSet.workout_exercise_id == workout_exercise_id)
        .order_by(UserWorkoutSet.set_number.desc())
        .first()
    )
    if not last_set:
        raise WorkoutValidationError("No logged sets to delete")
    db.delete(last_set)
    db.commit()


def complete_workout(db: Session, workout: UserWorkout) -> UserWorkout:
    if workout.status == "completed":
        return workout
    workout.status = "completed"
    if workout.started_at is None:
        workout.started_at = datetime.now(UTC).replace(tzinfo=None)
    workout.completed_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(workout)
    return workout


def _sets_volume(sets: list[UserWorkoutSet]) -> float:
    return float(
        sum((row.actual_reps or 0) * (row.actual_weight or 0) for row in sets if row.is_completed)
    )


def _top_weight(sets: list[UserWorkoutSet]) -> float | None:
    weights = [
        float(row.actual_weight)
        for row in sets
        if row.is_completed and row.actual_weight is not None
    ]
    return max(weights) if weights else None


def get_previous_completed_exercise(
    db: Session, user: User, workout: UserWorkout, exercise: UserWorkoutExercise
) -> UserWorkoutExercise | None:
    return (
        db.query(UserWorkoutExercise)
        .join(UserWorkout, UserWorkoutExercise.workout_id == UserWorkout.id)
        .join(UserProgram, UserWorkout.user_program_id == UserProgram.id)
        .options(joinedload(UserWorkoutExercise.sets), joinedload(UserWorkoutExercise.workout))
        .filter(
            UserProgram.user_id == user.id,
            UserWorkoutExercise.exercise_id == exercise.exercise_id,
            UserWorkout.id != workout.id,
            UserWorkout.status == "completed",
            UserWorkout.scheduled_date <= workout.scheduled_date,
        )
        .order_by(
            desc(UserWorkout.scheduled_date), desc(UserWorkout.completed_at), desc(UserWorkout.id)
        )
        .first()
    )
