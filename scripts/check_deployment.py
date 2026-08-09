"""Read-only smoke check for a deployed FitMiniApp instance."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse


def _read(base_url: str, path: str, *, timeout: float) -> tuple[int, bytes, str]:
    request = urllib.request.Request(
        urljoin(base_url.rstrip("/") + "/", path.lstrip("/")),
        headers={"User-Agent": "fitminiapp-deployment-check/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read(), response.headers.get("content-type", "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="deployment origin, for example https://app.example.com")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="allow plain HTTP for a local/private smoke test",
    )
    args = parser.parse_args()

    parsed = urlparse(args.base_url)
    allowed_schemes = {"https", "http"} if args.allow_http else {"https"}
    if parsed.scheme not in allowed_schemes or not parsed.netloc:
        parser.error("base_url must be an absolute HTTPS URL (or pass --allow-http for local use)")

    try:
        ready_status, ready_body, _ = _read(args.base_url, "/health/ready", timeout=args.timeout)
        ready = json.loads(ready_body)
        if not isinstance(ready, dict) or ready_status != 200 or ready.get("status") != "ok":
            raise RuntimeError(f"readiness returned {ready_status}: {ready!r}")

        config_status, config_body, _ = _read(
            args.base_url,
            "/api/v1/public/config",
            timeout=args.timeout,
        )
        config = json.loads(config_body)
        if not isinstance(config, dict) or config_status != 200 or "app_env" not in config:
            raise RuntimeError(f"public config returned {config_status}: {config!r}")

        app_status, app_body, content_type = _read(args.base_url, "/app", timeout=args.timeout)
        if app_status != 200 or b'<div id="root"></div>' not in app_body:
            raise RuntimeError(f"frontend returned {app_status} without the React root")
        if "text/html" not in content_type:
            raise RuntimeError(f"frontend content type is unexpected: {content_type!r}")
    except (OSError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"Deployment check failed: {exc}", file=sys.stderr)
        return 1

    print(f"Deployment is ready: {args.base_url.rstrip('/')}")
    print(f"Environment reported by API: {config['app_env']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
