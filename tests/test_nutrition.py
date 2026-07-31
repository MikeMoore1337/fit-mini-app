import math

import pytest
from pydantic import ValidationError

from app.schemas.nutrition import NutritionTargetSave
from app.services.nutrition import calculate_nutrition


def nutrition_payload(**overrides) -> NutritionTargetSave:
    values = {
        "sex": "male",
        "weight_kg": 78,
        "height_cm": 165,
        "age": 34,
        "daily_activity_level": "low",
        "strength_trainings_per_week": 4,
        "strength_training_duration_minutes": 60,
        "cardio_trainings_per_week": 3,
        "cardio_training_duration_minutes": 30,
        "cardio_intensity": "moderate",
        "goal": "recomposition",
    }
    values.update(overrides)
    return NutritionTargetSave(**values)


def test_kbju_verification_example() -> None:
    result = calculate_nutrition(
        nutrition_payload(
            daily_activity_level="high",
            strength_training_duration_minutes=90,
            cardio_training_duration_minutes=45,
        )
    )

    assert result == {
        "bmr": 1646,
        "base_tdee": 2469,
        "strength_daily_calories": 267,
        "cardio_daily_calories": 125,
        "tdee": 2862,
        "goal_multiplier": 0.95,
        "calories": 2720,
        "protein_g": 156,
        "fat_g": 62,
        "carbs_g": 385,
        "macro_warning": False,
    }


def test_mifflin_st_jeor_uses_female_constant() -> None:
    result = calculate_nutrition(
        nutrition_payload(
            sex="female",
            weight_kg=64,
            height_cm=168,
            age=28,
            daily_activity_level="sedentary",
            strength_trainings_per_week=0,
            cardio_trainings_per_week=0,
            goal="maintenance",
        )
    )

    assert result["bmr"] == 1389


@pytest.mark.parametrize(
    ("level", "coefficient"),
    [("sedentary", 1.2), ("low", 1.3), ("moderate", 1.4), ("high", 1.5)],
)
def test_daily_activity_coefficients(level: str, coefficient: float) -> None:
    result = calculate_nutrition(
        nutrition_payload(
            daily_activity_level=level,
            strength_trainings_per_week=0,
            cardio_trainings_per_week=0,
            goal="maintenance",
        )
    )

    assert result["base_tdee"] == math.floor((1646.25 * coefficient) + 0.5)
    assert result["strength_daily_calories"] == 0
    assert result["cardio_daily_calories"] == 0


@pytest.mark.parametrize(
    ("goal", "multiplier"),
    [("fat_loss", 0.85), ("recomposition", 0.95), ("maintenance", 1.0), ("muscle_gain", 1.05)],
)
def test_goal_multipliers_and_ten_calorie_rounding(goal: str, multiplier: float) -> None:
    result = calculate_nutrition(nutrition_payload(goal=goal))
    expected = math.floor((2401.9821428571427 * multiplier) / 10 + 0.5) * 10

    assert result["goal_multiplier"] == multiplier
    assert result["calories"] == expected
    assert result["calories"] % 10 == 0


@pytest.mark.parametrize(("intensity", "expected"), [("low", 50), ("moderate", 84), ("high", 117)])
def test_cardio_met_values(intensity: str, expected: int) -> None:
    result = calculate_nutrition(nutrition_payload(cardio_intensity=intensity))

    assert result["cardio_daily_calories"] == expected


def test_negative_carbohydrate_result_is_clamped_and_warned() -> None:
    result = calculate_nutrition(
        nutrition_payload(
            weight_kg=500,
            height_cm=50,
            age=120,
            daily_activity_level="sedentary",
            strength_trainings_per_week=0,
            cardio_trainings_per_week=0,
            goal="fat_loss",
        )
    )

    assert result["carbs_g"] == 0
    assert result["macro_warning"] is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"weight_kg": float("nan")},
        {"height_cm": float("inf")},
        {"age": 0},
        {"strength_trainings_per_week": -1},
        {"cardio_trainings_per_week": 15},
        {"strength_training_duration_minutes": 9},
        {"cardio_training_duration_minutes": 301},
    ],
)
def test_invalid_or_unrealistic_values_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        nutrition_payload(**overrides)
