from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.user import User


def has_verified_root_identity(db: Session, user: User) -> bool:
    """Root is derived only from the configured, verified Telegram identity."""

    telegram_user_id = user.telegram_user_id
    if telegram_user_id is None or telegram_user_id not in settings.admin_telegram_id_set:
        return False
    return (
        db.query(AuthIdentity.id)
        .filter(
            AuthIdentity.user_id == user.id,
            AuthIdentity.provider == "telegram",
            AuthIdentity.subject == str(telegram_user_id),
        )
        .first()
        is not None
    )


def is_root_user(user: User) -> bool:
    """Return whether this account is protected by the server Root configuration."""

    return (
        user.telegram_user_id is not None
        and user.telegram_user_id in settings.admin_telegram_id_set
    )


def is_root_telegram_user_id(telegram_user_id: int) -> bool:
    return telegram_user_id in settings.admin_telegram_id_set
