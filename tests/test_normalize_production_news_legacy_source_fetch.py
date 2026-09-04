from pathlib import Path

import pytest
from scripts.normalize_production_news_legacy_source_fetch import (
    normalize_production_news_legacy_source_fetch,
)


def test_disables_legacy_source_fetch_without_changing_other_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEWS_INGESTION_ENABLED=true\n"
        "NEWS_LEGACY_SOURCE_FETCH_ENABLED=true\n"
        "NEWS_AUTO_PUBLISH_LOW_RISK=false\n"
        "SECRET_KEY=keep-this-secret\n",
        encoding="utf-8",
    )

    value = normalize_production_news_legacy_source_fetch(env_file)

    assert value == "false"
    assert env_file.read_text(encoding="utf-8") == (
        "NEWS_INGESTION_ENABLED=true\n"
        "NEWS_LEGACY_SOURCE_FETCH_ENABLED=false\n"
        "NEWS_AUTO_PUBLISH_LOW_RISK=false\n"
        "SECRET_KEY=keep-this-secret\n"
    )


def test_adds_one_disabled_flag_and_is_idempotent(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=prod\n", encoding="utf-8")

    first = normalize_production_news_legacy_source_fetch(env_file)
    second = normalize_production_news_legacy_source_fetch(env_file)

    assert first == second == "false"
    assert env_file.read_text(encoding="utf-8") == (
        "APP_ENV=prod\nNEWS_LEGACY_SOURCE_FETCH_ENABLED=false\n"
    )


def test_removes_duplicate_flag_definitions(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEWS_LEGACY_SOURCE_FETCH_ENABLED=true\nNEWS_LEGACY_SOURCE_FETCH_ENABLED=false\n",
        encoding="utf-8",
    )

    normalize_production_news_legacy_source_fetch(env_file)

    assert env_file.read_text(encoding="utf-8") == ("NEWS_LEGACY_SOURCE_FETCH_ENABLED=false\n")


def test_refuses_missing_environment_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        normalize_production_news_legacy_source_fetch(tmp_path / ".env")


def test_production_deploy_normalizes_flag_before_compose_validation() -> None:
    root = Path(__file__).resolve().parents[1]
    deploy = (root / "scripts" / "deploy_production.sh").read_text(encoding="utf-8")

    normalize = "python3 scripts/normalize_production_news_legacy_source_fetch.py .env"
    assert normalize in deploy
    assert deploy.index(normalize) < deploy.index("docker compose config --quiet")
