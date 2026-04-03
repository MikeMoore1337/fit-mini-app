from app.core.config import settings
from fastapi import APIRouter

router = APIRouter()


@router.get("/public/config")
def public_config():
    return {
        "app_env": settings.APP_ENV,
        "enable_dev_auth": settings.ENABLE_DEV_AUTH,
    }
