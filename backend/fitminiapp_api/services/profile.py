from datetime import date

from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import DEFAULT_TIMEZONE, is_valid_timezone
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.user import UserProfileUpdate
from fitminiapp_api.services.heart_rate import (
    HeartRateCalculation,
    calculate_heart_rates,
    calculate_max_heart_rate,
)


class ProfileError(ValueError):
    pass


def calculate_profile_heart_rates(
    birth_date: date | None,
    resting_heart_rate: int | None,
    goal: str | None,
    *,
    today: date | None = None,
) -> HeartRateCalculation | None:
    if birth_date is None:
        return None
    reference_date = today or date.today()
    age = (
        reference_date.year
        - birth_date.year
        - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))
    )
    return calculate_heart_rates(age, resting_heart_rate, goal)


def ensure_profile(db: Session, user: User, *, commit: bool = True) -> UserProfile:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.flush()

    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    if setting is None:
        db.add(NotificationSetting(user_id=user.id))

    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(profile)
    return profile


def update_profile(
    db: Session,
    user: User,
    payload: UserProfileUpdate,
    *,
    changed_by: User | None = None,
    commit: bool = True,
) -> User:
    profile = ensure_profile(db, user, commit=commit)
    changes = payload.model_dump(exclude_unset=True)
    birth_date = changes.get("birth_date", profile.birth_date)
    resting_heart_rate = changes.get("resting_heart_rate", profile.resting_heart_rate)
    if birth_date is not None and resting_heart_rate is not None:
        reference_date = date.today()
        age = (
            reference_date.year
            - birth_date.year
            - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))
        )
        if resting_heart_rate >= calculate_max_heart_rate(age):
            raise ProfileError("Resting heart rate must be below maximum heart rate")
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
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(user)
    return user
