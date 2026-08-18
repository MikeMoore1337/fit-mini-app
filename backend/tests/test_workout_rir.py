from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError

from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.user import CoachClient
from fitminiapp_api.schemas.workout import WorkoutSetCreate


def _auth(client, telegram_user_id: int, *, is_coach: bool = False) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={
            "telegram_user_id": telegram_user_id,
            "is_coach": is_coach,
            "is_admin": False,
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_today_workout(client, headers: dict[str, str]) -> dict:
    exercise_id = client.get("/api/v1/programs/exercises", headers=headers).json()[0]["id"]
    created = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Программа для проверки повторов в запасе",
            "goal": "recomposition",
            "level": "intermediate",
            "mode": "self",
            "assign_after_create": True,
            "days": [
                {
                    "title": "День 1",
                    "exercises": [
                        {
                            "exercise_id": exercise_id,
                            "prescribed_sets": 1,
                            "prescribed_reps": "8-10",
                            "rest_seconds": 90,
                        }
                    ],
                }
            ],
        },
    )
    assert created.status_code == 200
    workout = client.get("/api/v1/workouts/today", headers=headers)
    assert workout.status_code == 200
    return workout.json()


def _load_migration():
    path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0040_workout_set_rir.py"
    spec = importlib.util.spec_from_file_location("workout_set_rir_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_rir_migration_preserves_old_sets_and_enforces_categories(tmp_path: Path) -> None:
    migration = _load_migration()
    assert migration.down_revision == "0039_exercise_domain"

    migration_engine = sa.create_engine(
        f"sqlite:///{(tmp_path / 'workout-rir-migration.db').as_posix()}"
    )
    metadata = sa.MetaData()
    workout_sets = sa.Table(
        "user_workout_sets",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_exercise_id", sa.Integer(), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("actual_reps", sa.Integer(), nullable=True),
        sa.Column("actual_weight", sa.Float(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
    )
    metadata.create_all(migration_engine)

    with migration_engine.begin() as connection:
        connection.execute(
            workout_sets.insert(),
            {
                "id": 1,
                "workout_exercise_id": 10,
                "set_number": 1,
                "actual_reps": 8,
                "actual_weight": 40,
                "is_completed": True,
            },
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        rir_column = next(
            column
            for column in sa.inspect(connection).get_columns("user_workout_sets")
            if column["name"] == "rir"
        )
        assert rir_column["nullable"] is True
        assert (
            connection.execute(sa.text("SELECT rir FROM user_workout_sets WHERE id = 1")).scalar()
            is None
        )

        for rir in ("0", "1", "2", "3", "4+"):
            connection.execute(
                sa.text("UPDATE user_workout_sets SET rir = :rir WHERE id = 1"),
                {"rir": rir},
            )
            assert (
                connection.execute(
                    sa.text("SELECT rir FROM user_workout_sets WHERE id = 1")
                ).scalar()
                == rir
            )

        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(sa.text("UPDATE user_workout_sets SET rir = '4' WHERE id = 1"))

        migration.downgrade()
        assert "rir" not in {
            column["name"] for column in sa.inspect(connection).get_columns("user_workout_sets")
        }

    migration_engine.dispose()


@pytest.mark.parametrize("rir", [None, "0", "1", "2", "3", "4+"])
def test_rir_categories_save_and_resume(client, rir: str | None) -> None:
    headers = _auth(client, 24_100)
    workout = _create_today_workout(client, headers)
    set_id = workout["exercises"][0]["sets"][0]["id"]

    assert (
        WorkoutSetCreate(
            workout_exercise_id=workout["exercises"][0]["id"],
            set_number=1,
            actual_reps=8,
            actual_weight=40,
            rir=rir,
        ).rir
        == rir
    )
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )

    saved = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        headers=headers,
        json={"actual_reps": 8, "actual_weight": 40, "rir": rir, "is_completed": True},
    )
    assert saved.status_code == 200
    assert saved.json()["rir"] == rir

    resumed = client.get("/api/v1/workouts/today", headers=headers)
    assert resumed.status_code == 200
    assert resumed.json()["exercises"][0]["sets"][0]["rir"] == rir

    if rir is not None:
        cleared = client.patch(
            f"/api/v1/workouts/sets/{set_id}",
            headers=headers,
            json={"rir": None},
        )
        assert cleared.status_code == 200
        assert cleared.json()["rir"] is None


@pytest.mark.parametrize("rir", ["4", "-1", "5", "many", 0, 4])
def test_invalid_rir_categories_are_rejected_by_api(client, rir: object) -> None:
    headers = _auth(client, 24_200)
    workout = _create_today_workout(client, headers)
    set_id = workout["exercises"][0]["sets"][0]["id"]
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )

    response = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        headers=headers,
        json={"rir": rir},
    )

    assert response.status_code == 422


def test_workout_completion_remains_compatible_without_rir(client) -> None:
    headers = _auth(client, 24_300)
    workout = _create_today_workout(client, headers)
    set_id = workout["exercises"][0]["sets"][0]["id"]
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )

    saved = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        headers=headers,
        json={"actual_reps": 8, "actual_weight": 40, "is_completed": True},
    )
    assert saved.status_code == 200
    assert saved.json()["rir"] is None

    finished = client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers)
    assert finished.status_code == 200
    assert finished.json()["exercises"][0]["sets"][0]["rir"] is None
    assert client.get("/api/v1/workouts/history", headers=headers).status_code == 200

    exported = client.get("/api/v1/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["programs"][0]["workouts"][0]["exercises"][0]["sets"][0]["rir"] is None


def test_four_plus_rir_is_preserved_in_completion_history_and_export(client) -> None:
    client_headers = _auth(client, 24_400)
    workout = _create_today_workout(client, client_headers)
    set_id = workout["exercises"][0]["sets"][0]["id"]
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=client_headers).status_code
        == 200
    )
    saved = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        headers=client_headers,
        json={"actual_reps": 8, "actual_weight": 40, "rir": "4+", "is_completed": True},
    )
    assert saved.status_code == 200

    finished = client.post(
        f"/api/v1/workouts/{workout['id']}/finish",
        headers=client_headers,
    )
    assert finished.status_code == 200
    assert finished.json()["exercises"][0]["sets"][0]["rir"] == "4+"

    coach_headers = _auth(client, 24_401, is_coach=True)
    client_id = client.get("/api/v1/me", headers=client_headers).json()["id"]
    coach_id = client.get("/api/v1/me", headers=coach_headers).json()["id"]
    with get_session_context() as db:
        db.add(
            CoachClient(
                coach_user_id=coach_id,
                client_user_id=client_id,
                status="active",
            )
        )

    timeline = client.get(
        f"/api/v1/coach/clients/{client_id}/workouts",
        headers=coach_headers,
    )
    assert timeline.status_code == 200
    assert timeline.json()[0]["exercises"][0]["sets"][0]["rir"] == "4+"

    exported = client.get("/api/v1/me/export", headers=client_headers)
    assert exported.status_code == 200
    assert exported.json()["programs"][0]["workouts"][0]["exercises"][0]["sets"][0]["rir"] == "4+"
