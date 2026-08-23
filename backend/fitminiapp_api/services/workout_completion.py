from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from fitminiapp_api.models.program import (
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import User
from fitminiapp_api.services.workouts import counts_toward_working_volume, working_volume_set_filter


def _exercise_result(exercise: UserWorkoutExercise, title: str) -> dict:
    completed_sets = [workout_set for workout_set in exercise.sets if workout_set.is_completed]
    reps = [
        workout_set.actual_reps
        for workout_set in completed_sets
        if workout_set.actual_reps is not None
    ]
    loads = [
        float(workout_set.actual_weight)
        for workout_set in completed_sets
        if workout_set.actual_weight is not None
    ]
    return {
        "workout_exercise_id": exercise.id,
        "exercise_id": exercise.exercise_id,
        "exercise_title": title,
        "completed_sets": len(completed_sets),
        "reps_total": sum(reps) if reps else None,
        "reps_recorded_sets": len(reps),
        "max_load_kg": max(loads) if loads else None,
        "load_recorded_sets": len(loads),
    }


def _personal_records(
    db: Session,
    user: User,
    workout: UserWorkout,
    titles: Mapping[int, str],
) -> list[dict]:
    if workout.completed_at is None:
        earlier_workout_filter = or_(
            UserWorkout.scheduled_date < workout.scheduled_date,
            and_(
                UserWorkout.scheduled_date == workout.scheduled_date,
                UserWorkout.id < workout.id,
            ),
        )
    else:
        earlier_workout_filter = or_(
            UserWorkout.scheduled_date < workout.scheduled_date,
            and_(
                UserWorkout.scheduled_date == workout.scheduled_date,
                or_(
                    UserWorkout.completed_at < workout.completed_at,
                    and_(
                        UserWorkout.completed_at == workout.completed_at,
                        UserWorkout.id < workout.id,
                    ),
                    and_(
                        UserWorkout.completed_at.is_(None),
                        UserWorkout.id < workout.id,
                    ),
                ),
            ),
        )
    previous_rows = (
        db.query(
            UserWorkoutExercise.exercise_id,
            func.max(UserWorkoutSet.actual_weight).label("max_load"),
            func.max(UserWorkoutSet.actual_weight * UserWorkoutSet.actual_reps).label(
                "best_set_volume"
            ),
        )
        .join(UserWorkout, UserWorkout.id == UserWorkoutExercise.workout_id)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .join(UserWorkoutSet, UserWorkoutSet.workout_exercise_id == UserWorkoutExercise.id)
        .filter(
            UserProgram.user_id == user.id,
            UserWorkout.status == "completed",
            UserWorkout.id != workout.id,
            earlier_workout_filter,
            UserWorkoutSet.is_completed.is_(True),
            working_volume_set_filter(),
        )
        .group_by(UserWorkoutExercise.exercise_id)
        .all()
    )
    previous = {
        row.exercise_id: (float(row.max_load or 0), float(row.best_set_volume or 0))
        for row in previous_rows
    }

    current: dict[int, dict] = {}
    for exercise in sorted(workout.exercises, key=lambda item: (item.sort_order, item.id)):
        working_sets = [
            workout_set
            for workout_set in exercise.sets
            if workout_set.is_completed and counts_toward_working_volume(workout_set)
        ]
        loads = [
            float(workout_set.actual_weight)
            for workout_set in working_sets
            if workout_set.actual_weight is not None
        ]
        volumes = [
            float(workout_set.actual_weight * workout_set.actual_reps)
            for workout_set in working_sets
            if workout_set.actual_weight is not None and workout_set.actual_reps is not None
        ]
        result = current.setdefault(
            exercise.exercise_id,
            {
                "exercise_id": exercise.exercise_id,
                "exercise_title": titles[exercise.id],
                "max_load": 0.0,
                "best_volume": 0.0,
            },
        )
        result["max_load"] = max(result["max_load"], max(loads, default=0.0))
        result["best_volume"] = max(result["best_volume"], max(volumes, default=0.0))

    records: list[dict] = []
    for result in current.values():
        max_load = result["max_load"]
        best_volume = result["best_volume"]
        previous_load, previous_volume = previous.get(result["exercise_id"], (0.0, 0.0))
        kinds = []
        if max_load > previous_load:
            kinds.append("max_load")
        if best_volume > previous_volume:
            kinds.append("best_set_volume")
        if not kinds:
            continue
        records.append(
            {
                "exercise_id": result["exercise_id"],
                "exercise_title": result["exercise_title"],
                "kinds": kinds,
                "max_load_kg": max_load if "max_load" in kinds else None,
                "best_set_volume_kg": best_volume if "best_set_volume" in kinds else None,
            }
        )
    return records


def _next_workout(db: Session, user: User, workout: UserWorkout) -> dict | None:
    next_workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserProgram.user_id == user.id,
            UserWorkout.id != workout.id,
            UserWorkout.status.in_({"planned", "in_progress"}),
            or_(
                UserWorkout.scheduled_date > workout.scheduled_date,
                and_(
                    UserWorkout.scheduled_date == workout.scheduled_date,
                    UserWorkout.id > workout.id,
                ),
            ),
        )
        .order_by(
            UserWorkout.scheduled_date.asc(),
            UserWorkout.scheduled_time.asc(),
            UserWorkout.id.asc(),
        )
        .first()
    )
    if next_workout is None:
        return None
    return {
        "id": next_workout.id,
        "scheduled_date": next_workout.scheduled_date,
        "scheduled_time": next_workout.scheduled_time,
        "title": next_workout.title,
    }


def build_workout_completion_summary(
    db: Session,
    user: User,
    workout: UserWorkout,
    exercise_titles: Mapping[int, str],
) -> dict | None:
    if workout.status != "completed":
        return None

    exercise_results = [
        _exercise_result(exercise, exercise_titles[exercise.id])
        for exercise in sorted(workout.exercises, key=lambda item: (item.sort_order, item.id))
    ]
    performed = [result for result in exercise_results if result["completed_sets"] > 0]
    reps = [
        workout_set.actual_reps
        for exercise in workout.exercises
        for workout_set in exercise.sets
        if workout_set.is_completed and workout_set.actual_reps is not None
    ]
    completed_sets = [
        workout_set
        for exercise in workout.exercises
        for workout_set in exercise.sets
        if workout_set.is_completed
    ]
    all_sets = [workout_set for exercise in workout.exercises for workout_set in exercise.sets]
    duration_seconds = None
    if workout.started_at is not None and workout.completed_at is not None:
        duration_seconds = max(0, int((workout.completed_at - workout.started_at).total_seconds()))

    return {
        "duration_seconds": duration_seconds,
        "performed_exercises": len(performed),
        "completed_sets": len(completed_sets),
        "total_sets": len(all_sets),
        "reps_total": sum(reps) if reps else None,
        "reps_recorded_sets": len(reps),
        "load_recorded_sets": sum(
            workout_set.actual_weight is not None for workout_set in completed_sets
        ),
        "exercises": performed,
        "personal_records": _personal_records(db, user, workout, exercise_titles),
        "next_workout": _next_workout(db, user, workout),
        "feedback": workout.completion_feedback,
        "note": workout.completion_note,
    }
