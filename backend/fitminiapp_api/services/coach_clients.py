from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.user import CoachClient, CoachClientInvite, User, UserProfile
from fitminiapp_api.services.client_codes import ensure_client_code
from fitminiapp_api.services.nutrition import get_nutrition_target_for_user
from fitminiapp_api.services.program_common import ProgramError
from fitminiapp_api.services.telegram_auth import normalize_telegram_username


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
