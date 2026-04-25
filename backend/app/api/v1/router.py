from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    billing,
    coach,
    me,
    notifications,
    nutrition,
    programs,
    public,
    workouts,
)

api_router = APIRouter(prefix="/v1")

api_router.include_router(public.router, tags=["public"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(coach.router, prefix="/coach", tags=["coach"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
