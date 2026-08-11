from datetime import date

from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import DEFAULT_TIMEZONE, is_valid_timezone
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.user import HeartRateZoneResponse, UserProfileUpdate

HEART_RATE_ZONE_RANGES = (
    ("Восстановление", 0.5, 0.6),
    ("Лёгкая", 0.6, 0.7),
    ("Аэробная", 0.7, 0.8),
    ("Пороговая", 0.8, 0.9),
    ("Максимальная", 0.9, 1.0),
)


def calculate_tanaka_heart_rate_zones(
    birth_date: date | None,
    *,
    today: date | None = None,
) -> tuple[int | None, list[HeartRateZoneResponse]]:
    if birth_date is None:
        return None, []
    reference_date = today or date.today()
    age = (
        reference_date.year
        - birth_date.year
        - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))
    )
    maximum = int(208 - 0.7 * age + 0.5)
    zones = [
        HeartRateZoneResponse(
            zone=index,
            title=title,
            min_bpm=int(maximum * lower + 0.5),
            max_bpm=int(maximum * upper + 0.5),
        )
        for index, (title, lower, upper) in enumerate(HEART_RATE_ZONE_RANGES, start=1)
    ]
    return maximum, zones


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
