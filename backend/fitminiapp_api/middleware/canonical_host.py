from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from fitminiapp_api.core.config import settings

APPLICATION_PATHS = frozenset(
    {
        "/app",
        "/admin",
        "/coach",
        "/verify-email",
        "/reset-password",
    }
)
APPLICATION_PATH_PREFIXES = ("/api/", "/join/")


def _is_application_path(path: str) -> bool:
    return path in APPLICATION_PATHS or path.startswith(APPLICATION_PATH_PREFIXES)


async def redirect_landing_application_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Keep browser sessions on the canonical application origin."""

    landing_domain = settings.landing_domain.strip().lower().rstrip(".")
    request_host = (request.url.hostname or "").lower().rstrip(".")
    if landing_domain and request_host == landing_domain and _is_application_path(request.url.path):
        target = f"{settings.frontend_base_url.rstrip('/')}{request.url.path}"
        if request.url.query:
            target = f"{target}?{request.url.query}"
        return RedirectResponse(target, status_code=308)
    return await call_next(request)
