import json
import logging
import sys
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from fitminiapp_api.core.logging_config import JsonFormatter
from fitminiapp_api.db.session import engine
from fitminiapp_api.middleware.request_context import RequestContextMiddleware


@contextmanager
def _capture_http_logs(caplog):
    logger = logging.getLogger("app.http")
    previous_disabled = logger.disabled
    previous_propagate = logger.propagate
    # Alembic's in-process replay can disable pre-existing loggers on this worker.
    logger.disabled = False
    logger.propagate = False
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="app.http"):
            yield
    finally:
        logger.removeHandler(caplog.handler)
        logger.disabled = previous_disabled
        logger.propagate = previous_propagate


def test_json_formatter_includes_request_context() -> None:
    record = logging.LogRecord(
        name="app.http",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http_request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.method = "GET"
    record.path = "/api/v1/me"
    record.status_code = 200
    record.duration_ms = 12.345
    record.sql_query_count = 7
    record.sql_duration_ms = 4.321
    record.db_pool_size = 10
    record.db_pool_checked_out = 1
    record.db_pool_overflow = 0

    payload = json.loads(JsonFormatter(service="api").format(record))

    assert payload["service"] == "api"
    assert payload["message"] == "http_request_completed"
    assert payload["request_id"] == "request-123"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/me"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12.345
    assert payload["sql_query_count"] == 7
    assert payload["sql_duration_ms"] == 4.321
    assert payload["db_pool_size"] == 10
    assert payload["db_pool_checked_out"] == 1
    assert payload["db_pool_overflow"] == 0


def test_json_formatter_rejects_arbitrary_values_and_keeps_safe_diagnostics() -> None:
    markers = (
        "private_note_marker",
        "configured-database-password",
        "https://backend.example/private",
        "Иван Иванов",
        "личная заметка",
        "талия 81.4",
        "chat_id=99887766",
    )
    try:
        raise RuntimeError(" ".join(markers))
    except RuntimeError:
        record = logging.LogRecord(
            name="app",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="private_note_marker",
            args=(),
            exc_info=sys.exc_info(),
        )
    record.request_id = "request-safe-123"
    record.reason = "личная заметка"
    record.chat_id = 99887766

    rendered = JsonFormatter(service="api").format(record)
    payload = json.loads(rendered)

    assert payload["message"] == "application_log"
    assert payload["exception_type"] == "RuntimeError"
    assert payload["request_id"] == "request-safe-123"
    assert "exception" not in payload
    assert "reason" not in payload
    assert "chat_id" not in payload
    for marker in markers:
        assert marker not in rendered


def test_request_log_has_duration_and_health_probes_are_quiet(caplog) -> None:
    test_app = FastAPI()
    test_app.add_middleware(RequestContextMiddleware)

    @test_app.get("/example")
    def example() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/health/ready")
    def health_ready() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/profiles/{profile_id}")
    def profile(profile_id: str) -> dict[str, str]:
        return {"profile_id": profile_id}

    with TestClient(test_app) as test_client, _capture_http_logs(caplog):
        response = test_client.get("/example", headers={"X-Request-ID": "edge-123"})
        health_response = test_client.get("/health/ready")
        profile_response = test_client.get("/profiles/private-user-99887766")

    assert response.headers["X-Request-ID"] == "edge-123"
    assert health_response.status_code == 200
    records = [record for record in caplog.records if record.name == "app.http"]
    assert profile_response.status_code == 200
    assert len(records) == 2
    assert records[0].request_id == "edge-123"
    assert records[0].method == "GET"
    assert records[0].path == "/example"
    assert records[0].status_code == 200
    assert records[0].duration_ms >= 0
    assert records[0].sql_query_count == 0
    assert records[0].sql_duration_ms == 0
    assert records[0].db_pool_checked_out >= 0
    assert records[1].path == "/profiles/{profile_id}"
    assert "private-user-99887766" not in records[1].path


def test_request_log_includes_sql_metrics_from_sync_endpoint(caplog) -> None:
    test_app = FastAPI()
    test_app.add_middleware(RequestContextMiddleware)

    @test_app.get("/database-example")
    def database_example() -> dict[str, str]:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}

    with TestClient(test_app) as test_client, _capture_http_logs(caplog):
        response = test_client.get("/database-example")

    assert response.status_code == 200
    records = [record for record in caplog.records if record.name == "app.http"]
    assert len(records) == 1
    assert records[0].sql_query_count == 1
    assert records[0].sql_duration_ms >= 0
