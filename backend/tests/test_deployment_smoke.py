from pathlib import Path

import pytest
from scripts.check_deployment import HttpResponse, check_deployment

BASE_URL = "https://app.example.test"
HTML = b'<html><body><div id="root"></div><script src="/assets/app-abc.js"></script></body></html>'


def _response(
    path: str,
    *,
    body: bytes,
    content_type: str,
    cache_control: str = "no-store",
    final_url: str | None = None,
) -> HttpResponse:
    return HttpResponse(
        status=200,
        body=body,
        content_type=content_type,
        final_url=final_url or f"{BASE_URL}{path}",
        headers={"cache-control": cache_control},
    )


def test_deployment_smoke_covers_health_auth_tma_and_versioned_asset() -> None:
    responses = {
        "/health/ready": _response(
            "/health/ready", body=b'{"status":"ok"}', content_type="application/json"
        ),
        "/health/live": _response(
            "/health/live", body=b'{"status":"ok"}', content_type="application/json"
        ),
        "/api/v1/public/config": _response(
            "/api/v1/public/config",
            body=(
                b'{"app_env":"prod","enable_dev_auth":false,'
                b'"enable_web_auth":true,"enable_email_auth":false}'
            ),
            content_type="application/json",
        ),
        "/app": _response("/app", body=HTML, content_type="text/html"),
        "/login": _response("/login", body=HTML, content_type="text/html"),
        "/app?tgWebAppPlatform=android": _response(
            "/app?tgWebAppPlatform=android", body=HTML, content_type="text/html"
        ),
        "/assets/app-abc.js": _response(
            "/assets/app-abc.js",
            body=b"export {};",
            content_type="text/javascript",
            cache_control="public, max-age=31536000, immutable",
        ),
    }

    def read(_base_url: str, path: str, *, timeout: float) -> HttpResponse:
        assert timeout == 3
        return responses[path]

    assert (
        check_deployment(
            BASE_URL,
            timeout=3,
            expected_environment="prod",
            read=read,
        )
        == "prod"
    )


def test_deployment_smoke_rejects_origin_escape() -> None:
    def read(_base_url: str, path: str, *, timeout: float) -> HttpResponse:
        del timeout
        return _response(
            path,
            body=b'{"status":"ok"}',
            content_type="application/json",
            final_url="http://internal.example.test/health/ready",
        )

    with pytest.raises(RuntimeError, match="escaped the deployment origin"):
        check_deployment(BASE_URL, timeout=3, read=read)


def test_production_deploy_is_fail_closed_before_backup_and_runs_public_smoke() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "deploy_production.sh").read_text(
        encoding="utf-8"
    )

    digest_gate = script.index("require_digest_ref POSTGRES_IMAGE")
    runtime_gate = script.index("Validating fail-closed production runtime configuration")
    backup = script.index("Creating a pre-deploy database backup")
    rollout = script.index("docker compose up")

    assert digest_gate < runtime_gate < backup < rollout
    assert 'check_deployment.py "$BASE_URL" --expected-environment prod' in script
    assert 'check_seo_surface.py "$PUBLIC_BASE_URL"' in script
