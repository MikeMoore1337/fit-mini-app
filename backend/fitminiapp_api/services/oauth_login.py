from __future__ import annotations

import base64
import hashlib
import json
import secrets
from hmac import compare_digest
from typing import Any
from urllib.parse import urlencode

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.services.auth_identities import IdentityConflictError, ensure_auth_identity
from fitminiapp_api.services.password_auth import utcnow
from fitminiapp_api.services.telegram_auth import normalize_telegram_username

oauth = OAuth()

VK_AUTHORIZE_URL = "https://id.vk.ru/authorize"
VK_TOKEN_URL = "https://id.vk.ru/oauth2/auth"
VK_USER_INFO_URL = "https://id.vk.ru/oauth2/user_info"
VK_SCOPE = "email"
VK_SESSION_KEY = "vk_oauth"


class OAuthAccountBlockedError(RuntimeError):
    pass


class OAuthStateError(RuntimeError):
    pass


class OAuthProviderResponseError(RuntimeError):
    def __init__(self, error: str) -> None:
        super().__init__("OAuth provider returned an authorization error")
        self.error = error


def oauth_transport_options(*, proxy_url: str | None = None) -> dict[str, object]:
    """Return isolated HTTPX options for a short-lived OAuth client."""

    configured_proxy_url = settings.oauth_proxy_url if proxy_url is None else proxy_url
    if configured_proxy_url:
        # The proxy is an explicit operator-configured route used only for
        # OAuth. It carries the provider's TLS stream without disabling
        # certificate or hostname verification.
        return {"proxy": configured_proxy_url}
    if settings.oauth_force_ipv4:
        return {"transport": httpx.AsyncHTTPTransport(local_address="0.0.0.0")}
    return {}


class OAuthAsyncOAuth2Client(AsyncOAuth2Client):
    """Create a fresh transport for each short-lived OAuth request."""

    def __init__(self, *args, **kwargs) -> None:
        for option, value in oauth_transport_options().items():
            kwargs.setdefault(option, value)
        super().__init__(*args, **kwargs)


class OAuthStarletteOAuth2App(StarletteOAuth2App):
    client_cls = OAuthAsyncOAuth2Client


class TelegramOAuthAsyncOAuth2Client(AsyncOAuth2Client):
    """Use Telegram's dedicated route without affecting other providers."""

    def __init__(self, *args, **kwargs) -> None:
        for option, value in oauth_transport_options(
            proxy_url=settings.telegram_oauth_proxy_url
        ).items():
            kwargs.setdefault(option, value)
        super().__init__(*args, **kwargs)


class TelegramOAuthStarletteOAuth2App(StarletteOAuth2App):
    client_cls = TelegramOAuthAsyncOAuth2Client


def _oauth_client_kwargs(scope: str, *, use_pkce: bool = False) -> dict[str, object]:
    client_kwargs: dict[str, object] = {
        "scope": scope,
        # OAuth credentials and authorization codes must never be routed
        # through an ambient proxy inherited by the container. On some hosts
        # HTTPX proxy discovery also makes provider connections time out even
        # though a direct connection succeeds.
        "trust_env": False,
        "timeout": settings.oauth_http_timeout_seconds,
    }
    if use_pkce:
        client_kwargs["code_challenge_method"] = "S256"
    return client_kwargs


def _register_oidc(
    name: str,
    client_id: str,
    client_secret: str,
    metadata_url: str,
    scope: str,
    *,
    client_cls: type[StarletteOAuth2App] = OAuthStarletteOAuth2App,
    use_pkce: bool = False,
) -> None:
    if not client_id.strip() or not client_secret.strip():
        return
    oauth.register(
        name,
        client_id=client_id,
        client_secret=client_secret,
        client_cls=client_cls,
        server_metadata_url=metadata_url,
        client_kwargs=_oauth_client_kwargs(scope, use_pkce=use_pkce),
    )


def _register_yandex(client_id: str, client_secret: str) -> None:
    if not client_id.strip() or not client_secret.strip():
        return
    oauth.register(
        "yandex",
        client_id=client_id,
        client_secret=client_secret,
        authorize_url="https://oauth.yandex.ru/authorize",
        access_token_url="https://oauth.yandex.ru/token",
        api_base_url="https://login.yandex.ru/",
        client_cls=OAuthStarletteOAuth2App,
        client_kwargs=_oauth_client_kwargs("login:info login:email", use_pkce=True),
    )


_register_oidc(
    "telegram",
    settings.telegram_oauth_client_id,
    settings.telegram_oauth_client_secret,
    "https://oauth.telegram.org/.well-known/openid-configuration",
    "openid profile",
    client_cls=TelegramOAuthStarletteOAuth2App,
    use_pkce=True,
)
_register_oidc(
    "google",
    settings.google_oauth_client_id,
    settings.google_oauth_client_secret,
    "https://accounts.google.com/.well-known/openid-configuration",
    "openid profile email",
    use_pkce=True,
)
_register_oidc(
    "apple",
    settings.apple_oauth_client_id,
    settings.apple_oauth_client_secret,
    "https://appleid.apple.com/.well-known/openid-configuration",
    "openid email",
)
_register_yandex(settings.yandex_oauth_client_id, settings.yandex_oauth_client_secret)


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class VKOAuthClient:
    """Minimal server-side VK ID OAuth 2.1 client with mandatory PKCE."""

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

    def create_authorization_data(self, redirect_uri: str) -> dict[str, str]:
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(48)
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "scope": VK_SCOPE,
                "state": state,
                "code_challenge": _pkce_challenge(code_verifier),
                "code_challenge_method": "S256",
            }
        )
        return {
            "url": f"{VK_AUTHORIZE_URL}?{query}",
            "state": state,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
        }

    async def _callback_params(self, request) -> dict[str, str]:
        cached = getattr(request.state, "oauth_callback_params", None)
        if isinstance(cached, dict):
            return cached

        params: dict[str, str] = {}
        for key, value in request.query_params.multi_items():
            normalized = str(value)
            existing = params.get(key)
            if existing is not None and existing != normalized:
                raise OAuthStateError("VK ID returned conflicting callback parameters")
            params[key] = normalized
        if request.scope.get("method", "GET") != "GET":
            async with request.form() as form:
                for key, value in form.multi_items():
                    normalized = str(value)
                    existing = params.get(key)
                    if existing is not None and existing != normalized:
                        raise OAuthStateError("VK ID returned conflicting callback parameters")
                    params[key] = normalized
        return merge_vk_callback_payload(params)

    async def authorize_access_token(self, request) -> dict[str, object]:
        params = await self._callback_params(request)
        error = params.get("error")
        if error:
            raise OAuthProviderResponseError(error)

        code = params.get("code")
        state = params.get("state")
        device_id = params.get("device_id")
        if not code or not state or not device_id:
            raise ValueError("VK ID callback is missing required parameters")

        session_data = request.session.pop(VK_SESSION_KEY, None)
        if not isinstance(session_data, dict):
            raise OAuthStateError("VK ID authorization state is invalid or expired")
        expected_state = session_data.get("state")
        if not isinstance(expected_state, str) or not compare_digest(expected_state, state):
            raise OAuthStateError("VK ID authorization state is invalid or expired")
        code_verifier = session_data.get("code_verifier")
        redirect_uri = session_data.get("redirect_uri")
        if not isinstance(code_verifier, str) or not isinstance(redirect_uri, str):
            raise OAuthStateError("VK ID authorization session is invalid")

        transport_options = oauth_transport_options()
        proxy = transport_options.get("proxy")
        transport = transport_options.get("transport")
        async with httpx.AsyncClient(
            trust_env=False,
            timeout=settings.oauth_http_timeout_seconds,
            proxy=proxy if isinstance(proxy, str) else None,
            transport=transport if isinstance(transport, httpx.AsyncBaseTransport) else None,
        ) as client:
            token_response = await client.post(
                VK_TOKEN_URL,
                params={
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "code_verifier": code_verifier,
                    "device_id": device_id,
                    "state": state,
                },
                data={"code": code},
            )
            token_response.raise_for_status()
            token = token_response.json()
            if not isinstance(token, dict):
                raise ValueError("VK ID returned an invalid token response")
            returned_state = token.get("state")
            if returned_state is not None and (
                not isinstance(returned_state, str) or not compare_digest(returned_state, state)
            ):
                raise OAuthStateError("VK ID token state does not match")
            access_token = token.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise ValueError("VK ID did not return an access token")

            profile_response = await client.post(
                VK_USER_INFO_URL,
                params={"client_id": self.client_id},
                data={"access_token": access_token},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            if not isinstance(profile, dict) or not isinstance(profile.get("user"), dict):
                raise ValueError("VK ID returned an invalid user profile")
            return {**token, "userinfo": profile["user"]}


def merge_vk_callback_payload(params: dict[str, str]) -> dict[str, str]:
    """Merge VK flat and JSON callback forms while rejecting conflicts."""

    merged = dict(params)
    raw_payload = merged.pop("payload", None)
    if not raw_payload:
        return merged
    try:
        payload = json.loads(raw_payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("VK ID returned an invalid callback payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("VK ID returned an invalid callback payload")
    for key, value in payload.items():
        if value is None:
            continue
        normalized = str(value)
        existing = merged.get(key)
        if existing is not None and existing != normalized:
            raise OAuthStateError("VK ID returned conflicting callback parameters")
        merged[key] = normalized
    return merged


def configured_oauth_client(provider: str):
    if provider not in settings.oauth_provider_names:
        return None
    if provider == "vk":
        return VKOAuthClient(settings.vk_oauth_client_id)
    return oauth.create_client(provider)


def _telegram_oidc_user_id(raw_claims: dict[str, Any]) -> int:
    """Read Telegram's stable OIDC subject without trusting an arbitrary value."""

    # Telegram Login's OIDC token identifies the account through the standard
    # ``sub`` claim. Keep accepting ``id`` for compatibility with previously
    # stored test fixtures and any provider response that includes it.
    raw_user_id = raw_claims.get("id", raw_claims.get("sub"))
    if isinstance(raw_user_id, bool):
        raise ValueError("Telegram did not return a valid user id")
    if isinstance(raw_user_id, int):
        telegram_user_id = raw_user_id
    elif isinstance(raw_user_id, str) and raw_user_id.isascii() and raw_user_id.isdecimal():
        telegram_user_id = int(raw_user_id)
    else:
        raise ValueError("Telegram did not return a valid user id")
    if telegram_user_id <= 0 or telegram_user_id > 2**63 - 1:
        raise ValueError("Telegram did not return a valid user id")
    return telegram_user_id


def _stable_subject(value: object, *, allow_integer: bool = False) -> str:
    if allow_integer and isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return str(value)
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 255
        or not value.isprintable()
    ):
        return ""
    return value


def _optional_string(value: object, *, max_length: int | None = None) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if max_length is not None and len(value) > max_length:
        return None
    return value


def normalize_oauth_claims(provider: str, raw_claims: dict[str, Any]) -> dict[str, Any]:
    if provider == "telegram":
        telegram_id = _telegram_oidc_user_id(raw_claims)
        username = normalize_telegram_username(
            _optional_string(raw_claims.get("preferred_username"))
        )
        if username is not None and len(username) > 64:
            username = None
        return {
            "subject": str(telegram_id),
            "telegram_user_id": telegram_id,
            "username": username,
            "first_name": _optional_string(raw_claims.get("given_name"), max_length=64),
            "last_name": _optional_string(raw_claims.get("family_name"), max_length=64),
            "full_name": _optional_string(raw_claims.get("name"), max_length=128),
            "photo_url": _optional_string(raw_claims.get("picture"), max_length=512),
            "email": None,
            "email_verified": False,
        }
    if provider == "yandex":
        subject = _stable_subject(raw_claims.get("id"), allow_integer=True)
        email = _optional_string(raw_claims.get("default_email"), max_length=320)
        return {
            "subject": subject,
            "telegram_user_id": None,
            "username": _optional_string(raw_claims.get("login"), max_length=64),
            "first_name": _optional_string(raw_claims.get("first_name"), max_length=64),
            "last_name": _optional_string(raw_claims.get("last_name"), max_length=64),
            "full_name": _optional_string(raw_claims.get("display_name"), max_length=128)
            or _optional_string(raw_claims.get("real_name"), max_length=128),
            "photo_url": None,
            "email": email,
            # Yandex exposes a contact email but no explicit verification claim.
            "email_verified": False,
        }
    if provider == "vk":
        subject = _stable_subject(raw_claims.get("user_id"), allow_integer=True)
        email = _optional_string(raw_claims.get("email"), max_length=320)
        first_name = _optional_string(raw_claims.get("first_name"), max_length=64)
        last_name = _optional_string(raw_claims.get("last_name"), max_length=64)
        full_name = _optional_string(
            " ".join(part for part in [first_name, last_name] if part),
            max_length=128,
        )
        return {
            "subject": subject,
            "telegram_user_id": None,
            "username": None,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "photo_url": _optional_string(raw_claims.get("avatar"), max_length=512),
            "email": email,
            # VK ID user_info returns email but no verification flag.
            "email_verified": False,
        }

    subject = _stable_subject(raw_claims.get("sub"))
    email = _optional_string(raw_claims.get("email"), max_length=320)
    email_verified = raw_claims.get("email_verified") is True
    if provider == "apple":
        # Apple's ID token represents this claim as a JSON string.
        email_verified = raw_claims.get("email_verified") in {True, "true"}
    return {
        "subject": subject,
        "telegram_user_id": None,
        "username": None,
        "first_name": _optional_string(raw_claims.get("given_name"), max_length=64),
        "last_name": _optional_string(raw_claims.get("family_name"), max_length=64),
        "full_name": _optional_string(raw_claims.get("name"), max_length=128),
        "photo_url": _optional_string(raw_claims.get("picture"), max_length=512),
        "email": email,
        "email_verified": email_verified,
    }


def get_or_create_oauth_user(
    db: Session,
    *,
    provider: str,
    raw_claims: dict[str, Any],
) -> User:
    claims = normalize_oauth_claims(provider, raw_claims)
    subject = claims["subject"]
    if not subject:
        raise ValueError(f"{provider} did not return a stable subject")

    identity = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == provider, AuthIdentity.subject == subject)
        .first()
    )
    user = db.query(User).filter(User.id == identity.user_id).first() if identity else None
    if user is None and provider == "telegram":
        user = db.query(User).filter(User.telegram_user_id == claims["telegram_user_id"]).first()

    if user is None:
        candidate = User(
            telegram_user_id=claims["telegram_user_id"],
            username=claims["username"],
            first_name=claims["first_name"],
            last_name=claims["last_name"],
            photo_url=claims["photo_url"],
            is_active=True,
        )
        try:
            # The provider subject is the concurrency boundary. Keeping the
            # candidate account and identity in one savepoint prevents an
            # orphan duplicate user when first-login requests race.
            with db.begin_nested():
                db.add(candidate)
                db.flush()
                db.add(
                    UserProfile(
                        user_id=candidate.id,
                        full_name=(
                            claims["full_name"]
                            or _optional_string(
                                " ".join(
                                    part
                                    for part in [claims["first_name"], claims["last_name"]]
                                    if part
                                ).strip(),
                                max_length=128,
                            )
                            or claims["username"]
                            or "Новый пользователь"
                        ),
                    )
                )
                db.add(NotificationSetting(user_id=candidate.id))
                identity = ensure_auth_identity(
                    db,
                    candidate,
                    provider=provider,
                    subject=subject,
                    email=claims["email"],
                    email_verified=claims["email_verified"],
                )
                db.flush()
            user = candidate
        except IntegrityError, IdentityConflictError:
            identity = (
                db.query(AuthIdentity)
                .filter(AuthIdentity.provider == provider, AuthIdentity.subject == subject)
                .first()
            )
            user = db.query(User).filter(User.id == identity.user_id).first() if identity else None
            if user is None and provider == "telegram":
                user = (
                    db.query(User)
                    .filter(User.telegram_user_id == claims["telegram_user_id"])
                    .first()
                )
            if user is None:
                raise

    if not user.is_active:
        raise OAuthAccountBlockedError("User account is blocked")

    if identity is None:
        try:
            with db.begin_nested():
                identity = ensure_auth_identity(
                    db,
                    user,
                    provider=provider,
                    subject=subject,
                    email=claims["email"],
                    email_verified=claims["email_verified"],
                )
                db.flush()
        except IntegrityError:
            identity = (
                db.query(AuthIdentity)
                .filter(AuthIdentity.provider == provider, AuthIdentity.subject == subject)
                .first()
            )
            if identity is None or identity.user_id != user.id:
                raise
    else:
        identity.email = claims["email"]
        identity.email_verified = claims["email_verified"]
        identity.last_login_at = utcnow()

    if provider == "telegram":
        user.username = claims["username"]
        user.first_name = claims["first_name"]
        user.last_name = claims["last_name"]
        user.photo_url = claims["photo_url"]
    db.commit()
    db.refresh(user)
    return user
