from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from fitminiapp_api.db.session import engine, get_session_context
from fitminiapp_api.models.exercise import (
    Equipment,
    ExerciseAlternative,
    ExerciseEquipment,
    ExerciseGuideMetadata,
    ExerciseMuscle,
    Muscle,
)
from fitminiapp_api.services.seed import seed_demo_data


def auth(client, telegram_user_id: int, *, is_coach: bool) -> dict[str, str]:
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


def _load_migration():
    path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0039_exercise_domain.py"
    spec = importlib.util.spec_from_file_location("exercise_domain_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_exercise_domain_migration_backfills_only_supported_metadata(tmp_path: Path) -> None:
    migration = _load_migration()
    assert migration.down_revision == "0038_food_progress_hardening"

    migration_engine = sa.create_engine(
        f"sqlite:///{(tmp_path / 'exercise-domain-migration.db').as_posix()}"
    )
    metadata = sa.MetaData()
    exercises = sa.Table(
        "exercises",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("primary_muscle", sa.String(length=64), nullable=True),
        sa.Column("equipment", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("source_exercise_id", sa.Integer(), nullable=True),
    )
    metadata.create_all(migration_engine)
    with migration_engine.begin() as connection:
        connection.execute(
            exercises.insert(),
            [
                {
                    "id": 1,
                    "slug": "bench-press",
                    "primary_muscle": "Грудь",
                    "equipment": "Штанга",
                    "created_by_user_id": None,
                    "source_exercise_id": None,
                },
                {
                    "id": 2,
                    "slug": "dumbbell-bench-press",
                    "primary_muscle": "Грудь",
                    "equipment": "Гантели",
                    "created_by_user_id": None,
                    "source_exercise_id": None,
                },
                {
                    "id": 3,
                    "slug": "bench-press-u-personal",
                    "primary_muscle": "Грудь",
                    "equipment": "Гантели",
                    "created_by_user_id": 9,
                    "source_exercise_id": 1,
                },
                {
                    "id": 4,
                    "slug": "my-unknown-move",
                    "primary_muscle": None,
                    "equipment": "Своё оборудование",
                    "created_by_user_id": 9,
                    "source_exercise_id": None,
                },
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        muscle_rows = connection.execute(
            sa.text(
                "SELECT em.exercise_id, m.identifier, em.role, em.position "
                "FROM exercise_muscles em JOIN muscles m ON m.id = em.muscle_id "
                "ORDER BY em.exercise_id, em.role, em.position"
            )
        ).all()
        assert (1, "chest", "primary", 0) in muscle_rows
        assert (1, "triceps", "secondary", 0) in muscle_rows
        assert (1, "anterior_deltoid", "secondary", 1) in muscle_rows
        assert (3, "chest", "primary", 0) in muscle_rows
        assert all(row[0] != 4 for row in muscle_rows)

        equipment_rows = connection.execute(
            sa.text(
                "SELECT ee.exercise_id, e.identifier FROM exercise_equipment ee "
                "JOIN equipment e ON e.id = ee.equipment_id ORDER BY ee.exercise_id"
            )
        ).all()
        assert equipment_rows == [(1, "barbell"), (2, "dumbbell"), (3, "dumbbell")]

        guides = connection.execute(
            sa.text(
                "SELECT exercise_id, source_name, source_license, media_reference "
                "FROM exercise_guide_metadata ORDER BY exercise_id"
            )
        ).all()
        assert guides == [
            (
                1,
                "free-exercise-db",
                "Unlicense (общественное достояние)",
                "exercise-guides:bench-press",
            ),
            (
                2,
                "free-exercise-db",
                "Unlicense (общественное достояние)",
                "exercise-guides:dumbbell-bench-press",
            ),
            (
                3,
                "free-exercise-db",
                "Unlicense (общественное достояние)",
                "exercise-guides:bench-press",
            ),
        ]
        assert connection.execute(
            sa.text("SELECT exercise_id, alternative_exercise_id FROM exercise_alternatives")
        ).all() == [(1, 2)]

        inspector = sa.inspect(connection)
        assert {index["name"] for index in inspector.get_indexes("exercise_muscles")} == {
            "ix_exercise_muscles_muscle_role_exercise"
        }
        assert {index["name"] for index in inspector.get_indexes("exercise_equipment")} == {
            "ix_exercise_equipment_equipment_exercise"
        }
        assert {index["name"] for index in inspector.get_indexes("exercise_alternatives")} == {
            "ix_exercise_alternatives_reverse"
        }

        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text(
                    "INSERT INTO exercise_alternatives "
                    "(exercise_id, alternative_exercise_id) VALUES (1, 1)"
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text(
                    "INSERT INTO exercise_alternatives "
                    "(exercise_id, alternative_exercise_id) VALUES (1, 2)"
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text(
                    "INSERT INTO exercise_muscles (exercise_id, muscle_id, role, position) "
                    "SELECT 1, id, 'primary', 0 FROM muscles WHERE identifier = 'chest'"
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                sa.text(
                    "INSERT INTO exercise_equipment (exercise_id, equipment_id, position) "
                    "SELECT 1, id, 0 FROM equipment WHERE identifier = 'barbell'"
                )
            )

        migration.downgrade()
        assert "exercise_muscles" not in sa.inspect(connection).get_table_names()
    migration_engine.dispose()


def test_seeded_exercise_metadata_and_alternatives_are_serialized(client) -> None:
    headers = auth(client, telegram_user_id=32301, is_coach=False)
    catalog = client.get("/api/v1/programs/exercises", headers=headers)

    assert catalog.status_code == 200
    bench = next(item for item in catalog.json() if item["slug"] == "bench-press")
    assert bench["primary_muscle"] == "Грудь"
    assert bench["equipment"] == "Штанга"
    assert bench["primary_muscle_ids"] == ["chest"]
    assert set(bench["secondary_muscle_ids"]) == {"triceps", "anterior_deltoid"}
    assert bench["equipment_ids"] == ["barbell"]
    assert {item["slug"] for item in bench["alternatives"]} == {
        "dumbbell-bench-press",
        "machine-chest-press",
    }

    details = client.get(f"/api/v1/programs/exercises/{bench['id']}", headers=headers)
    assert details.status_code == 200
    guide = details.json()["guide"]
    assert guide["media_reference"] == "exercise-guides:bench-press"
    assert guide["source_name"] == "free-exercise-db"
    assert guide["source_license"] == "Unlicense (общественное достояние)"
    assert guide["source_license_url"].endswith("/LICENSE.md")
    assert guide["media"][0] == {
        "type": "image",
        "url": "/static/exercise-guides/bench-press-active.jpg",
        "poster": "/static/exercise-guides/bench-press-active.jpg",
        "phase": "Позитивная фаза",
        "alt": "Жим лежа: позитивная фаза",
        "source_name": "free-exercise-db",
        "source_url": "https://github.com/yuhonas/free-exercise-db",
        "source_license": "Unlicense (общественное достояние)",
        "source_license_url": ("https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md"),
        "width": 850,
        "height": 567,
        "byte_size": 72202,
        "sort_order": 0,
    }
    assert guide["media"][1]["phase"] == "Негативная фаза"
    assert guide["images"] == [
        {
            "phase": "Позитивная фаза",
            "url": "/static/exercise-guides/bench-press-active.jpg",
            "alt": "Жим лежа: позитивная фаза",
        },
        {
            "phase": "Негативная фаза",
            "url": "/static/exercise-guides/bench-press-start.jpg",
            "alt": "Жим лежа: негативная фаза",
        },
    ]
    assert guide["safety_notes"]
    assert guide["equipment"] == [{"identifier": "barbell", "name": "Штанга"}]
    assert guide["muscles"][0]["identifier"] == "chest"
    assert guide["muscles"][0]["role_id"] == "primary"
    assert {item["slug"] for item in guide["alternatives"]} == {
        "dumbbell-bench-press",
        "machine-chest-press",
    }
    guide_response = client.get(
        f"/api/v1/programs/exercises/{bench['id']}/guide",
        headers=headers,
    )
    assert guide_response.status_code == 200
    assert guide_response.json()["media_reference"] == "exercise-guides:bench-press"
    assert guide_response.json()["source_license_url"].endswith("/LICENSE.md")

    lat_pulldown = next(item for item in catalog.json() if item["slug"] == "lat-pulldown")
    lat_pulldown_guide = client.get(
        f"/api/v1/programs/exercises/{lat_pulldown['id']}/guide",
        headers=headers,
    ).json()
    assert [item["phase"] for item in lat_pulldown_guide["media"]] == [
        "Позитивная фаза",
        "Негативная фаза",
    ]

    plank = next(item for item in catalog.json() if item["slug"] == "plank")
    plank_guide = client.get(
        f"/api/v1/programs/exercises/{plank['id']}/guide",
        headers=headers,
    ).json()
    assert [item["phase"] for item in plank_guide["media"]] == ["Подготовка", "Удержание"]


def test_custom_exercise_structured_metadata_can_be_partial(client) -> None:
    headers = auth(client, telegram_user_id=32302, is_coach=False)

    minimal = client.post(
        "/api/v1/programs/exercises",
        json={"title": "Моё движение без классификации"},
        headers=headers,
    )
    assert minimal.status_code == 201
    assert minimal.json()["primary_muscle_ids"] == []
    assert minimal.json()["secondary_muscle_ids"] == []
    assert minimal.json()["equipment_ids"] == []
    assert minimal.json()["alternatives"] == []

    recognized = client.post(
        "/api/v1/programs/exercises",
        json={
            "title": "Мой жим гантелей",
            "primary_muscle": "shoulders",
            "equipment": "dumbbell",
        },
        headers=headers,
    )
    assert recognized.status_code == 201
    assert recognized.json()["primary_muscle_ids"] == ["shoulders"]
    assert recognized.json()["secondary_muscle_ids"] == []
    assert recognized.json()["equipment_ids"] == ["dumbbell"]
    assert recognized.json()["has_guide"] is False


def test_personalized_copy_keeps_guide_provenance_and_base_alternatives(client) -> None:
    headers = auth(client, telegram_user_id=32303, is_coach=False)
    catalog = client.get("/api/v1/programs/exercises", headers=headers).json()
    bench = next(item for item in catalog if item["slug"] == "bench-press")

    updated = client.patch(
        f"/api/v1/programs/exercises/{bench['edit_target_id']}",
        json={
            "title": "Мой жим лежа",
            "primary_muscle": "Плечи",
            "equipment": "Гантели",
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["id"] == bench["id"]
    assert updated.json()["source_exercise_id"] == bench["id"]
    assert updated.json()["primary_muscle_ids"] == ["shoulders"]
    assert updated.json()["equipment_ids"] == ["dumbbell"]

    details = client.get(f"/api/v1/programs/exercises/{bench['id']}", headers=headers)
    assert details.status_code == 200
    assert details.json()["title"] == "Мой жим лежа"
    assert details.json()["guide"]["source_name"] == "free-exercise-db"
    assert details.json()["guide"]["media_reference"] == "exercise-guides:bench-press"
    assert {item["slug"] for item in details.json()["alternatives"]} == {
        "dumbbell-bench-press",
        "machine-chest-press",
    }


def test_exercise_domain_seed_is_idempotent() -> None:
    with get_session_context() as session:
        before = {
            "muscles": session.query(Muscle).count(),
            "equipment": session.query(Equipment).count(),
            "muscle_links": session.query(ExerciseMuscle).count(),
            "equipment_links": session.query(ExerciseEquipment).count(),
            "alternatives": session.query(ExerciseAlternative).count(),
            "guides": session.query(ExerciseGuideMetadata).count(),
        }
        seed_demo_data(session, include_demo_users=False)
        after = {
            "muscles": session.query(Muscle).count(),
            "equipment": session.query(Equipment).count(),
            "muscle_links": session.query(ExerciseMuscle).count(),
            "equipment_links": session.query(ExerciseEquipment).count(),
            "alternatives": session.query(ExerciseAlternative).count(),
            "guides": session.query(ExerciseGuideMetadata).count(),
        }
    assert before == after
    assert before["muscles"] == 26
    assert before["equipment"] == 9
    assert before["alternatives"] > 0


def test_exercise_catalog_metadata_loading_has_no_per_row_queries(client) -> None:
    headers = auth(client, telegram_user_id=32304, is_coach=False)
    select_count = 0

    def count_selects(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        nonlocal select_count
        if statement.lstrip().upper().startswith("SELECT"):
            select_count += 1

    event.listen(engine, "before_cursor_execute", count_selects)
    try:
        response = client.get("/api/v1/programs/exercises", headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", count_selects)

    assert response.status_code == 200
    assert len(response.json()) == 158
    assert select_count <= 20
