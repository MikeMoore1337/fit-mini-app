import math
from typing import TypedDict

from sqlalchemy.orm import Session, joinedload

from app.core.timezone import now_for_user_naive
from app.models.nutrition import NutritionTarget
from app.models.user import CoachClient, User
from app.schemas.nutrition import (
    NutritionAssignedByResponse,
    NutritionTargetResponse,
    NutritionTargetSave,
)
from app.services.profile import ensure_profile

VALID_SEXES = {"male", "female"}
VALID_GOALS = {"fat_loss", "muscle_gain", "maintenance", "recomposition"}
ACTIVITY_COEFFICIENTS = {
    "sedentary": 1.2,
    "low": 1.3,
    "moderate": 1.4,
    "high": 1.5,
}
CARDIO_MET_VALUES = {"low": 4, "moderate": 6, "high": 8}
GOAL_MULTIPLIERS = {
    "fat_loss": 0.85,
    "recomposition": 0.95,
    "maintenance": 1.0,
    "muscle_gain": 1.05,
}


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


def _target_calories(maintenance_calories: float, goal: str) -> int:
    return _round_to_ten(maintenance_calories * GOAL_MULTIPLIERS[goal])


def _macros(weight_kg: float, target_calories: int, goal: str) -> NutritionMacros:
    protein_per_kg = {
        "fat_loss": 2,
        "muscle_gain": 1.8,
        "maintenance": 1.6,
        "recomposition": 2,
    }.get(goal, 1.6)
    fat_per_kg = 0.9 if goal == "muscle_gain" else 0.8
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


def calculate_nutrition(payload: NutritionTargetSave) -> NutritionCalculation:
    sex = payload.sex.strip().lower()
    goal = payload.goal.strip()
    if sex not in VALID_SEXES:
        raise NutritionError("Invalid sex")
    if goal not in VALID_GOALS:
        raise NutritionError("Invalid goal")
    if payload.daily_activity_level not in ACTIVITY_COEFFICIENTS:
        raise NutritionError("Invalid daily activity level")
    if payload.cardio_intensity not in CARDIO_MET_VALUES:
        raise NutritionError("Invalid cardio intensity")

    sex_constant = -161 if sex == "female" else 5
    bmr = 10 * payload.weight_kg + 6.25 * payload.height_cm - 5 * payload.age + sex_constant
    base_tdee = bmr * ACTIVITY_COEFFICIENTS[payload.daily_activity_level]
    strength_weekly_calories = (
        5
        * payload.weight_kg
        * (payload.strength_training_duration_minutes / 60)
        * payload.strength_trainings_per_week
    )
    cardio_weekly_calories = (
        CARDIO_MET_VALUES[payload.cardio_intensity]
        * payload.weight_kg
        * (payload.cardio_training_duration_minutes / 60)
        * payload.cardio_trainings_per_week
    )
    strength_daily_calories = strength_weekly_calories / 7
    cardio_daily_calories = cardio_weekly_calories / 7
    maintenance_calories = base_tdee + strength_daily_calories + cardio_daily_calories
    calories = _target_calories(maintenance_calories, goal)

    return {
        "bmr": _round_number(bmr),
        "base_tdee": _round_number(base_tdee),
        "strength_daily_calories": _round_number(strength_daily_calories),
        "cardio_daily_calories": _round_number(cardio_daily_calories),
        "tdee": _round_number(maintenance_calories),
        "goal_multiplier": GOAL_MULTIPLIERS[goal],
        "calories": calories,
        **_macros(payload.weight_kg, calories, goal),
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

    if current_user.is_admin:
        return target_user

    if current_user.is_coach:
        link = (
            db.query(CoachClient)
            .filter(
                CoachClient.coach_user_id == current_user.id,
                CoachClient.client_user_id == target_user.id,
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

    return NutritionTargetResponse(
        user_id=target.user_id,
        telegram_user_id=user.telegram_user_id,
        sex=target.sex,
        weight_kg=target.weight_kg,
        height_cm=target.height_cm,
        age=target.age,
        daily_activity_level=target.daily_activity_level,
        strength_trainings_per_week=target.strength_trainings_per_week,
        strength_training_duration_minutes=target.strength_training_duration_minutes,
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


def get_nutrition_target_for_user(
    db: Session,
    user: User,
) -> NutritionTargetResponse | None:
    target = db.query(NutritionTarget).filter(NutritionTarget.user_id == user.id).first()
    return build_nutrition_target_response(db, target)


def save_nutrition_target(
    db: Session,
    current_user: User,
    payload: NutritionTargetSave,
) -> NutritionTargetResponse:
    target_user = _resolve_target_user(db, current_user, payload.target_telegram_user_id)
    calculations = calculate_nutrition(payload)
    ensure_profile(db, target_user)

    target = db.query(NutritionTarget).filter(NutritionTarget.user_id == target_user.id).first()
    if not target:
        target = NutritionTarget(user_id=target_user.id)
        db.add(target)

    target.assigned_by_user_id = current_user.id
    target.sex = payload.sex.strip().lower()
    target.weight_kg = payload.weight_kg
    target.height_cm = payload.height_cm
    target.age = payload.age
    target.daily_activity_level = payload.daily_activity_level
    target.strength_trainings_per_week = payload.strength_trainings_per_week
    target.strength_training_duration_minutes = payload.strength_training_duration_minutes
    target.cardio_trainings_per_week = payload.cardio_trainings_per_week
    target.cardio_training_duration_minutes = payload.cardio_training_duration_minutes
    target.cardio_intensity = payload.cardio_intensity
    target.goal = payload.goal.strip()
    target.bmr = calculations["bmr"]
    target.tdee = calculations["tdee"]
    target.calories = calculations["calories"]
    target.protein_g = calculations["protein_g"]
    target.fat_g = calculations["fat_g"]
    target.carbs_g = calculations["carbs_g"]
    target.saved_at = now_for_user_naive(target_user)

    db.commit()
    db.refresh(target)
    response = build_nutrition_target_response(db, target)
    if response is None:
        raise NutritionError("Nutrition target not found")
    return response
