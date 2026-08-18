from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.core.timezone import today_for_user
from fitminiapp_api.models.food_diary import FoodDiaryEntry
from fitminiapp_api.models.nutrition import NutritionTarget
from fitminiapp_api.models.program import (
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import BodyMeasurement, CoachClient, User

FORMULA_VERSION = "adherence-v1"
CALORIE_TOLERANCE = 0.10
ADHERENCE_WEIGHTS = {
    "workouts": 0.40,
    "cardio": 0.20,
    "calories": 0.20,
    "protein": 0.20,
}
BODY_METRICS = ("weight_kg", "chest_cm", "waist_cm", "hips_cm", "biceps_cm", "thigh_cm")
AdherenceStatus = Literal["available", "not_applicable", "insufficient_data", "unsupported"]


def calculate_adherence_component(
    *,
    achieved: int,
    evaluated: int,
    weight: float,
    unavailable_status: AdherenceStatus,
    unavailable_reason: str,
) -> dict:
    """Calculate one factual adherence ratio without inventing missing observations."""
    if evaluated <= 0:
        return {
            "status": unavailable_status,
            "percent": None,
            "achieved": 0,
            "evaluated": 0,
            "weight": weight,
            "reason": unavailable_reason,
        }
    if achieved < 0 or achieved > evaluated:
        raise ValueError("achieved must be between zero and evaluated")
    return {
        "status": "available",
        "percent": round(achieved * 100 / evaluated, 1),
        "achieved": achieved,
        "evaluated": evaluated,
        "weight": weight,
        "reason": None,
    }


def calculate_overall_adherence(components: dict[str, dict]) -> tuple[float | None, list[str]]:
    """Return the weighted mean of available components, renormalizing omitted weights."""
    included = [
        name for name, component in components.items() if component["status"] == "available"
    ]
    total_weight = sum(float(components[name]["weight"]) for name in included)
    if not included or total_weight <= 0:
        return None, []
    value = (
        sum(
            float(components[name]["percent"]) * float(components[name]["weight"])
            for name in included
        )
        / total_weight
    )
    return round(value, 1), included


def is_calorie_target_met(actual: Decimal, target: int) -> bool:
    if target <= 0:
        return False
    lower = Decimal(target) * Decimal(str(1 - CALORIE_TOLERANCE))
    upper = Decimal(target) * Decimal(str(1 + CALORIE_TOLERANCE))
    return lower <= actual <= upper


def is_protein_target_met(actual: Decimal, target: int) -> bool:
    return target > 0 and actual >= Decimal(target)


def _user_date_filter(
    user_ids: Iterable[int],
    starts: dict[int, date],
    ends: dict[int, date],
    user_column,
    date_column,
):
    return or_(
        *(
            and_(user_column == user_id, date_column.between(starts[user_id], ends[user_id]))
            for user_id in user_ids
        )
    )


def _body_trends(rows: list) -> list[dict]:
    trends: list[dict] = []
    for metric in BODY_METRICS:
        points = [row for row in rows if getattr(row, metric) is not None]
        if not points:
            continue
        first = points[0]
        latest = points[-1]
        first_value = float(getattr(first, metric))
        latest_value = float(getattr(latest, metric))
        trends.append(
            {
                "metric": metric,
                "first_value": first_value,
                "latest_value": latest_value,
                "change": round(latest_value - first_value, 2) if len(points) >= 2 else None,
                "first_measured_on": first.measured_on,
                "latest_measured_on": latest.measured_on,
            }
        )
    return trends


def _active_clients(db: Session, coach: User) -> list[tuple[User, str | None]]:
    rows = (
        db.query(User, CoachClient.private_name)
        .join(CoachClient, CoachClient.client_user_id == User.id)
        .options(joinedload(User.profile))
        .filter(
            CoachClient.coach_user_id == coach.id,
            CoachClient.status == "active",
            User.is_active.is_(True),
        )
        .order_by(User.id.desc())
        .all()
    )
    return [(client, private_name) for client, private_name in rows]


def build_trainer_client_summaries(
    db: Session,
    coach: User,
    period_days: int,
) -> list[dict]:
    client_rows = _active_clients(db, coach)
    clients = [client for client, _private_name in client_rows]
    summaries = build_progress_summaries(
        db,
        clients,
        period_days,
        nutrition_visible_user_ids={client.id for client in clients},
    )
    names = {
        client.id: private_name or (client.profile.full_name if client.profile else None)
        for client, private_name in client_rows
    }
    for summary in summaries:
        summary["client_name"] = names[summary["user_id"]]
    return summaries


def build_progress_summary(db: Session, user: User, period_days: int) -> dict:
    return build_progress_summaries(
        db,
        [user],
        period_days,
        nutrition_visible_user_ids={user.id},
    )[0]


def build_progress_summaries(
    db: Session,
    users: list[User],
    period_days: int,
    *,
    nutrition_visible_user_ids: set[int],
) -> list[dict]:
    if period_days not in {7, 30, 90}:
        raise ValueError("period_days must be 7, 30, or 90")
    if not users:
        return []

    user_ids = [user.id for user in users]
    today_by_user = {user.id: today_for_user(user) for user in users}
    start_by_user = {
        user_id: current_day - timedelta(days=period_days - 1)
        for user_id, current_day in today_by_user.items()
    }

    workout_rows = (
        db.query(
            UserProgram.user_id,
            UserWorkout.id,
            UserWorkout.scheduled_date,
            UserWorkout.scheduled_time,
            UserWorkout.title,
            UserWorkout.status,
        )
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            _user_date_filter(
                user_ids,
                start_by_user,
                today_by_user,
                UserProgram.user_id,
                UserWorkout.scheduled_date,
            )
        )
        .order_by(UserProgram.user_id, UserWorkout.scheduled_date, UserWorkout.id)
        .all()
    )
    workouts_by_user: dict[int, list] = defaultdict(list)
    for workout_row in workout_rows:
        workouts_by_user[workout_row.user_id].append(workout_row)

    next_candidates = (
        db.query(
            UserProgram.user_id.label("user_id"),
            UserWorkout.id.label("id"),
            UserWorkout.scheduled_date.label("scheduled_date"),
            UserWorkout.scheduled_time.label("scheduled_time"),
            UserWorkout.title.label("title"),
            UserWorkout.status.label("status"),
            func.row_number()
            .over(
                partition_by=UserProgram.user_id,
                order_by=(
                    UserWorkout.scheduled_date.asc(),
                    UserWorkout.scheduled_time.asc(),
                    UserWorkout.id.asc(),
                ),
            )
            .label("row_number"),
        )
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(
            UserWorkout.status.in_({"planned", "in_progress"}),
            or_(
                *(
                    and_(
                        UserProgram.user_id == user_id,
                        UserWorkout.scheduled_date >= today_by_user[user_id],
                    )
                    for user_id in user_ids
                )
            ),
        )
        .subquery()
    )
    next_rows = db.query(next_candidates).filter(next_candidates.c.row_number == 1).all()
    next_by_user = {row.user_id: row for row in next_rows}

    last_completed_rows = (
        db.query(
            UserProgram.user_id,
            func.max(UserWorkout.completed_at).label("completed_at"),
            func.max(UserWorkout.scheduled_date).label("scheduled_on"),
        )
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(UserProgram.user_id.in_(user_ids), UserWorkout.status == "completed")
        .group_by(UserProgram.user_id)
        .all()
    )
    last_completed_by_user = {
        row.user_id: row.completed_at.date() if row.completed_at else row.scheduled_on
        for row in last_completed_rows
    }

    measurement_rows = (
        db.query(BodyMeasurement)
        .filter(
            _user_date_filter(
                user_ids,
                start_by_user,
                today_by_user,
                BodyMeasurement.user_id,
                BodyMeasurement.measured_on,
            )
        )
        .order_by(BodyMeasurement.user_id, BodyMeasurement.measured_on, BodyMeasurement.id)
        .all()
    )
    measurements_by_user: dict[int, list[BodyMeasurement]] = defaultdict(list)
    for measurement_row in measurement_rows:
        measurements_by_user[measurement_row.user_id].append(measurement_row)

    latest_measurement_candidates = (
        db.query(
            BodyMeasurement,
            func.row_number()
            .over(
                partition_by=BodyMeasurement.user_id,
                order_by=(BodyMeasurement.measured_on.desc(), BodyMeasurement.id.desc()),
            )
            .label("row_number"),
        )
        .filter(BodyMeasurement.user_id.in_(user_ids))
        .subquery()
    )
    latest_measurement_rows = (
        db.query(latest_measurement_candidates)
        .filter(latest_measurement_candidates.c.row_number == 1)
        .all()
    )
    latest_measurement_by_user = {
        row.user_id: {
            "measured_on": row.measured_on,
            **{
                metric: float(getattr(row, metric)) if getattr(row, metric) is not None else None
                for metric in BODY_METRICS
            },
        }
        for row in latest_measurement_rows
    }

    visible_nutrition_ids = set(user_ids) & nutrition_visible_user_ids
    targets = (
        db.query(NutritionTarget).filter(NutritionTarget.user_id.in_(visible_nutrition_ids)).all()
        if visible_nutrition_ids
        else []
    )
    targets_by_user = {target.user_id: target for target in targets}

    nutrition_end_by_user = {
        user_id: current_day - timedelta(days=1) for user_id, current_day in today_by_user.items()
    }
    diary_rows = []
    if visible_nutrition_ids:
        diary_rows = (
            db.query(
                FoodDiaryEntry.user_id,
                FoodDiaryEntry.diary_date,
                func.sum(FoodDiaryEntry.weight_g * FoodDiaryEntry.energy_kcal_per_100g / 100).label(
                    "calories"
                ),
                func.sum(FoodDiaryEntry.weight_g * FoodDiaryEntry.protein_g_per_100g / 100).label(
                    "protein_g"
                ),
            )
            .filter(
                _user_date_filter(
                    visible_nutrition_ids,
                    start_by_user,
                    nutrition_end_by_user,
                    FoodDiaryEntry.user_id,
                    FoodDiaryEntry.diary_date,
                )
            )
            .group_by(FoodDiaryEntry.user_id, FoodDiaryEntry.diary_date)
            .order_by(FoodDiaryEntry.user_id, FoodDiaryEntry.diary_date)
            .all()
        )
    diary_by_user: dict[int, list] = defaultdict(list)
    for diary_row in diary_rows:
        diary_by_user[diary_row.user_id].append(diary_row)

    set_rows = (
        db.query(
            UserProgram.user_id,
            UserWorkoutExercise.exercise_id,
            UserWorkout.scheduled_date,
            UserWorkoutSet.actual_weight,
            UserWorkoutSet.actual_reps,
        )
        .join(UserWorkout, UserWorkout.user_program_id == UserProgram.id)
        .join(UserWorkoutExercise, UserWorkoutExercise.workout_id == UserWorkout.id)
        .join(UserWorkoutSet, UserWorkoutSet.workout_exercise_id == UserWorkoutExercise.id)
        .filter(
            UserWorkout.status == "completed",
            UserWorkoutSet.is_completed.is_(True),
            _user_date_filter(
                user_ids,
                start_by_user,
                today_by_user,
                UserProgram.user_id,
                UserWorkout.scheduled_date,
            ),
        )
        .all()
    )
    period_best: dict[tuple[int, int], tuple[float, float]] = {}
    volume_by_user: dict[int, float] = defaultdict(float)
    for set_row in set_rows:
        weight = float(set_row.actual_weight or 0)
        volume = weight * float(set_row.actual_reps or 0)
        volume_by_user[set_row.user_id] += volume
        key = (set_row.user_id, set_row.exercise_id)
        best_weight, best_volume = period_best.get(key, (0.0, 0.0))
        period_best[key] = (max(best_weight, weight), max(best_volume, volume))

    previous_best_rows = (
        db.query(
            UserProgram.user_id,
            UserWorkoutExercise.exercise_id,
            func.max(UserWorkoutSet.actual_weight).label("max_weight"),
            func.max(UserWorkoutSet.actual_weight * UserWorkoutSet.actual_reps).label(
                "max_set_volume"
            ),
        )
        .join(UserWorkout, UserWorkout.user_program_id == UserProgram.id)
        .join(UserWorkoutExercise, UserWorkoutExercise.workout_id == UserWorkout.id)
        .join(UserWorkoutSet, UserWorkoutSet.workout_exercise_id == UserWorkoutExercise.id)
        .filter(
            UserWorkout.status == "completed",
            UserWorkoutSet.is_completed.is_(True),
            or_(
                *(
                    and_(
                        UserProgram.user_id == user_id,
                        UserWorkout.scheduled_date < start_by_user[user_id],
                    )
                    for user_id in user_ids
                )
            ),
        )
        .group_by(UserProgram.user_id, UserWorkoutExercise.exercise_id)
        .all()
    )
    previous_best = {
        (row.user_id, row.exercise_id): (
            float(row.max_weight or 0),
            float(row.max_set_volume or 0),
        )
        for row in previous_best_rows
    }
    new_records_by_user: dict[int, int] = defaultdict(int)
    for (user_id, exercise_id), current in period_best.items():
        previous = previous_best.get((user_id, exercise_id), (0.0, 0.0))
        if current[0] > previous[0] or current[1] > previous[1]:
            new_records_by_user[user_id] += 1

    summaries: list[dict] = []
    for user in users:
        current_day = today_by_user[user.id]
        workouts = [row for row in workouts_by_user[user.id] if row.status != "cancelled"]
        evaluated_workouts = [
            row
            for row in workouts
            if row.scheduled_date < current_day or row.status in {"completed", "skipped"}
        ]
        completed_workouts = [row for row in evaluated_workouts if row.status == "completed"]
        workout_adherence = calculate_adherence_component(
            achieved=len(completed_workouts),
            evaluated=len(evaluated_workouts),
            weight=ADHERENCE_WEIGHTS["workouts"],
            unavailable_status="not_applicable",
            unavailable_reason="no_evaluable_planned_workouts",
        )

        nutrition_visible = user.id in visible_nutrition_ids
        target = targets_by_user.get(user.id)
        diary_days = diary_by_user[user.id]
        adherence_diary_days = (
            [row for row in diary_days if row.diary_date >= target.saved_at.date()]
            if target is not None
            else []
        )
        calorie_achieved = 0
        protein_achieved = 0
        if target is not None:
            calorie_achieved = sum(
                is_calorie_target_met(Decimal(row.calories), target.calories)
                for row in adherence_diary_days
            )
            protein_achieved = sum(
                is_protein_target_met(Decimal(row.protein_g), target.protein_g)
                for row in adherence_diary_days
            )

        nutrition_status: AdherenceStatus = "insufficient_data" if target else "not_applicable"
        nutrition_reason = (
            "no_logged_days_for_current_target" if target else "nutrition_target_missing"
        )
        calories_adherence = calculate_adherence_component(
            achieved=calorie_achieved,
            evaluated=len(adherence_diary_days),
            weight=ADHERENCE_WEIGHTS["calories"],
            unavailable_status=nutrition_status,
            unavailable_reason=nutrition_reason,
        )
        protein_adherence = calculate_adherence_component(
            achieved=protein_achieved,
            evaluated=len(adherence_diary_days),
            weight=ADHERENCE_WEIGHTS["protein"],
            unavailable_status=nutrition_status,
            unavailable_reason=nutrition_reason,
        )
        if not nutrition_visible:
            calories_adherence = calculate_adherence_component(
                achieved=0,
                evaluated=0,
                weight=ADHERENCE_WEIGHTS["calories"],
                unavailable_status="unsupported",
                unavailable_reason="nutrition_access_not_granted",
            )
            protein_adherence = calculate_adherence_component(
                achieved=0,
                evaluated=0,
                weight=ADHERENCE_WEIGHTS["protein"],
                unavailable_status="unsupported",
                unavailable_reason="nutrition_access_not_granted",
            )

        cardio_planned = bool(target and target.cardio_trainings_per_week > 0)
        cardio_adherence = calculate_adherence_component(
            achieved=0,
            evaluated=0,
            weight=ADHERENCE_WEIGHTS["cardio"],
            unavailable_status="unsupported" if cardio_planned else "not_applicable",
            unavailable_reason=(
                "cardio_log_unavailable" if cardio_planned else "cardio_not_planned"
            ),
        )
        components = {
            "workouts": workout_adherence,
            "cardio": cardio_adherence,
            "calories": calories_adherence,
            "protein": protein_adherence,
        }
        overall, included = calculate_overall_adherence(components)

        next_row = next_by_user.get(user.id)
        next_workout = None
        if next_row is not None:
            next_workout = {
                "id": next_row.id,
                "scheduled_date": next_row.scheduled_date,
                "scheduled_time": next_row.scheduled_time,
                "title": next_row.title,
                "status": next_row.status,
            }
        average_calories = (
            round(sum(float(row.calories) for row in diary_days) / len(diary_days), 1)
            if diary_days
            else None
        )
        average_protein = (
            round(sum(float(row.protein_g) for row in diary_days) / len(diary_days), 1)
            if diary_days
            else None
        )
        summary = {
            "user_id": user.id,
            "period_days": period_days,
            "period_start": start_by_user[user.id],
            "period_end": current_day,
            "training": {
                "planned_workouts": len(evaluated_workouts),
                "completed_workouts": len(completed_workouts),
                "frequency_per_week": round(len(completed_workouts) * 7 / period_days, 2),
                "volume_kg": round(volume_by_user[user.id], 2),
                "new_personal_records": new_records_by_user[user.id],
                "last_completed_workout_on": last_completed_by_user.get(user.id),
                "next_workout": next_workout,
            },
            "nutrition": {
                "visible": nutrition_visible,
                "logged_days": len(diary_days) if nutrition_visible else 0,
                "adherence_evaluated_days": (len(adherence_diary_days) if nutrition_visible else 0),
                "average_calories": average_calories if nutrition_visible else None,
                "target_calories": target.calories if target and nutrition_visible else None,
                "average_protein_g": average_protein if nutrition_visible else None,
                "target_protein_g": target.protein_g if target and nutrition_visible else None,
                "target_effective_on": (
                    target.saved_at.date() if target and nutrition_visible else None
                ),
            },
            "body": {
                "latest_measurement": latest_measurement_by_user.get(user.id),
                "trends": _body_trends(measurements_by_user[user.id]),
            },
            "adherence": {
                "formula_version": FORMULA_VERSION,
                "overall_percent": overall,
                "included_components": included,
                **components,
            },
        }
        summaries.append(summary)
    return summaries
