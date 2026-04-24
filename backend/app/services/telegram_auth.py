import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import CoachClient, CoachClientInvite, User, UserProfile


def build_secret_key(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def parse_init_data(init_data: str) -> dict[str, str]:
    return dict(parse_qsl(init_data, keep_blank_values=True))


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 24 * 60 * 60,
) -> dict:
    data = parse_init_data(init_data)

    received_hash = data.pop("hash", None)
    if not received_hash:
        raise ValueError("hash отсутствует в init_data")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))

    secret_key = build_secret_key(bot_token)
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Некорректная подпись Telegram initData")

    auth_date_raw = data.get("auth_date")
    if not auth_date_raw:
        raise ValueError("auth_date отсутствует в init_data")

    try:
        auth_date = int(auth_date_raw)
    except (TypeError, ValueError):
        raise ValueError("Некорректный auth_date в init_data")

    now = int(time.time())
    if auth_date > now + 60:
        raise ValueError("auth_date из будущего")
    if now - auth_date > max_age_seconds:
        raise ValueError("initData устарел")

    user_raw = data.get("user")
    if not user_raw:
        raise ValueError("В init_data отсутствует user")

    user_data = json.loads(user_raw)

    return {
        "auth_date": data.get("auth_date"),
        "user": user_data,
        "raw": data,
    }


def validate_init_data(init_data: str, bot_token: str) -> dict:
    return validate_telegram_init_data(init_data, bot_token)


def normalize_telegram_username(username: str | None) -> str | None:
    if not username:
        return None
    normalized = username.strip().lstrip("@").lower()
    return normalized or None


def _apply_bootstrap_admin_role(user: User) -> None:
    if user.telegram_user_id in settings.admin_telegram_id_set:
        user.is_admin = True


def _link_pending_client_invites(db: Session, user: User) -> None:
    username = normalize_telegram_username(user.username)
    if not username:
        return

    invites = db.query(CoachClientInvite).filter(CoachClientInvite.username == username).all()
    for invite in invites:
        link = (
            db.query(CoachClient)
            .filter(
                CoachClient.coach_user_id == invite.coach_user_id,
                CoachClient.client_user_id == user.id,
            )
            .first()
        )
        if not link and invite.coach_user_id != user.id:
            db.add(
                CoachClient(
                    coach_user_id=invite.coach_user_id,
                    client_user_id=user.id,
                )
            )
        db.delete(invite)


def get_or_create_user_from_init_data(db: Session, init_data: dict) -> User:
    user_data = init_data["user"]

    telegram_user_id = int(user_data["id"])
    username = normalize_telegram_username(user_data.get("username"))
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=telegram_user_id in settings.admin_telegram_id_set,
            is_active=True,
        )
        db.add(user)
        db.flush()

        full_name = (
            " ".join(part for part in [first_name, last_name] if part).strip()
            or username
            or f"User {telegram_user_id}"
        )

        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
        )
        db.add(profile)
        _link_pending_client_invites(db, user)
        db.commit()
        db.refresh(user)
        return user

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = True
    _apply_bootstrap_admin_role(user)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        full_name = (
            " ".join(part for part in [first_name, last_name] if part).strip()
            or username
            or f"User {telegram_user_id}"
        )
        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
        )
        db.add(profile)

    _link_pending_client_invites(db, user)
    db.commit()
    db.refresh(user)
    return user
