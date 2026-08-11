from pathlib import Path

import pytest
from scripts.configure_production_auth import configure_production_auth


def test_configures_web_auth_without_changing_secrets(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SECRET_KEY=keep-this-secret\n"
        "ENABLE_WEB_AUTH=false\n"
        "ENABLE_EMAIL_AUTH=true\n"
        "GOOGLE_OAUTH_CLIENT_SECRET=also-keep-this\n",
        encoding="utf-8",
    )

    configure_production_auth(env_file)

    assert env_file.read_text(encoding="utf-8") == (
        "SECRET_KEY=keep-this-secret\n"
        "ENABLE_WEB_AUTH=true\n"
        "ENABLE_EMAIL_AUTH=false\n"
        "GOOGLE_OAUTH_CLIENT_SECRET=also-keep-this\n"
    )


def test_adds_missing_flags_once_and_removes_duplicates(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_ENV=prod\nENABLE_WEB_AUTH=false\nENABLE_WEB_AUTH=false\n",
        encoding="utf-8",
    )

    configure_production_auth(env_file)
    configure_production_auth(env_file)

    content = env_file.read_text(encoding="utf-8")
    assert content.count("ENABLE_WEB_AUTH=true") == 1
    assert content.count("ENABLE_EMAIL_AUTH=false") == 1


def test_refuses_missing_environment_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        configure_production_auth(tmp_path / ".env")
