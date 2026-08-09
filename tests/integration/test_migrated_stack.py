from __future__ import annotations

import os
import sys
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
        assert '<div id="root"></div>' in frontend.text
        assert public_config.status_code == 200
        assert public_config.json()["app_env"] == "test"
        assert login.status_code == 200

        me = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["telegram_user_id"] == 9_900_001
