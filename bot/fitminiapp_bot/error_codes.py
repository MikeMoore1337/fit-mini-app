import httpx
from aiogram.exceptions import TelegramRetryAfter


def safe_error_code(error: Exception) -> str:
    """Return a bounded diagnostic code without serializing secrets or request payloads."""

    if isinstance(error, TelegramRetryAfter):
        return "telegram_rate_limited"
    if isinstance(error, httpx.HTTPStatusError):
        return f"http_status:{error.response.status_code}"
    if isinstance(error, httpx.TimeoutException):
        return "timeout"
    if isinstance(error, httpx.RequestError):
        return "transport_error"
    return f"unexpected:{type(error).__name__}"
