from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SupportSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    support_bot_token: str = ""
    support_admin_telegram_user_ids: str = ""
    support_bot_enabled: bool = False
    support_bot_polling_timeout: int = Field(default=30, ge=10, le=60)

    @property
    def admin_telegram_id_set(self) -> set[int]:
        result: set[int] = set()
        for item in self.support_admin_telegram_user_ids.replace(";", ",").split(","):
            value = item.strip()
            if not value:
                continue
            try:
                result.add(int(value))
            except ValueError as exc:
                raise ValueError(f"Invalid SUPPORT_ADMIN_TELEGRAM_USER_IDS value: {value}") from exc
        return result


settings = SupportSettings()
