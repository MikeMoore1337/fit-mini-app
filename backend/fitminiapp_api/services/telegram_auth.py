import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.services.auth_identities import ensure_telegram_identity


def build_secret_key(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def parse_init_data(init_data: str) -> dict[str, str]:
    pairs = parse_qsl(init_data, keep_blank_values=True)
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError("init_data содержит повторяющиеся параметры")
    return dict(pairs)


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 5 * 60,
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

    for field, max_length in {
        "username": 64,
        "first_name": 64,
        "last_name": 64,
        "photo_url": 512,
    }.items():
        value = user_data.get(field)
        if value is not None and (not isinstance(value, str) or len(value) > max_length):
            raise ValueError(f"Некорректный {field} пользователя в init_data")

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


def _display_name(
    telegram_user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> str:
    return (
        " ".join(part for part in [first_name, last_name] if part).strip()
        or username
        or f"User {telegram_user_id}"
    )


def get_or_insert_telegram_user(
    db: Session,
    *,
    telegram_user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    photo_url: str | None,
) -> User:
    values = {
        "telegram_user_id": telegram_user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "photo_url": photo_url,
        "is_admin": telegram_user_id in settings.admin_telegram_id_set,
        "is_active": True,
    }
    dialect_name = db.get_bind().dialect.name
    if dialect_name == "postgresql":
        db.execute(
            postgresql_insert(User)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["telegram_user_id"])
        )
        return db.query(User).filter(User.telegram_user_id == telegram_user_id).one()
    if dialect_name == "sqlite":
        db.execute(
            sqlite_insert(User)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["telegram_user_id"])
        )
        return db.query(User).filter(User.telegram_user_id == telegram_user_id).one()

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if user:
        return user
    candidate = User(**values)
    try:
        # The savepoint keeps the outer request transaction usable when two
        # first-login requests race on the unique Telegram id.
        with db.begin_nested():
            db.add(candidate)
            db.flush()
    except IntegrityError:
        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
        if user is None:  # pragma: no cover - defensive against a failed competing tx
            raise
        return user
    return candidate


def get_or_create_user_from_init_data(db: Session, init_data: dict) -> User:
    user_data = init_data["user"]

    telegram_user_id = user_data["id"]
    username = normalize_telegram_username(user_data.get("username"))
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")
    photo_url = user_data.get("photo_url")

    user = get_or_insert_telegram_user(
        db,
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        photo_url=photo_url,
    )

    # Serialise profile/settings provisioning for existing and new
    # accounts alike. This also makes retries after a partially provisioned
    # historical account safe and idempotent.
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).with_for_update().one()

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.photo_url = photo_url
    _apply_bootstrap_admin_role(user)
    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not existing_profile:
        existing_profile = UserProfile(
            user_id=user.id,
            full_name=_display_name(
                telegram_user_id,
                username,
                first_name,
                last_name,
            ),
        )
        db.add(existing_profile)

    notification_settings = (
        db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    )
    if notification_settings is None:
        db.add(NotificationSetting(user_id=user.id))

    ensure_telegram_identity(db, user)

    db.commit()
    db.refresh(user)
    return user
