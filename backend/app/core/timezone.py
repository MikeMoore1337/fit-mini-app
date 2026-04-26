from datetime import date, datetime
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Europe/Moscow"
MSK_TZ = ZoneInfo(DEFAULT_TIMEZONE)


def get_timezone(timezone_name: str | None) -> ZoneInfo:
    if not timezone_name:
        return MSK_TZ
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return MSK_TZ


def is_valid_timezone(timezone_name: str) -> bool:
    try:
        ZoneInfo(timezone_name)
        return True
    except Exception:
        return False


def get_user_timezone_name(user) -> str:
    timezone_name = getattr(getattr(user, "profile", None), "timezone", None)
    if timezone_name and is_valid_timezone(timezone_name):
        return timezone_name
    return DEFAULT_TIMEZONE


def now_msk() -> datetime:
    return datetime.now(MSK_TZ)


def now_msk_naive() -> datetime:
    return now_msk().replace(tzinfo=None)


def today_msk() -> date:
    return now_msk().date()


def now_in_timezone(timezone_name: str | None) -> datetime:
    return datetime.now(get_timezone(timezone_name))


def now_in_timezone_naive(timezone_name: str | None) -> datetime:
    return now_in_timezone(timezone_name).replace(tzinfo=None)


def today_in_timezone(timezone_name: str | None) -> date:
    return now_in_timezone(timezone_name).date()


def now_for_user_naive(user) -> datetime:
    return now_in_timezone_naive(get_user_timezone_name(user))


def today_for_user(user) -> date:
    return today_in_timezone(get_user_timezone_name(user))


def to_msk_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(MSK_TZ).replace(tzinfo=None)


def to_timezone_naive(value: datetime, timezone_name: str | None) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(get_timezone(timezone_name)).replace(tzinfo=None)


def to_user_timezone_naive(value: datetime, user) -> datetime:
    return to_timezone_naive(value, get_user_timezone_name(user))
