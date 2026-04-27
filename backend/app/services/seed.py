from sqlalchemy.orm import Session

from app.models.billing import Plan
from app.models.exercise import Exercise
from app.models.notification import NotificationSetting
from app.models.program import ProgramTemplate, ProgramTemplateDay, ProgramTemplateExercise
from app.models.user import User, UserProfile
from app.services.program_seed_data import (
    EXERCISE_CATALOG,
    LEGACY_TEMPLATE_SLUGS,
    STRENGTH_TEMPLATE_SPECS,
    TemplateDaySeed,
)


def _seed_exercise_catalog(db: Session) -> None:
    for slug, title, primary_muscle, equipment in EXERCISE_CATALOG:
        exercise = (
            db.query(Exercise)
            .filter(
                Exercise.slug == slug,
                Exercise.created_by_user_id.is_(None),
                Exercise.source_exercise_id.is_(None),
            )
            .first()
        )
        if exercise:
            exercise.title = title
            exercise.primary_muscle = primary_muscle
            exercise.equipment = equipment
            continue

        if db.query(Exercise).filter(Exercise.slug == slug).first():
            continue

        db.add(
            Exercise(
                slug=slug,
                title=title,
                primary_muscle=primary_muscle,
                equipment=equipment,
                created_by_user_id=None,
                source_exercise_id=None,
                is_deleted=False,
            )
        )

    db.flush()


def _clear_template_days(db: Session, template: ProgramTemplate) -> None:
    day_ids = [
        row.id
        for row in db.query(ProgramTemplateDay.id)
        .filter(ProgramTemplateDay.program_id == template.id)
        .all()
    ]
    if day_ids:
        db.query(ProgramTemplateExercise).filter(
            ProgramTemplateExercise.day_id.in_(day_ids)
        ).delete(synchronize_session=False)
        db.query(ProgramTemplateDay).filter(ProgramTemplateDay.id.in_(day_ids)).delete(
            synchronize_session=False
        )
    db.flush()


def _delete_legacy_templates(db: Session) -> None:
    for slug in LEGACY_TEMPLATE_SLUGS:
        template = db.query(ProgramTemplate).filter(ProgramTemplate.slug == slug).first()
        if not template:
            continue

        from app.services.programs import delete_template_cascade

        delete_template_cascade(db, template)
        db.flush()


def _seed_strength_templates(db: Session) -> None:
    exercise_map = {
        row.slug: row
        for row in db.query(Exercise)
        .filter(
            Exercise.created_by_user_id.is_(None),
            Exercise.source_exercise_id.is_(None),
            Exercise.is_deleted.is_(False),
        )
        .all()
    }

    for spec in STRENGTH_TEMPLATE_SPECS:
        slug = str(spec["slug"])
        template = db.query(ProgramTemplate).filter(ProgramTemplate.slug == slug).first()
        if not template:
            template = ProgramTemplate(slug=slug)
            db.add(template)
        else:
            _clear_template_days(db, template)

        template.title = str(spec["title"])
        template.goal = str(spec["goal"])
        template.level = str(spec["level"])
        template.owner_user_id = None
        template.created_by_user_id = None
        template.is_public = True
        db.flush()

        days: list[TemplateDaySeed] = spec["days"]  # type: ignore[assignment]
        for day_number, (day_title, exercises) in enumerate(days, start=1):
            day = ProgramTemplateDay(
                program_id=template.id,
                day_number=day_number,
                title=day_title,
            )
            db.add(day)
            db.flush()

            for sort_order, (exercise_slug, sets, reps, rest) in enumerate(exercises, start=1):
                exercise = exercise_map.get(exercise_slug)
                if exercise is None:
                    raise RuntimeError(f"Seed exercise is missing: {exercise_slug}")

                db.add(
                    ProgramTemplateExercise(
                        day_id=day.id,
                        exercise_id=exercise.id,
                        sort_order=sort_order,
                        prescribed_sets=sets,
                        prescribed_reps=reps,
                        rest_seconds=rest,
                    )
                )


def seed_demo_data(db: Session, include_demo_users: bool = True) -> None:
    if include_demo_users and db.query(User).count() == 0:
        coach = User(telegram_user_id=1001, username="coach_1001", is_coach=True, is_admin=True)
        client1 = User(telegram_user_id=2001, username="client_2001")
        client2 = User(telegram_user_id=2002, username="client_2002")
        db.add_all([coach, client1, client2])
        db.flush()
        db.add_all(
            [
                UserProfile(
                    user_id=coach.id,
                    full_name="Тренер Demo",
                    goal="recomposition",
                    level="advanced",
                ),
                UserProfile(
                    user_id=client1.id,
                    full_name="Клиент 2001",
                    goal="muscle_gain",
                    level="intermediate",
                ),
                UserProfile(
                    user_id=client2.id, full_name="Клиент 2002", goal="fat_loss", level="beginner"
                ),
                NotificationSetting(user_id=coach.id),
                NotificationSetting(user_id=client1.id),
                NotificationSetting(user_id=client2.id),
            ]
        )

    _seed_exercise_catalog(db)

    if db.query(Plan).count() == 0:
        db.add_all(
            [
                Plan(code="free", title="Free", price=0, currency="RUB", period_days=3650),
                Plan(code="premium", title="Premium", price=990, currency="RUB", period_days=30),
                Plan(code="coach", title="Coach", price=2490, currency="RUB", period_days=30),
            ]
        )

    _delete_legacy_templates(db)
    _seed_strength_templates(db)
    db.commit()
