from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.user import User


class IdentityConflictError(RuntimeError):
    pass


def ensure_auth_identity(
    db: Session,
    user: User,
    *,
    provider: str,
    subject: str,
    email: str | None = None,
    email_verified: bool = False,
    mark_login: bool = True,
) -> AuthIdentity:
    """Create or refresh a verified identity without moving it between users."""

    normalized_provider = provider.strip().lower()
    normalized_subject = subject.strip()
    if not normalized_provider or not normalized_subject:
        raise ValueError("provider and subject are required")

    identity = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.provider == normalized_provider,
            AuthIdentity.subject == normalized_subject,
        )
        .first()
    )
    if identity is not None:
        if identity.user_id != user.id:
            raise IdentityConflictError("Identity already belongs to another user")
        if email is not None:
            identity.email = email.strip().lower() or None
            identity.email_verified = email_verified
        if mark_login:
            identity.last_login_at = now_msk_naive()
        return identity

    existing_provider = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.user_id == user.id,
            AuthIdentity.provider == normalized_provider,
        )
        .first()
    )
    if existing_provider is not None:
        raise IdentityConflictError("User already has another identity for this provider")

    identity = AuthIdentity(
        user_id=user.id,
        provider=normalized_provider,
        subject=normalized_subject,
        email=email.strip().lower() if email and email.strip() else None,
        email_verified=email_verified,
    )
    db.add(identity)
    return identity


def ensure_telegram_identity(db: Session, user: User, *, mark_login: bool = True) -> AuthIdentity:
    return ensure_auth_identity(
        db,
        user,
        provider="telegram",
        subject=str(user.telegram_user_id),
        mark_login=mark_login,
    )
