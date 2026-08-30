from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from fitminiapp_api.core.timezone import today_msk
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.schemas.program import ProgramTemplateExerciseCreate
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.workout_metrics import (
    exercise_metric_type,
    normalize_exercise_prescription,
)


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _load_migration(filename: str):
    path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_metric_migrations_backfill_structured_cardio_and_preserve_history(tmp_path: Path) -> None:
    expand = _load_migration("0064_workout_metric_fields.py")
    backfill = _load_migration("0065_exercise_metric_backfill.py")
    workout_backfill = _load_migration("0066_workout_metric_backfill.py")
    engine = sa.create_engine(f"sqlite:///{(tmp_path / 'type-aware-workout.db').as_posix()}")
    metadata = sa.MetaData()
    exercises = sa.Table(
        "exercises",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
    )
    muscles = sa.Table(
        "muscles",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identifier", sa.String(), nullable=False),
    )
    exercise_muscles = sa.Table(
        "exercise_muscles",
        metadata,
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
    )
    sa.Table(
        "program_template_exercises",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    workout_exercises = sa.Table(
        "user_workout_exercises",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
    )
    workout_sets = sa.Table(
        "user_workout_sets",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actual_reps", sa.Integer(), nullable=True),
        sa.Column("actual_weight", sa.Float(), nullable=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            exercises.insert(),
            [{"id": 1, "title": "Велотренажёр"}, {"id": 2, "title": "Legacy row"}],
        )
        connection.execute(muscles.insert(), {"id": 1, "identifier": "cardio"})
        connection.execute(exercise_muscles.insert(), {"exercise_id": 1, "muscle_id": 1})
        connection.execute(
            workout_exercises.insert(),
            [{"id": 1, "exercise_id": 1}, {"id": 2, "exercise_id": 2}],
        )
        connection.execute(workout_sets.insert(), {"id": 1, "actual_reps": 8, "actual_weight": 40})

        operations = Operations(MigrationContext.configure(connection))
        expand.op = operations
        expand.upgrade()
        backfill.op = operations
        backfill.upgrade()
        workout_backfill.op = operations
        workout_backfill.upgrade()

        assert (
            connection.execute(
                sa.text("SELECT metric_type FROM exercises WHERE id = 1")
            ).scalar_one()
            == "cardio"
        )
        assert (
            connection.execute(
                sa.text("SELECT metric_type FROM exercises WHERE id = 2")
            ).scalar_one()
            == "strength"
        )
        assert connection.execute(
            sa.text("SELECT metric_type FROM user_workout_exercises ORDER BY id")
        ).scalars().all() == ["cardio", "strength"]
        assert connection.execute(
            sa.text("SELECT actual_reps, actual_weight FROM user_workout_sets WHERE id = 1")
        ).one() == (8, 40.0)
        assert {
            "duration_minutes",
            "distance_km",
            "average_heart_rate_bpm",
            "heart_rate_zone",
        }.issubset(
            {column["name"] for column in sa.inspect(connection).get_columns("user_workout_sets")}
        )
    engine.dispose()


def test_legacy_unclassified_exercise_has_safe_strength_fallback() -> None:
    assert (
        exercise_metric_type(Exercise(title="Legacy", slug="legacy", metric_type=None))
        == "strength"
    )


def test_saved_cardio_prescription_can_be_revalidated_without_weakening_strength_rest() -> None:
    payload = ProgramTemplateExerciseCreate(
        exercise_id=1,
        prescribed_duration_minutes=25,
        rest_seconds=0,
    )
    assert payload.rest_seconds == 0
    with pytest.raises(ProgramError, match="at least 15 seconds"):
        normalize_exercise_prescription(
            Exercise(title="Legacy", slug="legacy", metric_type="strength"),
            prescribed_sets=3,
            prescribed_reps="8-10",
            prescribed_duration_minutes=None,
            rest_seconds=0,
        )


def test_legacy_catalog_edit_does_not_reset_explicit_cardio_type(client) -> None:
    headers = _auth(client, 119_002)
    created = client.post(
        "/api/v1/programs/exercises",
        headers=headers,
        json={"title": "Кардио тест", "metric_type": "cardio"},
    )
    assert created.status_code == 201, created.text
    edited = client.patch(
        f"/api/v1/programs/exercises/{created.json()['id']}",
        headers=headers,
        json={"title": "Кардио тест обновлён"},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["metric_type"] == "cardio"


def test_assignment_snapshots_personalized_metric_type(client) -> None:
    headers = _auth(client, 119_003)
    catalog = client.get("/api/v1/programs/exercises", headers=headers).json()
    strength = next(
        item for item in catalog if item["metric_type"] == "strength" and not item["is_custom"]
    )
    personalized = client.patch(
        f"/api/v1/programs/exercises/{strength['edit_target_id']}",
        headers=headers,
        json={"title": strength["title"], "metric_type": "cardio"},
    )
    assert personalized.status_code == 200, personalized.text
    assert personalized.json()["source_exercise_id"] == strength["id"]
    assert personalized.json()["metric_type"] == "cardio"

    created = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Персональное кардио",
            "goal": "maintenance",
            "level": "beginner",
            "mode": "self",
            "assign_after_create": True,
            "start_date": today_msk().isoformat(),
            "schedule_weekdays": [today_msk().weekday()],
            "days": [
                {
                    "title": "Кардио",
                    "exercises": [
                        {
                            "exercise_id": strength["id"],
                            "prescribed_duration_minutes": 35,
                            "rest_seconds": 0,
                        }
                    ],
                }
            ],
        },
    )
    assert created.status_code == 200, created.text

    workout = client.get("/api/v1/workouts/today", headers=headers)
    assert workout.status_code == 200, workout.text
    exercise = workout.json()["exercises"][0]
    assert exercise["exercise_id"] == strength["id"]
    assert exercise["metric_type"] == "cardio"
    assert exercise["prescribed_duration_minutes"] == 35
    assert exercise["prescribed_sets"] == 1
    assert exercise["prescribed_reps"] == ""


def test_mixed_workout_persists_type_specific_results_and_completes(client) -> None:
    headers = _auth(client, 119_001)
    catalog = client.get("/api/v1/programs/exercises", headers=headers).json()
    strength = next(item for item in catalog if item["metric_type"] == "strength")
    cardio = next(item for item in catalog if item["metric_type"] == "cardio")
    created = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Смешанная тренировка",
            "goal": "maintenance",
            "level": "beginner",
            "mode": "self",
            "assign_after_create": True,
            "start_date": today_msk().isoformat(),
            "schedule_weekdays": [today_msk().weekday()],
            "days": [
                {
                    "title": "Сила и кардио",
                    "exercises": [
                        {
                            "exercise_id": strength["id"],
                            "prescribed_sets": 1,
                            "prescribed_reps": "8-10",
                            "rest_seconds": 90,
                        },
                        {
                            "exercise_id": cardio["id"],
                            "prescribed_duration_minutes": 25,
                            "rest_seconds": 90,
                        },
                    ],
                }
            ],
        },
    )
    assert created.status_code == 200, created.text

    with get_session_context() as db:
        db.query(Exercise).filter(Exercise.id == strength["id"]).update(
            {Exercise.metric_type: "cardio"}
        )
        db.query(Exercise).filter(Exercise.id == cardio["id"]).update(
            {Exercise.metric_type: "strength"}
        )

    started = client.get("/api/v1/workouts/today", headers=headers).json()
    started = client.post(f"/api/v1/workouts/{started['id']}/start", headers=headers).json()
    strength_row = next(item for item in started["exercises"] if item["metric_type"] == "strength")
    cardio_row = next(item for item in started["exercises"] if item["metric_type"] == "cardio")
    assert cardio_row["prescribed_duration_minutes"] == 25
    assert cardio_row["progression_guidance"] is None

    strength_saved = client.patch(
        f"/api/v1/workouts/sets/{strength_row['sets'][0]['id']}",
        headers=headers,
        json={"actual_reps": 9, "actual_weight": 42.5, "is_completed": True},
    )
    assert strength_saved.status_code == 200, strength_saved.text
    cardio_rejects_strength = client.patch(
        f"/api/v1/workouts/sets/{cardio_row['sets'][0]['id']}",
        headers=headers,
        json={"actual_reps": 10, "is_completed": True},
    )
    assert cardio_rejects_strength.status_code == 422
    cardio_saved = client.patch(
        f"/api/v1/workouts/sets/{cardio_row['sets'][0]['id']}",
        headers=headers,
        json={
            "duration_minutes": 27,
            "distance_km": 6.4,
            "average_heart_rate_bpm": 138,
            "heart_rate_zone": 3,
            "is_completed": True,
        },
    )
    assert cardio_saved.status_code == 200, cardio_saved.text

    reloaded = client.get("/api/v1/workouts/today", headers=headers).json()
    reloaded_cardio = next(
        item for item in reloaded["exercises"] if item["metric_type"] == "cardio"
    )
    assert reloaded_cardio["sets"][0]["duration_minutes"] == 27
    assert reloaded_cardio["sets"][0]["distance_km"] == 6.4
    assert reloaded_cardio["sets"][0]["average_heart_rate_bpm"] == 138
    assert reloaded_cardio["sets"][0]["heart_rate_zone"] == 3
    assert reloaded_cardio["sets"][0]["is_completed"] is True

    finished = client.post(f"/api/v1/workouts/{reloaded['id']}/finish", headers=headers)
    assert finished.status_code == 200, finished.text
    cardio_summary = next(
        item
        for item in finished.json()["completion_summary"]["exercises"]
        if item["metric_type"] == "cardio"
    )
    assert cardio_summary["duration_minutes"] == 27
    assert cardio_summary["distance_km"] == 6.4
    assert cardio_summary["average_heart_rate_bpm"] == 138
    assert cardio_summary["heart_rate_zone"] == 3
    assert all(
        item["exercise_id"] != cardio["id"]
        for item in finished.json()["completion_summary"]["personal_records"]
    )
