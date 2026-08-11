from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.core.timezone import today_for_user
from fitminiapp_api.models.program import (
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
)
from fitminiapp_api.models.user import BodyMeasurement, User
from fitminiapp_api.services.exercise_catalog import get_visible_exercise_display_map


def _completed_set_volume(workout_set) -> float:
    if not workout_set.is_completed:
        return 0.0
    return float((workout_set.actual_reps or 0) * (workout_set.actual_weight or 0))


def _load_workouts(db: Session, user: User) -> list[UserWorkout]:
    return (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .options(
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.exercise),
            joinedload(UserWorkout.exercises).joinedload(UserWorkoutExercise.sets),
        )
        .filter(UserProgram.user_id == user.id)
        .order_by(UserWorkout.scheduled_date.asc(), UserWorkout.id.asc())
        .all()
    )


def build_user_progress(db: Session, user: User) -> dict:
    today = today_for_user(user)
    workouts = _load_workouts(db, user)
    due_workouts = [
        workout
        for workout in workouts
        if workout.scheduled_date <= today and workout.status != "cancelled"
    ]
    completed = [workout for workout in due_workouts if workout.status == "completed"]
    skipped = [workout for workout in due_workouts if workout.status == "skipped"]
    missed = [
        workout
        for workout in due_workouts
        if workout.status in {"planned", "in_progress"} and workout.scheduled_date < today
    ]
    adherence_base = len(completed) + len(skipped) + len(missed)
    adherence = round(len(completed) * 100 / adherence_base, 1) if adherence_base else 0.0

    streak = 0
    for workout in reversed(due_workouts):
        if workout.status == "completed":
            streak += 1
        elif workout.scheduled_date == today and workout.status in {"planned", "in_progress"}:
            continue
        elif workout.status in {"skipped", "planned", "in_progress"}:
            break

    measurements = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user.id, BodyMeasurement.weight_kg.is_not(None))
        .order_by(BodyMeasurement.measured_on.asc(), BodyMeasurement.id.asc())
        .all()
    )
    weight_points = [
        (row.measured_on, float(row.weight_kg)) for row in measurements if row.weight_kg is not None
    ]
    weights = [
        {"measured_on": measured_on, "weight_kg": weight_kg}
        for measured_on, weight_kg in weight_points
    ]
    weight_change = (
        round(weight_points[-1][1] - weight_points[0][1], 2) if len(weight_points) >= 2 else None
    )

    weekly: dict = defaultdict(lambda: {"completed_workouts": 0, "volume_kg": 0.0})
    display_map = get_visible_exercise_display_map(db, user)
    records: dict[int, dict] = {}
    for workout in completed:
        week_start = workout.scheduled_date - timedelta(days=workout.scheduled_date.weekday())
        weekly[week_start]["completed_workouts"] += 1
        for exercise in workout.exercises:
            exercise_title = (
                display_map[exercise.exercise_id].title
                if exercise.exercise_id in display_map
                else (
                    exercise.exercise.title
                    if exercise.exercise is not None
                    else f"Упражнение {exercise.exercise_id}"
                )
            )
            record = records.setdefault(
                exercise.exercise_id,
                {
                    "exercise_id": exercise.exercise_id,
                    "exercise_title": exercise_title,
                    "max_weight_kg": None,
                    "best_set_volume_kg": 0.0,
                    "last_performed_on": workout.scheduled_date,
                },
            )
            record["last_performed_on"] = max(record["last_performed_on"], workout.scheduled_date)
            for workout_set in exercise.sets:
                volume = _completed_set_volume(workout_set)
                weekly[week_start]["volume_kg"] += volume
                record["best_set_volume_kg"] = max(record["best_set_volume_kg"], volume)
                if workout_set.is_completed and workout_set.actual_weight is not None:
                    current_max = record["max_weight_kg"]
                    record["max_weight_kg"] = max(
                        float(workout_set.actual_weight),
                        float(current_max) if current_max is not None else 0.0,
                    )

    return {
        "workouts_total": len(due_workouts),
        "workouts_completed": len(completed),
        "workouts_skipped": len(skipped),
        "workouts_missed": len(missed),
        "adherence_percent": adherence,
        "current_streak": streak,
        "weight_change_kg": weight_change,
        "weights": weights,
        "weekly_volume": [
            {
                "week_start": week_start,
                "completed_workouts": values["completed_workouts"],
                "volume_kg": round(values["volume_kg"], 2),
            }
            for week_start, values in sorted(weekly.items())
        ],
        "personal_records": sorted(
            records.values(),
            key=lambda item: (item["last_performed_on"], item["exercise_title"]),
            reverse=True,
        ),
    }


def build_workout_timeline(db: Session, user: User, limit: int = 30) -> list[dict]:
    display_map = get_visible_exercise_display_map(db, user)
    workouts = list(reversed(_load_workouts(db, user)))[:limit]
    result: list[dict] = []
    for workout in workouts:
        completed_sets = 0
        volume = 0.0
        exercises: list[dict] = []
        for exercise in sorted(workout.exercises, key=lambda item: item.sort_order):
            sets = []
            for workout_set in sorted(exercise.sets, key=lambda item: item.set_number):
                completed_sets += int(workout_set.is_completed)
                volume += _completed_set_volume(workout_set)
                sets.append(
                    {
                        "set_number": workout_set.set_number,
                        "actual_reps": workout_set.actual_reps,
                        "actual_weight": workout_set.actual_weight,
                        "is_completed": workout_set.is_completed,
                    }
                )
            exercises.append(
                {
                    "exercise_id": exercise.exercise_id,
                    "exercise_title": (
                        display_map[exercise.exercise_id].title
                        if exercise.exercise_id in display_map
                        else (
                            exercise.exercise.title
                            if exercise.exercise is not None
                            else f"Упражнение {exercise.exercise_id}"
                        )
                    ),
                    "notes": exercise.notes,
                    "sets": sets,
                }
            )
        result.append(
            {
                "id": workout.id,
                "scheduled_date": workout.scheduled_date,
                "scheduled_time": workout.scheduled_time,
                "title": workout.title,
                "status": workout.status,
                "completed_at": workout.completed_at,
                "completed_sets": completed_sets,
                "volume_kg": round(volume, 2),
                "exercises": exercises,
            }
        )
    return result
