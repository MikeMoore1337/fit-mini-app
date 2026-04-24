from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_env: str
    app_name: str
    app_host: str
    app_port: int
    app_debug: bool

    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    database_url: str
    enable_dev_auth: bool = False

    frontend_base_url: str = "http://localhost:8000"
    telegram_bot_token: str

    payment_provider: str = "mock"
    payment_public_url: str = ""

    worker_poll_seconds: int = 10


settings = Settings()
