from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.user import User
from fitminiapp_api.services.coach_clients import (
    _can_manage_user_id,
    _coach_client_ids,
    _resolve_manageable_user,
)
from fitminiapp_api.services.exercise_domain import (
    exercise_metadata_load_options,
    sync_exercise_domain_metadata,
)
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.root_admin import has_verified_root_identity


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or f"exercise-{uuid4().hex[:8]}"


def _effective_exercise_id(exercise: Exercise) -> int:
    return exercise.source_exercise_id or exercise.id


def _personal_slug(base: str) -> str:
    return f"{base}-u-{uuid4().hex[:8]}"


def _normalize_optional_text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _load_visible_exercise_rows(db: Session, current_user: User) -> list[Exercise]:
    base_rows = (
        db.query(Exercise)
        .options(*exercise_metadata_load_options())
        .filter(
            Exercise.created_by_user_id.is_(None),
            Exercise.source_exercise_id.is_(None),
        )
        .order_by(Exercise.title.asc())
        .all()
    )

    personal_rows = (
        db.query(Exercise)
        .options(*exercise_metadata_load_options())
        .filter(Exercise.created_by_user_id == current_user.id)
        .all()
    )

    overrides_by_source: dict[int, Exercise] = {}
    personal_custom_rows: list[Exercise] = []

    for row in personal_rows:
        if row.source_exercise_id:
            overrides_by_source[row.source_exercise_id] = row
        else:
            personal_custom_rows.append(row)

    visible: list[Exercise] = []

    for base in base_rows:
        override = overrides_by_source.get(base.id)
        if override is not None:
            if not override.is_deleted:
                visible.append(override)
        else:
            if not base.is_deleted:
                visible.append(base)

    for row in personal_custom_rows:
        if not row.is_deleted:
            visible.append(row)

    visible.sort(key=lambda x: x.title.lower())
    return visible


def get_visible_exercise_display_map(db: Session, current_user: User) -> dict[int, Exercise]:
    rows = _load_visible_exercise_rows(db, current_user)
    return {_effective_exercise_id(row): row for row in rows}


def list_exercises(db: Session, current_user: User) -> list[Exercise]:
    rows = _load_visible_exercise_rows(db, current_user)

    client_ids = _coach_client_ids(db, current_user) if current_user.is_coach else []
    if client_ids:
        rows.extend(
            db.query(Exercise)
            .options(*exercise_metadata_load_options())
            .filter(
                Exercise.created_by_user_id.in_(client_ids),
                Exercise.is_deleted.is_(False),
            )
            .all()
        )

    by_id = {row.id: row for row in rows}
    return sorted(by_id.values(), key=lambda x: x.title.lower())


def create_exercise(
    db: Session,
    current_user: User,
    title: str,
    primary_muscle: str | None,
    equipment: str | None,
    metric_type: str = "strength",
    difficulty_level: str = "intermediate",
    target_telegram_user_id: int | None = None,
) -> Exercise:
    normalized_title = title.strip()
    normalized_muscle = _normalize_optional_text(primary_muscle)
    normalized_equipment = _normalize_optional_text(equipment)

    if not normalized_title:
        raise ProgramError("Exercise title is required")

    owner_user = _resolve_manageable_user(db, current_user, target_telegram_user_id)
    is_global_admin_exercise = (
        has_verified_root_identity(db, current_user) and owner_user.id == current_user.id
    )
    visible_rows = _load_visible_exercise_rows(
        db,
        current_user if is_global_admin_exercise else owner_user,
    )
    if any(row.title.lower() == normalized_title.lower() for row in visible_rows):
        raise ProgramError("Exercise with this title already exists")

    base_slug = _slugify(normalized_title)
    slug = base_slug
    counter = 2
    while db.query(Exercise).filter(Exercise.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    exercise = Exercise(
        slug=slug,
        title=normalized_title,
        primary_muscle=normalized_muscle,
        equipment=normalized_equipment,
        metric_type=metric_type,
        difficulty_level=difficulty_level,
        created_by_user_id=None if is_global_admin_exercise else owner_user.id,
        source_exercise_id=None,
        is_deleted=False,
    )
    db.add(exercise)
    sync_exercise_domain_metadata(db, exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def _find_personal_override(
    db: Session, current_user: User, base_exercise_id: int
) -> Exercise | None:
    return (
        db.query(Exercise)
        .filter(
            Exercise.created_by_user_id == current_user.id,
            Exercise.source_exercise_id == base_exercise_id,
        )
        .first()
    )


def update_exercise_for_user(
    db: Session,
    current_user: User,
    exercise_id: int,
    title: str,
    primary_muscle: str | None,
    equipment: str | None,
    metric_type: str | None = None,
    difficulty_level: str = "intermediate",
    target_telegram_user_id: int | None = None,
) -> Exercise:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise ProgramError("Exercise not found")

    normalized_title = title.strip()
    normalized_muscle = _normalize_optional_text(primary_muscle)
    normalized_equipment = _normalize_optional_text(equipment)

    if not normalized_title:
        raise ProgramError("Exercise title is required")

    if exercise.created_by_user_id is not None and not _can_manage_user_id(
        db,
        current_user,
        exercise.created_by_user_id,
    ):
        raise ProgramError("No permission to edit exercise")

    owner_user = (
        _resolve_manageable_user(db, current_user, target_telegram_user_id)
        if exercise.created_by_user_id is None
        else db.query(User).filter(User.id == exercise.created_by_user_id).first()
    )
    if owner_user is None:
        raise ProgramError("No permission to edit exercise")

    edits_global_exercise = (
        exercise.created_by_user_id is None
        and has_verified_root_identity(db, current_user)
        and owner_user.id == current_user.id
    )

    visible_rows = _load_visible_exercise_rows(
        db,
        current_user if edits_global_exercise else owner_user,
    )
    visible_names = {
        row.title.lower()
        for row in visible_rows
        if (_effective_exercise_id(row) != _effective_exercise_id(exercise))
    }
    if normalized_title.lower() in visible_names:
        raise ProgramError("Exercise with this title already exists")

    if exercise.created_by_user_id is not None or edits_global_exercise:
        exercise.title = normalized_title
        exercise.primary_muscle = normalized_muscle
        exercise.equipment = normalized_equipment
        if metric_type is not None:
            exercise.metric_type = metric_type
        exercise.difficulty_level = difficulty_level
        exercise.is_deleted = False
        sync_exercise_domain_metadata(db, exercise)
        db.commit()
        db.refresh(exercise)
        return exercise

    if exercise.created_by_user_id is None:
        override = _find_personal_override(db, owner_user, exercise.id)
        if override is None:
            override = Exercise(
                slug=_personal_slug(exercise.slug),
                title=normalized_title,
                primary_muscle=normalized_muscle,
                equipment=normalized_equipment,
                metric_type=metric_type or exercise.metric_type,
                difficulty_level=difficulty_level,
                created_by_user_id=owner_user.id,
                source_exercise_id=exercise.id,
                is_deleted=False,
            )
            db.add(override)
        else:
            override.title = normalized_title
            override.primary_muscle = normalized_muscle
            override.equipment = normalized_equipment
            if metric_type is not None:
                override.metric_type = metric_type
            override.difficulty_level = difficulty_level
            override.is_deleted = False

        sync_exercise_domain_metadata(db, override)
        db.commit()
        db.refresh(override)
        return override

    raise ProgramError("No permission to edit exercise")


def delete_exercise_for_user(
    db: Session,
    current_user: User,
    exercise_id: int,
    target_telegram_user_id: int | None = None,
) -> None:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise ProgramError("Exercise not found")

    if exercise.created_by_user_id is not None:
        if not _can_manage_user_id(db, current_user, exercise.created_by_user_id):
            raise ProgramError("No permission to delete exercise")

        exercise.is_deleted = True
        db.commit()
        return

    if exercise.created_by_user_id is None:
        owner_user = _resolve_manageable_user(db, current_user, target_telegram_user_id)
        if has_verified_root_identity(db, current_user) and owner_user.id == current_user.id:
            exercise.is_deleted = True
            db.commit()
            return

        override = _find_personal_override(db, owner_user, exercise.id)
        if override is None:
            override = Exercise(
                slug=_personal_slug(exercise.slug),
                title=exercise.title,
                primary_muscle=exercise.primary_muscle,
                equipment=exercise.equipment,
                metric_type=exercise.metric_type,
                difficulty_level=exercise.difficulty_level,
                created_by_user_id=owner_user.id,
                source_exercise_id=exercise.id,
                is_deleted=True,
            )
            db.add(override)
        else:
            override.is_deleted = True

        db.commit()
        return

    raise ProgramError("No permission to delete exercise")
