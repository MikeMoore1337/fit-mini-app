from __future__ import annotations

import re
from urllib.parse import urlencode

SAFE_AUTH_PATHS = frozenset({"/app", "/coach", "/admin"})
SAFE_JOIN_PATH = re.compile(r"/join/[A-Za-z0-9_-]{20,128}\Z")
AUTH_ERROR_CODES = frozenset(
    {
        "unavailable",
        "denied",
        "invalid_state",
        "conflict",
        "blocked",
        "provider_failure",
    }
)
OAUTH_PROVIDERS = frozenset({"telegram", "google", "yandex", "vk", "apple"})


def safe_auth_next_path(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized in SAFE_AUTH_PATHS or SAFE_JOIN_PATH.fullmatch(normalized):
        return normalized
    return None


def auth_error_redirect(code: str, *, next_path: str | None = None) -> str:
    normalized_code = code if code in AUTH_ERROR_CODES else "provider_failure"
    target = safe_auth_next_path(next_path) or "/app"
    return f"/login?{urlencode({'next': target, 'auth_error': normalized_code})}"


def account_link_error_redirect(code: str) -> str:
    normalized_code = code if code in AUTH_ERROR_CODES else "provider_failure"
    return f"/app?{urlencode({'auth_error': normalized_code})}"
