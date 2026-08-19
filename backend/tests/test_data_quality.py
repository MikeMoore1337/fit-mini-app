from fitminiapp_api.services.data_quality import (
    TrainingDataCounts,
    build_anthropometry_signal,
    build_body_metric_signal,
    build_nutrition_coverage_signal,
    build_schedule_adherence_signal,
    build_training_data_sufficiency,
)


def test_nutrition_coverage_uses_period_aware_observation_counts() -> None:
    empty = build_nutrition_coverage_signal(
        logged_day_count=0,
        eligible_day_count=6,
        visible=True,
    )
    assert empty["status"] == "insufficient"
    assert empty["reason_keys"] == ["no_logged_days"]

    partial = build_nutrition_coverage_signal(
        logged_day_count=2,
        eligible_day_count=6,
        visible=True,
    )
    assert partial["status"] == "limited"
    assert partial["counters"]["coverage_percent"] == 33.3

    full_short_period = build_nutrition_coverage_signal(
        logged_day_count=6,
        eligible_day_count=6,
        visible=True,
    )
    assert full_short_period["status"] == "sufficient"
    assert full_short_period["counters"]["required_logged_day_count"] == 6

    partial_long_period = build_nutrition_coverage_signal(
        logged_day_count=6,
        eligible_day_count=29,
        visible=True,
    )
    assert partial_long_period["status"] == "limited"
    full_long_period = build_nutrition_coverage_signal(
        logged_day_count=7,
        eligible_day_count=89,
        visible=True,
    )
    assert full_long_period["status"] == "sufficient"
    assert full_long_period["counters"]["required_logged_day_count"] == 7


def test_body_signals_require_repeated_points_and_timespan() -> None:
    assert build_body_metric_signal(point_count=0, span_days=0)["status"] == "insufficient"
    partial = build_body_metric_signal(point_count=3, span_days=5)
    assert partial["status"] == "limited"
    assert partial["reason_keys"] == ["timespan_too_short"]
    assert build_body_metric_signal(point_count=3, span_days=14)["status"] == "sufficient"

    anthropometry = build_anthropometry_signal(
        [
            {"metric": "weight_kg", "point_count": 4, "span_days": 20},
            {"metric": "waist_cm", "point_count": 2, "span_days": 20},
            {"metric": "chest_cm", "point_count": 3, "span_days": 4},
        ]
    )
    assert anthropometry["status"] == "limited"
    assert anthropometry["counters"]["measured_metric_count"] == 2
    assert anthropometry["reason_keys"] == ["timespan_too_short"]

    sufficient_anthropometry = build_anthropometry_signal(
        [{"metric": "waist_cm", "point_count": 3, "span_days": 14}]
    )
    assert sufficient_anthropometry["status"] == "sufficient"
    assert sufficient_anthropometry["counters"]["sufficient_metric_count"] == 1


def test_training_signals_keep_optional_rir_independent_from_workout_logging() -> None:
    empty = build_training_data_sufficiency(TrainingDataCounts())
    assert {signal["status"] for key, signal in empty.items() if key != "ruleset_version"} == {
        "insufficient"
    }

    partial_without_rir = build_training_data_sufficiency(
        TrainingDataCounts(
            completed_workout_count=1,
            prescribed_set_count=3,
            logged_set_count=2,
            workout_session_count=1,
            working_set_count=2,
            rir_recorded_set_count=0,
        )
    )
    assert partial_without_rir["workout_logging"]["status"] == "limited"
    assert partial_without_rir["working_sets"]["status"] == "limited"
    assert partial_without_rir["rir_coverage"]["status"] == "insufficient"
    assert partial_without_rir["rir_coverage"]["reason_keys"] == ["no_rir_observations"]

    full = build_training_data_sufficiency(
        TrainingDataCounts(
            completed_workout_count=2,
            prescribed_set_count=6,
            logged_set_count=6,
            workout_session_count=2,
            working_set_count=6,
            rir_recorded_set_count=3,
        )
    )
    assert full["workout_logging"]["status"] == "sufficient"
    assert full["working_sets"]["status"] == "sufficient"
    assert full["rir_coverage"]["status"] == "sufficient"


def test_schedule_adherence_distinguishes_empty_partial_and_sufficient() -> None:
    assert build_schedule_adherence_signal(evaluable_workout_count=0)["status"] == ("insufficient")
    assert build_schedule_adherence_signal(evaluable_workout_count=2)["status"] == "limited"
    assert build_schedule_adherence_signal(evaluable_workout_count=3)["status"] == "sufficient"
