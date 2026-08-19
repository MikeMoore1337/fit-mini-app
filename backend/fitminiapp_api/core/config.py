from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
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
        hide_input_in_errors=True,
    )

    app_env: Literal["dev", "test", "prod"]
    app_name: str
    app_debug: bool

    secret_key: str
    access_token_expire_minutes: int = Field(gt=0, le=24 * 60)
    refresh_token_expire_days: int = Field(gt=0, le=365)
    refresh_cookie_name: str = "fit_refresh_token"

    database_url: str
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=200)
    db_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)
    db_pool_recycle_seconds: int = Field(default=1800, ge=60, le=86400)
    enable_dev_auth: bool = False
    enable_web_auth: bool = False
    enable_email_auth: bool = False
    admin_telegram_user_ids: str = ""

    app_domain: str = ""
    landing_domain: str = ""
    frontend_base_url: str = "https://app.your-fitness-coach.ru"
    google_site_verification: str = ""
    yandex_verification: str = ""
    telegram_bot_token: str
    telegram_bot_username: str = ""
    telegram_init_data_max_age_seconds: int = Field(default=300, ge=60, le=3600)
    bot_internal_token: str = ""

    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_starttls: bool = True
    smtp_use_ssl: bool = False

    telegram_oauth_client_id: str = ""
    telegram_oauth_client_secret: str = ""
    oauth_http_timeout_seconds: float = Field(default=15, ge=5, le=60)
    oauth_force_ipv4: bool = True
    oauth_proxy_url: str = ""
    telegram_oauth_proxy_url: str = ""
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    yandex_oauth_client_id: str = ""
    yandex_oauth_client_secret: str = ""
    vk_oauth_client_id: str = ""
    apple_oauth_client_id: str = ""
    apple_oauth_client_secret: str = ""

    food_provider: Literal["disabled", "open_food_facts"] = "disabled"
    open_food_facts_user_agent: str = ""
    food_provider_timeout_seconds: float = Field(default=4, ge=1, le=15)

    worker_poll_seconds: int = Field(default=10, ge=1, le=3600)
    reminder_sync_seconds: int = Field(default=60, ge=10, le=3600)
    notification_delivery_concurrency: int = Field(default=8, ge=1, le=30)

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
        if self.enable_email_auth and (
            not self.smtp_host.strip() or not self.smtp_from_email.strip()
        ):
            raise ValueError(
                "SMTP_HOST and SMTP_FROM_EMAIL must be configured when email auth is enabled in prod"
            )
        if (
            self.enable_web_auth
            and "telegram" in self.oauth_provider_names
            and not self.telegram_oauth_proxy_url
        ):
            raise ValueError(
                "TELEGRAM_OAUTH_PROXY_URL must be configured when Telegram browser OAuth "
                "is enabled in prod"
            )
        _ = self.admin_telegram_id_set

        parsed = urlparse(self.frontend_base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("FRONTEND_BASE_URL must be an absolute HTTPS URL in prod")
        return self

    @model_validator(mode="after")
    def validate_food_provider(self) -> Settings:
        if self.food_provider == "disabled":
            return self
        user_agent = self.open_food_facts_user_agent.strip()
        if (
            not user_agent
            or "/" not in user_agent
            or "(" not in user_agent
            or ")" not in user_agent
        ):
            raise ValueError(
                "OPEN_FOOD_FACTS_USER_AGENT must identify the app, version, and contact"
            )
        return self

    @field_validator("open_food_facts_user_agent")
    @classmethod
    def normalize_open_food_facts_user_agent(cls, value: str) -> str:
        normalized = value.strip()
        if "\r" in normalized or "\n" in normalized or len(normalized) > 256:
            raise ValueError(
                "OPEN_FOOD_FACTS_USER_AGENT must be a single line up to 256 characters"
            )
        return normalized

    @field_validator("oauth_proxy_url", "telegram_oauth_proxy_url")
    @classmethod
    def validate_oauth_proxy_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return ""
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https", "socks5", "socks5h"} or not parsed.hostname:
            raise ValueError("OAuth proxy URL must be an absolute HTTP(S) or SOCKS5 URL")
        if parsed.query or parsed.fragment:
            raise ValueError("OAuth proxy URL must not contain query parameters or a fragment")
        return normalized

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

    @property
    def oauth_provider_names(self) -> list[str]:
        configured = [
            (
                "telegram",
                bool(
                    self.telegram_oauth_client_id.strip()
                    and self.telegram_oauth_client_secret.strip()
                ),
            ),
            (
                "google",
                bool(
                    self.google_oauth_client_id.strip() and self.google_oauth_client_secret.strip()
                ),
            ),
            (
                "yandex",
                bool(
                    self.yandex_oauth_client_id.strip() and self.yandex_oauth_client_secret.strip()
                ),
            ),
            ("vk", bool(self.vk_oauth_client_id.strip())),
            (
                "apple",
                bool(self.apple_oauth_client_id.strip() and self.apple_oauth_client_secret.strip()),
            ),
        ]
        return [name for name, enabled in configured if enabled]


settings = Settings()
