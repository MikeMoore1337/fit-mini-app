from fastapi import APIRouter

from fitminiapp_api.api.v1.router import api_router as api_v1_router

api_router = APIRouter(prefix="/api")
api_router.include_router(api_v1_router)
