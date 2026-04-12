from sqlalchemy.orm import Session

from app.models.billing import Plan
from app.models.exercise import Exercise
from app.models.notification import NotificationSetting
from app.models.program import ProgramTemplate, ProgramTemplateDay, ProgramTemplateExercise
from app.models.user import User, UserProfile


def seed_demo_data(db: Session) -> None:
    if db.query(User).count() == 0:
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

    if db.query(Exercise).count() == 0:
        db.add_all(
            [
                Exercise(
                    slug="bench-press",
                    title="Жим лёжа",
                    primary_muscle="chest",
                    equipment="barbell",
                ),
                Exercise(
                    slug="barbell-row",
                    title="Тяга штанги в наклоне",
                    primary_muscle="back",
                    equipment="barbell",
                ),
                Exercise(
                    slug="squat", title="Приседания", primary_muscle="legs", equipment="barbell"
                ),
                Exercise(
                    slug="romanian-deadlift",
                    title="Румынская тяга",
                    primary_muscle="hamstrings",
                    equipment="barbell",
                ),
                Exercise(
                    slug="overhead-press",
                    title="Жим стоя",
                    primary_muscle="shoulders",
                    equipment="barbell",
                ),
                Exercise(
                    slug="lat-pulldown",
                    title="Вертикальная тяга",
                    primary_muscle="back",
                    equipment="machine",
                ),
                Exercise(
                    slug="leg-press", title="Жим ногами", primary_muscle="legs", equipment="machine"
                ),
                Exercise(
                    slug="leg-curl",
                    title="Сгибание ног лёжа",
                    primary_muscle="hamstrings",
                    equipment="machine",
                ),
            ]
        )
        db.flush()

    if db.query(Plan).count() == 0:
        db.add_all(
            [
                Plan(code="free", title="Free", price=0, currency="RUB", period_days=3650),
                Plan(code="premium", title="Premium", price=990, currency="RUB", period_days=30),
                Plan(code="coach", title="Coach", price=2490, currency="RUB", period_days=30),
            ]
        )

    if not db.query(ProgramTemplate).filter(ProgramTemplate.slug == "upper-lower-4x").first():
        exercise_map = {row.slug: row for row in db.query(Exercise).all()}
        template = ProgramTemplate(
            slug="upper-lower-4x",
            title="Upper/Lower 4x",
            goal="recomposition",
            level="intermediate",
            is_public=True,
        )
        db.add(template)
        db.flush()
        day1 = ProgramTemplateDay(program_id=template.id, day_number=1, title="Верх тела A")
        day2 = ProgramTemplateDay(program_id=template.id, day_number=2, title="Низ тела A")
        db.add_all([day1, day2])
        db.flush()
        db.add_all(
            [
                ProgramTemplateExercise(
                    day_id=day1.id,
                    exercise_id=exercise_map["bench-press"].id,
                    sort_order=1,
                    prescribed_sets=4,
                    prescribed_reps="6-8",
                    rest_seconds=120,
                ),
                ProgramTemplateExercise(
                    day_id=day1.id,
                    exercise_id=exercise_map["barbell-row"].id,
                    sort_order=2,
                    prescribed_sets=4,
                    prescribed_reps="8-10",
                    rest_seconds=120,
                ),
                ProgramTemplateExercise(
                    day_id=day2.id,
                    exercise_id=exercise_map["squat"].id,
                    sort_order=1,
                    prescribed_sets=4,
                    prescribed_reps="6-8",
                    rest_seconds=150,
                ),
                ProgramTemplateExercise(
                    day_id=day2.id,
                    exercise_id=exercise_map["romanian-deadlift"].id,
                    sort_order=2,
                    prescribed_sets=3,
                    prescribed_reps="8-10",
                    rest_seconds=120,
                ),
            ]
        )
    db.commit()
