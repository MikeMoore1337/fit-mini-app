from __future__ import annotations

from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.services.auth_identities import ensure_auth_identity
from fitminiapp_api.services.password_auth import utcnow
from fitminiapp_api.services.telegram_auth import normalize_telegram_username

oauth = OAuth()


def oauth_transport_options() -> dict[str, object]:
    """Return isolated HTTPX options for a short-lived OAuth client."""

    if settings.oauth_proxy_url:
        # The proxy is an explicit operator-configured route used only for
        # OAuth. It carries the provider's TLS stream without disabling
        # certificate or hostname verification.
        return {"proxy": settings.oauth_proxy_url}
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


def _register_oidc(
    name: str,
    client_id: str,
    client_secret: str,
    metadata_url: str,
    scope: str,
) -> None:
    if not client_id.strip() or not client_secret.strip():
        return
    oauth.register(
        name,
        client_id=client_id,
        client_secret=client_secret,
        client_cls=OAuthStarletteOAuth2App,
        server_metadata_url=metadata_url,
        client_kwargs={
            "scope": scope,
            # OAuth credentials and authorization codes must never be routed
            # through an ambient proxy inherited by the container. On some
            # hosts HTTPX proxy discovery also makes Telegram connections time
            # out even though a direct connection succeeds.
            "trust_env": False,
            # HTTPX defaults to a five-second connect timeout. Telegram's OAuth
            # endpoint can take longer to establish a connection from production
            # networks, especially while IPv4/IPv6 routes are being selected.
            "timeout": settings.oauth_http_timeout_seconds,
        },
    )


_register_oidc(
    "telegram",
    settings.telegram_oauth_client_id,
    settings.telegram_oauth_client_secret,
    "https://oauth.telegram.org/.well-known/openid-configuration",
    "openid profile",
)
_register_oidc(
    "google",
    settings.google_oauth_client_id,
    settings.google_oauth_client_secret,
    "https://accounts.google.com/.well-known/openid-configuration",
    "openid profile email",
)
_register_oidc(
    "apple",
    settings.apple_oauth_client_id,
    settings.apple_oauth_client_secret,
    "https://appleid.apple.com/.well-known/openid-configuration",
    "openid email",
)
if settings.yandex_oauth_client_id.strip() and settings.yandex_oauth_client_secret.strip():
    oauth.register(
        "yandex",
        client_id=settings.yandex_oauth_client_id,
        client_secret=settings.yandex_oauth_client_secret,
        authorize_url="https://oauth.yandex.ru/authorize",
        access_token_url="https://oauth.yandex.ru/token",
        api_base_url="https://login.yandex.ru/",
        client_kwargs={"scope": "login:info login:email"},
    )


def configured_oauth_client(provider: str):
    if provider not in settings.oauth_provider_names:
        return None
    return oauth.create_client(provider)


def normalize_oauth_claims(provider: str, raw_claims: dict[str, Any]) -> dict[str, Any]:
    if provider == "telegram":
        telegram_id = raw_claims.get("id")
        if not isinstance(telegram_id, int) or isinstance(telegram_id, bool) or telegram_id <= 0:
            raise ValueError("Telegram did not return a valid user id")
        return {
            "subject": str(telegram_id),
            "telegram_user_id": telegram_id,
            "username": normalize_telegram_username(raw_claims.get("preferred_username")),
            "first_name": raw_claims.get("given_name"),
            "last_name": raw_claims.get("family_name"),
            "full_name": raw_claims.get("name"),
            "photo_url": raw_claims.get("picture"),
            "email": None,
            "email_verified": False,
        }
    if provider == "yandex":
        subject = raw_claims.get("id")
        email = raw_claims.get("default_email")
        return {
            "subject": str(subject or ""),
            "telegram_user_id": None,
            "username": raw_claims.get("login"),
            "first_name": raw_claims.get("first_name"),
            "last_name": raw_claims.get("last_name"),
            "full_name": raw_claims.get("display_name") or raw_claims.get("real_name"),
            "photo_url": None,
            "email": email,
            "email_verified": bool(email),
        }

    subject = raw_claims.get("sub")
    email = raw_claims.get("email")
    return {
        "subject": str(subject or ""),
        "telegram_user_id": None,
        "username": None,
        "first_name": raw_claims.get("given_name"),
        "last_name": raw_claims.get("family_name"),
        "full_name": raw_claims.get("name"),
        "photo_url": raw_claims.get("picture"),
        "email": email,
        "email_verified": bool(raw_claims.get("email_verified", provider == "apple" and email)),
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
        user = User(
            telegram_user_id=claims["telegram_user_id"],
            username=claims["username"],
            first_name=claims["first_name"],
            last_name=claims["last_name"],
            photo_url=claims["photo_url"],
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(
            UserProfile(
                user_id=user.id,
                full_name=(
                    claims["full_name"]
                    or " ".join(
                        part for part in [claims["first_name"], claims["last_name"]] if part
                    ).strip()
                    or claims["username"]
                    or "Новый пользователь"
                ),
            )
        )
        db.add(NotificationSetting(user_id=user.id))

    if not user.is_active:
        raise ValueError("User account is blocked")

    if identity is None:
        identity = ensure_auth_identity(
            db,
            user,
            provider=provider,
            subject=subject,
            email=claims["email"],
            email_verified=claims["email_verified"],
        )
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
