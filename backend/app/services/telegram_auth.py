import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from app.models.user import User, UserProfile
from sqlalchemy.orm import Session


def build_secret_key(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def parse_init_data(init_data: str) -> dict[str, str]:
    return dict(parse_qsl(init_data, keep_blank_values=True))


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
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


def get_or_create_user_from_init_data(db: Session, init_data: dict) -> User:
    user_data = init_data["user"]

    telegram_user_id = int(user_data["id"])
    username = user_data.get("username")
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
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
        db.commit()
        db.refresh(user)
        return user

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = True

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

    db.commit()
    db.refresh(user)
    return user
