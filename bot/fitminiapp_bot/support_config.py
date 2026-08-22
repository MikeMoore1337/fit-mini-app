from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SupportSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        hide_input_in_errors=True,
    )

    support_bot_token: str = ""
    support_bot_enabled: bool = False
    support_bot_polling_timeout: int = Field(default=30, ge=10, le=60)


settings = SupportSettings()
