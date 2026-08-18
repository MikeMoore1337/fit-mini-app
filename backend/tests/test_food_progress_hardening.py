from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import (
    Column,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    select,
)

from fitminiapp_api import main as main_module


def test_food_progress_hardening_migration_upgrades_and_downgrades(tmp_path: Path) -> None:
    migration_path = (
        Path(main_module.__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0038_food_progress_hardening.py"
    )
    spec = importlib.util.spec_from_file_location("food_progress_hardening", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.down_revision == "0037_recipes_copying"

    engine = create_engine(f"sqlite:///{(tmp_path / 'food-progress-hardening.db').as_posix()}")
    metadata = MetaData()
    foods = Table(
        "foods",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(256), nullable=False),
        Column("brand", String(128), nullable=True),
        Column("search_text", String(1024), nullable=False),
    )
    coach_clients = Table(
        "coach_clients",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("coach_user_id", Integer, nullable=False),
        Column("client_user_id", Integer, nullable=False),
        Column("status", String(16), nullable=False),
    )
    Index(
        "ix_coach_clients_coach_status",
        coach_clients.c.coach_user_id,
        coach_clients.c.status,
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            foods.insert(),
            {
                "id": 1,
                "name": "Straße",
                "brand": "Test",
                "search_text": "straße test",
            },
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        schema = inspect(connection)
        assert "ix_foods_search_text_trgm" in {
            index["name"] for index in schema.get_indexes("foods")
        }
        assert "ix_coach_clients_coach_status" not in {
            index["name"] for index in schema.get_indexes("coach_clients")
        }
        assert "ix_coach_clients_coach_status_client" in {
            index["name"] for index in schema.get_indexes("coach_clients")
        }
        assert connection.execute(select(foods.c.search_text)).scalar_one() == "strasse test"

        migration.downgrade()
        schema = inspect(connection)
        assert "ix_foods_search_text_trgm" not in {
            index["name"] for index in schema.get_indexes("foods")
        }
        assert "ix_coach_clients_coach_status" in {
            index["name"] for index in schema.get_indexes("coach_clients")
        }
        assert "ix_coach_clients_coach_status_client" not in {
            index["name"] for index in schema.get_indexes("coach_clients")
        }

    engine.dispose()
