from fastapi import APIRouter

from fitminiapp_api.core.config import settings

router = APIRouter()


@router.get("/public/config")
def public_config() -> dict[str, str | bool | list[str]]:
    return {
        "app_env": settings.app_env,
        "enable_dev_auth": settings.enable_dev_auth,
        "enable_web_auth": settings.enable_web_auth,
        "telegram_bot_username": settings.telegram_bot_username,
        "oauth_providers": settings.oauth_provider_names if settings.enable_web_auth else [],
    }
