from __future__ import annotations

from sqlalchemy.orm import Session

from fitminiapp_api.models.auth_identity import AuthIdentity, LocalCredential
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.support import BotSupportCase
from fitminiapp_api.models.user import User
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.root_admin import is_root_user
from fitminiapp_api.services.weekly_digest import disable_digest_for_unlinked_telegram


class IdentityUnlinkError(ValueError):
    pass


class IdentityNotFoundError(IdentityUnlinkError):
    pass


class LastIdentityError(IdentityUnlinkError):
    pass


class ProtectedIdentityError(IdentityUnlinkError):
    pass


def unlink_auth_identity(db: Session, user: User, provider: str) -> None:
    normalized_provider = provider.strip().lower()
    db.query(User.id).filter(User.id == user.id).with_for_update().one()
    identities = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.user_id == user.id)
        .order_by(AuthIdentity.id.asc())
        .with_for_update()
        .all()
    )
    identity = next(
        (row for row in identities if row.provider == normalized_provider),
        None,
    )
    if identity is None:
        raise IdentityNotFoundError("Способ входа не найден")
    if len(identities) <= 1:
        raise LastIdentityError("Нельзя отключить последний способ входа")
    if normalized_provider == "telegram" and is_root_user(user):
        raise ProtectedIdentityError("Root Telegram нельзя отключить")

    if normalized_provider == "telegram":
        telegram_user_id = user.telegram_user_id
        disable_digest_for_unlinked_telegram(db, user.id)
        user.telegram_user_id = None
        user.username = None
        setting = (
            db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
        )
        if setting is not None:
            setting.telegram_enabled = False
        db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.channel == "telegram",
            Notification.status.in_(("queued", "processing")),
        ).update(
            {
                "status": "cancelled",
                "last_error": "telegram_identity_unlinked",
                "next_attempt_at": None,
                "processing_started_at": None,
            },
            synchronize_session=False,
        )
        if telegram_user_id is not None:
            db.query(BotSupportCase).filter(
                BotSupportCase.telegram_user_id == telegram_user_id
            ).delete(synchronize_session=False)
    elif normalized_provider == "password":
        db.query(LocalCredential).filter(LocalCredential.user_id == user.id).delete(
            synchronize_session=False
        )

    db.delete(identity)
    record_audit_event(
        db,
        action="account.identity_unlinked",
        resource_type="auth_identity",
        actor_user_id=user.id,
        target_user_id=user.id,
        resource_id=identity.id,
        details={"provider": normalized_provider},
    )
    db.flush()
