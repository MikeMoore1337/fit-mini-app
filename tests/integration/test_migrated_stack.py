from __future__ import annotations

import os
import re
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

RUN_MIGRATED_STACK_TEST = os.environ.get("RUN_MIGRATED_STACK_TEST") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_MIGRATED_STACK_TEST,
    reason="set RUN_MIGRATED_STACK_TEST=1 and provide a migrated PostgreSQL database",
)


def test_migrated_postgres_serves_api_and_frontend() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    assert database_url.startswith("postgresql+psycopg://"), (
        "the migrated-stack test must run against PostgreSQL"
    )

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend"))

    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from fitminiapp_api.db.session import engine
    from fitminiapp_api.main import app

    alembic_config = Config(str(root / "backend" / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(root / "backend" / "alembic"))
    expected_revision = ScriptDirectory.from_config(alembic_config).get_current_head()
    with engine.connect() as connection:
        actual_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert actual_revision == expected_revision

    with TestClient(app) as client:
        ready = client.get("/health/ready")
        frontend = client.get("/app")
        public_config = client.get("/api/v1/public/config")
        login = client.post(
            "/api/v1/auth/dev-login",
            json={
                "telegram_user_id": 9_900_001,
                "username": "ci_migrated_stack",
                "full_name": "CI Migrated Stack",
            },
        )

        assert ready.status_code == 200
        assert frontend.status_code == 200
        assert re.search(r'<div\s+id=["\']root["\'][^>]*>', frontend.text)
        assert public_config.status_code == 200
        assert public_config.json()["app_env"] == "test"
        assert login.status_code == 200

        me = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["telegram_user_id"] == 9_900_001


def test_migrated_postgres_account_deletion_removes_owner_nutrition_graph() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    assert database_url.startswith("postgresql+psycopg://"), (
        "the account-deletion regression must run against PostgreSQL"
    )

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend"))

    from fastapi.testclient import TestClient

    from fitminiapp_api.core.timezone import now_msk_naive
    from fitminiapp_api.db.session import get_session_context
    from fitminiapp_api.main import app
    from fitminiapp_api.models.food import Food, FoodFavorite
    from fitminiapp_api.models.food_diary import (
        FoodDiaryCopyOperation,
        FoodDiaryDayStatus,
        FoodDiaryEntry,
    )
    from fitminiapp_api.models.nutrition import EnergyCalibration, NutritionTarget
    from fitminiapp_api.models.recipe import Recipe, RecipeIngredient

    with TestClient(app) as client:
        owner_login = client.post(
            "/api/v1/auth/dev-login",
            json={"telegram_user_id": 9_900_011, "full_name": "Deletion owner"},
        )
        other_login = client.post(
            "/api/v1/auth/dev-login",
            json={"telegram_user_id": 9_900_012, "full_name": "Deletion other"},
        )
        assert owner_login.status_code == 200
        assert other_login.status_code == 200
        owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
        owner_id = client.get("/api/v1/me", headers=owner_headers).json()["id"]
        other_id = client.get("/api/v1/me", headers=other_headers).json()["id"]

        with get_session_context() as db:
            today = now_msk_naive().date()
            private_food = Food(
                name="PostgreSQL deletion owner food",
                energy_kcal_per_100g=Decimal("210"),
                protein_g_per_100g=Decimal("12"),
                fat_g_per_100g=Decimal("8"),
                carbs_g_per_100g=Decimal("20"),
                food_type="user",
                owner_user_id=owner_id,
                provenance="user",
                source_name=None,
                trust_level="unverified",
                status="active",
            )
            other_food = Food(
                name="PostgreSQL deletion other food",
                energy_kcal_per_100g=Decimal("180"),
                protein_g_per_100g=Decimal("9"),
                fat_g_per_100g=Decimal("7"),
                carbs_g_per_100g=Decimal("22"),
                food_type="user",
                owner_user_id=other_id,
                provenance="user",
                source_name=None,
                trust_level="unverified",
                status="active",
            )
            db.add_all([private_food, other_food])
            db.flush()
            private_food_id = private_food.id
            other_food_id = other_food.id
            db.add(FoodFavorite(user_id=owner_id, food_id=private_food_id))

            recipe = Recipe(owner_user_id=owner_id, name="PostgreSQL deletion recipe")
            db.add(recipe)
            db.flush()
            recipe_id = recipe.id
            ingredient = RecipeIngredient(
                recipe_id=recipe_id,
                food_id=private_food_id,
                position=0,
                amount=Decimal("100"),
                amount_unit="g",
                weight_g=Decimal("100"),
                food_name=private_food.name,
                food_brand=None,
                energy_kcal_per_100g=Decimal("210"),
                protein_g_per_100g=Decimal("12"),
                fat_g_per_100g=Decimal("8"),
                carbs_g_per_100g=Decimal("20"),
                fiber_g_per_100g=None,
            )
            db.add(ingredient)
            db.flush()
            ingredient_id = ingredient.id

            copy_operation = FoodDiaryCopyOperation(
                user_id=owner_id,
                idempotency_key="postgres-account-delete-copy",
                request_fingerprint="b" * 64,
                copy_scope="product",
                source_entry_id=None,
                source_date=today,
                source_meal_type="breakfast",
                target_date=today,
                target_meal_type="lunch",
            )
            db.add(copy_operation)
            db.flush()
            copy_operation_id = copy_operation.id
            db.add(
                FoodDiaryEntry(
                    user_id=owner_id,
                    food_id=private_food_id,
                    copy_operation_id=copy_operation_id,
                    diary_date=today,
                    meal_type="lunch",
                    amount=Decimal("1"),
                    amount_unit="serving",
                    weight_g=Decimal("50"),
                    food_name=private_food.name,
                    food_brand=None,
                    energy_kcal_per_100g=Decimal("210"),
                    protein_g_per_100g=Decimal("12"),
                    fat_g_per_100g=Decimal("8"),
                    carbs_g_per_100g=Decimal("20"),
                    fiber_g_per_100g=None,
                    serving_amount=Decimal("1"),
                    serving_unit="serving",
                    serving_weight_g=Decimal("50"),
                )
            )
            db.add(FoodDiaryDayStatus(user_id=owner_id, diary_date=today, status="complete"))

            target = NutritionTarget(
                user_id=owner_id,
                assigned_by_user_id=owner_id,
                calories=2200,
                protein_g=150,
                fat_g=70,
                carbs_g=240,
                effective_from=today,
                source="manual",
            )
            db.add(target)
            db.flush()
            target_id = target.id
            calibration = EnergyCalibration(
                user_id=owner_id,
                ruleset_version="account-delete-test-v1",
                status="accepted",
                sufficiency_status="sufficient",
                period_start=today - timedelta(days=28),
                period_end=today,
                goal="maintenance",
                logged_day_count=28,
                eligible_day_count=28,
                weight_point_count=6,
                weight_span_days=28,
                average_intake_kcal=2200,
                smoothed_start_weight_kg=Decimal("80.0"),
                smoothed_end_weight_kg=Decimal("80.0"),
                estimated_expenditure_kcal=2200,
                estimate_low_kcal=2100,
                estimate_high_kcal=2300,
                previous_target_calories=2200,
                previous_target_saved_at=now_msk_naive(),
                proposed_target_calories=None,
                sufficiency_counters={"logged_days": 28},
                sufficiency_reason_keys=[],
                rationale_keys=["stable_weight"],
                decided_at=now_msk_naive(),
            )
            db.add(calibration)
            db.flush()
            calibration_id = calibration.id

        deleted = client.request(
            "DELETE",
            "/api/v1/me/account",
            headers=owner_headers,
            json={"confirmation": "DELETE"},
        )
        assert deleted.status_code == 204

        with get_session_context() as db:
            assert db.get(Food, private_food_id) is None
            assert db.get(Food, other_food_id) is not None
            assert db.query(FoodFavorite).filter_by(user_id=owner_id).count() == 0
            assert db.get(Recipe, recipe_id) is None
            assert db.get(RecipeIngredient, ingredient_id) is None
            assert db.query(FoodDiaryEntry).filter_by(user_id=owner_id).count() == 0
            assert db.query(FoodDiaryDayStatus).filter_by(user_id=owner_id).count() == 0
            assert db.get(FoodDiaryCopyOperation, copy_operation_id) is None
            assert db.get(NutritionTarget, target_id) is None
            assert db.get(EnergyCalibration, calibration_id) is None
