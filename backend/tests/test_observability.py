import json
import logging
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fitminiapp_api.core.logging_config import JsonFormatter
from fitminiapp_api.middleware.request_context import RequestContextMiddleware


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

    payload = json.loads(JsonFormatter(service="api").format(record))

    assert payload["service"] == "api"
    assert payload["message"] == "http_request_completed"
    assert payload["request_id"] == "request-123"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/me"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12.345


def test_json_formatter_redacts_configured_secrets_urls_and_exception() -> None:
    secret = "configured-database-password"
    try:
        raise RuntimeError(f"failed at https://backend.example/path with {secret}")
    except RuntimeError:
        record = logging.LogRecord(
            name="app",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=f"request https://backend.example/path used {secret}",
            args=(),
            exc_info=sys.exc_info(),
        )

    rendered = JsonFormatter(service="api", sensitive_values=(secret,)).format(record)
    payload = json.loads(rendered)

    assert payload["message"] == "request [url] used [redacted]"
    assert "[url]" in payload["exception"]
    assert "[redacted]" in payload["exception"]
    assert secret not in rendered
    assert "backend.example" not in rendered


def test_request_log_has_duration_and_health_probes_are_quiet(caplog) -> None:
    test_app = FastAPI()
    test_app.add_middleware(RequestContextMiddleware)

    @test_app.get("/example")
    def example() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/health/ready")
    def health_ready() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(test_app) as test_client, caplog.at_level(logging.INFO, logger="app.http"):
        response = test_client.get("/example", headers={"X-Request-ID": "edge-123"})
        health_response = test_client.get("/health/ready")

    assert response.headers["X-Request-ID"] == "edge-123"
    assert health_response.status_code == 200
    records = [record for record in caplog.records if record.name == "app.http"]
    assert len(records) == 1
    assert records[0].request_id == "edge-123"
    assert records[0].method == "GET"
    assert records[0].path == "/example"
    assert records[0].status_code == 200
    assert records[0].duration_ms >= 0
