from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra='ignore')
    bot_token: str = 'replace-me'
    frontend_base_url: str = 'http://localhost:8000'


settings = Settings()
