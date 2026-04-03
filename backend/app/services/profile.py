from sqlalchemy.orm import Session

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
        setattr(profile, field, value)
    db.commit()
    db.refresh(user)
    return user
