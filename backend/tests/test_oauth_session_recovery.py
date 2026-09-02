import base64
import json
from datetime import UTC, datetime, timedelta
from time import time
from urllib.parse import parse_qs, quote, urlparse

from itsdangerous import TimestampSigner
from starlette.responses import Response

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.oauth_transaction import OAuthTransaction
from fitminiapp_api.services.jwt import decode_token


class FakeOAuthClient:
    name = "google"

    def __init__(self) -> None:
        self.states: list[str] = []
        self.token_calls = 0

    async def create_authorization_url(self, redirect_uri: str) -> dict[str, str]:
        state = f"google-test-state-{len(self.states) + 1:03d}"
        self.states.append(state)
        return {
            "url": f"https://accounts.example/authorize?state={state}",
            "state": state,
            "code_verifier": "test-code-verifier-which-is-kept-server-side",
            "nonce": "test-nonce-which-is-kept-server-side",
            "redirect_uri": redirect_uri,
        }

    async def authorize_access_token(self, request):
        callback_params = getattr(request.state, "oauth_callback_params", {})
        state = callback_params.get("state")
        assert isinstance(state, str)
        state_data = request.session.pop(f"_state_{self.name}_{state}", None)
        assert isinstance(state_data, dict)
        assert state_data["data"]["code_verifier"] == (
            "test-code-verifier-which-is-kept-server-side"
        )
        assert state_data["data"]["nonce"] == "test-nonce-which-is-kept-server-side"
        self.token_calls += 1
        return {
            "userinfo": {
                "sub": "google-recovery-subject",
                "email": "oauth-recovery@example.com",
                "email_verified": True,
                "name": "OAuth Recovery User",
            }
        }


def _configure_fake_google(monkeypatch, fake: FakeOAuthClient) -> None:
    from fitminiapp_api.api.v1 import auth as auth_api

    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(settings, "google_oauth_client_id", "google-client")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "google-secret")
    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: fake if provider == "google" else None,
    )


def _start(client, *, next_path: str | None = None) -> str:
    path = "/api/v1/auth/oauth/google/start"
    if next_path:
        path += f"?next={quote(next_path, safe='')}"
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["location"]).query)
    return query["state"][0]


def _callback(client, state: str, **params):
    return client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "provider-code", "state": state, **params},
        follow_redirects=False,
    )


def _post_callback(client, state: str, **params):
    return client.post(
        "/api/v1/auth/oauth/google/callback",
        data={"code": "provider-code", "state": state, **params},
        follow_redirects=False,
    )


def test_wrong_state_does_not_exchange_and_retry_completes(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)

    first_state = _start(client, next_path="/coach")
    failed = _callback(client, "attacker-state-value")

    assert failed.status_code == 303
    assert failed.headers["location"] == (
        "/login?next=%2Fapp&auth_error=invalid_state&oauth_provider=google"
    )
    assert fake.token_calls == 0

    second_state = _start(client)
    succeeded = _callback(client, second_state)

    assert succeeded.status_code == 303
    assert succeeded.headers["location"] == "/app"
    assert "access_token" not in succeeded.headers["location"]
    assert "fit_refresh_token=" in succeeded.headers["set-cookie"]
    assert fake.token_calls == 1

    with get_session_context() as db:
        rows = {
            row.state: row.status
            for row in db.query(OAuthTransaction)
            .filter(OAuthTransaction.state.in_([first_state, second_state]))
            .all()
        }
    assert rows[first_state] == "pending"
    assert rows[second_state] == "completed"


def test_sequential_tabs_and_provider_denial_are_isolated(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)

    first_state = _start(client)
    second_state = _start(client)

    assert _callback(client, first_state).headers["location"] == "/app"
    assert _callback(client, second_state).headers["location"] == "/app"
    assert fake.token_calls == 2

    denied_state = _start(client)
    denied = _callback(client, denied_state, error="access_denied")

    assert denied.status_code == 303
    assert denied.headers["location"] == (
        "/login?next=%2Fapp&auth_error=denied&oauth_provider=google"
    )
    assert fake.token_calls == 2
    with get_session_context() as db:
        row = db.query(OAuthTransaction).filter(OAuthTransaction.state == denied_state).one()
        assert row.status == "failed"
        assert row.failure_reason == "provider_denied"


def test_form_post_and_repeated_callback_are_safe(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)

    state = _start(client)
    response = _post_callback(client, state)
    repeated = _callback(client, state)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    assert repeated.status_code == 303
    assert repeated.headers["location"] == (
        "/login?next=%2Fapp&auth_error=invalid_state&oauth_provider=google"
    )
    assert fake.token_calls == 1
    assert settings.refresh_cookie_name not in repeated.headers.get("set-cookie", "")


def test_malformed_and_legacy_oauth_cookies_are_removed(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)

    client.cookies.set(settings.oauth_session_cookie_name, "not-a-valid-signed-cookie")
    malformed = _callback(client, "attacker-state-value")

    assert malformed.status_code == 303
    assert f'{settings.oauth_session_cookie_name}=""' in malformed.headers["set-cookie"]
    assert "Max-Age=0" in malformed.headers["set-cookie"]

    legacy = {
        "_state_google_old-state": {
            "data": {"redirect_uri": "https://app.example/callback"},
            "exp": (datetime.now(UTC) + timedelta(minutes=5)).timestamp(),
        },
        "oauth_next": "/evil",
        "oauth_link_token": "raw-token-that-must-not-return",
    }
    encoded = base64.b64encode(json.dumps(legacy).encode("utf-8"))
    signed = TimestampSigner(settings.secret_key).sign(encoded).decode("utf-8")
    client.cookies.set(settings.oauth_session_cookie_name, signed)

    stale = _callback(client, "attacker-state-value")

    assert stale.status_code == 303
    assert f"{settings.oauth_session_cookie_name}=null" in stale.headers["set-cookie"]
    assert "raw-token-that-must-not-return" not in stale.headers.get("set-cookie", "")
    assert fake.token_calls == 0


def test_expired_and_rotated_oauth_cookies_are_removed(client, monkeypatch):
    _configure_fake_google(monkeypatch, FakeOAuthClient())

    for secret, timestamp in (
        (
            settings.secret_key,
            int(time()) - settings.oauth_transaction_ttl_seconds - 1,
        ),
        ("previous-secret-key-that-is-not-current", None),
    ):
        client.cookies.clear()
        signer = TimestampSigner(secret)
        if timestamp is not None:
            signer.get_timestamp = lambda timestamp=timestamp: timestamp
        client.cookies.set(
            settings.oauth_session_cookie_name,
            signer.sign(base64.b64encode(b"{}")).decode("utf-8"),
        )

        response = _callback(client, "attacker-state-value")

        assert response.status_code == 303
        assert f'{settings.oauth_session_cookie_name}=""' in response.headers["set-cookie"]
        assert "Max-Age=0" in response.headers["set-cookie"]


def test_oauth_cookie_deletion_keeps_prod_attributes_and_refresh_cookie(monkeypatch):
    from fitminiapp_api.api.v1 import auth as auth_api

    monkeypatch.setattr(settings, "app_env", "prod")
    response = Response()

    auth_api._clear_oauth_cookie(response)

    header = response.headers["set-cookie"].lower()
    assert f'{settings.oauth_session_cookie_name}=""' in header
    assert "max-age=0" in header
    assert "path=/" in header
    assert "httponly" in header
    assert "samesite=none" in header
    assert "secure" in header
    assert settings.refresh_cookie_name not in header


def test_expired_transaction_is_not_exchanged(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)
    state = _start(client)

    with get_session_context() as db:
        row = db.query(OAuthTransaction).filter(OAuthTransaction.state == state).one()
        row.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
        db.commit()

    response = _callback(client, state)

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/login?next=%2Fapp&auth_error=invalid_state&oauth_provider=google"
    )
    assert fake.token_calls == 0
    with get_session_context() as db:
        row = db.query(OAuthTransaction).filter(OAuthTransaction.state == state).one()
        assert row.status == "expired"


def test_new_start_prunes_old_terminal_transactions(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)
    state = _start(client)

    with get_session_context() as db:
        row = db.query(OAuthTransaction).filter(OAuthTransaction.state == state).one()
        row.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(
            seconds=settings.oauth_transaction_ttl_seconds + 1
        )
        db.commit()

    replacement_state = _start(client)

    with get_session_context() as db:
        assert (
            db.query(OAuthTransaction).filter(OAuthTransaction.state == state).one_or_none() is None
        )
        assert db.query(OAuthTransaction).filter(OAuthTransaction.state == replacement_state).one()


def test_link_transaction_keeps_refresh_family_and_stores_only_hash(client, monkeypatch):
    fake = FakeOAuthClient()
    _configure_fake_google(monkeypatch, fake)

    login = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": 8_840_101},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    before_cookie = client.cookies.get(settings.refresh_cookie_name)

    created = client.post("/api/v1/me/auth/oauth-link/google", headers=headers)
    assert created.status_code == 200
    raw_token = parse_qs(urlparse(created.json()["oauth_url"]).query)["token"][0]
    started = client.get(created.json()["oauth_url"], follow_redirects=False)
    assert started.status_code == 302
    state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]

    with get_session_context() as db:
        row = db.query(OAuthTransaction).filter(OAuthTransaction.state == state).one()
        assert row.purpose == "link"
        assert row.link_action_token_hash
        assert raw_token not in row.link_action_token_hash
        assert (
            row.session_family_id
            == decode_token(login.json()["access_token"], expected_type="access")["sid"]
        )

    linked = _callback(client, state)

    assert linked.status_code == 303
    assert linked.headers["location"] == "/app?auth_linked=google"
    assert "fit_refresh_token=" not in linked.headers.get("set-cookie", "")
    assert client.cookies.get(settings.refresh_cookie_name) == before_cookie
