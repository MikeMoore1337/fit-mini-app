from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """X-Request-ID на запрос и в ответ; базовое логирование после обработки."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid

        response = await call_next(request)
        response.headers["X-Request-ID"] = rid

        path = request.url.path
        if not path.startswith("/static") and path != "/health":
            logger.info(
                "%s %s -> %s",
                request.method,
                path,
                response.status_code,
                extra={"request_id": rid},
            )
        return response
