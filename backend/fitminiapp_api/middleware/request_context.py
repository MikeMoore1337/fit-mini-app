from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Awaitable, Callable
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fitminiapp_api.db.performance import (
    begin_sql_metrics,
    current_sql_metrics,
    pool_snapshot,
    reset_sql_metrics,
)
from fitminiapp_api.db.session import engine

logger = logging.getLogger("app.http")
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "")
    if REQUEST_ID_PATTERN.fullmatch(supplied):
        return supplied
    return str(uuid.uuid4())


def _is_health_probe(path: str) -> bool:
    return path == "/health" or path.startswith("/health/")


def _log_request(request: Request, *, status_code: int, started_at: float, rid: str) -> None:
    path = request.url.path
    if _is_health_probe(path):
        return
    sql_metrics = current_sql_metrics()
    logger.info(
        "http_request_completed",
        extra={
            "request_id": rid,
            "method": request.method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            "sql_query_count": sql_metrics.query_count,
            "sql_duration_ms": round(sql_metrics.duration_ms, 3),
            **pool_snapshot(engine),
        },
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """X-Request-ID на запрос и в ответ; базовое логирование после обработки."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = _request_id(request)
        request.state.request_id = rid
        started_at = perf_counter()
        sql_metrics_token = begin_sql_metrics()

        try:
            response = await call_next(request)
        except Exception:
            _log_request(request, status_code=500, started_at=started_at, rid=rid)
            raise
        else:
            response.headers["X-Request-ID"] = rid
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
            response.headers.setdefault(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=()",
            )
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' https://telegram.org; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://t.me "
                "https://*.telegram.org https://*.cdn-telegram.org; connect-src 'self'; "
                "font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; "
                "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org",
            )

            path = request.url.path
            if path.startswith("/assets/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif path.startswith("/static/exercise-guides/"):
                response.headers["Cache-Control"] = (
                    "public, max-age=2592000, stale-while-revalidate=86400"
                )
            elif path.startswith("/api/v1/") and not path.startswith("/api/v1/public/"):
                response.headers["Cache-Control"] = "no-store, private"
                response.headers["Pragma"] = "no-cache"
            if not path.startswith("/static"):
                _log_request(
                    request,
                    status_code=response.status_code,
                    started_at=started_at,
                    rid=rid,
                )
            return response
        finally:
            reset_sql_metrics(sql_metrics_token)
