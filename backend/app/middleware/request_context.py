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
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' https://telegram.org "
            "'sha256-3m1gKcj65gT2KV/P9rZQ5zLb6LcF9QxmPKwUThveNeU=' "
            "'sha256-w+SoYpK8BvsqYpHeOkmkyMAVjznFJesDnyaa7MXPJcE=' "
            "'sha256-IhR9LI5auG7rssnWFs5yOAMKXOGr8Ract51Byz4quhc=' "
            "'sha256-qZ9Yq8gtZkgu5ry8phv1nJ9TDNKl5ITFOiv5Danv/DE='; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://t.me "
            "https://*.telegram.org; connect-src 'self'; "
            "font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org",
        )

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
