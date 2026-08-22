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
    script = ScriptDirectory.from_config(alembic_config)
    expected_revision = script.get_current_head()
    previous_revision = script.get_revision(expected_revision).down_revision
    assert isinstance(previous_revision, str)

    command.upgrade(alembic_config, "head")

    def current_revision() -> str:
        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                return connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
        finally:
            engine.dispose()

    assert current_revision() == expected_revision

    command.downgrade(alembic_config, previous_revision)
    assert current_revision() == previous_revision

    command.upgrade(alembic_config, "head")
    assert current_revision() == expected_revision
