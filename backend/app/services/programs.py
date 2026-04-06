from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4

from app.models.exercise import Exercise
from app.models.notification import Notification, NotificationSetting
from app.models.program import (
    ProgramTemplate,
    ProgramTemplateDay,
    ProgramTemplateExercise,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from app.models.user import CoachClient, User, UserProfile
from app.schemas.program import ProgramTemplateCreate
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

GOALS = {"muscle_gain", "fat_loss", "maintenance", "recomposition"}
LEVELS = {"beginner", "intermediate", "advanced"}
MODES = {"self", "coach"}


class ProgramError(ValueError):
    pass


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
                full_name=full_name or f"Пользователь {telegram_user_id}",
            )
        )
        db.add(NotificationSetting(user_id=user.id))
        db.commit()
        db.refresh(user)
    return user


def ensure_coach_link(db: Session, coach: User, client: User) -> None:
    coach.is_coach = True
    if not coach.is_admin:
        coach.is_admin = True

    link = (
        db.query(CoachClient)
        .filter(
            CoachClient.coach_user_id == coach.id,
            CoachClient.client_user_id == client.id,
        )
        .first()
    )
    if not link:
        db.add(CoachClient(coach_user_id=coach.id, client_user_id=client.id))
        db.flush()


def build_template_response(item: ProgramTemplate) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "slug": item.slug,
        "goal": item.goal,
        "level": item.level,
        "owner_user_id": item.owner_user_id,
        "created_by_user_id": item.created_by_user_id,
        "is_public": item.is_public,
        "days": [
            {
                "id": day.id,
                "day_number": day.day_number,
                "title": day.title,
                "exercises": [
                    {
                        "id": ex.id,
                        "exercise_id": ex.exercise_id,
                        "exercise_title": ex.exercise.title,
                        "prescribed_sets": ex.prescribed_sets,
                        "prescribed_reps": ex.prescribed_reps,
                        "rest_seconds": ex.rest_seconds,
                        "notes": ex.notes,
                    }
                    for ex in day.exercises
                ],
            }
            for day in item.days
        ],
    }


def list_exercises(db: Session, current_user: User) -> list[Exercise]:
    return (
        db.query(Exercise)
        .filter(
            or_(
                Exercise.created_by_user_id.is_(None),
                Exercise.created_by_user_id == current_user.id,
            )
        )
        .order_by(Exercise.title.asc())
        .all()
    )


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or f"exercise-{uuid4().hex[:8]}"


def create_exercise(
    db: Session,
    current_user: User,
    title: str,
    primary_muscle: str,
    equipment: str,
) -> Exercise:
    normalized_title = title.strip()
    normalized_muscle = primary_muscle.strip()
    normalized_equipment = equipment.strip()

    if not normalized_title:
        raise ProgramError("Exercise title is required")
    if not normalized_muscle:
        raise ProgramError("Primary muscle is required")
    if not normalized_equipment:
        raise ProgramError("Equipment is required")

    existing_title = (
        db.query(Exercise)
        .filter(
            Exercise.title.ilike(normalized_title),
            or_(
                Exercise.created_by_user_id.is_(None),
                Exercise.created_by_user_id == current_user.id,
            ),
        )
        .first()
    )
    if existing_title:
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
        created_by_user_id=current_user.id,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def validate_program_payload(payload: ProgramTemplateCreate) -> None:
    if payload.goal not in GOALS:
        raise ProgramError("Unsupported goal")
    if payload.level not in LEVELS:
        raise ProgramError("Unsupported level")
    if payload.mode not in MODES:
        raise ProgramError("Unsupported mode")
    if not payload.days:
        raise ProgramError("At least one day is required")
    if payload.mode == "coach" and not payload.target_telegram_user_id:
        raise ProgramError("target_telegram_user_id is required for coach mode")


def create_template(
    db: Session,
    current_user: User,
    payload: ProgramTemplateCreate,
) -> ProgramTemplate:
    validate_program_payload(payload)

    template = ProgramTemplate(
        slug=f"custom-{uuid4().hex[:10]}",
        title=payload.title,
        goal=payload.goal,
        level=payload.level,
        owner_user_id=current_user.id if payload.mode == "self" else None,
        created_by_user_id=current_user.id,
        is_public=False,
    )
    db.add(template)
    db.flush()

    visible_exercise_ids = {
        ex.id for ex in list_exercises(db, current_user)
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
            if ex.exercise_id not in visible_exercise_ids:
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


def schedule_workout_notifications(
    db: Session,
    target_user: User,
    workouts: list[UserWorkout],
) -> None:
    settings = (
        db.query(NotificationSetting)
        .filter(NotificationSetting.user_id == target_user.id)
        .first()
    )
    if settings and not settings.workout_reminders_enabled:
        return

    reminder_hour = settings.reminder_hour if settings else 9

    for workout in workouts:
        scheduled = datetime.combine(
            workout.scheduled_date,
            time(reminder_hour, 0),
            tzinfo=UTC,
        )
        db.add(
            Notification(
                user_id=target_user.id,
                title="Напоминание о тренировке",
                body=f"Сегодня запланирована тренировка: {workout.title}",
                scheduled_for=scheduled,
                status="queued",
            )
        )


def assign_template_to_user(
    db: Session,
    template: ProgramTemplate,
    target_user: User,
    assigned_by: User,
) -> tuple[UserProgram, int]:
    db.query(UserProgram).filter(
        UserProgram.user_id == target_user.id,
        UserProgram.is_active.is_(True),
    ).update({"is_active": False})

    user_program = UserProgram(
        user_id=target_user.id,
        template_id=template.id,
        assigned_by_user_id=assigned_by.id,
        is_active=True,
    )
    db.add(user_program)
    db.flush()

    workouts: list[UserWorkout] = []
    start_date = date.today()
    created = 0

    for offset, day in enumerate(template.days):
        workout = UserWorkout(
            user_program_id=user_program.id,
            scheduled_date=start_date + timedelta(days=offset),
            day_number=day.day_number,
            title=day.title,
            status="planned",
        )
        db.add(workout)
        db.flush()
        workouts.append(workout)

        for exercise_item in day.exercises:
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

    schedule_workout_notifications(db, target_user, workouts)
    db.flush()
    return user_program, created


def create_and_optionally_assign_program(db: Session, current_user: User, payload: ProgramTemplateCreate):
    target_user = current_user
    target_user_data = {
        "id": current_user.id,
        "telegram_user_id": current_user.telegram_user_id,
        "full_name": None,
    }

    if payload.mode == "coach":
        current_user.is_coach = True
        current_user.is_admin = True
        target_user = get_or_create_user_by_telegram_id(
            db,
            payload.target_telegram_user_id,
            payload.target_full_name,
        )
        ensure_coach_link(db, current_user, target_user)

    template = create_template(db, current_user, payload)
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

    target_profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == target_user.id)
        .first()
    )
    target_user_data = {
        "id": target_user.id,
        "telegram_user_id": target_user.telegram_user_id,
        "full_name": target_profile.full_name if target_profile else None,
    }

    return template, assigned_program, workouts_created, target_user_data


def list_user_templates(db: Session, current_user: User) -> list[ProgramTemplate]:
    return (
        db.query(ProgramTemplate)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
            .joinedload(ProgramTemplateExercise.exercise)
        )
        .filter(
            or_(
                ProgramTemplate.created_by_user_id == current_user.id,
                ProgramTemplate.owner_user_id == current_user.id,
                ProgramTemplate.is_public.is_(True),
            )
        )
        .order_by(ProgramTemplate.id.desc())
        .all()
    )


def list_clients(db: Session, coach: User) -> list[User]:
    return (
        db.query(User)
        .join(CoachClient, CoachClient.client_user_id == User.id)
        .options(joinedload(User.profile))
        .filter(CoachClient.coach_user_id == coach.id)
        .order_by(User.id.desc())
        .all()
    )


def assign_existing_template_to_user(
    db: Session,
    current_user: User,
    template_id: int,
    target_telegram_user_id: int,
    target_full_name: str | None = None,
):
    template = (
        db.query(ProgramTemplate)
        .options(
            joinedload(ProgramTemplate.days)
            .joinedload(ProgramTemplateDay.exercises)
        )
        .filter(ProgramTemplate.id == template_id)
        .first()
    )
    if not template:
        raise ProgramError("Template not found")

    target_user = get_or_create_user_by_telegram_id(
        db,
        target_telegram_user_id,
        target_full_name,
    )
    ensure_coach_link(db, current_user, target_user)
    program, created = assign_template_to_user(db, template, target_user, current_user)
    db.commit()
    db.refresh(program)
    return program, created, target_user


def delete_template_for_user(
    db: Session,
    current_user: User,
    template_id: int,
) -> None:
    template = (
        db.query(ProgramTemplate)
        .filter(ProgramTemplate.id == template_id)
        .first()
    )
    if not template:
        raise ProgramError("Template not found")

    can_delete = (
        current_user.is_admin
        or current_user.is_coach
        or template.owner_user_id == current_user.id
        or template.created_by_user_id == current_user.id
    )
    if not can_delete:
        raise ProgramError("No permission to delete template")

    user_programs = db.query(UserProgram).filter(UserProgram.template_id == template.id).all()
    user_program_ids = [item.id for item in user_programs]

    if user_program_ids:
        workouts = db.query(UserWorkout).filter(UserWorkout.user_program_id.in_(user_program_ids)).all()
        workout_ids = [item.id for item in workouts]

        if workout_ids:
            workout_exercises = db.query(UserWorkoutExercise).filter(
                UserWorkoutExercise.workout_id.in_(workout_ids)
            ).all()
            workout_exercise_ids = [item.id for item in workout_exercises]

            if workout_exercise_ids:
                db.query(UserWorkoutSet).filter(
                    UserWorkoutSet.workout_exercise_id.in_(workout_exercise_ids)
                ).delete(synchronize_session=False)

                db.query(UserWorkoutExercise).filter(
                    UserWorkoutExercise.id.in_(workout_exercise_ids)
                ).delete(synchronize_session=False)

            db.query(UserWorkout).filter(
                UserWorkout.id.in_(workout_ids)
            ).delete(synchronize_session=False)

        db.query(UserProgram).filter(
            UserProgram.id.in_(user_program_ids)
        ).delete(synchronize_session=False)

    days = db.query(ProgramTemplateDay).filter(ProgramTemplateDay.program_id == template.id).all()
    day_ids = [item.id for item in days]

    if day_ids:
        db.query(ProgramTemplateExercise).filter(
            ProgramTemplateExercise.day_id.in_(day_ids)
        ).delete(synchronize_session=False)

        db.query(ProgramTemplateDay).filter(
            ProgramTemplateDay.id.in_(day_ids)
        ).delete(synchronize_session=False)

    db.delete(template)
    db.commit()
