from __future__ import annotations

import importlib.util
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, inspect

from fitminiapp_api import main as main_module
from fitminiapp_api.core import timezone as timezone_module
from fitminiapp_api.db.performance import begin_sql_metrics, current_sql_metrics, reset_sql_metrics
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.food import Food
from fitminiapp_api.models.food_diary import FoodDiaryEntry
from fitminiapp_api.models.user import User
from fitminiapp_api.services.foods import search_foods


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={
            "telegram_user_id": telegram_user_id,
            "is_coach": False,
            "is_admin": False,
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _food_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Домашний йогурт",
        "brand": "Моя кухня",
        "energy_kcal_per_100g": "88.4",
        "protein_g_per_100g": "3.1",
        "fat_g_per_100g": "1.7",
        "carbs_g_per_100g": "15.0",
        "fiber_g_per_100g": "1.8",
        "standard_serving_amount": "1",
        "standard_serving_unit": "serving",
        "standard_serving_weight_g": "250",
    }
    payload.update(overrides)
    return payload


def _catalog_food(name: str, food_type: str, *, brand: str | None = None) -> Food:
    return Food(
        name=name,
        brand=brand,
        energy_kcal_per_100g=Decimal("100"),
        protein_g_per_100g=Decimal("5"),
        fat_g_per_100g=Decimal("3"),
        carbs_g_per_100g=Decimal("12"),
        food_type=food_type,
        owner_user_id=None,
        provenance="internal",
        source_name="yfc-test",
        trust_level="verified",
        status="active",
    )


def test_personal_food_api_crud_is_private_and_can_feed_diary_without_external_source(
    client,
) -> None:
    owner_headers = _auth(client, 17_001)
    other_headers = _auth(client, 17_002)

    created = client.post(
        "/api/v1/nutrition/foods",
        headers=owner_headers,
        json=_food_payload(barcode="4006381333931"),
    )
    assert created.status_code == 201
    food_id = created.json()["id"]
    assert created.json()["food_type"] == "user"
    assert created.json()["is_favorite"] is False

    assert (
        client.get(f"/api/v1/nutrition/foods/{food_id}", headers=owner_headers).status_code == 200
    )
    assert (
        client.get(f"/api/v1/nutrition/foods/{food_id}", headers=other_headers).status_code == 404
    )
    assert (
        client.patch(
            f"/api/v1/nutrition/foods/{food_id}",
            headers=other_headers,
            json={"name": "Чужое изменение"},
        ).status_code
        == 404
    )

    updated = client.patch(
        f"/api/v1/nutrition/foods/{food_id}",
        headers=owner_headers,
        json={
            "name": "Йогурт домашний",
            "brand": None,
            "standard_serving_amount": None,
            "standard_serving_unit": None,
            "standard_serving_weight_g": None,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Йогурт домашний"
    assert updated.json()["brand"] is None
    assert updated.json()["standard_serving_weight_g"] is None

    duplicate = client.post(
        "/api/v1/nutrition/foods",
        headers=owner_headers,
        json=_food_payload(name="Дубликат", barcode="4006381333931"),
    )
    assert duplicate.status_code == 409
    assert (
        client.post(
            "/api/v1/nutrition/foods",
            headers=other_headers,
            json=_food_payload(name="Такой же штрихкод", barcode="4006381333931"),
        ).status_code
        == 201
    )

    today = timezone_module.today_in_timezone("Europe/Moscow")
    diary_entry = client.post(
        "/api/v1/nutrition/diary/entries",
        headers=owner_headers,
        json={
            "food_id": food_id,
            "diary_date": today.isoformat(),
            "meal_type": "breakfast",
            "amount": "125",
        },
    )
    assert diary_entry.status_code == 201
    assert diary_entry.json()["food_name"] == "Йогурт домашний"

    assert (
        client.delete(f"/api/v1/nutrition/foods/{food_id}", headers=other_headers).status_code
        == 404
    )
    assert (
        client.delete(f"/api/v1/nutrition/foods/{food_id}", headers=owner_headers).status_code
        == 204
    )
    assert (
        client.get(f"/api/v1/nutrition/foods/{food_id}", headers=owner_headers).status_code == 404
    )


def test_favorites_recent_order_and_cross_user_isolation(client) -> None:
    owner_headers = _auth(client, 17_010)
    other_headers = _auth(client, 17_011)
    first_id = client.post(
        "/api/v1/nutrition/foods",
        headers=owner_headers,
        json=_food_payload(name="первый йогурт", barcode=None),
    ).json()["id"]
    second_id = client.post(
        "/api/v1/nutrition/foods",
        headers=owner_headers,
        json=_food_payload(name="второй йогурт", barcode=None),
    ).json()["id"]
    foreign_id = client.post(
        "/api/v1/nutrition/foods",
        headers=other_headers,
        json=_food_payload(name="чужой йогурт", barcode=None),
    ).json()["id"]

    assert (
        client.put(
            f"/api/v1/nutrition/foods/{first_id}/favorite", headers=owner_headers
        ).status_code
        == 200
    )
    repeated = client.put(
        f"/api/v1/nutrition/foods/{first_id}/favorite",
        headers=owner_headers,
    )
    assert repeated.status_code == 200
    assert repeated.json()["is_favorite"] is True
    assert (
        client.put(
            f"/api/v1/nutrition/foods/{foreign_id}/favorite", headers=owner_headers
        ).status_code
        == 404
    )

    today = timezone_module.today_in_timezone("Europe/Moscow").isoformat()
    entry_ids = []
    for food_id in (first_id, second_id):
        response = client.post(
            "/api/v1/nutrition/diary/entries",
            headers=owner_headers,
            json={
                "food_id": food_id,
                "diary_date": today,
                "meal_type": "snacks",
                "amount": "100",
            },
        )
        assert response.status_code == 201
        entry_ids.append(response.json()["id"])
    client.post(
        "/api/v1/nutrition/diary/entries",
        headers=other_headers,
        json={
            "food_id": foreign_id,
            "diary_date": today,
            "meal_type": "snacks",
            "amount": "100",
        },
    )
    with get_session_context() as db:
        first_entry = db.get(FoodDiaryEntry, entry_ids[0])
        second_entry = db.get(FoodDiaryEntry, entry_ids[1])
        assert first_entry is not None and second_entry is not None
        first_entry.updated_at = datetime(2026, 8, 18, 10, 0)
        second_entry.updated_at = datetime(2026, 8, 18, 11, 0)

    recent = client.get("/api/v1/nutrition/foods/recent", headers=owner_headers)
    assert recent.status_code == 200
    assert [item["id"] for item in recent.json()["items"]] == [second_id, first_id]
    assert foreign_id not in {item["id"] for item in recent.json()["items"]}
    search = client.get(
        "/api/v1/nutrition/foods/search",
        headers=owner_headers,
        params={"q": "йогурт"},
    ).json()
    assert {item["id"] for item in search["items"]} == {first_id, second_id}

    favorites = client.get("/api/v1/nutrition/foods/favorites", headers=owner_headers)
    assert favorites.status_code == 200
    assert [item["id"] for item in favorites.json()["items"]] == [first_id]
    assert (
        client.delete(
            f"/api/v1/nutrition/foods/{first_id}/favorite",
            headers=owner_headers,
        ).status_code
        == 204
    )
    assert (
        client.get("/api/v1/nutrition/foods/favorites", headers=owner_headers).json()["total"] == 0
    )


def test_local_search_ranking_normalization_pagination_and_query_bound(client) -> None:
    headers = _auth(client, 17_020)
    recent_id = client.post(
        "/api/v1/nutrition/foods",
        headers=headers,
        json=_food_payload(name="недавний йогурт", barcode=None),
    ).json()["id"]
    own_id = client.post(
        "/api/v1/nutrition/foods",
        headers=headers,
        json=_food_payload(name="личный йогурт", barcode=None),
    ).json()["id"]
    with get_session_context() as db:
        favorite = _catalog_food("избранный йогурт", "branded", brand="Локальная марка")
        system = _catalog_food("системный йогурт", "system")
        branded = _catalog_food("брендовый йогурт", "branded")
        db.add_all([favorite, system, branded])
        db.flush()
        favorite_id, system_id, branded_id = favorite.id, system.id, branded.id

    assert (
        client.put(f"/api/v1/nutrition/foods/{favorite_id}/favorite", headers=headers).status_code
        == 200
    )
    today = timezone_module.today_in_timezone("Europe/Moscow").isoformat()
    assert (
        client.post(
            "/api/v1/nutrition/diary/entries",
            headers=headers,
            json={
                "food_id": recent_id,
                "diary_date": today,
                "meal_type": "lunch",
                "amount": "100",
            },
        ).status_code
        == 201
    )

    response = client.get(
        "/api/v1/nutrition/foods/search",
        headers=headers,
        params={"q": "  ЙОГУРТ  ", "limit": 5},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 5
    assert [item["id"] for item in response.json()["items"]] == [
        recent_id,
        favorite_id,
        own_id,
        system_id,
        branded_id,
    ]
    page = client.get(
        "/api/v1/nutrition/foods/search",
        headers=headers,
        params={"q": "йогурт", "limit": 2, "offset": 2},
    ).json()
    assert page["total"] == 5
    assert [item["id"] for item in page["items"]] == [own_id, system_id]
    assert (
        client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "я"},
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "йогурт", "limit": 51},
        ).status_code
        == 422
    )

    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == 17_020).one()
        token = begin_sql_metrics()
        try:
            direct = search_foods(db, user, "йогурт", limit=20, offset=0)
            metrics = current_sql_metrics()
        finally:
            reset_sql_metrics(token)
    assert direct.total == 5
    assert metrics.query_count == 2


def test_food_library_migration_upgrades_from_diary_head(tmp_path: Path) -> None:
    migration_path = (
        Path(main_module.__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0036_food_library_search.py"
    )
    spec = importlib.util.spec_from_file_location("food_library_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.down_revision == "0035_food_diary"

    engine = create_engine(f"sqlite:///{(tmp_path / 'food-library-migration.db').as_posix()}")
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table(
        "foods",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(256), nullable=False),
        Column("brand", String(128), nullable=True),
        Column("status", String(16), nullable=False),
        Column("food_type", String(16), nullable=False),
    )
    Table(
        "food_diary_entries",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, nullable=False),
        Column("food_id", Integer, nullable=True),
        Column("updated_at", DateTime, nullable=False),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            metadata.tables["foods"].insert(),
            {
                "id": 1,
                "name": "Oat YOGURT",
                "brand": "Brand",
                "status": "active",
                "food_type": "system",
            },
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        schema = inspect(connection)
        assert "food_favorites" in schema.get_table_names()
        assert "search_text" in {column["name"] for column in schema.get_columns("foods")}
        assert {index["name"] for index in schema.get_indexes("food_favorites")} == {
            "ix_food_favorites_user_created"
        }
        assert "ix_food_diary_entries_user_food_updated" in {
            index["name"] for index in schema.get_indexes("food_diary_entries")
        }
        assert "ix_foods_status_type_name" in {
            index["name"] for index in schema.get_indexes("foods")
        }
        upgraded_foods = Table("foods", MetaData(), autoload_with=connection)
        assert (
            connection.execute(
                upgraded_foods.select().with_only_columns(upgraded_foods.c.search_text)
            ).scalar_one()
            == "oat yogurt brand"
        )
        migration.downgrade()
        assert "food_favorites" not in inspect(connection).get_table_names()
        assert "search_text" not in {
            column["name"] for column in inspect(connection).get_columns("foods")
        }

    engine.dispose()
