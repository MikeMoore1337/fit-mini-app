import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_session_context
from app.middleware.request_context import RequestContextMiddleware
from app.services.seed import seed_demo_data

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.DEBUG if settings.app_debug else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    with get_session_context() as session:
        seed_demo_data(session, include_demo_users=settings.app_env == "dev")
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
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
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.head("/health")
def health_head() -> Response:
    return Response(status_code=200)


@app.get("/app")
def miniapp() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/admin")
def admin_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "admin.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/coach")
def coach_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "coach.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
