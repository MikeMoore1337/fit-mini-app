import runpy
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace


def test_alembic_env_accepts_percent_encoded_database_url(monkeypatch) -> None:
    from alembic import context
    from fitminiapp_api.core import config as app_config

    root = Path(__file__).resolve().parents[2]
    captured: dict[str, str] = {}
    fake_config = SimpleNamespace(
        config_file_name=None,
        config_ini_section="alembic",
        set_main_option=lambda key, value: captured.setdefault(key, value),
        get_main_option=lambda key: captured[key],
    )
    monkeypatch.setattr(context, "config", fake_config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", lambda: True)
    monkeypatch.setattr(context, "configure", lambda **_kwargs: None)
    monkeypatch.setattr(context, "begin_transaction", nullcontext)
    monkeypatch.setattr(context, "run_migrations", lambda: None)
    monkeypatch.setattr(
        app_config.settings,
        "database_url",
        "postgresql+psycopg://app:encoded%21password@db/app",
    )

    runpy.run_path(str(root / "backend" / "alembic" / "env.py"))

    assert captured["sqlalchemy.url"] == ("postgresql+psycopg://app:encoded%%21password@db/app")
