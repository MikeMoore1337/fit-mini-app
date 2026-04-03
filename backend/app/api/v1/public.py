from app.core.config import settings
from fastapi import APIRouter

router = APIRouter()


@router.get("/public/config")
def public_config() -> dict[str, str | bool]:
    return {
        "app_env": settings.app_env,
        "enable_dev_auth": settings.enable_dev_auth,
    }
