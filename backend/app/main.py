from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.db.session import get_session_context
from app.services.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_session_context() as session:
        seed_demo_data(session)
    yield


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
app.mount("/app-static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/app")
def miniapp() -> FileResponse:
    return FileResponse(Path("app/static/index.html"))


@app.get("/admin")
def admin_page() -> FileResponse:
    return FileResponse(Path("app/static/admin.html"))
