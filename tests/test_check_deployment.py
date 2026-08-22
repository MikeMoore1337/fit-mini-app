from __future__ import annotations

import json
import sys

import pytest
from scripts import check_deployment


def _fake_read(config: dict[str, object]):
    responses = {
        "/health/ready": (200, b'{"status":"ok"}', "application/json"),
        "/api/v1/public/config": (
            200,
            json.dumps(config).encode(),
            "application/json",
        ),
        "/app": (200, b'<div id="root"></div>', "text/html; charset=utf-8"),
    }

    def read(_base_url: str, path: str, *, timeout: float) -> tuple[int, bytes, str]:
        assert timeout == 10.0
        return responses[path]

    return read


def test_production_smoke_requires_safe_environment_and_auth_flags(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        check_deployment,
        "_read",
        _fake_read(
            {
                "app_env": "prod",
                "enable_dev_auth": False,
                "enable_web_auth": True,
                "enable_email_auth": False,
            }
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_deployment.py", "https://app.example.test", "--expect-app-env", "prod"],
    )

    assert check_deployment.main() == 0
    assert "Environment reported by API: prod" in capsys.readouterr().out


@pytest.mark.parametrize(
    "config, expected_error",
    [
        (
            {
                "app_env": "test",
                "enable_dev_auth": False,
                "enable_web_auth": True,
                "enable_email_auth": False,
            },
            "expected 'prod'",
        ),
        (
            {
                "app_env": "prod",
                "enable_dev_auth": True,
                "enable_web_auth": True,
                "enable_email_auth": False,
            },
            "production auth flags are unsafe",
        ),
    ],
)
def test_production_smoke_rejects_unsafe_public_config(
    config: dict[str, object],
    expected_error: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(check_deployment, "_read", _fake_read(config))
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_deployment.py", "https://app.example.test", "--expect-app-env", "prod"],
    )

    assert check_deployment.main() == 1
    assert expected_error in capsys.readouterr().err
