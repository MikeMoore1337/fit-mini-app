from fitminiapp_api.api.v1.me import _build_user_response
from fitminiapp_api.db.performance import (
    begin_sql_metrics,
    current_sql_metrics,
    reset_sql_metrics,
)
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.nutrition import NutritionTarget
from fitminiapp_api.models.user import CoachClient, User, UserProfile
from fitminiapp_api.services.programs import list_clients


def test_coach_client_list_query_count_is_constant() -> None:
    with get_session_context() as db:
        coach = User(telegram_user_id=910_000, username="scale_coach", is_coach=True)
        db.add(coach)
        db.flush()
        db.add(UserProfile(user_id=coach.id, full_name="Scale Coach"))

        clients: list[User] = []
        for index in range(25):
            user = User(
                telegram_user_id=911_000 + index,
                username=f"scale_client_{index}",
            )
            db.add(user)
            db.flush()
            db.add(UserProfile(user_id=user.id, full_name=f"Scale Client {index}"))
            db.add(
                CoachClient(
                    coach_user_id=coach.id,
                    client_user_id=user.id,
                    private_name=f"Private Client {index}",
                )
            )
            clients.append(user)

        db.add(
            NutritionTarget(
                user_id=clients[0].id,
                assigned_by_user_id=coach.id,
                sex="male",
                weight_kg=80,
                height_cm=180,
                age=30,
                daily_activity_level="moderate",
                daily_routine="mixed",
                steps_range="from_7000_to_10000",
                strength_trainings_per_week=3,
                strength_training_duration_minutes=60,
                strength_training_type="regular",
                strength_rest="one_to_two",
                cardio_trainings_per_week=1,
                cardio_training_duration_minutes=30,
                cardio_intensity="moderate",
                cardio_trainings=[],
                goal="maintenance",
                bmr=1800,
                tdee=2500,
                calories=2500,
                protein_g=160,
                fat_g=72,
                carbs_g=303,
            )
        )
        db.commit()
        db.refresh(coach)

        token = begin_sql_metrics()
        try:
            result = list_clients(db, coach)
            metrics = current_sql_metrics()
        finally:
            reset_sql_metrics(token)

    assert len(result) == 25
    assert metrics.query_count == 4
    assert result[-1]["kbju"].assigned_by.full_name == "Scale Coach"


def test_me_response_needs_four_queries_after_authentication() -> None:
    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == 2001).one()
        token = begin_sql_metrics()
        try:
            response = _build_user_response(db, user)
            metrics = current_sql_metrics()
        finally:
            reset_sql_metrics(token)

    assert response.telegram_user_id == 2001
    assert response.auth_providers == ["telegram"]
    assert metrics.query_count == 4
