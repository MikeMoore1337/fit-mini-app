from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.http")
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "")
    if REQUEST_ID_PATTERN.fullmatch(supplied):
        return supplied
    return str(uuid.uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    """X-Request-ID на запрос и в ответ; базовое логирование после обработки."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = _request_id(request)
        request.state.request_id = rid

        response = await call_next(request)
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
            "https://*.telegram.org; connect-src 'self'; "
            "font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org",
        )

        path = request.url.path
        if path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/static/exercise-guides/"):
            response.headers["Cache-Control"] = "public, max-age=2592000"
        if not path.startswith("/static") and path != "/health":
            logger.info(
                "%s %s -> %s",
                request.method,
                path,
                response.status_code,
                extra={"request_id": rid},
            )
        return response
