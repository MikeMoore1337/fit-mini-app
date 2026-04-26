from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str = Field(validation_alias=AliasChoices("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"))
    frontend_base_url: str = "https://app.your-fitness-coach.ru"
    backend_internal_url: str = "http://backend:8000"


settings = Settings()
