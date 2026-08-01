import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from sqlalchemy import or_
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.user import CoachClientInvite, User, UserProfile
from fitminiapp_api.services.client_codes import ensure_client_code


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
    except TypeError, ValueError:
        raise ValueError("Некорректный auth_date в init_data")

    now = int(time.time())
    if auth_date > now + 60:
        raise ValueError("auth_date из будущего")
    if now - auth_date > max_age_seconds:
        raise ValueError("initData устарел")

    user_raw = data.get("user")
    if not user_raw:
        raise ValueError("В init_data отсутствует user")

    try:
        user_data = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Некорректный user в init_data") from exc
    if not isinstance(user_data, dict):
        raise ValueError("Некорректный user в init_data")

    telegram_user_id = user_data.get("id")
    if not isinstance(telegram_user_id, int) or isinstance(telegram_user_id, bool):
        raise ValueError("Некорректный id пользователя в init_data")
    if telegram_user_id <= 0 or telegram_user_id > 2**63 - 1:
        raise ValueError("Некорректный id пользователя в init_data")

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
    """Attach a verified Telegram identity to invitations without accepting them."""
    username = normalize_telegram_username(user.username)
    filters = [CoachClientInvite.telegram_user_id == user.telegram_user_id]
    if username:
        filters.append(CoachClientInvite.username == username)
    invites = (
        db.query(CoachClientInvite)
        .filter(CoachClientInvite.status == "pending", or_(*filters))
        .order_by(CoachClientInvite.id.desc())
        .all()
    )
    keep_by_coach: dict[int, CoachClientInvite] = {}
    for invite in invites:
        if invite.coach_user_id in keep_by_coach:
            db.delete(invite)
        else:
            keep_by_coach[invite.coach_user_id] = invite
    db.flush()

    for invite in keep_by_coach.values():
        invite.telegram_user_id = user.telegram_user_id
        invite.client_user_id = user.id
        if username:
            invite.username = username


def get_or_create_user_from_init_data(db: Session, init_data: dict) -> User:
    user_data = init_data["user"]

    telegram_user_id = user_data["id"]
    username = normalize_telegram_username(user_data.get("username"))
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")
    photo_url = user_data.get("photo_url")

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url,
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
        ensure_client_code(db, user)
        _link_pending_client_invites(db, user)
        db.commit()
        db.refresh(user)
        return user

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.photo_url = photo_url
    _apply_bootstrap_admin_role(user)
    ensure_client_code(db, user)

    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not existing_profile:
        full_name = (
            " ".join(part for part in [first_name, last_name] if part).strip()
            or username
            or f"User {telegram_user_id}"
        )
        existing_profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
        )
        db.add(existing_profile)

    _link_pending_client_invites(db, user)
    db.commit()
    db.refresh(user)
    return user
