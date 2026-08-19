from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
SAFE_CODE_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,127}\Z")
SAFE_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")
SAFE_METHOD_PATTERN = re.compile(r"[A-Z]{3,10}\Z")
SAFE_ROUTE_PATTERN = re.compile(r"(?:/[A-Za-z0-9_./{}:-]{0,255}|unmatched)\Z")
SAFE_EVENT_NAMES = frozenset(
    {
        "application_started",
        "application_stopped",
        "auth_email_delivery_failed",
        "food_provider_barcode_unavailable",
        "food_provider_search_unavailable",
        "http_request_completed",
        "http_request_rejected",
        "notification_delivery_failed",
        "oauth_link_conflict",
        "oauth_link_failed",
        "oauth_link_start_failed",
        "oauth_login_blocked",
        "oauth_login_failed",
        "oauth_start_failed",
        "telegram_auth_rejected",
        "telegram_delivery_skipped",
        "unhandled_exception",
        "worker_started",
    }
)
SAFE_PROVIDER_NAMES = frozenset({"apple", "google", "open_food_facts", "telegram", "vk", "yandex"})
STRUCTURED_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "sql_query_count",
    "sql_duration_ms",
    "db_pool_size",
    "db_pool_checked_out",
    "db_pool_overflow",
    "body_limit_bytes",
    "notification_ref",
    "delivery_error",
    "provider",
    "reason",
)
INTEGER_FIELDS = {
    "status_code",
    "sql_query_count",
    "db_pool_size",
    "db_pool_checked_out",
    "db_pool_overflow",
    "body_limit_bytes",
}
FLOAT_FIELDS = {"duration_ms", "sql_duration_ms"}
CODE_FIELDS = {"notification_ref", "delivery_error", "reason"}


class JsonFormatter(logging.Formatter):
    """Small dependency-free JSON formatter for container stdout logs."""

    def __init__(
        self,
        *,
        service: str,
        sensitive_values: tuple[str, ...] = (),
        include_exception_details: bool = False,
    ) -> None:
        super().__init__()
        self.service = service
        self.include_exception_details = include_exception_details
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

    def _event_name(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, str) and record.msg in SAFE_EVENT_NAMES:
            return record.msg
        return "application_log"

    def _structured_value(self, field: str, value: object) -> object | None:
        if field in INTEGER_FIELDS:
            return (
                value
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0
                else None
            )
        if field in FLOAT_FIELDS:
            return (
                value
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0
                else None
            )
        if not isinstance(value, str):
            return None
        if field == "request_id":
            return value if SAFE_REQUEST_ID_PATTERN.fullmatch(value) else None
        if field == "method":
            return value if SAFE_METHOD_PATTERN.fullmatch(value) else None
        if field == "path":
            return value if SAFE_ROUTE_PATTERN.fullmatch(value) else None
        if field == "provider":
            return value if value in SAFE_PROVIDER_NAMES else None
        if field in CODE_FIELDS:
            return value if SAFE_CODE_PATTERN.fullmatch(value) else None
        return None

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": self._event_name(record),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                safe_value = self._structured_value(field, value)
                if safe_value is not None:
                    payload[field] = safe_value
        if record.exc_info:
            exception_class = record.exc_info[0]
            if exception_class is not None and SAFE_CODE_PATTERN.fullmatch(
                exception_class.__name__
            ):
                payload["exception_type"] = exception_class.__name__
            if self.include_exception_details:
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
    handler.setFormatter(
        JsonFormatter(
            service=service,
            sensitive_values=sensitive_values,
            include_exception_details=debug,
        )
    )

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
