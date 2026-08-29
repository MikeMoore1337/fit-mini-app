from pathlib import Path

import pytest
from scripts.normalize_production_news_image_provider import (
    normalize_production_news_image_provider,
)


def test_disables_unsupported_legacy_provider_without_changing_secrets(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SECRET_KEY=keep-this-secret\n"
        "NEWS_IMAGE_PROVIDER=openai\n"
        "NEWS_IMAGE_CLOUDFLARE_API_TOKEN=also-keep-this\n",
        encoding="utf-8",
    )

    provider = normalize_production_news_image_provider(env_file)

    assert provider == "disabled"
    assert env_file.read_text(encoding="utf-8") == (
        "SECRET_KEY=keep-this-secret\n"
        "NEWS_IMAGE_PROVIDER=disabled\n"
        "NEWS_IMAGE_CLOUDFLARE_API_TOKEN=also-keep-this\n"
    )


def test_preserves_supported_provider_and_removes_duplicates(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEWS_IMAGE_PROVIDER=disabled\nNEWS_IMAGE_PROVIDER=cloudflare_workers_ai\n",
        encoding="utf-8",
    )

    first = normalize_production_news_image_provider(env_file)
    second = normalize_production_news_image_provider(env_file)

    assert first == second == "cloudflare_workers_ai"
    assert env_file.read_text(encoding="utf-8") == ("NEWS_IMAGE_PROVIDER=cloudflare_workers_ai\n")


def test_adds_safe_default_when_provider_is_missing(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=prod\n", encoding="utf-8")

    provider = normalize_production_news_image_provider(env_file)

    assert provider == "disabled"
    assert env_file.read_text(encoding="utf-8") == ("APP_ENV=prod\nNEWS_IMAGE_PROVIDER=disabled\n")


def test_refuses_missing_environment_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        normalize_production_news_image_provider(tmp_path / ".env")


def test_production_deploy_normalizes_provider_before_compose_validation() -> None:
    root = Path(__file__).resolve().parents[1]
    deploy = (root / "scripts" / "deploy_production.sh").read_text(encoding="utf-8")

    normalize = "python3 scripts/normalize_production_news_image_provider.py .env"
    assert normalize in deploy
    assert deploy.index(normalize) < deploy.index("docker compose config --quiet")
