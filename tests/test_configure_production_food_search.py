from pathlib import Path

import pytest
from scripts.configure_production_food_search import configure_production_food_search


def test_enables_food_search_without_changing_secrets(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SECRET_KEY=keep-this-secret\n"
        "FOOD_PROVIDER=disabled\n"
        "OPEN_FOOD_FACTS_USER_AGENT=\n"
        "TELEGRAM_BOT_TOKEN=also-keep-this\n",
        encoding="utf-8",
    )

    configure_production_food_search(env_file)

    assert env_file.read_text(encoding="utf-8") == (
        "SECRET_KEY=keep-this-secret\n"
        "FOOD_PROVIDER=open_food_facts\n"
        "OPEN_FOOD_FACTS_USER_AGENT=YourFitnessCoach/0.1 (https://your-fitness-coach.ru)\n"
        "TELEGRAM_BOT_TOKEN=also-keep-this\n"
    )


def test_adds_missing_flags_once_and_removes_duplicates(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_ENV=prod\nFOOD_PROVIDER=disabled\nFOOD_PROVIDER=disabled\n",
        encoding="utf-8",
    )

    configure_production_food_search(env_file)
    configure_production_food_search(env_file)

    content = env_file.read_text(encoding="utf-8")
    assert content.count("FOOD_PROVIDER=open_food_facts") == 1
    assert content.count("OPEN_FOOD_FACTS_USER_AGENT=YourFitnessCoach/0.1") == 1


def test_refuses_missing_environment_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        configure_production_food_search(tmp_path / ".env")


def test_production_deploy_enables_provider_before_compose_validation() -> None:
    root = Path(__file__).resolve().parents[1]
    deploy = (root / "scripts" / "deploy_production.sh").read_text(encoding="utf-8")

    configure = "python3 scripts/configure_production_food_search.py .env"
    assert configure in deploy
    assert deploy.index(configure) < deploy.index("docker compose config --quiet")
