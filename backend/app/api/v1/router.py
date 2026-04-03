from fastapi import APIRouter

from app.api.v1 import admin, auth, billing, me, notifications, programs, workouts

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(programs.router)
api_router.include_router(workouts.router)
api_router.include_router(billing.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
