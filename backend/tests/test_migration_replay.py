from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from alembic import command


def test_sqlite_migration_history_replays_to_head(tmp_path: Path, monkeypatch) -> None:
    from fitminiapp_api.core import config as app_config

    root = Path(__file__).resolve().parents[2]
    database_path = tmp_path / "migration-replay.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    alembic_config = Config(str(root / "backend" / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(root / "backend" / "alembic"))
    monkeypatch.setattr(app_config.settings, "database_url", database_url)
    expected_revision = ScriptDirectory.from_config(alembic_config).get_current_head()

    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
    finally:
        engine.dispose()

    assert revision == expected_revision
