from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REVISION = sys.argv[1].lower()
WRITE_RESULTS: dict[str, int] = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _send(
        self,
        status: int,
        body: bytes,
        content_type: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in {"/health", "/health/live", "/health/ready"}:
            self._send(200, b'{"status":"ok"}', "application/json")
            return
        if path == "/api/v1/public/config":
            body = json.dumps(
                {
                    "app_env": "prod",
                    "enable_dev_auth": False,
                    "enable_web_auth": True,
                    "enable_email_auth": False,
                }
            ).encode()
            self._send(200, body, "application/json")
            return
        if path == "/api/v1/me":
            self._send(401, b'{"detail":"Not authenticated"}', "application/json")
            return
        if path in {"/", "/app", "/login"}:
            body = (
                f'<div id="root" data-revision="{REVISION}"></div>'
                f'<script src="/assets/app-{REVISION}.js"></script>'
            ).encode()
            self._send(
                200,
                body,
                "text/html; charset=utf-8",
                headers={"Cache-Control": "no-store"},
            )
            return
        if path == f"/assets/app-{REVISION}.js":
            self._send(
                200,
                f'globalThis.release="{REVISION}";'.encode(),
                "text/javascript",
                headers={"Cache-Control": "public, max-age=31536000, immutable"},
            )
            return
        if path == "/session":
            cookie = self.headers.get("Cookie", "")
            if "drill_session=stable" not in cookie:
                self._send(
                    200,
                    b"stable",
                    "text/plain",
                    headers={"Set-Cookie": "drill_session=stable; Path=/; HttpOnly"},
                )
            else:
                self._send(200, b"stable", "text/plain")
            return
        self._send(404, b"missing", "text/plain")

    def do_POST(self) -> None:
        if self.path != "/write":
            self._send(404, b"missing", "text/plain")
            return
        operation_id = self.headers.get("Idempotency-Key", "missing")
        WRITE_RESULTS[operation_id] = WRITE_RESULTS.get(operation_id, 0) + 1
        body = json.dumps(
            {
                "revision": REVISION,
                "operation_id": operation_id,
                "count": WRITE_RESULTS[operation_id],
            }
        ).encode()
        self._send(200, body, "application/json")


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
