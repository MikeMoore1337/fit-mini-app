from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_env: str = "dev"
    app_name: str = "FitMiniApp"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    database_url: str
    enable_dev_auth: bool = True

    frontend_base_url: str = "http://localhost:8000"
    telegram_bot_token: str = "replace-me"
    telegram_bot_username: str = "replace-me"


settings = Settings()
