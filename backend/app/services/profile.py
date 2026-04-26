from sqlalchemy.orm import Session

from app.core.timezone import DEFAULT_TIMEZONE, is_valid_timezone
from app.models.notification import NotificationSetting
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileUpdate


def ensure_profile(db: Session, user: User) -> UserProfile:
    if user.profile:
        return user.profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.flush()
    setting = NotificationSetting(user_id=user.id)
    db.add(setting)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(db: Session, user: User, payload: UserProfileUpdate) -> User:
    profile = ensure_profile(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "timezone":
            if not value:
                value = DEFAULT_TIMEZONE
            elif not is_valid_timezone(value):
                continue
        setattr(profile, field, value)
    db.commit()
    db.refresh(user)
    return user
