from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        hide_input_in_errors=True,
    )

    bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    frontend_base_url: str = "https://app.your-fitness-coach.ru"
    backend_internal_url: str = "http://backend:8000"
    bot_internal_token: str
    bot_polling_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("BOT_POLLING_ENABLED", "TELEGRAM_BOT_POLLING_ENABLED"),
    )
    bot_polling_lock_dir: str = "/var/lock/fitminiapp-bot"
    bot_conflict_retry_seconds: int = Field(default=300, ge=30)
    admin_telegram_user_ids: str = ""

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

    @model_validator(mode="after")
    def validate_admin_ids(self) -> Settings:
        _ = self.admin_telegram_id_set
        return self


settings = Settings()
