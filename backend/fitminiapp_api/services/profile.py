from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import DEFAULT_TIMEZONE, is_valid_timezone
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.user import UserProfileUpdate


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


def update_profile(
    db: Session,
    user: User,
    payload: UserProfileUpdate,
    *,
    changed_by: User | None = None,
) -> User:
    profile = ensure_profile(db, user)
    changes = payload.model_dump(exclude_unset=True)
    nutrition_field_map = {
        "goal": "goal",
        "height_cm": "height_cm",
        "weight_kg": "weight_kg",
        "workouts_per_week": "strength_trainings_per_week",
        "cardio_trainings_per_week": "cardio_trainings_per_week",
    }
    nutrition_updates: dict[str, object] = {}
    for field, value in changes.items():
        if field == "timezone":
            if not value:
                value = DEFAULT_TIMEZONE
            elif not is_valid_timezone(value):
                continue
        if field in nutrition_field_map and value is not None and getattr(profile, field) != value:
            nutrition_updates[nutrition_field_map[field]] = value
        setattr(profile, field, value)

    if nutrition_updates:
        # Local import avoids a module cycle: nutrition uses ensure_profile on first save.
        from fitminiapp_api.services.nutrition import recalculate_nutrition_target

        recalculate_nutrition_target(
            db,
            user,
            nutrition_updates,
            changed_by or user,
        )
    db.commit()
    db.refresh(user)
    return user
