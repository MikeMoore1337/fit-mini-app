import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from fitminiapp_api.api.router import api_router
from fitminiapp_api.core.config import settings
from fitminiapp_api.core.logging_config import configure_logging
from fitminiapp_api.core.rate_limit import limiter
from fitminiapp_api.db.session import engine
from fitminiapp_api.middleware.request_context import RequestContextMiddleware

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
EXERCISE_GUIDES_DIR = BACKEND_DIR / "assets" / "exercise-guides"
LOCAL_FRONTEND_DIST_DIR = BACKEND_DIR.parent / "frontend" / "dist"
CONTAINER_FRONTEND_DIST_DIR = Path("/app/frontend-dist")
FRONTEND_DIST_DIR = (
    CONTAINER_FRONTEND_DIST_DIR if CONTAINER_FRONTEND_DIST_DIR.exists() else LOCAL_FRONTEND_DIST_DIR
)

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    configure_logging(
        debug=settings.app_debug,
        service="api",
        sensitive_values=(
            settings.secret_key,
            settings.telegram_bot_token,
            settings.bot_internal_token,
            settings.smtp_password,
            settings.database_url,
        ),
    )
    logger.info("application_started")
    try:
        yield
    finally:
        logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
    docs_url=None if settings.app_env == "prod" else "/docs",
    redoc_url=None if settings.app_env == "prod" else "/redoc",
    openapi_url=None if settings.app_env == "prod" else "/openapi.json",
)

if FRONTEND_DIST_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")),
        name="frontend-assets",
    )
app.mount(
    "/static/exercise-guides",
    StaticFiles(directory=str(EXERCISE_GUIDES_DIR)),
    name="exercise-guides",
)
app.include_router(api_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    # HTTPException и RequestValidationError обрабатываются встроенными хендлерами FastAPI,
    # сюда попадают только остальные исключения.
    rid = getattr(request.state, "request_id", None)
    logger.error("Необработанная ошибка", exc_info=exc, extra={"request_id": rid})
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Внутренняя ошибка сервера",
            "request_id": rid,
        },
        headers={"X-Request-ID": rid} if rid else None,
    )


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.head("/health")
def health_head() -> Response:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return Response(status_code=200)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> dict[str, str]:
    return health()


def _frontend_index() -> FileResponse:
    index = FRONTEND_DIST_DIR / "index.html"
    if not index.exists():
        raise RuntimeError("Frontend build is missing. Run `npm run build` in frontend/.")
    return FileResponse(
        index,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/app")
def miniapp() -> FileResponse:
    return _frontend_index()


@app.get("/")
def landing_page() -> FileResponse:
    return _frontend_index()


@app.get("/admin")
def admin_page() -> FileResponse:
    return _frontend_index()


@app.get("/coach")
def coach_page() -> FileResponse:
    return _frontend_index()


@app.get("/verify-email")
def verify_email_page() -> FileResponse:
    return _frontend_index()


@app.get("/reset-password")
def reset_password_page() -> FileResponse:
    return _frontend_index()
