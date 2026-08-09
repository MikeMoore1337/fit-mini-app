from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
STRUCTURED_FIELDS = (
    "error_code",
    "retry_seconds",
    "retry_attempt",
)


class JsonFormatter(logging.Formatter):
    """JSON formatter that removes configured secrets and raw HTTP URLs."""

    def __init__(self, *, sensitive_values: tuple[str, ...] = ()) -> None:
        super().__init__()
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
            "service": "telegram-bot",
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


def configure_logging(*, bot_token: str, internal_token: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(sensitive_values=(bot_token, internal_token)),
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
