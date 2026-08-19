import math
from typing import TypedDict, cast

from pydantic import ValidationError
from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.core.timezone import now_for_user_naive, user_local_naive_to_utc_naive
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.nutrition import NutritionTarget
from fitminiapp_api.models.user import CoachClient, User
from fitminiapp_api.schemas.nutrition import (
    CardioIntensity,
    CardioTraining,
    NutritionAssignedByResponse,
    NutritionTargetResponse,
    NutritionTargetSave,
)
from fitminiapp_api.services.profile import ensure_profile

VALID_SEXES = {"male", "female"}
VALID_GOALS = {"fat_loss", "muscle_gain", "maintenance", "recomposition"}
LEGACY_ACTIVITY_COEFFICIENTS = {
    "sedentary": 1.2,
    "low": 1.3,
    "moderate": 1.4,
    "high": 1.5,
}
ACTIVITY_COEFFICIENTS = {
    "mostly_sitting": {
        "up_to_4000": 1.2,
        "from_4000_to_7000": 1.25,
        "from_7000_to_10000": 1.3,
        "from_10000_to_14000": 1.35,
        "over_14000": 1.4,
        "unknown": 1.2,
    },
    "mixed": {
        "up_to_4000": 1.25,
        "from_4000_to_7000": 1.3,
        "from_7000_to_10000": 1.35,
        "from_10000_to_14000": 1.4,
        "over_14000": 1.45,
        "unknown": 1.3,
    },
    "mostly_on_feet": {
        "up_to_4000": 1.3,
        "from_4000_to_7000": 1.35,
        "from_7000_to_10000": 1.4,
        "from_10000_to_14000": 1.45,
        "over_14000": 1.5,
        "unknown": 1.4,
    },
    "physical_work": {
        "up_to_4000": 1.4,
        "from_4000_to_7000": 1.45,
        "from_7000_to_10000": 1.5,
        "from_10000_to_14000": 1.55,
        "over_14000": 1.6,
        "unknown": 1.5,
    },
}
LEGACY_DAILY_ROUTINES = {
    "sedentary": "mostly_sitting",
    "low": "mixed",
    "moderate": "mostly_on_feet",
    "high": "physical_work",
}
STRENGTH_MET_VALUES = {
    "calm": 3.5,
    "regular": 5.0,
    "heavy": 5.0,
    "dense": 6.0,
    "circuit": 7.0,
}
STRENGTH_REST_ADJUSTMENTS = {
    "under_60": 0.5,
    "one_to_two": 0.25,
    "two_to_three": 0.0,
    "over_three": -0.5,
    "varied": 0.0,
}
CARDIO_BASE_MET_VALUES = {
    "walking": 3.5,
    "running": 8.0,
    "elliptical": 5.0,
    "stationary_bike": 5.5,
    "cycling": 6.0,
    "rowing": 6.0,
    "stepper": 6.0,
    "swimming": 6.0,
    "other": 5.0,
}
CARDIO_INTENSITY_MULTIPLIERS = {
    "very_light": 0.7,
    "light": 0.85,
    "moderate": 1.0,
    "hard": 1.2,
    "very_hard": 1.4,
}
LEGACY_CARDIO_INTENSITIES = {"low": "light", "moderate": "moderate", "high": "hard"}
GOAL_MULTIPLIERS = {
    "fat_loss": 0.85,
    "recomposition": 1.0,
    "maintenance": 1.0,
    "muscle_gain": 1.05,
}
NUTRITION_INPUT_FIELDS = (
    "sex",
    "weight_kg",
    "height_cm",
    "age",
    "daily_routine",
    "steps_range",
    "strength_trainings_per_week",
    "strength_training_duration_minutes",
    "strength_training_type",
    "strength_rest",
    "cardio_trainings",
    "goal",
)


class NutritionError(Exception):
    pass


class NutritionMacros(TypedDict):
    protein_g: int
    fat_g: int
    carbs_g: int
    macro_warning: bool


class NutritionCalculation(NutritionMacros):
    bmr: int
    base_tdee: int
    strength_daily_calories: int
    cardio_daily_calories: int
    tdee: int
    goal_multiplier: float
    calories: int


def _round_number(value: float) -> int:
    return max(0, math.floor(value + 0.5))


def _round_to_ten(value: float) -> int:
    return max(0, math.floor(value / 10 + 0.5) * 10)


def _round_up_to_ten(value: float) -> int:
    return max(0, math.ceil(value / 10) * 10)


def _target_calories(maintenance_calories: float, goal: str) -> int:
    return _round_to_ten(maintenance_calories * GOAL_MULTIPLIERS[goal])


def calculate_macros(weight_kg: float, target_calories: int, goal: str) -> NutritionMacros:
    protein_per_kg = {
        "fat_loss": 2.2,
        "muscle_gain": 1.8,
        "maintenance": 1.8,
        "recomposition": 2,
    }.get(goal, 1.8)
    fat_per_kg = 0.9 if goal in {"maintenance", "muscle_gain"} else 0.8
    protein = _round_number(weight_kg * protein_per_kg)
    fat = _round_number(weight_kg * fat_per_kg)
    remaining_calories = target_calories - protein * 4 - fat * 9
    carbs = _round_number(remaining_calories / 4)
    return {
        "protein_g": protein,
        "fat_g": fat,
        "carbs_g": carbs,
        "macro_warning": remaining_calories < 0,
    }


def _daily_activity(payload: NutritionTargetSave) -> tuple[str, str, float]:
    if payload.daily_routine is not None and payload.steps_range is not None:
        return (
            payload.daily_routine,
            payload.steps_range,
            ACTIVITY_COEFFICIENTS[payload.daily_routine][payload.steps_range],
        )
    legacy_level = payload.daily_activity_level or "sedentary"
    routine = LEGACY_DAILY_ROUTINES[legacy_level]
    return routine, "unknown", LEGACY_ACTIVITY_COEFFICIENTS[legacy_level]


def _cardio_trainings(payload: NutritionTargetSave) -> list[CardioTraining]:
    if payload.cardio_trainings is not None:
        return payload.cardio_trainings
    trainings_per_week = payload.cardio_trainings_per_week or 0
    if trainings_per_week == 0:
        return []
    legacy_intensity = payload.cardio_intensity or "moderate"
    return [
        CardioTraining(
            kind="other",
            trainings_per_week=trainings_per_week,
            duration_minutes=payload.cardio_training_duration_minutes or 30,
            intensity=cast(
                CardioIntensity,
                LEGACY_CARDIO_INTENSITIES[legacy_intensity],
            ),
        )
    ]


def _net_exercise_kcal(
    met_value: float,
    weight_kg: float,
    duration_minutes: int,
) -> float:
    return max(0, (met_value - 1) * 3.5 * weight_kg / 200 * duration_minutes)


def calculate_nutrition(payload: NutritionTargetSave) -> NutritionCalculation:
    sex = payload.sex.strip().lower()
    goal = payload.goal.strip()
    if sex not in VALID_SEXES:
        raise NutritionError("Invalid sex")
    if goal not in VALID_GOALS:
        raise NutritionError("Invalid goal")
    sex_constant = -161 if sex == "female" else 5
    bmr = 10 * payload.weight_kg + 6.25 * payload.height_cm - 5 * payload.age + sex_constant
    _, _, activity_coefficient = _daily_activity(payload)
    base_tdee = bmr * activity_coefficient
    strength_met = STRENGTH_MET_VALUES[payload.strength_training_type or "regular"]
    strength_met += STRENGTH_REST_ADJUSTMENTS.get(payload.strength_rest or "varied", 0)
    strength_weekly_calories = (
        _net_exercise_kcal(
            strength_met,
            payload.weight_kg,
            payload.strength_training_duration_minutes,
        )
        * payload.strength_trainings_per_week
    )
    cardio_weekly_calories = sum(
        _net_exercise_kcal(
            CARDIO_BASE_MET_VALUES[training.kind]
            * CARDIO_INTENSITY_MULTIPLIERS[training.intensity],
            payload.weight_kg,
            training.duration_minutes,
        )
        * training.trainings_per_week
        for training in _cardio_trainings(payload)
    )
    strength_daily_calories = strength_weekly_calories / 7
    cardio_daily_calories = cardio_weekly_calories / 7
    maintenance_calories = base_tdee + strength_daily_calories + cardio_daily_calories
    calories = _target_calories(maintenance_calories, goal)
    macros = calculate_macros(payload.weight_kg, calories, goal)
    if macros["macro_warning"]:
        # A calorie target below its own protein/fat allocation is internally
        # inconsistent and could previously become zero for accepted edge
        # inputs. Raise it only as far as needed to make every macro nonnegative.
        calories = _round_up_to_ten(macros["protein_g"] * 4 + macros["fat_g"] * 9)
        macros = calculate_macros(payload.weight_kg, calories, goal)
        macros["macro_warning"] = True

    return {
        "bmr": _round_number(bmr),
        "base_tdee": _round_number(base_tdee),
        "strength_daily_calories": _round_number(strength_daily_calories),
        "cardio_daily_calories": _round_number(cardio_daily_calories),
        "tdee": _round_number(maintenance_calories),
        "goal_multiplier": GOAL_MULTIPLIERS[goal],
        "calories": calories,
        **macros,
    }


def _resolve_target_user(
    db: Session,
    current_user: User,
    target_telegram_user_id: int | None,
) -> User:
    if not target_telegram_user_id or target_telegram_user_id == current_user.telegram_user_id:
        return current_user

    target_user = db.query(User).filter(User.telegram_user_id == target_telegram_user_id).first()
    if not target_user:
        raise NutritionError("Target user not found")

    if current_user.is_coach:
        link = (
            db.query(CoachClient)
            .filter(
                CoachClient.coach_user_id == current_user.id,
                CoachClient.client_user_id == target_user.id,
                CoachClient.status == "active",
            )
            .first()
        )
        if link:
            return target_user

    raise NutritionError("No permission to manage this user")


def _assigned_by_response(user: User | None) -> NutritionAssignedByResponse | None:
    if not user:
        return None
    return NutritionAssignedByResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        full_name=user.profile.full_name if user.profile else None,
    )


def build_nutrition_target_response_from_users(
    target: NutritionTarget,
    user: User,
    assigned_by: User | None,
) -> NutritionTargetResponse:
    """Serialize a target when its related users were loaded by the caller."""
    return NutritionTargetResponse(
        user_id=target.user_id,
        telegram_user_id=user.telegram_user_id,
        sex=target.sex,
        weight_kg=target.weight_kg,
        height_cm=target.height_cm,
        age=target.age,
        daily_routine=target.daily_routine,
        steps_range=target.steps_range,
        daily_activity_level=target.daily_activity_level,
        strength_trainings_per_week=target.strength_trainings_per_week,
        strength_training_duration_minutes=target.strength_training_duration_minutes,
        strength_training_type=target.strength_training_type,
        strength_rest=target.strength_rest,
        cardio_trainings=[CardioTraining.model_validate(row) for row in target.cardio_trainings],
        cardio_trainings_per_week=target.cardio_trainings_per_week,
        cardio_training_duration_minutes=target.cardio_training_duration_minutes,
        cardio_intensity=target.cardio_intensity,
        goal=target.goal,
        bmr=target.bmr,
        tdee=target.tdee,
        calories=target.calories,
        protein_g=target.protein_g,
        fat_g=target.fat_g,
        carbs_g=target.carbs_g,
        saved_at=target.saved_at,
        assigned_by=_assigned_by_response(assigned_by),
    )


def build_nutrition_target_response(
    db: Session,
    target: NutritionTarget | None,
) -> NutritionTargetResponse | None:
    if not target:
        return None

    user = db.query(User).filter(User.id == target.user_id).first()
    if not user:
        return None

    assigned_by = None
    if target.assigned_by_user_id:
        assigned_by = (
            db.query(User)
            .options(joinedload(User.profile))
            .filter(User.id == target.assigned_by_user_id)
            .first()
        )

    return build_nutrition_target_response_from_users(target, user, assigned_by)


def get_nutrition_target_for_user(
    db: Session,
    user: User,
) -> NutritionTargetResponse | None:
    target = db.query(NutritionTarget).filter(NutritionTarget.user_id == user.id).first()
    return build_nutrition_target_response_for_user(db, target, user)


def build_nutrition_target_response_for_user(
    db: Session,
    target: NutritionTarget | None,
    user: User,
) -> NutritionTargetResponse | None:
    if not target:
        return None
    assigned_by = None
    if target.assigned_by_user_id:
        assigned_by = (
            db.query(User)
            .options(joinedload(User.profile))
            .filter(User.id == target.assigned_by_user_id)
            .first()
        )
    return build_nutrition_target_response_from_users(target, user, assigned_by)


def _target_payload(target: NutritionTarget) -> NutritionTargetSave:
    return NutritionTargetSave.model_validate(
        {
            "sex": target.sex,
            "weight_kg": target.weight_kg,
            "height_cm": target.height_cm,
            "age": target.age,
            "daily_routine": target.daily_routine,
            "steps_range": target.steps_range,
            "strength_trainings_per_week": target.strength_trainings_per_week,
            "strength_training_duration_minutes": (target.strength_training_duration_minutes),
            "strength_training_type": target.strength_training_type,
            "strength_rest": target.strength_rest,
            "cardio_trainings": target.cardio_trainings,
            "goal": target.goal,
        }
    )


def _apply_calculation(target: NutritionTarget, calculations: NutritionCalculation) -> None:
    target.bmr = calculations["bmr"]
    target.tdee = calculations["tdee"]
    target.calories = calculations["calories"]
    target.protein_g = calculations["protein_g"]
    target.fat_g = calculations["fat_g"]
    target.carbs_g = calculations["carbs_g"]


def _queue_nutrition_updated_notification(
    db: Session,
    target_user: User,
    target: NutritionTarget,
    changed_by: User,
) -> None:
    scheduled_for = now_for_user_naive(target_user)
    actor_text = (
        "Тренер обновил параметры питания."
        if changed_by.id != target_user.id
        else "Ваши параметры питания изменились."
    )
    db.add(
        Notification(
            user_id=target_user.id,
            channel="telegram",
            title="КБЖУ пересчитаны",
            body=(
                f"{actor_text} Новые ориентиры: {target.calories} ккал · "
                f"Б {target.protein_g} г · Ж {target.fat_g} г · У {target.carbs_g} г. "
                "Проверьте раздел «КБЖУ»."
            ),
            scheduled_for=scheduled_for,
            scheduled_for_utc=user_local_naive_to_utc_naive(scheduled_for, target_user),
            status="queued",
        )
    )


def recalculate_nutrition_target(
    db: Session,
    target_user: User,
    updates: dict[str, object],
    changed_by: User,
) -> bool:
    """Update stored calculation inputs and queue an immediate client notification."""
    target = db.query(NutritionTarget).filter(NutritionTarget.user_id == target_user.id).first()
    if target is None:
        return False

    changed = False
    for field in NUTRITION_INPUT_FIELDS:
        value = updates.get(field)
        if value is None or getattr(target, field) == value:
            continue
        setattr(target, field, value)
        changed = True

    if not changed:
        return False

    try:
        payload = _target_payload(target)
    except ValidationError as exc:
        raise NutritionError("Nutrition inputs are outside supported ranges") from exc
    calculations = calculate_nutrition(payload)
    _apply_calculation(target, calculations)
    target.assigned_by_user_id = changed_by.id
    target.saved_at = now_for_user_naive(target_user)
    _queue_nutrition_updated_notification(db, target_user, target, changed_by)
    return True


def save_nutrition_target(
    db: Session,
    current_user: User,
    payload: NutritionTargetSave,
) -> NutritionTargetResponse:
    target_user = _resolve_target_user(db, current_user, payload.target_telegram_user_id)
    calculations = calculate_nutrition(payload)
    ensure_profile(db, target_user)

    target = db.query(NutritionTarget).filter(NutritionTarget.user_id == target_user.id).first()
    previous_inputs = (
        {field: getattr(target, field) for field in NUTRITION_INPUT_FIELDS} if target else None
    )
    if not target:
        target = NutritionTarget(user_id=target_user.id)
        db.add(target)

    target.assigned_by_user_id = current_user.id
    daily_routine, steps_range, _ = _daily_activity(payload)
    cardio_trainings = _cardio_trainings(payload)
    target.sex = payload.sex.strip().lower()
    target.weight_kg = payload.weight_kg
    target.height_cm = payload.height_cm
    target.age = payload.age
    target.daily_routine = daily_routine
    target.steps_range = steps_range
    target.daily_activity_level = payload.daily_activity_level or "sedentary"
    target.strength_trainings_per_week = payload.strength_trainings_per_week
    target.strength_training_duration_minutes = payload.strength_training_duration_minutes
    target.strength_training_type = payload.strength_training_type or "regular"
    target.strength_rest = payload.strength_rest
    target.cardio_trainings = [training.model_dump() for training in cardio_trainings]
    target.cardio_trainings_per_week = sum(
        training.trainings_per_week for training in cardio_trainings
    )
    first_cardio = cardio_trainings[0] if cardio_trainings else None
    target.cardio_training_duration_minutes = (
        first_cardio.duration_minutes
        if first_cardio
        else (payload.cardio_training_duration_minutes or 30)
    )
    target.cardio_intensity = payload.cardio_intensity or "moderate"
    target.goal = payload.goal.strip()
    _apply_calculation(target, calculations)
    target.saved_at = now_for_user_naive(target_user)

    current_inputs = {field: getattr(target, field) for field in NUTRITION_INPUT_FIELDS}
    if previous_inputs is None or previous_inputs != current_inputs:
        _queue_nutrition_updated_notification(db, target_user, target, current_user)

    db.commit()
    db.refresh(target)
    response = build_nutrition_target_response(db, target)
    if response is None:
        raise NutritionError("Nutrition target not found")
    return response
