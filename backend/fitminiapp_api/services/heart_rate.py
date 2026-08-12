from dataclasses import dataclass

HEART_RATE_ZONE_RANGES = (
    ("Восстановление", 0.5, 0.6),
    ("Лёгкая", 0.6, 0.7),
    ("Аэробная", 0.7, 0.8),
    ("Пороговая", 0.8, 0.9),
    ("Максимальная", 0.9, 1.0),
)

GOAL_CARDIO_RANGES = {
    "fat_loss": (0.5, 0.6),
    "recomposition": (0.45, 0.6),
    "maintenance": (0.4, 0.6),
    "muscle_gain": (0.4, 0.5),
}


@dataclass(frozen=True)
class HeartRateZone:
    zone: int
    title: str
    min_bpm: int
    max_bpm: int


@dataclass(frozen=True)
class HeartRateRange:
    min_bpm: int
    max_bpm: int


@dataclass(frozen=True)
class HeartRateCalculation:
    maximum: int
    reserve: int | None
    is_personalized: bool
    zones: tuple[HeartRateZone, ...]
    recommended_cardio_range: HeartRateRange | None


def round_heart_rate(value: float) -> int:
    """Round a positive heart-rate value to nearest integer, with .5 rounded up."""
    return int(value + 0.5)


def calculate_max_heart_rate(age: int) -> int:
    if age < 10 or age > 100:
        raise ValueError("Age must be between 10 and 100 years")
    return round_heart_rate(208 - 0.7 * age)


def calculate_heart_rate_reserve(maximum: int, resting_heart_rate: int) -> int:
    if resting_heart_rate < 30 or resting_heart_rate > 120:
        raise ValueError("Resting heart rate must be between 30 and 120 bpm")
    if resting_heart_rate >= maximum:
        raise ValueError("Resting heart rate must be below maximum heart rate")
    return maximum - resting_heart_rate


def calculate_target_heart_rate(
    maximum: int,
    resting_heart_rate: int | None,
    intensity: float,
) -> int:
    if intensity < 0 or intensity > 1:
        raise ValueError("Intensity must be between 0 and 1")
    if resting_heart_rate is None:
        return round_heart_rate(maximum * intensity)
    reserve = calculate_heart_rate_reserve(maximum, resting_heart_rate)
    return round_heart_rate(resting_heart_rate + reserve * intensity)


def calculate_heart_rate_zones(
    maximum: int,
    resting_heart_rate: int | None,
) -> tuple[HeartRateZone, ...]:
    return tuple(
        HeartRateZone(
            zone=index,
            title=title,
            min_bpm=calculate_target_heart_rate(maximum, resting_heart_rate, lower),
            max_bpm=calculate_target_heart_rate(maximum, resting_heart_rate, upper),
        )
        for index, (title, lower, upper) in enumerate(HEART_RATE_ZONE_RANGES, start=1)
    )


def calculate_goal_cardio_range(
    maximum: int,
    resting_heart_rate: int | None,
    goal: str | None,
) -> HeartRateRange | None:
    if resting_heart_rate is None or goal not in GOAL_CARDIO_RANGES:
        return None
    lower, upper = GOAL_CARDIO_RANGES[goal]
    return HeartRateRange(
        min_bpm=calculate_target_heart_rate(maximum, resting_heart_rate, lower),
        max_bpm=calculate_target_heart_rate(maximum, resting_heart_rate, upper),
    )


def calculate_heart_rates(
    age: int,
    resting_heart_rate: int | None,
    goal: str | None,
) -> HeartRateCalculation:
    maximum = calculate_max_heart_rate(age)
    reserve = (
        calculate_heart_rate_reserve(maximum, resting_heart_rate)
        if resting_heart_rate is not None
        else None
    )
    return HeartRateCalculation(
        maximum=maximum,
        reserve=reserve,
        is_personalized=resting_heart_rate is not None,
        zones=calculate_heart_rate_zones(maximum, resting_heart_rate),
        recommended_cardio_range=calculate_goal_cardio_range(
            maximum,
            resting_heart_rate,
            goal,
        ),
    )
