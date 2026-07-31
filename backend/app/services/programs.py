from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.timezone import now_msk_naive, today_for_user
from app.models.exercise import Exercise
from app.models.notification import Notification
from app.models.program import (
    HiddenProgramTemplate,
    ProgramTemplate,
    ProgramTemplateDay,
    ProgramTemplateExercise,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from app.models.user import CoachClient, CoachClientInvite, User, UserProfile
from app.schemas.program import ProgramTemplateCreate
from app.services.client_codes import ensure_client_code
from app.services.nutrition import get_nutrition_target_for_user
from app.services.telegram_auth import normalize_telegram_username

GOALS = {"muscle_gain", "fat_loss", "maintenance", "recomposition"}
LEVELS = {"beginner", "intermediate", "advanced"}
MODES = {"self", "coach"}
LEGACY_DEMO_TEMPLATE_SLUG = "upper-lower-4x"


class ProgramError(ValueError):
    pass


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
        .filter(
            Exercise.created_by_user_id.is_(None),
            Exercise.source_exercise_id.is_(None),
        )
        .order_by(Exercise.title.asc())
        .all()
    )

    personal_rows = db.query(Exercise).filter(Exercise.created_by_user_id == current_user.id).all()

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


def get_or_create_user_by_telegram_id(
    db: Session,
    telegram_user_id: int,
    full_name: str | None = None,
) -> User:
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if not user:
        user = User(
            telegram_user_id=telegram_user_id,
            username=f"user_{telegram_user_id}",
        )
        db.add(user)
        db.flush()

        db.add(
            UserProfile(
                user_id=user.id,
                full_name=full_name or f"Клиент {telegram_user_id}",
            )
        )
        ensure_client_code(db, user)
        db.commit()
        db.refresh(user)
    return user


def _coach_client_ids(db: Session, coach: User) -> list[int]:
    return [
        row.client_user_id
        for row in db.query(CoachClient.client_user_id)
        .filter(CoachClient.coach_user_id == coach.id, CoachClient.status == "active")
        .all()
    ]


def _is_coach_client(db: Session, coach: User, client: User) -> bool:
    return (
        db.query(CoachClient)
        .filter(
            CoachClient.coach_user_id == coach.id,
            CoachClient.client_user_id == client.id,
            CoachClient.status == "active",
        )
        .first()
        is not None
    )


def get_client_managed_by_coach(db: Session, coach: User, client_id: int) -> User:
    """Return an active client from this coach's own client list."""
    client = (
        db.query(User)
        .options(joinedload(User.profile))
        .join(CoachClient, CoachClient.client_user_id == User.id)
        .filter(
            CoachClient.coach_user_id == coach.id,
            CoachClient.client_user_id == client_id,
            CoachClient.status == "active",
            User.is_active.is_(True),
        )
        .first()
    )
    if not client:
        raise ProgramError("Client link not found")
    return client


def _get_existing_user_by_telegram_id(db: Session, telegram_user_id: int) -> User | None:
    return db.query(User).filter(User.telegram_user_id == telegram_user_id).first()


def _resolve_manageable_user(
    db: Session,
    current_user: User,
    target_telegram_user_id: int | None,
) -> User:
    if not target_telegram_user_id or target_telegram_user_id == current_user.telegram_user_id:
        return current_user

    target_user = _get_existing_user_by_telegram_id(db, target_telegram_user_id)
    if not target_user:
        raise ProgramError("Client is not linked to coach")

    if current_user.is_admin:
        return target_user

    if current_user.is_coach and _is_coach_client(db, current_user, target_user):
        return target_user

    raise ProgramError("No permission to manage this user")


def _can_manage_user_id(db: Session, current_user: User, owner_user_id: int | None) -> bool:
    if current_user.is_admin:
        return True
    if owner_user_id is None:
        return False
    if owner_user_id == current_user.id:
        return True
    return current_user.is_coach and owner_user_id in _coach_client_ids(db, current_user)


def _set_profile_name(db: Session, user: User, full_name: str | None) -> None:
    if not full_name:
        return

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if profile:
        profile.full_name = full_name
    else:
        db.add(UserProfile(user_id=user.id, full_name=full_name))


def _client_entry_from_user(db: Session, user: User) -> dict:
    profile = user.profile
    return {
        "id": user.id,
        "invite_id": None,
        "telegram_user_id": user.telegram_user_id,
        "username": user.username,
        "full_name": profile.full_name if profile else None,
        "goal": profile.goal if profile else None,
        "level": profile.level if profile else None,
        "height_cm": profile.height_cm if profile else None,
        "weight_kg": profile.weight_kg if profile else None,
        "workouts_per_week": profile.workouts_per_week if profile else None,
        "cardio_trainings_per_week": (profile.cardio_trainings_per_week if profile else None),
        "kbju": get_nutrition_target_for_user(db, user),
        "status": "active",
    }


def _client_entry_from_invite(invite: CoachClientInvite) -> dict:
    synthetic_username = (
        invite.telegram_user_id is not None and invite.username == f"user_{invite.telegram_user_id}"
    )
    return {
        "id": None,
        "invite_id": invite.id,
        "telegram_user_id": invite.telegram_user_id,
        "username": None if synthetic_username else invite.username,
        "full_name": invite.full_name,
        "goal": None,
        "level": None,
        "height_cm": None,
        "weight_kg": None,
        "workouts_per_week": None,
        "cardio_trainings_per_week": None,
        "kbju": None,
        "status": "pending",
    }


def _trainer_entry_from_user(user: User) -> dict:
    display_name = user.profile.full_name if user.profile else None
    if not display_name:
        name_parts = [user.first_name, user.last_name]
        display_name = " ".join(part for part in name_parts if part) or None

    return {
        "id": user.id,
        "telegram_user_id": user.telegram_user_id,
        "username": user.username,
        "full_name": display_name,
        "can_open_chat": bool(user.username),
        "chat_url": f"https://t.me/{user.username}" if user.username else None,
        "chat_unavailable_reason": None
        if user.username
        else "У тренера не указан username, открыть чат из приложения нельзя",
    }


def _queue_client_request_notification(
    db: Session, coach: User, client: User, invite: CoachClientInvite
) -> None:
    db.flush()
    coach_name = _trainer_entry_from_user(coach)["full_name"] or coach.username or "Тренер"
    db.add(
        Notification(
            user_id=client.id,
            channel="telegram",
            title=f"Тренер {coach_name} хочет добавить вас в качестве клиента",
            body="Откройте приложение, чтобы принять или отклонить запрос.",
            scheduled_for=now_msk_naive(),
            scheduled_for_utc=datetime.now(UTC).replace(tzinfo=None),
            status="queued",
            dedupe_key=f"trainer_request:{invite.id}",
        )
    )


def cancel_client_request_notification(db: Session, invite_id: int) -> None:
    db.query(Notification).filter(
        Notification.dedupe_key == f"trainer_request:{invite_id}",
        Notification.status == "queued",
    ).update({Notification.status: "cancelled"}, synchronize_session=False)


def add_client_for_coach(
    db: Session,
    coach: User,
    telegram_user_id: int | None = None,
    username: str | None = None,
    client_code: str | None = None,
    source: str | None = None,
    full_name: str | None = None,
    allow_unregistered_username: bool = True,
) -> dict:
    normalized_username = normalize_telegram_username(username)
    normalized_name = full_name.strip() if full_name else None
    normalized_code = client_code.strip().upper() if client_code else None

    if not telegram_user_id and not normalized_username and not normalized_code:
        raise ProgramError("Укажите код клиента или username")

    if telegram_user_id == coach.telegram_user_id or (
        normalized_username and normalized_username == coach.username
    ):
        raise ProgramError("Cannot add yourself as a client")

    db.query(User).filter(User.id == coach.id).with_for_update().one()

    if normalized_code:
        client = (
            db.query(User)
            .options(joinedload(User.profile))
            .filter(User.client_code == normalized_code, User.is_active.is_(True))
            .first()
        )
        if not client:
            raise ProgramError("Клиент с таким кодом не найден")
        request_source = "client_code"
    elif telegram_user_id:
        client = _get_existing_user_by_telegram_id(db, telegram_user_id)
        request_source = source or "telegram_user_picker"
    else:
        client = (
            db.query(User)
            .options(joinedload(User.profile))
            .filter(func.lower(User.username) == normalized_username, User.is_active.is_(True))
            .first()
        )
        request_source = "username_search"

    if client:
        if client.id == coach.id:
            raise ProgramError("Cannot add yourself as a client")
        existing_link = (
            db.query(CoachClient)
            .filter(
                CoachClient.coach_user_id == coach.id,
                CoachClient.client_user_id == client.id,
                CoachClient.status == "active",
            )
            .first()
        )
        if existing_link:
            return _client_entry_from_user(db, client)

        invite = (
            db.query(CoachClientInvite)
            .filter(
                CoachClientInvite.coach_user_id == coach.id,
                CoachClientInvite.client_user_id == client.id,
                CoachClientInvite.status == "pending",
            )
            .first()
        )
        if invite:
            invite.telegram_user_id = client.telegram_user_id
            invite.username = normalize_telegram_username(client.username)
        else:
            invite = CoachClientInvite(
                coach_user_id=coach.id,
                client_user_id=client.id,
                telegram_user_id=client.telegram_user_id,
                username=normalize_telegram_username(client.username),
                full_name=client.profile.full_name if client.profile else None,
                source=request_source,
                status="pending",
                expires_at=now_msk_naive() + timedelta(days=14),
            )
            db.add(invite)
            _queue_client_request_notification(db, coach, client, invite)
        db.commit()
        db.refresh(invite)
        return _client_entry_from_invite(invite)

    if telegram_user_id:
        raise ProgramError("Пользователь ещё не зарегистрирован в приложении")
    if not allow_unregistered_username:
        raise ProgramError("Пользователь с таким username не найден в приложении")

    invite = (
        db.query(CoachClientInvite)
        .filter(
            CoachClientInvite.coach_user_id == coach.id,
            CoachClientInvite.username == normalized_username,
            CoachClientInvite.status == "pending",
        )
        .first()
    )
    if invite:
        invite.full_name = normalized_name or invite.full_name
    else:
        invite = CoachClientInvite(
            coach_user_id=coach.id,
            telegram_user_id=None,
            username=normalized_username,
            full_name=normalized_name,
            source="username_search",
            status="pending",
            expires_at=now_msk_naive() + timedelta(days=14),
        )
        db.add(invite)

    db.commit()
    db.refresh(invite)
    return _client_entry_from_invite(invite)


def remove_client_for_coach(db: Session, coach: User, client_id: int) -> None:
    link = (
        db.query(CoachClient)
        .filter(
            CoachClient.coach_user_id == coach.id,
            CoachClient.client_user_id == client_id,
            CoachClient.status == "active",
        )
        .first()
    )
    if not link:
        raise ProgramError("Client link not found")

    link.status = "ended"
    link.ended_at = now_msk_naive()
    link.ended_reason = "removed_by_trainer"
    db.commit()


def remove_pending_client_invite(db: Session, coach: User, username: str) -> None:
    normalized_username = normalize_telegram_username(username)
    if not normalized_username:
        raise ProgramError("Client invite not found")

    deleted = (
        db.query(CoachClientInvite)
        .filter(
            CoachClientInvite.coach_user_id == coach.id,
            CoachClientInvite.username == normalized_username,
        )
        .delete(synchronize_session=False)
    )
    if not deleted:
        raise ProgramError("Client invite not found")

    db.commit()


def get_current_trainer(db: Session, client: User) -> dict | None:
    trainer = (
        db.query(User)
        .join(CoachClient, CoachClient.coach_user_id == User.id)
        .options(joinedload(User.profile))
        .filter(
            CoachClient.client_user_id == client.id,
            CoachClient.status == "active",
            User.is_active.is_(True),
            or_(User.is_coach.is_(True), User.is_admin.is_(True)),
        )
        .order_by(CoachClient.id.desc())
        .first()
    )
    if not trainer:
        return None
    return _trainer_entry_from_user(trainer)


def remove_current_trainer(db: Session, client: User) -> None:
    relation = (
        db.query(CoachClient)
        .filter(CoachClient.client_user_id == client.id, CoachClient.status == "active")
        .first()
    )
    if relation:
        relation.status = "ended"
        relation.ended_at = now_msk_naive()
        relation.ended_reason = "removed_by_client"
    db.commit()


def list_coach_invites_for_client(db: Session, client: User) -> list[dict]:
    username = normalize_telegram_username(client.username)
    filters = [CoachClientInvite.client_user_id == client.id]
    filters.append(CoachClientInvite.telegram_user_id == client.telegram_user_id)
    if username:
        filters.append(CoachClientInvite.username == username)

    invites = (
        db.query(CoachClientInvite)
        .filter(CoachClientInvite.status == "pending", or_(*filters))
        .order_by(CoachClientInvite.id.desc())
        .all()
    )
    result: list[dict] = []
    expired = False
    current_trainer = get_current_trainer(db, client)
    for invite in invites:
        if invite.expires_at and invite.expires_at < now_msk_naive():
            invite.status = "expired"
            cancel_client_request_notification(db, invite.id)
            expired = True
            continue
        coach = db.query(User).filter(User.id == invite.coach_user_id).first()
        if not coach or not coach.is_active or not (coach.is_coach or coach.is_admin):
            continue
        result.append(
            {
                "id": invite.id,
                "coach": _trainer_entry_from_user(coach),
                "created_at": invite.created_at,
                "source": invite.source,
                "expires_at": invite.expires_at,
                "requires_trainer_change": bool(
                    current_trainer and current_trainer["id"] != coach.id
                ),
                "already_current_trainer": bool(
                    current_trainer and current_trainer["id"] == coach.id
                ),
                "current_trainer": current_trainer,
            }
        )
    if expired:
        db.commit()
    return result


def respond_to_coach_invite(
    db: Session,
    client: User,
    invite_id: int,
    *,
    accept: bool,
) -> None:
    username = normalize_telegram_username(client.username)
    filters = [CoachClientInvite.client_user_id == client.id]
    filters.append(CoachClientInvite.telegram_user_id == client.telegram_user_id)
    if username:
        filters.append(CoachClientInvite.username == username)

    invite = (
        db.query(CoachClientInvite).filter(CoachClientInvite.id == invite_id, or_(*filters)).first()
    )
    if not invite:
        raise ProgramError("Client invite not found")

    if invite.status == "accepted" and accept:
        return
    if invite.status != "pending":
        raise ProgramError("Client invite not found")
    if invite.expires_at and invite.expires_at < now_msk_naive():
        invite.status = "expired"
        cancel_client_request_notification(db, invite.id)
        db.commit()
        raise ProgramError("Срок действия приглашения истёк")

    if accept:
        coach = db.query(User).filter(User.id == invite.coach_user_id).first()
        if not coach or not coach.is_active or not (coach.is_coach or coach.is_admin):
            raise ProgramError("Coach is not available")
        db.query(User).filter(User.id == client.id).with_for_update().one()
        active_relation = (
            db.query(CoachClient)
            .filter(CoachClient.client_user_id == client.id, CoachClient.status == "active")
            .first()
        )
        if active_relation and active_relation.coach_user_id != coach.id:
            active_relation.status = "ended"
            active_relation.ended_at = now_msk_naive()
            active_relation.ended_reason = "client_switched_trainer"
        if not active_relation or active_relation.coach_user_id != coach.id:
            db.add(
                CoachClient(
                    coach_user_id=coach.id,
                    client_user_id=client.id,
                    status="active",
                    accepted_at=now_msk_naive(),
                )
            )
        invite.status = "accepted"
        invite.accepted_at = now_msk_naive()
        invite.client_user_id = client.id
    else:
        invite.status = "declined"
        invite.declined_at = now_msk_naive()
    cancel_client_request_notification(db, invite.id)
    db.commit()


def create_coach_invite_link(db: Session, coach: User) -> dict:
    raw_token = secrets.token_urlsafe(24)
    invite = CoachClientInvite(
        coach_user_id=coach.id,
        source="invite_link",
        status="pending",
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=now_msk_naive() + timedelta(days=14),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    start_param = f"trainer_{raw_token}"
    bot_username = settings.telegram_bot_username.strip().lstrip("@")
    return {
        "invite_id": invite.id,
        "start_param": start_param,
        "url": f"https://t.me/{bot_username}?startapp={start_param}" if bot_username else None,
        "expires_at": invite.expires_at,
    }


def claim_coach_invite_link(db: Session, client: User, raw_token: str) -> dict:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    invite = (
        db.query(CoachClientInvite)
        .filter(CoachClientInvite.token_hash == token_hash)
        .with_for_update()
        .first()
    )
    if not invite or invite.status not in {"pending", "accepted"}:
        raise ProgramError("Приглашение не найдено или уже недействительно")
    if invite.expires_at and invite.expires_at < now_msk_naive():
        invite.status = "expired"
        db.commit()
        raise ProgramError("Срок действия приглашения истёк")
    if invite.client_user_id and invite.client_user_id != client.id:
        raise ProgramError("Это приглашение уже использовано другим клиентом")
    if invite.coach_user_id == client.id:
        raise ProgramError("Нельзя принять собственное приглашение")

    db.query(User).filter(User.id == client.id).with_for_update().one()

    duplicate = (
        db.query(CoachClientInvite)
        .filter(
            CoachClientInvite.coach_user_id == invite.coach_user_id,
            CoachClientInvite.client_user_id == client.id,
            CoachClientInvite.status == "pending",
            CoachClientInvite.id != invite.id,
        )
        .first()
    )
    if duplicate:
        invite.status = "revoked"
        invite = duplicate
    else:
        invite.client_user_id = client.id
        invite.telegram_user_id = client.telegram_user_id
        invite.username = normalize_telegram_username(client.username)
        invite.full_name = client.profile.full_name if client.profile else None
    db.commit()
    coach = (
        db.query(User)
        .options(joinedload(User.profile))
        .filter(User.id == invite.coach_user_id)
        .first()
    )
    if not coach or not coach.is_active or not (coach.is_coach or coach.is_admin):
        raise ProgramError("Тренер недоступен")
    return {
        "id": invite.id,
        "coach": _trainer_entry_from_user(coach),
        "created_at": invite.created_at,
        "source": invite.source,
        "expires_at": invite.expires_at,
    }


def build_template_response(item: ProgramTemplate, db: Session, current_user: User) -> dict:
    visible_map = get_visible_exercise_display_map(db, current_user)
    owner = (
        db.query(User).filter(User.id == item.owner_user_id).first() if item.owner_user_id else None
    )
    assignment = (
        db.query(UserProgram)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.template_id == item.id,
        )
        .order_by(UserProgram.is_active.desc(), UserProgram.id.desc())
        .first()
    )
    assigned_by = (
        db.query(User).filter(User.id == assignment.assigned_by_user_id).first()
        if assignment and assignment.assigned_by_user_id
        else None
    )

    return {
        "id": item.id,
        "title": item.title,
        "slug": item.slug,
        "goal": item.goal,
        "level": item.level,
        "owner_user_id": item.owner_user_id,
        "owner_telegram_user_id": owner.telegram_user_id if owner else None,
        "owner_full_name": owner.profile.full_name if owner and owner.profile else None,
        "created_by_user_id": item.created_by_user_id,
        "is_public": item.is_public,
        "is_example": _is_example_template(item),
        "is_assigned_to_current_user": assignment is not None,
        "is_active_for_current_user": bool(assignment and assignment.is_active),
        "assigned_by_user_id": assignment.assigned_by_user_id if assignment else None,
        "assigned_by_full_name": (
            assigned_by.profile.full_name if assigned_by and assigned_by.profile else None
        ),
        "days": [
            {
                "id": day.id,
                "day_number": day.day_number,
                "title": day.title,
                "exercises": [
                    {
                        "id": ex.id,
                        "exercise_id": ex.exercise_id,
                        "exercise_title": (
                            visible_map[ex.exercise_id].title
                            if ex.exercise_id in visible_map
                            else ex.exercise.title
                        ),
                        "prescribed_sets": ex.prescribed_sets,
                        "prescribed_reps": ex.prescribed_reps,
                        "rest_seconds": ex.rest_seconds,
                        "notes": ex.notes,
                    }
                    for ex in sorted(day.exercises, key=lambda row: row.sort_order)
                ],
            }
            for day in sorted(item.days, key=lambda row: row.day_number)
        ],
    }


def list_exercises(db: Session, current_user: User) -> list[Exercise]:
    rows = _load_visible_exercise_rows(db, current_user)

    client_ids = _coach_client_ids(db, current_user) if current_user.is_coach else []
    if client_ids:
        rows.extend(
            db.query(Exercise)
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
    difficulty_level: str = "intermediate",
    target_telegram_user_id: int | None = None,
) -> Exercise:
    normalized_title = title.strip()
    normalized_muscle = _normalize_optional_text(primary_muscle)
    normalized_equipment = _normalize_optional_text(equipment)

    if not normalized_title:
        raise ProgramError("Exercise title is required")

    owner_user = _resolve_manageable_user(db, current_user, target_telegram_user_id)
    is_global_admin_exercise = current_user.is_admin and owner_user.id == current_user.id
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
        difficulty_level=difficulty_level,
        created_by_user_id=None if is_global_admin_exercise else owner_user.id,
        source_exercise_id=None,
        is_deleted=False,
    )
    db.add(exercise)
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
        and current_user.is_admin
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
        exercise.difficulty_level = difficulty_level
        exercise.is_deleted = False
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
            override.difficulty_level = difficulty_level
            override.is_deleted = False

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
        if current_user.is_admin and owner_user.id == current_user.id:
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


def validate_program_payload(
    payload: ProgramTemplateCreate,
    require_coach_target: bool = True,
) -> None:
    if payload.goal not in GOALS:
        raise ProgramError("Unsupported goal")
    if payload.level not in LEVELS:
        raise ProgramError("Unsupported level")
    if payload.mode not in MODES:
        raise ProgramError("Unsupported mode")
    if not payload.days:
        raise ProgramError("At least one day is required")
    if payload.mode == "coach" and require_coach_target and not payload.target_telegram_user_id:
        raise ProgramError("target_telegram_user_id is required for coach mode")


def _exercise_scope_for_template(
    current_user: User,
    target_user: User,
    is_public: bool,
) -> User:
    return current_user if is_public else target_user


def _template_owner(db: Session, template: ProgramTemplate) -> User | None:
    if not template.owner_user_id:
        return None
    return db.query(User).filter(User.id == template.owner_user_id).first()


def _created_by_current_user_with_manageable_owner(
    db: Session,
    current_user: User,
    template: ProgramTemplate,
) -> bool:
    if template.created_by_user_id != current_user.id:
        return False
    return template.owner_user_id is None or _can_manage_user_id(
        db,
        current_user,
        template.owner_user_id,
    )


def _can_view_template(db: Session, current_user: User, template: ProgramTemplate) -> bool:
    return (
        current_user.is_admin
        or template.is_public
        or template.owner_user_id == current_user.id
        or _created_by_current_user_with_manageable_owner(db, current_user, template)
        or (current_user.is_coach and template.owner_user_id in _coach_client_ids(db, current_user))
        or db.query(UserProgram.id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.template_id == template.id,
        )
        .first()
        is not None
    )


def _can_manage_template(db: Session, current_user: User, template: ProgramTemplate) -> bool:
    return (
        current_user.is_admin
        or template.owner_user_id == current_user.id
        or _created_by_current_user_with_manageable_owner(db, current_user, template)
        or (current_user.is_coach and template.owner_user_id in _coach_client_ids(db, current_user))
    )


def create_template(
    db: Session,
    current_user: User,
    payload: ProgramTemplateCreate,
    target_user: User | None = None,
) -> ProgramTemplate:
    validate_program_payload(payload)

    is_public = current_user.is_admin
    owner_user = target_user if payload.mode == "coach" else current_user
    template = ProgramTemplate(
        slug=f"custom-{uuid4().hex[:10]}",
        title=payload.title,
        goal=payload.goal,
        level=payload.level,
        owner_user_id=None if is_public else owner_user.id,
        created_by_user_id=current_user.id,
        is_public=is_public,
    )
    db.add(template)
    db.flush()

    exercise_scope_user = _exercise_scope_for_template(current_user, owner_user, is_public)
    visible_effective_ids = {
        _effective_exercise_id(ex) for ex in _load_visible_exercise_rows(db, exercise_scope_user)
    }

    for index, day in enumerate(payload.days, start=1):
        day_row = ProgramTemplateDay(
            program_id=template.id,
            day_number=index,
            title=day.title,
        )
        db.add(day_row)
        db.flush()

        for sort_order, ex in enumerate(day.exercises, start=1):
            if ex.exercise_id not in visible_effective_ids:
                raise ProgramError("Exercise is not available for current user")

            db.add(
                ProgramTemplateExercise(
                    day_id=day_row.id,
                    exercise_id=ex.exercise_id,
                    sort_order=sort_order,
                    prescribed_sets=ex.prescribed_sets,
                    prescribed_reps=ex.prescribed_reps,
                    rest_seconds=ex.rest_seconds,
                    notes=ex.notes,
                )
            )

    db.flush()
    return template


def assign_template_to_user(
    db: Session,
    template: ProgramTemplate,
    target_user: User,
    assigned_by: User,
    start_date: date | None = None,
) -> tuple[UserProgram, int]:
    # Сериализуем конкурирующие назначения для одного пользователя. Частичный
    # unique index остаётся последней линией защиты на уровне БД.
    db.query(User).filter(User.id == target_user.id).with_for_update().one()
    db.query(UserProgram).filter(
        UserProgram.user_id == target_user.id,
        UserProgram.is_active.is_(True),
    ).update({"is_active": False})

    # A fresh coach assignment should put a previously hidden example back into
    # the client's library, where the client can hide it again if desired.
    db.query(HiddenProgramTemplate).filter(
        HiddenProgramTemplate.user_id == target_user.id,
        HiddenProgramTemplate.template_id == template.id,
    ).delete(synchronize_session=False)

    user_program = UserProgram(
        user_id=target_user.id,
        template_id=template.id,
        assigned_by_user_id=assigned_by.id,
        is_active=True,
    )
    db.add(user_program)
    db.flush()

    workouts: list[UserWorkout] = []
    effective_start_date = start_date or today_for_user(target_user)
    created = 0

    for offset, day in enumerate(sorted(template.days, key=lambda row: row.day_number)):
        workout = UserWorkout(
            user_program_id=user_program.id,
            scheduled_date=effective_start_date + timedelta(days=offset),
            day_number=day.day_number,
            title=day.title,
            status="planned",
        )
        db.add(workout)
        db.flush()
        workouts.append(workout)

        for exercise_item in sorted(day.exercises, key=lambda row: row.sort_order):
            workout_exercise = UserWorkoutExercise(
                workout_id=workout.id,
                exercise_id=exercise_item.exercise_id,
                sort_order=exercise_item.sort_order,
                prescribed_sets=exercise_item.prescribed_sets,
                prescribed_reps=exercise_item.prescribed_reps,
                rest_seconds=exercise_item.rest_seconds,
            )
            db.add(workout_exercise)
            db.flush()

            for set_number in range(1, exercise_item.prescribed_sets + 1):
                db.add(
                    UserWorkoutSet(
                        workout_exercise_id=workout_exercise.id,
                        set_number=set_number,
                        actual_reps=None,
                        actual_weight=None,
                        is_completed=False,
                    )
                )

        created += 1

    db.flush()
    return user_program, created


def create_and_optionally_assign_program(
    db: Session, current_user: User, payload: ProgramTemplateCreate
):
    target_user = current_user

    if payload.mode == "coach":
        if not current_user.is_coach and not current_user.is_admin:
            raise ProgramError("No permission to assign program as coach")

        if current_user.is_admin:
            target_user = get_or_create_user_by_telegram_id(
                db,
                payload.target_telegram_user_id,
                payload.target_full_name,
            )
        else:
            target_user = _resolve_manageable_user(
                db,
                current_user,
                payload.target_telegram_user_id,
            )

    template = create_template(db, current_user, payload, target_user)
    assigned_program = None
    workouts_created = 0

    if payload.assign_after_create:
        assigned_program, workouts_created = assign_template_to_user(
            db,
            template,
            target_user,
            current_user,
        )

    db.commit()

    template = (
        db.query(ProgramTemplate)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
            .joinedload(ProgramTemplateExercise.exercise)
        )
        .filter(ProgramTemplate.id == template.id)
        .first()
    )

    target_profile = db.query(UserProfile).filter(UserProfile.user_id == target_user.id).first()
    target_user_data = {
        "id": target_user.id,
        "telegram_user_id": target_user.telegram_user_id,
        "full_name": target_profile.full_name if target_profile else None,
    }

    return template, assigned_program, workouts_created, target_user_data


def list_user_templates(db: Session, current_user: User) -> list[ProgramTemplate]:
    client_ids = _coach_client_ids(db, current_user) if current_user.is_coach else []
    visibility_filters = [
        ProgramTemplate.is_public.is_(True),
        ProgramTemplate.owner_user_id == current_user.id,
        ProgramTemplate.created_by_user_id == current_user.id,
    ]
    if client_ids:
        visibility_filters.append(ProgramTemplate.owner_user_id.in_(client_ids))

    assigned_template_ids = db.query(UserProgram.template_id).filter(
        UserProgram.user_id == current_user.id,
        UserProgram.template_id.is_not(None),
    )
    visibility_filters.append(ProgramTemplate.id.in_(assigned_template_ids))

    hidden_template_ids = db.query(HiddenProgramTemplate.template_id).filter(
        HiddenProgramTemplate.user_id == current_user.id
    )

    templates = (
        db.query(ProgramTemplate)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
            .joinedload(ProgramTemplateExercise.exercise)
        )
        .filter(or_(*visibility_filters))
        .filter(ProgramTemplate.id.not_in(hidden_template_ids))
        .filter(ProgramTemplate.slug != LEGACY_DEMO_TEMPLATE_SLUG)
        .order_by(ProgramTemplate.id.desc())
        .all()
    )
    return [template for template in templates if _can_view_template(db, current_user, template)]


def list_hidden_example_templates(db: Session, current_user: User) -> list[ProgramTemplate]:
    return (
        db.query(ProgramTemplate)
        .join(HiddenProgramTemplate, HiddenProgramTemplate.template_id == ProgramTemplate.id)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
            .joinedload(ProgramTemplateExercise.exercise)
        )
        .filter(
            HiddenProgramTemplate.user_id == current_user.id,
            ProgramTemplate.is_public.is_(True),
            ProgramTemplate.owner_user_id.is_(None),
            ProgramTemplate.created_by_user_id.is_(None),
            ProgramTemplate.slug != LEGACY_DEMO_TEMPLATE_SLUG,
        )
        .order_by(HiddenProgramTemplate.hidden_at.desc())
        .all()
    )


def get_template_for_user(
    db: Session,
    current_user: User,
    template_id: int,
) -> ProgramTemplate:
    template = (
        db.query(ProgramTemplate)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
            .joinedload(ProgramTemplateExercise.exercise)
        )
        .filter(
            ProgramTemplate.id == template_id,
            ProgramTemplate.slug != LEGACY_DEMO_TEMPLATE_SLUG,
        )
        .first()
    )
    if not template:
        raise ProgramError("Template not found")

    if _is_template_hidden(db, current_user, template.id):
        raise ProgramError("Template not found")

    if not _can_view_template(db, current_user, template):
        raise ProgramError("No permission to view template")

    return template


def update_template_for_user(
    db: Session,
    current_user: User,
    template_id: int,
    payload: ProgramTemplateCreate,
) -> ProgramTemplate:
    template = (
        db.query(ProgramTemplate)
        .filter(
            ProgramTemplate.id == template_id,
            ProgramTemplate.slug != LEGACY_DEMO_TEMPLATE_SLUG,
        )
        .first()
    )
    if not template:
        raise ProgramError("Template not found")

    if not _can_manage_template(db, current_user, template):
        raise ProgramError("No permission to edit template")

    validate_program_payload(
        payload,
        require_coach_target=template.owner_user_id is None and payload.mode == "coach",
    )

    template.title = payload.title
    template.goal = payload.goal
    template.level = payload.level

    target_user = _template_owner(db, template) or current_user
    if not template.is_public:
        if payload.mode == "coach" and payload.target_telegram_user_id:
            target_user = _resolve_manageable_user(
                db,
                current_user,
                payload.target_telegram_user_id,
            )
            template.owner_user_id = target_user.id
        elif payload.mode == "self" and template.owner_user_id in (None, current_user.id):
            target_user = current_user
            template.owner_user_id = current_user.id

    old_day_ids = [
        day_id
        for (day_id,) in db.query(ProgramTemplateDay.id)
        .filter(ProgramTemplateDay.program_id == template.id)
        .all()
    ]

    if old_day_ids:
        db.query(ProgramTemplateExercise).filter(
            ProgramTemplateExercise.day_id.in_(old_day_ids)
        ).delete(synchronize_session=False)
        db.query(ProgramTemplateDay).filter(ProgramTemplateDay.id.in_(old_day_ids)).delete(
            synchronize_session=False
        )
        db.flush()

    visible_effective_ids = {
        _effective_exercise_id(ex) for ex in _load_visible_exercise_rows(db, target_user)
    }

    for index, day in enumerate(payload.days, start=1):
        day_row = ProgramTemplateDay(
            program_id=template.id,
            day_number=index,
            title=day.title,
        )
        db.add(day_row)
        db.flush()

        for sort_order, ex in enumerate(day.exercises, start=1):
            if ex.exercise_id not in visible_effective_ids:
                raise ProgramError("Exercise is not available for current user")

            db.add(
                ProgramTemplateExercise(
                    day_id=day_row.id,
                    exercise_id=ex.exercise_id,
                    sort_order=sort_order,
                    prescribed_sets=ex.prescribed_sets,
                    prescribed_reps=ex.prescribed_reps,
                    rest_seconds=ex.rest_seconds,
                    notes=ex.notes,
                )
            )

    db.commit()
    return get_template_for_user(db, current_user, template.id)


def list_clients(db: Session, coach: User) -> list[dict]:
    clients = (
        db.query(User)
        .join(CoachClient, CoachClient.client_user_id == User.id)
        .options(joinedload(User.profile))
        .filter(CoachClient.coach_user_id == coach.id, CoachClient.status == "active")
        .order_by(User.id.desc())
        .all()
    )
    invites = (
        db.query(CoachClientInvite)
        .filter(
            CoachClientInvite.coach_user_id == coach.id,
            CoachClientInvite.status == "pending",
            or_(
                CoachClientInvite.expires_at.is_(None),
                CoachClientInvite.expires_at >= now_msk_naive(),
            ),
        )
        .order_by(CoachClientInvite.id.desc())
        .all()
    )

    return [_client_entry_from_user(db, user) for user in clients] + [
        _client_entry_from_invite(invite) for invite in invites
    ]


def list_coach_assigned_programs(db: Session, coach: User) -> list[dict]:
    """Return programs this coach assigned to clients they currently manage."""
    rows = (
        db.query(UserProgram, User)
        .join(User, User.id == UserProgram.user_id)
        .join(
            CoachClient,
            CoachClient.client_user_id == UserProgram.user_id,
        )
        .options(
            joinedload(UserProgram.template),
            joinedload(UserProgram.workouts),
            joinedload(User.profile),
        )
        .filter(
            CoachClient.coach_user_id == coach.id,
            CoachClient.status == "active",
            UserProgram.assigned_by_user_id == coach.id,
        )
        .order_by(UserProgram.assigned_at.desc(), UserProgram.id.desc())
        .all()
    )

    result: list[dict] = []
    for program, client in rows:
        workouts = list(program.workouts)
        completed = sum(workout.status == "completed" for workout in workouts)
        planned = sum(workout.status == "planned" for workout in workouts)
        today = today_for_user(client)
        upcoming_dates = [
            workout.scheduled_date
            for workout in workouts
            if workout.status != "completed" and workout.scheduled_date >= today
        ]
        profile = client.profile
        template = program.template
        result.append(
            {
                "id": program.id,
                "client_id": client.id,
                "client_telegram_user_id": client.telegram_user_id,
                "client_username": client.username,
                "client_full_name": profile.full_name if profile else None,
                "template_id": program.template_id,
                "title": template.title if template else "Архивная программа",
                "goal": template.goal if template else None,
                "level": template.level if template else None,
                "assigned_at": program.assigned_at,
                "is_active": program.is_active,
                "workouts_total": len(workouts),
                "workouts_completed": completed,
                "workouts_planned": planned,
                "next_workout_date": min(upcoming_dates) if upcoming_dates else None,
            }
        )
    return result


def assign_template_to_self(
    db: Session,
    current_user: User,
    template_id: int,
    start_date: date | None = None,
) -> tuple[UserProgram, int]:
    template = (
        db.query(ProgramTemplate)
        .options(joinedload(ProgramTemplate.days).joinedload(ProgramTemplateDay.exercises))
        .filter(
            ProgramTemplate.id == template_id,
            ProgramTemplate.slug != LEGACY_DEMO_TEMPLATE_SLUG,
        )
        .first()
    )
    if not template:
        raise ProgramError("Template not found")

    if _is_template_hidden(db, current_user, template.id):
        raise ProgramError("Template not found")

    can_use = (
        current_user.is_admin
        or template.is_public
        or template.owner_user_id == current_user.id
        or (
            template.created_by_user_id == current_user.id
            and template.owner_user_id in (None, current_user.id)
        )
        or db.query(UserProgram.id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.template_id == template.id,
        )
        .first()
        is not None
    )
    if not can_use:
        raise ProgramError("No permission to use template")

    program, created = assign_template_to_user(
        db, template, current_user, current_user, start_date=start_date
    )
    db.commit()
    db.refresh(program)
    return program, created


def delete_template_cascade(db: Session, template: ProgramTemplate) -> None:
    # Назначения уже содержат snapshot тренировок. Отвязываем их от шаблона,
    # чтобы удаление шаблона/тренера не уничтожало историю других пользователей.
    db.query(UserProgram).filter(UserProgram.template_id == template.id).update(
        {"template_id": None},
        synchronize_session=False,
    )
    db.query(HiddenProgramTemplate).filter(HiddenProgramTemplate.template_id == template.id).delete(
        synchronize_session=False
    )

    days = db.query(ProgramTemplateDay).filter(ProgramTemplateDay.program_id == template.id).all()
    day_ids = [item.id for item in days]

    if day_ids:
        db.query(ProgramTemplateExercise).filter(
            ProgramTemplateExercise.day_id.in_(day_ids)
        ).delete(synchronize_session=False)

        db.query(ProgramTemplateDay).filter(ProgramTemplateDay.id.in_(day_ids)).delete(
            synchronize_session=False
        )

    db.delete(template)


def delete_template_for_user(
    db: Session,
    current_user: User,
    template_id: int,
) -> None:
    template = (
        db.query(ProgramTemplate)
        .filter(
            ProgramTemplate.id == template_id,
            ProgramTemplate.slug != LEGACY_DEMO_TEMPLATE_SLUG,
        )
        .first()
    )
    if not template:
        raise ProgramError("Template not found")

    if _is_example_template(template):
        if not _can_view_template(db, current_user, template):
            raise ProgramError("No permission to delete template")
        if not _is_template_hidden(db, current_user, template.id):
            db.add(HiddenProgramTemplate(user_id=current_user.id, template_id=template.id))
        db.commit()
        return

    if not _can_manage_template(db, current_user, template):
        raise ProgramError("No permission to delete template")

    delete_template_cascade(db, template)
    db.commit()


def restore_example_template_for_user(
    db: Session,
    current_user: User,
    template_id: int,
) -> None:
    hidden = (
        db.query(HiddenProgramTemplate)
        .join(ProgramTemplate, ProgramTemplate.id == HiddenProgramTemplate.template_id)
        .filter(
            HiddenProgramTemplate.user_id == current_user.id,
            HiddenProgramTemplate.template_id == template_id,
            ProgramTemplate.is_public.is_(True),
            ProgramTemplate.owner_user_id.is_(None),
            ProgramTemplate.created_by_user_id.is_(None),
        )
        .first()
    )
    if not hidden:
        raise ProgramError("Hidden template not found")
    db.delete(hidden)
    db.commit()


def _is_example_template(template: ProgramTemplate) -> bool:
    return bool(
        template.is_public
        and template.owner_user_id is None
        and template.created_by_user_id is None
    )


def _is_template_hidden(
    db: Session,
    current_user: User,
    template_id: int,
) -> bool:
    return (
        db.query(HiddenProgramTemplate.id)
        .filter(
            HiddenProgramTemplate.user_id == current_user.id,
            HiddenProgramTemplate.template_id == template_id,
        )
        .first()
        is not None
    )
