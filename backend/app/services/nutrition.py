import math
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

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


class NutritionError(Exception):
    pass


def _round_number(value: float) -> int:
    return max(0, math.floor(value + 0.5))


def _activity_factor(strength_sessions: int, cardio_sessions: int) -> float:
    sessions = strength_sessions + cardio_sessions
    if sessions <= 0:
        return 1.2
    if sessions <= 2:
        return 1.375
    if sessions <= 4:
        return 1.55
    if sessions <= 6:
        return 1.725
    return 1.9


def _target_calories(tdee: float, goal: str) -> int:
    multiplier = {
        "fat_loss": 0.85,
        "muscle_gain": 1.1,
        "maintenance": 1,
        "recomposition": 0.95,
    }.get(goal, 1)
    return _round_number(tdee * multiplier)


def _macros(weight_kg: float, target_calories: int, goal: str) -> dict[str, int]:
    protein_per_kg = {
        "fat_loss": 2,
        "muscle_gain": 1.8,
        "maintenance": 1.6,
        "recomposition": 2,
    }.get(goal, 1.6)
    fat_per_kg = 0.9 if goal == "muscle_gain" else 0.8
    protein = _round_number(weight_kg * protein_per_kg)
    fat = _round_number(weight_kg * fat_per_kg)
    carbs = _round_number((target_calories - protein * 4 - fat * 9) / 4)
    return {"protein_g": protein, "fat_g": fat, "carbs_g": carbs}


def calculate_nutrition(payload: NutritionTargetSave) -> dict[str, int]:
    sex = payload.sex.strip().lower()
    goal = payload.goal.strip()
    if sex not in VALID_SEXES:
        raise NutritionError("Invalid sex")
    if goal not in VALID_GOALS:
        raise NutritionError("Invalid goal")

    sex_constant = -161 if sex == "female" else 5
    bmr = 10 * payload.weight_kg + 6.25 * payload.height_cm - 5 * payload.age + sex_constant
    tdee = bmr * _activity_factor(
        payload.strength_trainings_per_week,
        payload.cardio_trainings_per_week,
    )
    calories = _target_calories(tdee, goal)

    return {
        "bmr": _round_number(bmr),
        "tdee": _round_number(tdee),
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
        strength_trainings_per_week=target.strength_trainings_per_week,
        cardio_trainings_per_week=target.cardio_trainings_per_week,
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
    target.strength_trainings_per_week = payload.strength_trainings_per_week
    target.cardio_trainings_per_week = payload.cardio_trainings_per_week
    target.goal = payload.goal.strip()
    target.bmr = calculations["bmr"]
    target.tdee = calculations["tdee"]
    target.calories = calculations["calories"]
    target.protein_g = calculations["protein_g"]
    target.fat_g = calculations["fat_g"]
    target.carbs_g = calculations["carbs_g"]
    target.saved_at = datetime.now(UTC)

    db.commit()
    db.refresh(target)
    response = build_nutrition_target_response(db, target)
    if response is None:
        raise NutritionError("Nutrition target not found")
    return response
