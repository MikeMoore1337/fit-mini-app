from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_placeholder_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "change-me", "replace-me", "secret", "test-secret"} or (
        normalized.startswith(("change-", "replace-"))
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_env: Literal["dev", "test", "prod"]
    app_name: str
    app_host: str
    app_port: int
    app_debug: bool

    secret_key: str
    access_token_expire_minutes: int = Field(gt=0, le=24 * 60)
    refresh_token_expire_days: int = Field(gt=0, le=365)
    refresh_cookie_name: str = "fit_refresh_token"

    database_url: str
    enable_dev_auth: bool = False
    admin_telegram_user_ids: str = ""

    frontend_base_url: str = "https://app.your-fitness-coach.ru"
    telegram_bot_token: str
    telegram_bot_username: str = ""
    bot_internal_token: str = ""

    payment_provider: str = "mock"
    payment_public_url: str = ""

    worker_poll_seconds: int = Field(default=10, ge=1, le=3600)
    reminder_sync_seconds: int = Field(default=60, ge=10, le=3600)

    @model_validator(mode="after")
    def validate_production_safety(self) -> Settings:
        if self.app_env != "prod":
            return self

        if _is_placeholder_secret(self.secret_key) or len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters and non-placeholder in prod"
            )
        if _is_placeholder_secret(self.telegram_bot_token):
            raise ValueError("TELEGRAM_BOT_TOKEN must be configured in prod")
        if _is_placeholder_secret(self.bot_internal_token) or len(self.bot_internal_token) < 32:
            raise ValueError(
                "BOT_INTERNAL_TOKEN must be at least 32 characters and non-placeholder in prod"
            )
        if self.enable_dev_auth:
            raise ValueError("ENABLE_DEV_AUTH must be false in prod")
        if self.app_debug:
            raise ValueError("APP_DEBUG must be false in prod")
        _ = self.admin_telegram_id_set

        for name, value in {
            "FRONTEND_BASE_URL": self.frontend_base_url,
            "PAYMENT_PUBLIC_URL": self.payment_public_url or self.frontend_base_url,
        }.items():
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"{name} must be an absolute HTTPS URL in prod")
        return self

    @property
    def admin_telegram_id_set(self) -> set[int]:
        result: set[int] = set()
        for item in self.admin_telegram_user_ids.replace(";", ",").split(","):
            value = item.strip()
            if not value:
                continue
            try:
                result.add(int(value))
            except ValueError as exc:
                raise ValueError(f"Invalid ADMIN_TELEGRAM_USER_IDS value: {value}") from exc
        return result


settings = Settings()
