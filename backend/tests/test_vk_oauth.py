import json
from urllib.parse import parse_qs, urlparse

import httpx

from fitminiapp_api.core.config import settings
from fitminiapp_api.services.oauth_login import normalize_oauth_claims


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _vk_transport(
    monkeypatch,
    *,
    user_id: str = "vk-user-001",
    mismatched_token_state: bool = False,
):
    from fitminiapp_api.services import oauth_login

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth2/auth":
            query = parse_qs(request.url.query.decode())
            assert query["grant_type"] == ["authorization_code"]
            assert query["client_id"] == ["vk-client"]
            assert query["device_id"] == ["test-device"]
            assert len(query["code_verifier"][0]) >= 43
            body = parse_qs(request.content.decode())
            assert body == {"code": ["test-code"]}
            return httpx.Response(
                200,
                json={
                    "access_token": "vk-access-token",
                    "state": "different-state" if mismatched_token_state else query["state"][0],
                },
            )
        if request.url.path == "/oauth2/user_info":
            assert parse_qs(request.url.query.decode())["client_id"] == ["vk-client"]
            assert parse_qs(request.content.decode()) == {"access_token": ["vk-access-token"]}
            return httpx.Response(
                200,
                json={
                    "user": {
                        "user_id": user_id,
                        "email": "vk-owner@example.com",
                        "first_name": "VK",
                        "last_name": "Owner",
                        "avatar": "https://example.com/avatar.jpg",
                    }
                },
            )
        return httpx.Response(404)

    monkeypatch.setattr(
        oauth_login,
        "oauth_transport_options",
        lambda: {"transport": httpx.MockTransport(handler)},
    )
    return requests


def _start_vk(client, path: str = "/api/v1/auth/oauth/vk/start") -> str:
    started = client.get(path, follow_redirects=False)
    assert started.status_code == 302
    authorization_url = urlparse(started.headers["location"])
    assert authorization_url.scheme == "https"
    assert authorization_url.netloc == "id.vk.ru"
    assert authorization_url.path == "/authorize"
    query = parse_qs(authorization_url.query)
    assert query["client_id"] == ["vk-client"]
    assert query["scope"] == ["email"]
    assert query["code_challenge_method"] == ["s256"]
    assert len(query["code_challenge"][0]) == 43
    return query["state"][0]


def _finish_vk(client, state: str):
    return client.get(
        "/api/v1/auth/oauth/vk/callback",
        params={"code": "test-code", "device_id": "test-device", "state": state},
        follow_redirects=False,
    )


def test_vk_oauth_login_uses_pkce_and_creates_browser_session(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "telegram_oauth_client_id", "")
    monkeypatch.setattr(settings, "telegram_oauth_client_secret", "")
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch)

    state = _start_vk(client)
    callback = _finish_vk(client, state)

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app"
    assert "fit_refresh_token=" in callback.headers["set-cookie"]
    assert [request.url.path for request in requests] == ["/oauth2/auth", "/oauth2/user_info"]

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    me = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["auth_providers"] == ["vk"]
    assert me.json()["profile"]["full_name"] == "VK Owner"


def test_telegram_profile_can_explicitly_link_vk_login(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    _vk_transport(monkeypatch, user_id="vk-link-subject")
    telegram_headers = _auth(client, telegram_user_id=8_830_001)
    telegram_user = client.get("/api/v1/me", headers=telegram_headers).json()

    created = client.post("/api/v1/me/auth/oauth-link/vk", headers=telegram_headers)
    assert created.status_code == 200
    assert created.json()["expires_in_seconds"] == 600

    state = _start_vk(client, created.json()["oauth_url"])
    callback = _finish_vk(client, state)

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app?auth_linked=vk"
    me = client.get("/api/v1/me", headers=telegram_headers).json()
    assert me["id"] == telegram_user["id"]
    assert me["telegram_user_id"] == 8_830_001
    assert me["auth_providers"] == ["telegram", "vk"]


def test_vk_claims_require_a_stable_user_id():
    assert normalize_oauth_claims("vk", {"email": "missing-id@example.com"})["subject"] == ""


def test_public_config_exposes_requested_oauth_providers_in_ui_order(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "telegram_oauth_client_id", "")
    monkeypatch.setattr(settings, "telegram_oauth_client_secret", "")
    monkeypatch.setattr(settings, "google_oauth_client_id", "google-client")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "google-secret")
    monkeypatch.setattr(settings, "yandex_oauth_client_id", "yandex-client")
    monkeypatch.setattr(settings, "yandex_oauth_client_secret", "yandex-secret")
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")

    response = client.get("/api/v1/public/config")

    assert response.status_code == 200
    assert response.json()["oauth_providers"] == ["google", "yandex", "vk"]


def test_vk_oauth_rejects_callback_with_wrong_state_without_network_call(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch)

    _start_vk(client)
    callback = _finish_vk(client, "attacker-state")

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app?auth_error=invalid_state"
    assert requests == []


def test_vk_oauth_session_cookie_stays_bounded_after_repeated_starts(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")

    for _ in range(20):
        _start_vk(client)

    session_cookie = client.cookies.get("fit_oauth_session")
    assert session_cookie is not None
    assert len(session_cookie) < 1024


def test_vk_oauth_accepts_json_payload_callback_variant(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch, user_id="vk-json-payload-user")
    state = _start_vk(client)

    callback = client.get(
        "/api/v1/auth/oauth/vk/callback",
        params={
            "payload": json.dumps(
                {
                    "type": "code_v2",
                    "code": "test-code",
                    "device_id": "test-device",
                    "state": state,
                }
            )
        },
        follow_redirects=False,
    )

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app"
    assert [request.url.path for request in requests] == ["/oauth2/auth", "/oauth2/user_info"]


def test_vk_oauth_rejects_missing_device_without_network_call(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch)
    state = _start_vk(client)

    callback = client.get(
        "/api/v1/auth/oauth/vk/callback",
        params={"code": "test-code", "state": state},
        follow_redirects=False,
    )

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app?auth_error=provider_failure"
    assert requests == []


def test_vk_oauth_rejects_conflicting_flat_and_payload_state(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch)
    state = _start_vk(client)

    callback = client.get(
        "/api/v1/auth/oauth/vk/callback",
        params={
            "state": state,
            "payload": json.dumps(
                {
                    "code": "test-code",
                    "device_id": "test-device",
                    "state": "attacker-state",
                }
            ),
        },
        follow_redirects=False,
    )

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app?auth_error=invalid_state"
    assert requests == []


def test_vk_oauth_rejects_mismatched_token_state(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch, mismatched_token_state=True)
    state = _start_vk(client)

    callback = _finish_vk(client, state)

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app?auth_error=invalid_state"
    assert [request.url.path for request in requests] == ["/oauth2/auth"]


def test_vk_oauth_json_payload_cancel_is_normalized(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "vk_oauth_client_id", "vk-client")
    requests = _vk_transport(monkeypatch)
    _start_vk(client)

    callback = client.get(
        "/api/v1/auth/oauth/vk/callback",
        params={"payload": json.dumps({"error": "access_denied"})},
        follow_redirects=False,
    )

    assert callback.status_code == 303
    assert callback.headers["location"] == "/app?auth_error=denied"
    assert requests == []
