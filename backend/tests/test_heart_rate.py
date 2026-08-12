import pytest

from fitminiapp_api.services.heart_rate import (
    calculate_heart_rate_reserve,
    calculate_heart_rates,
    calculate_max_heart_rate,
    calculate_target_heart_rate,
    round_heart_rate,
)


def test_tanaka_maximum_for_control_age() -> None:
    assert calculate_max_heart_rate(34) == 184


def test_karvonen_control_values() -> None:
    maximum = calculate_max_heart_rate(34)

    assert calculate_heart_rate_reserve(maximum, 75) == 109
    assert calculate_target_heart_rate(maximum, 75, 0.5) == 130
    assert calculate_target_heart_rate(maximum, 75, 0.6) == 140


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("fat_loss", (130, 140)),
        ("recomposition", (124, 140)),
        ("maintenance", (119, 140)),
        ("muscle_gain", (119, 130)),
    ],
)
def test_goal_cardio_ranges(goal: str, expected: tuple[int, int]) -> None:
    result = calculate_heart_rates(34, 75, goal)

    assert result.recommended_cardio_range is not None
    assert (
        result.recommended_cardio_range.min_bpm,
        result.recommended_cardio_range.max_bpm,
    ) == expected


def test_physiological_zones_do_not_depend_on_goal() -> None:
    results = [
        calculate_heart_rates(34, 75, goal)
        for goal in ("fat_loss", "recomposition", "maintenance", "muscle_gain")
    ]

    assert all(result.zones == results[0].zones for result in results[1:])
    assert len({result.recommended_cardio_range for result in results}) == 4


def test_missing_resting_heart_rate_uses_percent_maximum_fallback() -> None:
    result = calculate_heart_rates(34, None, "fat_loss")

    assert result.maximum == 184
    assert result.reserve is None
    assert result.is_personalized is False
    assert result.recommended_cardio_range is None
    assert result.zones[0].min_bpm == 92
    assert result.zones[-1].max_bpm == 184


@pytest.mark.parametrize("resting_heart_rate", [29, 121, 184])
def test_resting_heart_rate_validation(resting_heart_rate: int) -> None:
    with pytest.raises(ValueError):
        calculate_heart_rates(34, resting_heart_rate, "fat_loss")


def test_rounding_half_up_is_explicit() -> None:
    assert round_heart_rate(129.4) == 129
    assert round_heart_rate(129.5) == 130
