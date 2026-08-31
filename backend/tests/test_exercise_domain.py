from __future__ import annotations

import hashlib
import importlib.util
import json
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
from fitminiapp_api.services.exercise_catalog_metadata import (
    CATALOG_METADATA,
    LOWER_BODY_MACHINE_SLUGS,
    UPPER_BODY_MACHINE_SLUGS,
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
        "url": "/static/exercise-guides/bench-press-start.jpg",
        "poster": "/static/exercise-guides/bench-press-start.jpg",
        "phase_id": "concentric_end",
        "phase": "Фаза усилия",
        "alt": "Жим лежа: фаза усилия",
        "asset_id": None,
        "asset_version": None,
        "variant_key": None,
        "source_name": "free-exercise-db",
        "source_url": "https://github.com/yuhonas/free-exercise-db",
        "source_license": "Unlicense (общественное достояние)",
        "source_license_url": ("https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md"),
        "width": 850,
        "height": 567,
        "byte_size": 72816,
        "sort_order": 0,
        "sources": [
            {
                "url": "/static/exercise-guides/bench-press-start.jpg",
                "mime_type": "image/jpeg",
                "width": 850,
                "height": 567,
                "byte_size": 72816,
            }
        ],
    }
    assert guide["media"][1]["phase"] == "Фаза возврата"
    assert guide["images"] == [
        {
            "phase": "Фаза усилия",
            "url": "/static/exercise-guides/bench-press-start.jpg",
            "alt": "Жим лежа: фаза усилия",
        },
        {
            "phase": "Фаза возврата",
            "url": "/static/exercise-guides/bench-press-active.jpg",
            "alt": "Жим лежа: фаза возврата",
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
        "Фаза усилия",
        "Фаза возврата",
    ]

    plank = next(item for item in catalog.json() if item["slug"] == "plank")
    plank_guide = client.get(
        f"/api/v1/programs/exercises/{plank['id']}/guide",
        headers=headers,
    ).json()
    assert [item["phase"] for item in plank_guide["media"]] == ["Подготовка", "Удержание"]

    reviewed_pairs = {
        "hyperextension": [
            ("hyperextension-start.jpg", "Фаза усилия"),
            ("hyperextension-active.jpg", "Фаза возврата"),
        ],
        "lying-dumbbell-triceps-extension": [
            ("lying-dumbbell-triceps-extension-active.jpg", "Фаза усилия"),
            ("lying-dumbbell-triceps-extension-start.jpg", "Фаза возврата"),
        ],
        "romanian-deadlift": [
            ("romanian-deadlift-active.jpg", "Фаза усилия"),
            ("romanian-deadlift-start.jpg", "Фаза возврата"),
        ],
        "smith-squat": [
            ("smith-squat-active.jpg", "Фаза усилия"),
            ("smith-squat-start.jpg", "Фаза возврата"),
        ],
        "triceps-kickback": [
            ("triceps-kickback-start.jpg", "Фаза усилия"),
            ("triceps-kickback-active.jpg", "Фаза возврата"),
        ],
        "upright-row": [
            ("upright-row-start.jpg", "Фаза усилия"),
            ("upright-row-active.jpg", "Фаза возврата"),
        ],
        "pallof-press": [
            ("pallof-press-start.jpg", "Подготовка"),
            ("pallof-press-active.jpg", "Удержание"),
        ],
        "rowing-machine": [
            ("rowing-machine-start.jpg", "Первое положение"),
            ("rowing-machine-active.jpg", "Второе положение"),
        ],
        "walking-lunge": [
            ("walking-lunge-start.jpg", "Первое положение"),
            ("walking-lunge-active.jpg", "Второе положение"),
        ],
        "wall-ball": [
            ("wall-ball-start.jpg", "Начало движения"),
            ("wall-ball-active.jpg", "Следующая позиция"),
        ],
    }
    catalog_by_slug = {item["slug"]: item for item in catalog.json()}
    for slug, expected_media in reviewed_pairs.items():
        reviewed_guide = client.get(
            f"/api/v1/programs/exercises/{catalog_by_slug[slug]['id']}/guide",
            headers=headers,
        ).json()
        assert [
            (item["url"].rsplit("/", 1)[-1], item["phase"]) for item in reviewed_guide["media"]
        ] == expected_media


def test_task_120b_upper_body_machine_batch_contract(client) -> None:
    headers = auth(client, telegram_user_id=32305, is_coach=False)
    catalog_response = client.get("/api/v1/programs/exercises", headers=headers)

    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    by_slug = {item["slug"]: item for item in catalog}
    assert len(by_slug) == len(catalog) == 176
    assert set(UPPER_BODY_MACHINE_SLUGS) <= set(by_slug)
    assert len({item["title"] for item in catalog}) == len(catalog)

    for slug in UPPER_BODY_MACHINE_SLUGS:
        item = by_slug[slug]
        assert item["metric_type"] == "strength"
        assert item["aliases"]
        assert item["movement_pattern"]
        assert item["execution_variant_tags"]
        assert item["has_guide"] is True
        assert item["equipment_ids"] == (
            ["dumbbell"] if slug == "chest-supported-dumbbell-row" else ["machine"]
        )

    high_row = by_slug["lever-high-row"]
    assert "верхняя тяга хаммер" in high_row["aliases"]
    assert high_row["machine_variant_tags"] == ["plate_loaded", "lever", "independent"]
    assert high_row["primary_muscle_ids"] == ["back"]
    assert {item["slug"] for item in high_row["alternatives"]} == {"chest-supported-row"}

    guide_response = client.get(
        f"/api/v1/programs/exercises/{high_row['id']}/guide",
        headers=headers,
    )
    assert guide_response.status_code == 200
    guide = guide_response.json()
    assert guide["source_name"] == "Your Fitness Coach"
    assert guide["source_license"] == "Иллюстрация создана для приложения"
    assert guide["source_license_url"] is None
    assert guide["technique_steps"][0].startswith("Настрой сиденье и грудной упор")
    assert {item["identifier"] for item in guide["muscles"] if item["role_id"] == "secondary"} == {
        "biceps",
        "posterior_deltoid",
        "forearms",
    }
    assert [item["url"].rsplit("/", 1)[-1] for item in guide["media"]] == [
        "concentric_end-480w.webp",
        "eccentric_end-480w.webp",
    ]
    assert [item["phase_id"] for item in guide["media"]] == [
        "concentric_end",
        "eccentric_end",
    ]
    assert all(item["asset_version"] == "120e-v1" for item in guide["media"])
    assert all(len(item["sources"]) == 3 for item in guide["media"])
    assert [item["phase"] for item in guide["media"]] == [
        "Фаза усилия",
        "Фаза возврата",
    ]
    assert all("Верхняя рычажная тяга" in item["alt"] for item in guide["media"])

    machine_biceps = by_slug["machine-biceps-curl"]
    assert "сгибание на скамье Скотта в тренажере" in machine_biceps["aliases"]

    normalized_titles = {
        " ".join(item["title"].casefold().split()): item["slug"] for item in catalog
    }
    alias_owners: dict[str, str] = {}
    for slug, metadata in CATALOG_METADATA.items():
        for alias in metadata["aliases"]:
            normalized = " ".join(alias.casefold().split())
            assert normalized
            assert normalized not in alias_owners
            alias_owners[normalized] = slug
            if normalized in normalized_titles:
                assert normalized_titles[normalized] == slug


def test_task_120e_human_visual_manifest_provenance_and_integrity() -> None:
    assets = Path(__file__).resolve().parents[1] / "assets" / "exercise-guides"
    manifest = json.loads((assets / "manifest.json").read_text(encoding="utf-8"))
    slugs = set(UPPER_BODY_MACHINE_SLUGS) | set(LOWER_BODY_MACHINE_SLUGS)

    assert manifest["schema_version"] == 2
    assert manifest["asset_count"] == 343
    assert manifest["derivative_count"] == 415
    assert len(manifest["exercises"]) == 176
    derivative_hashes: dict[str, str] = {}
    for slug in slugs:
        exercise = manifest["exercises"][slug]
        source = exercise["source"]
        assert source["source_kind"] == "yfc_ai_generated"
        assert source["source_revision_or_retrieved_at"] == "2026-08-31"
        assert source["license_url_or_local_notice"] == "backend/assets/exercise-guides/NOTICE.md"
        assert source["origin"] == "ai_generated"
        assert source["asset_type"] == "render_3d"
        assert source["asset_version"] == "120e-v1"
        assert source["variant_key"].startswith("canonical_")
        assert source["generation"]["provider"] == "OpenAI built-in image_gen"
        assert source["rights"]["commercial_use_verified"] is True
        assert source["rights"]["redistribution_verified"] is True
        assert source["rights"]["modification_verified"] is True
        assert source["owner_gates"]["gate_a"]["status"] == "approved"
        assert source["owner_gates"]["gate_b"]["status"] == "approved"
        assert source["owner_gates"]["gate_b"]["verdict"] == "APPROVE_120E_EXACT_ASSET_REVISION"
        assert len(exercise["media"]) == 2
        assert [item["phase_id"] for item in exercise["media"]] == [
            "concentric_end",
            "eccentric_end",
        ]
        mobile_pair_bytes = 0
        for media in exercise["media"]:
            path = assets / media["path"]
            assert path.suffix == ".webp"
            assert path.is_file()
            assert media["alt"]
            assert media["width"] == 480
            assert media["height"] == 320
            assert media["asset_version"] == "120e-v1"
            assert media["variant_key"] == source["variant_key"]
            assert media["asset_id"].endswith(":120e-v1")
            assert len(media["sources"]) == 3
            assert [item["width"] for item in media["sources"]] == [480, 768, 1280]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == media["asset_sha256"]
            mobile_pair_bytes += media["byte_size"]
            assert media["byte_size"] <= 160 * 1024
            assert all(
                value in {"pass", "pass_with_limitations"}
                for value in media["reviews"].values()
                if isinstance(value, str) and value != "2026-08-31"
            )
            for derivative in media["sources"]:
                derivative_path = assets / derivative["path"]
                assert derivative_path.is_file()
                assert derivative_path.stat().st_size == derivative["byte_size"]
                digest = hashlib.sha256(derivative_path.read_bytes()).hexdigest()
                assert digest == derivative["sha256"]
                assert digest not in derivative_hashes
                derivative_hashes[digest] = derivative["path"]
        assert mobile_pair_bytes <= 320 * 1024

    legacy_names = {f"{slug}-{phase}.svg" for slug in slugs for phase in ("start", "active")}
    assert not any((assets / name).exists() for name in legacy_names)


def test_task_120e_builder_cannot_mint_semantic_approval(tmp_path: Path) -> None:
    from scripts.build_exercise_human_visual_assets import load_review_lock

    review_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "exercises"
        / "catalog-v2"
        / "120E_ASSET_REVIEW.json"
    )
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["automated_semantic_approval"] = True
    invalid_lock = tmp_path / "invalid-review-lock.json"
    invalid_lock.write_text(json.dumps(review), encoding="utf-8")

    with pytest.raises(ValueError, match="Automated semantic approval"):
        load_review_lock(invalid_lock)


def test_task_120e_builders_require_exact_gate_b_verdict(tmp_path: Path) -> None:
    from scripts.build_exercise_human_visual_assets import load_review_lock

    review_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "exercises"
        / "catalog-v2"
        / "120E_ASSET_REVIEW.json"
    )
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["owner_gates"]["gate_b"] = {
        "status": "approved",
        "verdict": "APPROVE_DIFFERENT_REVISION",
        "approved_at": "2026-08-31",
    }
    invalid_lock = tmp_path / "wrong-gate-b-verdict-review-lock.json"
    invalid_lock.write_text(json.dumps(review), encoding="utf-8")

    with pytest.raises(ValueError, match="Gate B exact verdict"):
        load_review_lock(invalid_lock)


def test_task_120e_builder_stages_before_replacing_derivatives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image
    from scripts import build_exercise_human_visual_assets as builder

    slug = "test-machine"
    monkeypatch.setattr(
        builder,
        "HUMAN_VISUAL_SPECS",
        {slug: builder.HumanVisualSpec("canonical_test_machine")},
    )
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    source_name = f"{slug}-concentric_end-v1.png"
    source_path = source_dir / source_name
    Image.new("RGB", (1536, 1024), (32, 32, 32)).save(source_path)
    source_digest = builder.sha256(source_path)
    reviews = {
        "domain": "pass",
        "anatomy": "pass",
        "equipment": "pass",
        "phase": "pass",
        "visual_style": "pass",
        "mobile": "pass",
        "legal": "pass_with_limitations",
    }
    lock = {
        "schema_version": 1,
        "asset_version": builder.ASSET_VERSION,
        "review_record_kind": "human_review_exact_revision",
        "automated_semantic_approval": False,
        "owner_gates": {
            "gate_a": {
                "status": "approved",
                "verdict": "APPROVE_120E_VISUAL_DIRECTION",
            },
            "gate_b": {
                "status": "approved",
                "verdict": "APPROVE_120E_EXACT_ASSET_REVISION",
            },
        },
        "exercises": {
            slug: {
                "variant_key": "canonical_test_machine",
                "phases": {
                    "concentric_end": {
                        "source_master_filename": source_name,
                        "source_master_sha256": source_digest,
                        "reviews": reviews,
                        "sources": [],
                    }
                },
            }
        },
        "source_set_sha256": "not-reached",
        "derivative_set_sha256": "not-reached",
    }
    lock_path = tmp_path / "review-lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    asset_dir = tmp_path / "assets"
    existing = asset_dir / "human-v1" / slug / "concentric_end-480w.webp"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"approved-existing-derivative")

    with pytest.raises(ValueError, match="Derivative output is not the reviewed revision"):
        builder.build(source_dir, asset_dir, lock_path)

    assert existing.read_bytes() == b"approved-existing-derivative"


def test_task_120c_lower_body_machine_batch_contract_and_workout_integration(client) -> None:
    headers = auth(client, telegram_user_id=32306, is_coach=False)
    catalog_response = client.get("/api/v1/programs/exercises", headers=headers)

    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    by_slug = {item["slug"]: item for item in catalog}
    assert len(by_slug) == len(catalog) == 176
    assert set(LOWER_BODY_MACHINE_SLUGS) <= set(by_slug)
    assert len({item["title"] for item in catalog}) == len(catalog)

    expected_patterns = {
        "pendulum-squat": "squat",
        "plate-loaded-leg-press": "squat",
        "unilateral-leg-press": "squat",
        "machine-hip-thrust": "glute",
        "smith-split-squat": "lunge",
        "machine-glute-kickback": "leg_isolation",
        "v-squat-machine": "squat",
        "reverse-hyperextension": "hinge",
    }
    for slug, movement_pattern in expected_patterns.items():
        item = by_slug[slug]
        assert item["metric_type"] == "strength"
        assert item["aliases"]
        assert item["movement_pattern"] == movement_pattern
        assert item["machine_variant_tags"]
        assert item["execution_variant_tags"]
        assert item["equipment_ids"] == ["machine"]
        assert item["has_guide"] is True

        guide_response = client.get(
            f"/api/v1/programs/exercises/{item['id']}/guide",
            headers=headers,
        )
        assert guide_response.status_code == 200
        guide = guide_response.json()
        assert len(guide["technique_steps"]) == 3
        assert len(guide["common_mistakes"]) == 3
        assert guide["safety_notes"]
        assert guide["source_name"] == "Your Fitness Coach"
        assert guide["source_license"] == "Иллюстрация создана для приложения"
        assert [media["url"].rsplit("/", 1)[-1] for media in guide["media"]] == [
            "concentric_end-480w.webp",
            "eccentric_end-480w.webp",
        ]
        assert [media["phase_id"] for media in guide["media"]] == [
            "concentric_end",
            "eccentric_end",
        ]
        assert all(media["asset_version"] == "120e-v1" for media in guide["media"])
        assert all(media["alt"] for media in guide["media"])

    assert "жим ногами на блинах" in by_slug["plate-loaded-leg-press"]["aliases"]
    assert "pendulum squat" in by_slug["pendulum-squat"]["aliases"]
    assert "ягодичный тренажер" in by_slug["machine-hip-thrust"]["aliases"]
    assert "smith lunge" in by_slug["smith-split-squat"]["aliases"]
    assert "смит присед" in by_slug["smith-squat"]["aliases"]
    assert "hack squat" in by_slug["hack-squat"]["aliases"]
    assert "сгибание ног лежа" in by_slug["leg-curl"]["aliases"]
    assert "сгибание ног сидя" in by_slug["seated-leg-curl"]["aliases"]
    assert "сгибание ног стоя" in by_slug["standing-leg-curl"]["aliases"]
    assert "жим ногами широкая постановка" in by_slug["leg-press"]["aliases"]
    assert by_slug["calf-press"]["movement_pattern"] == "calf"
    assert by_slug["unilateral-leg-press"]["execution_variant_tags"] == ["unilateral"]
    assert by_slug["smith-split-squat"]["machine_variant_tags"] == ["smith"]
    assert {item["slug"] for item in by_slug["machine-hip-thrust"]["alternatives"]} == {
        "hip-thrust"
    }

    machine_hip_thrust = by_slug["machine-hip-thrust"]
    created = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Ноги и ягодицы 120C",
            "goal": "recomposition",
            "level": "beginner",
            "mode": "self",
            "assign_after_create": True,
            "days": [
                {
                    "title": "Низ тела",
                    "exercises": [
                        {
                            "exercise_id": machine_hip_thrust["id"],
                            "prescribed_sets": 1,
                            "prescribed_reps": "10-12",
                            "rest_seconds": 90,
                        }
                    ],
                }
            ],
        },
    )
    assert created.status_code == 200
    today = client.get("/api/v1/workouts/today", headers=headers)
    assert today.status_code == 200
    workout = today.json()
    assert workout["exercises"][0]["exercise_id"] == machine_hip_thrust["id"]
    assert workout["exercises"][0]["exercise_title"] == machine_hip_thrust["title"]
    started = client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers)
    assert started.status_code == 200


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
    assert len(response.json()) == 176
    assert select_count <= 20
