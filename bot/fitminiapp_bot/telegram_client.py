from aiogram.client.session.aiohttp import AiohttpSession

from .config import settings


def _aiogram_proxy_url(proxy_url: str) -> str:
    # Aiogram always enables remote DNS for SOCKS5, but its parser accepts only
    # the socks5 scheme rather than the conventional socks5h spelling.
    if proxy_url.lower().startswith("socks5h://"):
        return f"socks5://{proxy_url.split('://', 1)[1]}"
    return proxy_url


def create_bot_api_session(*, timeout: int | None = None) -> AiohttpSession:
    """Build a TLS-verifying Bot API session over the configured route."""

    options: dict[str, object] = {}
    if settings.bot_api_proxy_url:
        options["proxy"] = _aiogram_proxy_url(settings.bot_api_proxy_url)
    if timeout is not None:
        options["timeout"] = timeout
    return AiohttpSession(**options)
