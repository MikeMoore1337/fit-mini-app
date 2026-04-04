import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from app.core.config import settings
from app.models.user import User
from sqlalchemy.orm import Session


def build_secret_key(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def parse_init_data(init_data: str) -> dict[str, str]:
    return dict(parse_qsl(init_data, keep_blank_values=True))


def validate_init_data(init_data: str, bot_token: str) -> dict:
    data = parse_init_data(init_data)

    received_hash = data.pop("hash", None)
    if not received_hash:
        raise ValueError("hash отсутствует в init_data")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

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


def validate_telegram_init_data(init_data: str) -> bool:
    try:
        validate_init_data(init_data, settings.telegram_bot_token)
        return True
    except Exception:
        return False


def get_or_create_user_from_init_data(db: Session, init_data: str) -> User:
    validated = validate_init_data(init_data, settings.telegram_bot_token)
    tg_user = validated["user"]

    telegram_user_id = int(tg_user["id"])
    username = tg_user.get("username")
    first_name = tg_user.get("first_name")
    last_name = tg_user.get("last_name")

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if user:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        db.commit()
        db.refresh(user)
        return user

    user = User(
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_coach=False,
        is_admin=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
