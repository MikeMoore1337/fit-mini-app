from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.core.timezone import now_msk_naive, today_for_user
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.program import (
    HiddenProgramTemplate,
    ProgramTemplate,
    ProgramTemplateDay,
    ProgramTemplateExercise,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import CoachClient, CoachClientInvite, User, UserProfile
from fitminiapp_api.schemas.program import ProgramTemplateCreate
from fitminiapp_api.services.coach_clients import (
    _can_manage_user_id,
    _client_entry_from_invite,
    _client_entry_from_user,
    _coach_client_ids,
    _resolve_manageable_user,
    get_or_create_user_by_telegram_id,
)
from fitminiapp_api.services.exercise_catalog import (
    _effective_exercise_id,
    _load_visible_exercise_rows,
    get_visible_exercise_display_map,
)
from fitminiapp_api.services.program_common import ProgramError

GOALS = {"muscle_gain", "fat_loss", "maintenance", "recomposition"}
LEVELS = {"beginner", "intermediate", "advanced"}
MODES = {"self", "coach"}
LEGACY_DEMO_TEMPLATE_SLUG = "upper-lower-4x"


def _serialize_template_with_context(
    item: ProgramTemplate,
    *,
    visible_map: dict[int, Exercise],
    owners: dict[int, User],
    assignments: dict[int, UserProgram],
    assigners: dict[int, User],
) -> dict:
    owner = owners.get(item.owner_user_id) if item.owner_user_id else None
    assignment = assignments.get(item.id)
    assigned_by = (
        assigners.get(assignment.assigned_by_user_id)
        if assignment and assignment.assigned_by_user_id is not None
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


def build_template_responses(
    items: list[ProgramTemplate],
    db: Session,
    current_user: User,
) -> list[dict]:
    if not items:
        return []

    visible_map = get_visible_exercise_display_map(db, current_user)
    owner_ids = {item.owner_user_id for item in items if item.owner_user_id is not None}
    owners = {
        user.id: user
        for user in db.query(User)
        .options(joinedload(User.profile))
        .filter(User.id.in_(owner_ids))
        .all()
    }

    template_ids = [item.id for item in items]
    assignment_rows = (
        db.query(UserProgram)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.template_id.in_(template_ids),
        )
        .order_by(
            UserProgram.template_id.asc(),
            UserProgram.is_active.desc(),
            UserProgram.id.desc(),
        )
        .all()
    )
    assignments: dict[int, UserProgram] = {}
    for assignment in assignment_rows:
        if assignment.template_id is not None:
            assignments.setdefault(assignment.template_id, assignment)

    assigner_ids = {
        assignment.assigned_by_user_id
        for assignment in assignments.values()
        if assignment.assigned_by_user_id is not None
    }
    assigners = {
        user.id: user
        for user in db.query(User)
        .options(joinedload(User.profile))
        .filter(User.id.in_(assigner_ids))
        .all()
    }
    return [
        _serialize_template_with_context(
            item,
            visible_map=visible_map,
            owners=owners,
            assignments=assignments,
            assigners=assigners,
        )
        for item in items
    ]


def build_template_response(item: ProgramTemplate, db: Session, current_user: User) -> dict:
    return build_template_responses([item], db, current_user)[0]


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
    if owner_user is None:
        raise ProgramError("Target user is required in coach mode")
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

        if payload.target_telegram_user_id is None:
            raise ProgramError("Target Telegram user id is required in coach mode")
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

    loaded_template = (
        db.query(ProgramTemplate)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
            .joinedload(ProgramTemplateExercise.exercise)
        )
        .filter(ProgramTemplate.id == template.id)
        .first()
    )
    if loaded_template is None:
        raise ProgramError("Template not found after creation")

    target_profile = db.query(UserProfile).filter(UserProfile.user_id == target_user.id).first()
    target_user_data = {
        "id": target_user.id,
        "telegram_user_id": target_user.telegram_user_id,
        "full_name": target_profile.full_name if target_profile else None,
    }

    return loaded_template, assigned_program, workouts_created, target_user_data


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
    client_id_set = set(client_ids)
    assigned_id_set = {
        template_id
        for (template_id,) in db.query(UserProgram.template_id)
        .filter(
            UserProgram.user_id == current_user.id,
            UserProgram.template_id.is_not(None),
        )
        .all()
        if template_id is not None
    }
    return [
        template
        for template in templates
        if (
            current_user.is_admin
            or template.is_public
            or template.owner_user_id == current_user.id
            or (
                template.created_by_user_id == current_user.id
                and template.owner_user_id in ({None, current_user.id} | client_id_set)
            )
            or (current_user.is_coach and template.owner_user_id in client_id_set)
            or template.id in assigned_id_set
        )
    ]


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
        db.query(User, CoachClient.private_name)
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

    return [_client_entry_from_user(db, user, private_name) for user, private_name in clients] + [
        _client_entry_from_invite(invite) for invite in invites
    ]


def list_coach_assigned_programs(db: Session, coach: User) -> list[dict]:
    """Return programs this coach assigned to clients they currently manage."""
    rows = (
        db.query(UserProgram, User, CoachClient.private_name)
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
    for program, client, private_name in rows:
        workouts = list(program.workouts)
        completed = sum(workout.status == "completed" for workout in workouts)
        planned = sum(workout.status == "planned" for workout in workouts)
        today = today_for_user(client)
        upcoming_dates = [
            workout.scheduled_date
            for workout in workouts
            if workout.status != "completed" and workout.scheduled_date >= today
        ]
        template = program.template
        result.append(
            {
                "id": program.id,
                "client_id": client.id,
                "client_telegram_user_id": client.telegram_user_id,
                "client_username": client.username,
                "client_full_name": private_name,
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
