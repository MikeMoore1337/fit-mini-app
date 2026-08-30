from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError

from fitminiapp_api.core.timezone import today_msk
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.program import UserWorkoutSet
from fitminiapp_api.models.user import CoachClient


def _auth(client, telegram_user_id: int, *, is_coach: bool = False) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": is_coach},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _template_payload(exercise_ids: list[int]) -> dict:
    return {
        "title": "Суперсет без псевдометрик",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": False,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercise_ids[0],
                        "prescribed_sets": 3,
                        "prescribed_reps": "6-10",
                        "rest_seconds": 60,
                        "superset_group": 1,
                        "superset_order": 1,
                    },
                    {
                        "exercise_id": exercise_ids[1],
                        "prescribed_sets": 1,
                        "prescribed_reps": "10-12",
                        "rest_seconds": 60,
                        "superset_group": 1,
                        "superset_order": 2,
                    },
                ],
            }
        ],
    }


def _strength_exercises(client, headers: dict[str, str]) -> list[dict]:
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    return [exercise for exercise in exercises if exercise["metric_type"] == "strength"][:2]


def _load_migration():
    path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0043_advanced_set_semantics.py"
    )
    spec = importlib.util.spec_from_file_location("advanced_set_semantics_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_migration_preserves_legacy_sets_and_enforces_new_invariants(tmp_path: Path) -> None:
    migration = _load_migration()
    assert migration.down_revision == "0042_workout_comments"

    engine = sa.create_engine(f"sqlite:///{(tmp_path / 'set-semantics.db').as_posix()}")
    metadata = sa.MetaData()
    template_exercises = sa.Table(
        "program_template_exercises",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day_id", sa.Integer(), nullable=False),
    )
    workout_exercises = sa.Table(
        "user_workout_exercises",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_id", sa.Integer(), nullable=False),
    )
    workout_sets = sa.Table(
        "user_workout_sets",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_exercise_id", sa.Integer(), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("rir", sa.String(2), nullable=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(template_exercises.insert(), {"id": 1, "day_id": 10})
        connection.execute(workout_exercises.insert(), {"id": 1, "workout_id": 20})
        connection.execute(
            workout_sets.insert(),
            {"id": 1, "workout_exercise_id": 1, "set_number": 1, "rir": "2"},
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        legacy = connection.execute(
            sa.text("SELECT set_kind, reached_failure FROM user_workout_sets WHERE id = 1")
        ).one()
        assert legacy == (None, None)

        for set_kind in ("warmup", "working", "drop"):
            connection.execute(
                sa.text("UPDATE user_workout_sets SET set_kind = :kind WHERE id = 1"),
                {"kind": set_kind},
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text("UPDATE user_workout_sets SET set_kind = 'effective' WHERE id = 1")
            )

        connection.execute(
            sa.text(
                "UPDATE program_template_exercises "
                "SET superset_group = 1, superset_order = 1 WHERE id = 1"
            )
        )
        connection.execute(
            sa.text("INSERT INTO program_template_exercises (id, day_id) VALUES (2, 10)")
        )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text(
                    "UPDATE program_template_exercises "
                    "SET superset_group = 1, superset_order = 1 WHERE id = 2"
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text(
                    "UPDATE user_workout_exercises "
                    "SET superset_group = 1, superset_order = NULL WHERE id = 1"
                )
            )

        migration.downgrade()
        assert "set_kind" not in {
            column["name"] for column in sa.inspect(connection).get_columns("user_workout_sets")
        }

    engine.dispose()


@pytest.mark.parametrize(
    ("superset_group", "superset_order"),
    [(1, None), (None, 1), (0, 1), (1, 3)],
)
def test_template_rejects_invalid_superset_pairs(
    client, superset_group: int | None, superset_order: int | None
) -> None:
    headers = _auth(client, 29_100 + (superset_order or 0))
    exercises = _strength_exercises(client, headers)
    payload = _template_payload([exercise["id"] for exercise in exercises])
    payload["days"][0]["exercises"][0]["superset_group"] = superset_group
    payload["days"][0]["exercises"][0]["superset_order"] = superset_order

    response = client.post("/api/v1/programs/templates", headers=headers, json=payload)

    assert response.status_code == 422


def test_template_rejects_a_single_exercise_superset(client) -> None:
    headers = _auth(client, 29_150)
    exercises = _strength_exercises(client, headers)
    payload = _template_payload([exercise["id"] for exercise in exercises])
    payload["days"][0]["exercises"][1]["superset_group"] = None
    payload["days"][0]["exercises"][1]["superset_order"] = None

    response = client.post("/api/v1/programs/templates", headers=headers, json=payload)

    assert response.status_code == 422


def test_superset_materialization_set_combinations_history_export_and_analytics(client) -> None:
    headers = _auth(client, 29_200)
    exercises = _strength_exercises(client, headers)
    payload = _template_payload([exercise["id"] for exercise in exercises])
    created = client.post("/api/v1/programs/templates", headers=headers, json=payload)
    assert created.status_code == 200, created.text
    template = created.json()["template"]
    assert [
        (item["superset_group"], item["superset_order"])
        for item in template["days"][0]["exercises"]
    ] == [(1, 1), (1, 2)]

    updated = client.patch(
        f"/api/v1/programs/templates/{template['id']}",
        headers=headers,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["days"][0]["exercises"][1]["superset_order"] == 2

    assigned = client.post(
        f"/api/v1/programs/templates/{template['id']}/assign-to-me",
        headers=headers,
        json={"start_date": today_msk().isoformat()},
    )
    assert assigned.status_code == 200, assigned.text
    workout = client.get("/api/v1/workouts/today", headers=headers).json()
    assert [(item["superset_group"], item["superset_order"]) for item in workout["exercises"]] == [
        (1, 1),
        (1, 2),
    ]
    assert {
        set_row["set_kind"] for exercise in workout["exercises"] for set_row in exercise["sets"]
    } == {"working"}

    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )
    first_sets = workout["exercises"][0]["sets"]
    second_set = workout["exercises"][1]["sets"][0]
    updates = [
        (first_sets[0]["id"], "warmup", "2", False, 10, 10),
        (first_sets[1]["id"], "working", "0", True, 8, 20),
        (first_sets[2]["id"], "drop", "3", False, 6, 15),
        (second_set["id"], "working", None, None, 12, 5),
    ]
    for set_id, set_kind, rir, failure, reps, weight in updates:
        saved = client.patch(
            f"/api/v1/workouts/sets/{set_id}",
            headers=headers,
            json={
                "actual_reps": reps,
                "actual_weight": weight,
                "rir": rir,
                "set_kind": set_kind,
                "reached_failure": failure,
                "is_completed": True,
            },
        )
        assert saved.status_code == 200, saved.text
        assert saved.json()["set_kind"] == set_kind
        assert saved.json()["reached_failure"] is failure

    invalid_kind = client.patch(
        f"/api/v1/workouts/sets/{first_sets[0]['id']}",
        headers=headers,
        json={"set_kind": "effective"},
    )
    assert invalid_kind.status_code == 422

    finished = client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers)
    assert finished.status_code == 200, finished.text
    serialized_sets = finished.json()["exercises"][0]["sets"]
    assert [item["set_kind"] for item in serialized_sets] == ["warmup", "working", "drop"]
    assert serialized_sets[1]["rir"] == "0"
    assert serialized_sets[1]["reached_failure"] is True

    summary = client.get("/api/v1/workouts/history/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["completed_sets"] == 4
    assert summary.json()["volume_kg"] == 310.0

    analytics = client.get(
        "/api/v1/workouts/progress/training-analytics?period_days=7",
        headers=headers,
    )
    assert analytics.status_code == 200, analytics.text
    assert analytics.json()["completed_set_count"] == 3
    assert analytics.json()["external_load_volume_kg"] == 310.0
    kinds = {
        item["set_kind"]
        for exercise in analytics.json()["exercises"]
        for session in exercise["sessions"]
        for item in session["sets"]
    }
    assert kinds == {"working", "drop"}

    exported = client.get("/api/v1/me/export", headers=headers).json()
    exported_exercise = exported["programs"][0]["workouts"][0]["exercises"][0]
    assert exported_exercise["superset_group"] == 1
    assert exported_exercise["sets"][2]["set_kind"] == "drop"
    assert exported_exercise["sets"][1]["reached_failure"] is True

    coach_headers = _auth(client, 29_201, is_coach=True)
    client_id = client.get("/api/v1/me", headers=headers).json()["id"]
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
    assert timeline.json()[0]["exercises"][0]["superset_order"] == 1
    assert timeline.json()[0]["exercises"][0]["sets"][0]["set_kind"] == "warmup"
    assert timeline.json()[0]["volume_kg"] == 310.0


def test_legacy_null_set_kind_remains_in_working_analytics(client) -> None:
    headers = _auth(client, 29_300)
    exercises = _strength_exercises(client, headers)
    payload = _template_payload([exercise["id"] for exercise in exercises])
    payload["assign_after_create"] = True
    payload["start_date"] = today_msk().isoformat()
    created = client.post("/api/v1/programs/templates", headers=headers, json=payload)
    assert created.status_code == 200, created.text
    workout = client.get("/api/v1/workouts/today", headers=headers).json()
    set_id = workout["exercises"][0]["sets"][0]["id"]
    with get_session_context() as db:
        db.query(UserWorkoutSet).filter(UserWorkoutSet.id == set_id).update(
            {
                "set_kind": None,
                "actual_reps": 5,
                "actual_weight": 20,
                "is_completed": True,
            }
        )

    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )
    finished = client.post(
        f"/api/v1/workouts/{workout['id']}/finish",
        headers=headers,
        json={"confirm_incomplete": True},
    )
    assert finished.status_code == 200
    analytics = client.get(
        "/api/v1/workouts/progress/training-analytics?period_days=7",
        headers=headers,
    ).json()
    assert analytics["completed_set_count"] == 1
    assert analytics["external_load_volume_kg"] == 100.0
    assert analytics["exercises"][0]["sessions"][0]["sets"][0]["set_kind"] is None
