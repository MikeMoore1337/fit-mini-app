from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from fitminiapp_api.core.timezone import today_msk
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.program import (
    TrainingBlock,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import User
from fitminiapp_api.services.progression_guidance import (
    SessionFacts,
    evaluate_progression,
    parse_rep_target,
)


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _assigned_workout(client, headers: dict[str, str]) -> dict:
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    exercise_id = next(item["id"] for item in exercises if item["metric_type"] == "strength")
    template = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Проверка прогрессии",
            "goal": "recomposition",
            "level": "intermediate",
            "mode": "self",
            "assign_after_create": False,
            "days": [
                {
                    "title": "Силовая тренировка",
                    "exercises": [
                        {
                            "exercise_id": exercise_id,
                            "prescribed_sets": 2,
                            "prescribed_reps": "8–10",
                            "rest_seconds": 90,
                        }
                    ],
                }
            ],
        },
    )
    assert template.status_code == 200, template.text
    today = today_msk()
    assigned = client.post(
        f"/api/v1/programs/templates/{template.json()['template']['id']}/assign-to-me",
        headers=headers,
        json={
            "start_date": today.isoformat(),
            "duration_weeks": 2,
            "schedule_weekdays": [today.weekday()],
        },
    )
    assert assigned.status_code == 200, assigned.text
    response = client.get("/api/v1/workouts/today", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _add_history(
    workout_id: int,
    sessions: list[list[tuple[int, float, str | None, str | None, bool | None]]],
) -> None:
    with get_session_context() as db:
        current = db.query(UserWorkout).filter(UserWorkout.id == workout_id).one()
        current_exercise = current.exercises[0]
        for session_index, sets in enumerate(sessions, start=1):
            previous = UserWorkout(
                user_program_id=current.user_program_id,
                scheduled_date=current.scheduled_date - timedelta(days=7 * session_index),
                day_number=1,
                week_number=max(1, current.week_number - session_index),
                title="Предыдущая тренировка",
                status="completed",
                started_at=datetime(2026, 8, 1, 10, 0),
                completed_at=datetime(2026, 8, 1, 11, 0),
            )
            db.add(previous)
            db.flush()
            previous_exercise = UserWorkoutExercise(
                workout_id=previous.id,
                exercise_id=current_exercise.exercise_id,
                sort_order=1,
                prescribed_sets=current_exercise.prescribed_sets,
                prescribed_reps=current_exercise.prescribed_reps,
                rest_seconds=current_exercise.rest_seconds,
            )
            db.add(previous_exercise)
            db.flush()
            for set_number, (reps, weight, rir, set_kind, failure) in enumerate(sets, start=1):
                db.add(
                    UserWorkoutSet(
                        workout_exercise_id=previous_exercise.id,
                        set_number=set_number,
                        actual_reps=reps,
                        actual_weight=weight,
                        rir=rir,
                        set_kind=set_kind,
                        reached_failure=failure,
                        is_completed=True,
                    )
                )


def _facts(
    *,
    day: int,
    reps: tuple[int, ...],
    weight: float = 40,
    rir: tuple[str, ...] = (),
    failure: bool = False,
    complete: bool = True,
) -> SessionFacts:
    return SessionFacts(
        workout_id=day,
        scheduled_date=date(2026, 8, day),
        working_set_count=len(reps),
        load=weight if complete else None,
        reps_min=min(reps),
        reps_max=max(reps),
        rir_values=rir,
        reached_failure=failure,
        complete=complete,
        completion_feedback=None,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("8", (8, 8)),
        ("8-10", (8, 10)),
        ("8–10", (8, 10)),
        ("10—12", (10, 12)),
        ("AMRAP", None),
        ("10-8", None),
        ("0-8", None),
    ],
)
def test_rep_prescription_parser_is_narrow_and_deterministic(value, expected) -> None:
    parsed = parse_rep_target(value)
    actual = (parsed.minimum, parsed.maximum) if parsed else None
    assert actual == expected


def test_progression_without_rir_requires_three_stable_sessions() -> None:
    two_sessions = [_facts(day=20, reps=(10, 10)), _facts(day=13, reps=(10, 10))]
    held = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8-10",
        sessions=two_sessions,
    )
    assert held["outcome"] == "hold"
    assert held["evidence"]["required_session_count"] == 3
    assert "need_one_more_stable_session" in held["evidence"]["reason_keys"]

    progressed = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8-10",
        sessions=[*two_sessions, _facts(day=6, reps=(10, 10))],
    )
    assert progressed["outcome"] == "consider_progressing"
    assert progressed["suggested_weight"] is None
    assert "conservative_without_rir" in progressed["evidence"]["reason_keys"]


def test_full_optional_rir_allows_two_sessions_and_preserves_lb_increment() -> None:
    result = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8–10",
        sessions=[
            _facts(day=20, reps=(10, 10), weight=100, rir=("1", "2")),
            _facts(day=13, reps=(10, 10), weight=100, rir=("2", "2")),
        ],
        load_unit="lb",
        configured_increment=5,
    )
    assert result["outcome"] == "consider_progressing"
    assert result["suggested_increment"] == 5
    assert result["suggested_weight"] == 105
    assert result["load_unit"] == "lb"
    assert {item["load_unit"] for item in result["evidence"]["sessions"]} == {"lb"}


def test_reduction_is_a_two_session_rule_not_a_diagnosis() -> None:
    result = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8-10",
        sessions=[_facts(day=20, reps=(6, 7)), _facts(day=13, reps=(7, 7))],
        configured_increment=2.5,
    )
    assert result["outcome"] == "consider_reducing"
    assert result["suggested_weight"] == 37.5
    assert "перетренированности" in result["detail"]


def test_failure_or_zero_rir_never_strengthens_progression() -> None:
    result = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8-10",
        sessions=[
            _facts(day=20, reps=(10, 10), rir=("0", "1"), failure=True),
            _facts(day=13, reps=(10, 10), rir=("1", "2")),
            _facts(day=6, reps=(10, 10), rir=("1", "2")),
        ],
    )
    assert result["outcome"] == "hold"
    assert "zero_rir_or_failure_recorded" in result["evidence"]["reason_keys"]


def test_optional_completion_feedback_is_evidence_not_a_decision_input() -> None:
    sessions = [
        _facts(day=20, reps=(10, 10), rir=("1", "2")),
        _facts(day=13, reps=(10, 10), rir=("2", "2")),
    ]
    easier = [replace(item, completion_feedback="easier_than_expected") for item in sessions]
    harder = [replace(item, completion_feedback="harder_than_expected") for item in sessions]

    easier_result = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8-10",
        sessions=easier,
    )
    harder_result = evaluate_progression(
        prescribed_sets=2,
        prescribed_reps="8-10",
        sessions=harder,
    )
    assert easier_result["outcome"] == harder_result["outcome"] == "consider_progressing"
    assert easier_result["evidence"]["sessions"][0]["completion_feedback"] == (
        "easier_than_expected"
    )
    assert harder_result["evidence"]["sessions"][0]["completion_feedback"] == (
        "harder_than_expected"
    )


def test_today_api_excludes_warmup_and_drop_and_repeats_identically(client) -> None:
    headers = _auth(client, 63_001)
    workout = _assigned_workout(client, headers)
    _add_history(
        workout["id"],
        [
            [(10, 40, "2", "warmup", False), (10, 40, "2", "working", False)],
            [(10, 40, "2", "working", False), (10, 35, "2", "drop", False)],
        ],
    )

    first = client.get("/api/v1/workouts/today", headers=headers)
    second = client.get("/api/v1/workouts/today", headers=headers)
    assert first.status_code == second.status_code == 200
    guidance = first.json()["exercises"][0]["progression_guidance"]
    assert guidance == second.json()["exercises"][0]["progression_guidance"]
    assert guidance["outcome"] == "review"
    assert guidance["evidence"]["comparable_session_count"] == 0
    assert "incomplete_session_facts" in guidance["evidence"]["reason_keys"]


def test_today_api_uses_only_completed_working_sets_with_optional_rir(client) -> None:
    headers = _auth(client, 63_002)
    workout = _assigned_workout(client, headers)
    _add_history(
        workout["id"],
        [
            [(10, 40, "1", "working", False), (10, 40, "2", "working", False)],
            [(10, 40, "2", None, False), (10, 40, "2", "working", False)],
        ],
    )

    response = client.get("/api/v1/workouts/today", headers=headers)
    assert response.status_code == 200, response.text
    guidance = response.json()["exercises"][0]["progression_guidance"]
    assert guidance["outcome"] == "consider_progressing"
    assert guidance["load_unit"] == "kg"
    assert guidance["suggested_weight"] is None
    assert guidance["evidence"]["target_reps_min"] == 8
    assert guidance["evidence"]["target_reps_max"] == 10
    assert guidance["evidence"]["rir_recorded_set_count"] == 4


def test_today_api_does_not_cross_a_training_block_boundary(client) -> None:
    headers = _auth(client, 63_003)
    workout = _assigned_workout(client, headers)
    _add_history(
        workout["id"],
        [
            [(10, 40, "1", "working", False), (10, 40, "2", "working", False)],
            [(10, 40, "2", "working", False), (10, 40, "2", "working", False)],
        ],
    )
    with get_session_context() as db:
        current = db.query(UserWorkout).filter(UserWorkout.id == workout["id"]).one()
        db.add(
            TrainingBlock(
                user_program_id=current.user_program_id,
                title="Новый блок",
                start_date=current.scheduled_date,
                end_date=current.scheduled_date,
                purpose="Проверить новый контекст нагрузки.",
                status="active",
            )
        )

    response = client.get("/api/v1/workouts/today", headers=headers)
    assert response.status_code == 200, response.text
    guidance = response.json()["exercises"][0]["progression_guidance"]
    assert guidance["outcome"] == "review"
    assert guidance["evidence"]["comparable_session_count"] == 0
    assert "program_context_changed" in guidance["evidence"]["reason_keys"]


def test_today_api_reviews_history_after_prescription_change(client) -> None:
    headers = _auth(client, 63_004)
    workout = _assigned_workout(client, headers)
    _add_history(
        workout["id"],
        [
            [(10, 40, "1", "working", False), (10, 40, "2", "working", False)],
            [(10, 40, "2", "working", False), (10, 40, "2", "working", False)],
        ],
    )
    with get_session_context() as db:
        current = db.query(UserWorkout).filter(UserWorkout.id == workout["id"]).one()
        for previous in (
            db.query(UserWorkoutExercise)
            .join(UserWorkout, UserWorkoutExercise.workout_id == UserWorkout.id)
            .filter(
                UserWorkout.user_program_id == current.user_program_id,
                UserWorkout.status == "completed",
            )
            .all()
        ):
            previous.prescribed_reps = "6-8"

    response = client.get("/api/v1/workouts/today", headers=headers)
    assert response.status_code == 200, response.text
    guidance = response.json()["exercises"][0]["progression_guidance"]
    assert guidance["outcome"] == "review"
    assert guidance["evidence"]["comparable_session_count"] == 0
    assert "program_context_changed" in guidance["evidence"]["reason_keys"]


def test_today_api_keeps_trainer_assigned_program_owned_by_athlete(client) -> None:
    athlete_headers = _auth(client, 63_005)
    _auth(client, 63_006)
    workout = _assigned_workout(client, athlete_headers)
    _add_history(
        workout["id"],
        [
            [(10, 40, "1", "working", False), (10, 40, "2", "working", False)],
            [(10, 40, "2", "working", False), (10, 40, "2", "working", False)],
        ],
    )
    with get_session_context() as db:
        current = db.query(UserWorkout).filter(UserWorkout.id == workout["id"]).one()
        trainer = db.query(User).filter(User.telegram_user_id == 63_006).one()
        current.user_program.assigned_by_user_id = trainer.id

    response = client.get("/api/v1/workouts/today", headers=athlete_headers)
    assert response.status_code == 200, response.text
    guidance = response.json()["exercises"][0]["progression_guidance"]
    assert guidance["outcome"] == "consider_progressing"
    assert guidance["evidence"]["comparable_session_count"] == 2
