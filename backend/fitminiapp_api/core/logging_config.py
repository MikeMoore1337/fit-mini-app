from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
STRUCTURED_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "notification_id",
    "chat_id",
    "delivery_error",
    "provider",
    "reason",
)


class JsonFormatter(logging.Formatter):
    """Small dependency-free JSON formatter for container stdout logs."""

    def __init__(self, *, service: str, sensitive_values: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.service = service
        self.sensitive_values = tuple(
            sorted((value for value in sensitive_values if value), key=len, reverse=True)
        )

    def _sanitize(self, value: object) -> object:
        if not isinstance(value, str):
            return value
        sanitized = value
        for secret in self.sensitive_values:
            sanitized = sanitized.replace(secret, "[redacted]")
        return URL_PATTERN.sub("[url]", sanitized)

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": self._sanitize(record.getMessage()),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = self._sanitize(value)
        if record.exc_info:
            payload["exception"] = self._sanitize(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(
    *,
    debug: bool,
    service: str,
    sensitive_values: tuple[str, ...] = (),
) -> None:
    """Route application and Uvicorn records through one JSON stdout handler."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service=service, sensitive_values=sensitive_values))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Uvicorn installs dedicated text handlers before loading the application.
    # Propagating through root keeps startup, shutdown and application logs uniform.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
