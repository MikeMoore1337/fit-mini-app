"""Read-only smoke check for a deployed Your Fitness Coach instance."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    content_type: str
    final_url: str
    headers: dict[str, str]


def _read(base_url: str, path: str, *, timeout: float) -> HttpResponse:
    request = urllib.request.Request(
        urljoin(base_url.rstrip("/") + "/", path.lstrip("/")),
        headers={"User-Agent": "fitminiapp-deployment-check/2"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return HttpResponse(
            status=response.status,
            body=response.read(),
            content_type=response.headers.get("content-type", ""),
            final_url=response.geturl(),
            headers={key.lower(): value for key, value in response.headers.items()},
        )


def _expect_same_origin(base_url: str, response: HttpResponse, label: str) -> None:
    expected = urlparse(base_url)
    actual = urlparse(response.final_url)
    if actual.scheme != expected.scheme or actual.netloc != expected.netloc:
        raise RuntimeError(f"{label} escaped the deployment origin: {response.final_url!r}")


def _expect_frontend(response: HttpResponse, label: str) -> None:
    if (
        response.status != 200
        or re.search(rb'<div\s+id=["\']root["\'][^>]*>', response.body) is None
    ):
        raise RuntimeError(f"{label} returned {response.status} without the React root")
    if "text/html" not in response.content_type.lower():
        raise RuntimeError(f"{label} content type is unexpected: {response.content_type!r}")
    cache_control = response.headers.get("cache-control", "").lower()
    if "no-store" not in cache_control:
        raise RuntimeError(f"{label} must be served with no-store HTML caching")


def _first_versioned_asset(document: bytes) -> str:
    match = re.search(rb'(?:src|href)="(/assets/[^"?]+)"', document)
    if match is None:
        raise RuntimeError("frontend HTML contains no versioned /assets/ resource")
    return match.group(1).decode("ascii")


def check_deployment(
    base_url: str,
    *,
    timeout: float,
    expected_environment: str | None = None,
    read=_read,
) -> str:
    ready = read(base_url, "/health/ready", timeout=timeout)
    _expect_same_origin(base_url, ready, "readiness")
    ready_payload = json.loads(ready.body)
    if (
        not isinstance(ready_payload, dict)
        or ready.status != 200
        or ready_payload.get("status") != "ok"
    ):
        raise RuntimeError(f"readiness returned {ready.status}: {ready_payload!r}")

    live = read(base_url, "/health/live", timeout=timeout)
    _expect_same_origin(base_url, live, "liveness")
    live_payload = json.loads(live.body)
    if (
        not isinstance(live_payload, dict)
        or live.status != 200
        or live_payload.get("status") != "ok"
    ):
        raise RuntimeError(f"liveness returned {live.status}: {live_payload!r}")

    config_response = read(base_url, "/api/v1/public/config", timeout=timeout)
    _expect_same_origin(base_url, config_response, "public config")
    config = json.loads(config_response.body)
    if not isinstance(config, dict) or config_response.status != 200 or "app_env" not in config:
        raise RuntimeError(f"public config returned {config_response.status}: {config!r}")
    environment = str(config["app_env"])
    if expected_environment is not None and environment != expected_environment:
        raise RuntimeError(
            f"deployment reports environment {environment!r}, expected {expected_environment!r}"
        )

    app = read(base_url, "/app", timeout=timeout)
    _expect_same_origin(base_url, app, "application shell")
    _expect_frontend(app, "application shell")

    login = read(base_url, "/login", timeout=timeout)
    _expect_same_origin(base_url, login, "browser auth shell")
    _expect_frontend(login, "browser auth shell")

    tma_shell = read(base_url, "/app?tgWebAppPlatform=android", timeout=timeout)
    _expect_same_origin(base_url, tma_shell, "TMA shell")
    _expect_frontend(tma_shell, "TMA shell")

    asset_path = _first_versioned_asset(app.body)
    asset = read(base_url, asset_path, timeout=timeout)
    _expect_same_origin(base_url, asset, "frontend asset")
    if asset.status != 200 or not asset.body:
        raise RuntimeError(f"frontend asset returned {asset.status} or an empty body")
    if "public" not in asset.headers.get("cache-control", "").lower():
        raise RuntimeError("versioned frontend asset is missing public cache semantics")

    return environment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="deployment origin, for example https://app.example.com")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--expected-environment", choices=("dev", "test", "prod"))
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
        environment = check_deployment(
            args.base_url,
            timeout=args.timeout,
            expected_environment=args.expected_environment,
        )
    except (OSError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"Deployment check failed: {exc}", file=sys.stderr)
        return 1

    print(f"Deployment is ready: {args.base_url.rstrip('/')}")
    print(f"Environment reported by API: {environment}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
