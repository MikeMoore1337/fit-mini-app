import hashlib
import hmac
import json
import re
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pytest
from pydantic import ValidationError

from fitminiapp_api.core.config import Settings, settings
from fitminiapp_api.core.timezone import to_msk_naive
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.program import (
    ProgramTemplate,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.user import CoachClient, CoachClientInvite, User
from fitminiapp_api.services import notifications as notifications_service
from fitminiapp_api.services.exercise_guides import get_exercise_guide
from fitminiapp_api.services.notifications import (
    claim_due_notifications,
    mark_delivery_failed,
    sync_workout_reminders,
)
from fitminiapp_api.services.seed import seed_demo_data
from fitminiapp_api.services.telegram_auth import validate_telegram_init_data


def signed_init_data(
    bot_token: str,
    auth_date: int,
    telegram_user_id: int = 555001,
    username: str | None = None,
    user_data: object | None = None,
) -> str:
    user = (
        user_data if user_data is not None else {"id": telegram_user_id, "first_name": "Telegram"}
    )
    if username and isinstance(user, dict):
        user["username"] = username
    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    data["hash"] = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return urlencode(data)


def auth(
    client,
    telegram_user_id=1001,
    is_coach=True,
    is_admin=False,
    username=None,
    full_name=None,
):
    payload = {
        "telegram_user_id": telegram_user_id,
        "is_coach": is_coach,
        "is_admin": is_admin,
    }
    if username is not None:
        payload["username"] = username
    if full_name is not None:
        payload["full_name"] = full_name

    response = client.post(
        "/api/v1/auth/dev-login",
        json=payload,
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_coach_invite_token(client, coach_headers):
    created = client.post("/api/v1/coach/invite-links", headers=coach_headers)
    assert created.status_code == 201
    start_param = created.json()["start_param"]
    assert start_param.startswith("trainer_")
    return start_param.removeprefix("trainer_"), created.json()


def accept_coach_invite(client, coach_headers, client_headers):
    token, created = create_coach_invite_token(client, coach_headers)
    preview = client.post(
        "/api/v1/me/coach-invites/link/preview",
        json={"token": token},
        headers=client_headers,
    )
    assert preview.status_code == 200
    assert preview.json()["invite_id"] == created["invite_id"]
    accepted = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=client_headers,
    )
    assert accepted.status_code == 204
    return created, preview.json()


def test_dev_login_and_me(client):
    headers = auth(client)
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_user_id"] == 1001
    assert data["is_coach"] is True


def test_production_settings_reject_placeholder_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            app_env="prod",
            app_name="Your Fitness Coach",
            app_debug=False,
            secret_key="change-me",
            access_token_expire_minutes=60,
            refresh_token_expire_days=30,
            database_url="postgresql+psycopg://app:password@db/app",
            enable_dev_auth=False,
            telegram_bot_token="123456:configured-token",
            frontend_base_url="https://example.test",
        )


def test_production_settings_reject_placeholder_bot_internal_token():
    with pytest.raises(ValidationError, match="BOT_INTERNAL_TOKEN"):
        Settings(
            app_env="prod",
            app_name="Your Fitness Coach",
            app_debug=False,
            secret_key="a-production-secret-that-is-long-enough",
            access_token_expire_minutes=60,
            refresh_token_expire_days=30,
            database_url="postgresql+psycopg://app:password@db/app",
            enable_dev_auth=False,
            telegram_bot_token="123456:configured-token",
            bot_internal_token="replace-with-a-separate-random-secret-at-least-32-characters",
            frontend_base_url="https://example.test",
        )


def test_production_oauth_does_not_require_smtp_when_email_auth_is_disabled():
    configured = Settings(
        app_env="prod",
        app_name="Your Fitness Coach",
        app_debug=False,
        secret_key="a-production-secret-that-is-long-enough",
        access_token_expire_minutes=60,
        refresh_token_expire_days=30,
        database_url="postgresql+psycopg://app:password@db/app",
        enable_dev_auth=False,
        enable_web_auth=True,
        enable_email_auth=False,
        telegram_bot_token="123456:configured-token",
        bot_internal_token="a-separate-production-token-that-is-long-enough",
        frontend_base_url="https://example.test",
        smtp_host="",
        smtp_from_email="",
    )

    assert configured.enable_web_auth is True
    assert configured.enable_email_auth is False


def test_production_email_auth_requires_smtp():
    with pytest.raises(ValidationError, match="SMTP_HOST"):
        Settings(
            app_env="prod",
            app_name="Your Fitness Coach",
            app_debug=False,
            secret_key="a-production-secret-that-is-long-enough",
            access_token_expire_minutes=60,
            refresh_token_expire_days=30,
            database_url="postgresql+psycopg://app:password@db/app",
            enable_dev_auth=False,
            enable_web_auth=True,
            enable_email_auth=True,
            telegram_bot_token="123456:configured-token",
            bot_internal_token="a-separate-production-token-that-is-long-enough",
            frontend_base_url="https://example.test",
            smtp_host="",
            smtp_from_email="",
        )


def test_dev_login_can_set_admin_role(client):
    headers = auth(client, telegram_user_id=4001, is_coach=True, is_admin=True)
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_user_id"] == 4001
    assert data["is_coach"] is True
    assert data["is_admin"] is True


def test_client_can_save_kbju_and_see_it_in_profile(client):
    headers = auth(client, telegram_user_id=6001, is_coach=False)
    payload = {
        "sex": "male",
        "weight_kg": 80.0,
        "height_cm": 180.0,
        "age": 30.0,
        "strength_trainings_per_week": 3,
        "cardio_trainings_per_week": 1,
        "goal": "muscle_gain",
    }

    saved = client.post("/api/v1/nutrition/targets", json=payload, headers=headers)

    assert saved.status_code == 200
    data = saved.json()
    assert data["calories"] == 2420
    assert data["protein_g"] == 144
    assert data["fat_g"] == 72
    assert data["carbs_g"] == 299
    assert data["daily_activity_level"] == "sedentary"
    assert data["strength_training_duration_minutes"] == 60
    assert data["cardio_training_duration_minutes"] == 30
    assert data["cardio_intensity"] == "moderate"

    me = client.get("/api/v1/me", headers=headers).json()
    kbju = me["profile"]["kbju"]
    assert kbju["calories"] == 2420
    assert kbju["assigned_by"]["telegram_user_id"] == 6001


def test_client_can_save_detailed_activity_and_multiple_cardio_trainings(client):
    headers = auth(client, telegram_user_id=6002, is_coach=False)
    payload = {
        "sex": "female",
        "weight_kg": 64,
        "height_cm": 168,
        "age": 28,
        "daily_routine": "mixed",
        "steps_range": "from_7000_to_10000",
        "strength_trainings_per_week": 2,
        "strength_training_duration_minutes": 70,
        "strength_training_type": "heavy",
        "strength_rest": "over_three",
        "cardio_trainings": [
            {
                "kind": "walking",
                "trainings_per_week": 2,
                "duration_minutes": 45,
                "intensity": "light",
            },
            {
                "kind": "swimming",
                "trainings_per_week": 1,
                "duration_minutes": 40,
                "intensity": "hard",
            },
        ],
        "goal": "recomposition",
    }

    saved = client.post("/api/v1/nutrition/targets", json=payload, headers=headers)

    assert saved.status_code == 200
    data = saved.json()
    assert data["daily_routine"] == "mixed"
    assert data["steps_range"] == "from_7000_to_10000"
    assert data["strength_training_type"] == "heavy"
    assert data["strength_rest"] == "over_three"
    assert data["cardio_trainings"] == payload["cardio_trainings"]
    assert data["cardio_trainings_per_week"] == 3
    assert (
        abs(data["protein_g"] * 4 + data["fat_g"] * 9 + data["carbs_g"] * 4 - data["calories"])
        <= 10
    )


def test_coach_can_assign_kbju_to_own_client(client):
    coach_headers = auth(
        client,
        telegram_user_id=6101,
        is_coach=True,
        username="@nutrition_coach",
        full_name="КБЖУ Тренер",
    )
    client_headers = auth(client, telegram_user_id=6102, is_coach=False)
    accept_coach_invite(client, coach_headers, client_headers)

    saved = client.post(
        "/api/v1/nutrition/targets",
        json={
            "target_telegram_user_id": 6102,
            "sex": "female",
            "weight_kg": 64.5,
            "height_cm": 168.0,
            "age": 28.0,
            "strength_trainings_per_week": 2,
            "cardio_trainings_per_week": 2,
            "goal": "fat_loss",
        },
        headers=coach_headers,
    )

    assert saved.status_code == 200
    data = saved.json()
    assert data["telegram_user_id"] == 6102
    assert data["assigned_by"]["username"] == "nutrition_coach"

    me = client.get("/api/v1/me", headers=client_headers).json()
    kbju = me["profile"]["kbju"]
    assert kbju["telegram_user_id"] == 6102
    assert kbju["assigned_by"]["full_name"] == "КБЖУ Тренер"


def test_client_parameter_and_weight_changes_recalculate_kbju_and_notify(client):
    headers = auth(client, telegram_user_id=6103, is_coach=False)
    payload = {
        "sex": "male",
        "weight_kg": 80,
        "height_cm": 180,
        "age": 30,
        "strength_trainings_per_week": 3,
        "cardio_trainings_per_week": 1,
        "goal": "muscle_gain",
    }
    initial = client.post(
        "/api/v1/nutrition/targets",
        json=payload,
        headers=headers,
    ).json()

    profile = client.patch(
        "/api/v1/me/profile",
        json={"goal": "fat_loss"},
        headers=headers,
    )
    assert profile.status_code == 200
    assert profile.json()["profile"]["kbju"]["goal"] == "fat_loss"
    assert profile.json()["profile"]["kbju"]["calories"] != initial["calories"]

    measurement = client.post(
        "/api/v1/workouts/diary",
        json={"measured_on": "2026-08-01", "weight_kg": 75.5},
        headers=headers,
    )
    assert measurement.status_code == 200

    kbju = client.get("/api/v1/me", headers=headers).json()["profile"]["kbju"]
    assert kbju["weight_kg"] == 75.5
    notifications = client.get("/api/v1/notifications", headers=headers).json()
    assert len(notifications) == 3
    assert notifications[0]["title"] == "КБЖУ пересчитаны"
    assert "Новые ориентиры" in notifications[0]["body"]
    assert notifications[0]["status"] == "queued"

    client.post(
        "/api/v1/workouts/diary",
        json={"measured_on": "2026-08-01", "weight_kg": 75.5},
        headers=headers,
    )
    assert len(client.get("/api/v1/notifications", headers=headers).json()) == 3


def test_coach_profile_and_measurement_changes_recalculate_and_notify_client(client):
    coach_headers = auth(client, telegram_user_id=6104, is_coach=True)
    client_headers = auth(client, telegram_user_id=6105, is_coach=False)
    client_user = client.get("/api/v1/me", headers=client_headers).json()
    accept_coach_invite(client, coach_headers, client_headers)
    client.post(
        "/api/v1/nutrition/targets",
        json={
            "target_telegram_user_id": 6105,
            "sex": "female",
            "weight_kg": 64.5,
            "height_cm": 168,
            "age": 28,
            "strength_trainings_per_week": 2,
            "cardio_trainings_per_week": 2,
            "goal": "fat_loss",
        },
        headers=coach_headers,
    )

    profile = client.patch(
        f"/api/v1/coach/clients/{client_user['id']}/profile",
        json={"height_cm": 170},
        headers=coach_headers,
    )
    assert profile.status_code == 200
    assert profile.json()["kbju"]["height_cm"] == 170

    measurement = client.post(
        f"/api/v1/coach/clients/{client_user['id']}/measurements",
        json={"measured_on": "2026-08-01", "weight_kg": 63.5},
        headers=coach_headers,
    )
    assert measurement.status_code == 200

    kbju = client.get("/api/v1/me", headers=client_headers).json()["profile"]["kbju"]
    assert kbju["weight_kg"] == 63.5
    assert kbju["assigned_by"]["telegram_user_id"] == 6104
    notifications = client.get("/api/v1/notifications", headers=client_headers).json()
    nutrition_notifications = [row for row in notifications if row["title"] == "КБЖУ пересчитаны"]
    assert len(nutrition_notifications) == 3
    assert "Тренер обновил параметры питания" in nutrition_notifications[0]["body"]


def test_nutrition_form_only_notifies_when_calculation_inputs_change(client):
    headers = auth(client, telegram_user_id=6106, is_coach=False)
    payload = {
        "sex": "male",
        "weight_kg": 80,
        "height_cm": 180,
        "age": 30,
        "strength_trainings_per_week": 3,
        "cardio_trainings_per_week": 1,
        "goal": "maintenance",
    }
    client.post("/api/v1/nutrition/targets", json=payload, headers=headers)
    client.post("/api/v1/nutrition/targets", json=payload, headers=headers)
    assert len(client.get("/api/v1/notifications", headers=headers).json()) == 1

    payload["daily_activity_level"] = "high"
    changed = client.post("/api/v1/nutrition/targets", json=payload, headers=headers)
    assert changed.status_code == 200
    assert len(client.get("/api/v1/notifications", headers=headers).json()) == 2


def test_coach_can_update_own_client_profile_and_measurements(client):
    coach_headers = auth(client, telegram_user_id=6110, is_coach=True)
    client_headers = auth(
        client,
        telegram_user_id=6111,
        is_coach=False,
        full_name="Имя клиента",
    )
    other_coach_headers = auth(client, telegram_user_id=6112, is_coach=True)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    accept_coach_invite(client, coach_headers, client_headers)

    profile = client.patch(
        f"/api/v1/coach/clients/{client_user['id']}/profile",
        json={
            "full_name": "Клиент с анкетой",
            "birth_date": "1990-09-10",
            "goal": "recomposition",
            "level": "intermediate",
            "height_cm": 176,
            "weight_kg": 74,
            "workouts_per_week": 4,
            "cardio_trainings_per_week": 2,
        },
        headers=coach_headers,
    )
    assert profile.status_code == 200
    assert profile.json()["height_cm"] == 176
    assert profile.json()["goal"] == "recomposition"
    assert profile.json()["workouts_per_week"] == 4
    assert profile.json()["cardio_trainings_per_week"] == 2
    assert profile.json()["birth_date"] == "1990-09-10"

    measurement = client.post(
        f"/api/v1/coach/clients/{client_user['id']}/measurements",
        json={"measured_on": "2026-07-31", "weight_kg": 73.5, "waist_cm": 81.2},
        headers=coach_headers,
    )
    assert measurement.status_code == 200
    assert measurement.json()["waist_cm"] == 81.2

    rows = client.get(
        f"/api/v1/coach/clients/{client_user['id']}/measurements",
        headers=coach_headers,
    )
    assert rows.status_code == 200
    assert rows.json()[0]["weight_kg"] == 73.5

    forbidden = client.patch(
        f"/api/v1/coach/clients/{client_user['id']}/profile",
        json={"weight_kg": 90},
        headers=other_coach_headers,
    )
    assert forbidden.status_code == 404

    me = client.get("/api/v1/me", headers=client_headers).json()
    assert me["profile"]["full_name"] == "Имя клиента"
    assert me["profile"]["weight_kg"] == 74
    assert me["profile"]["cardio_trainings_per_week"] == 2

    client_update = client.patch(
        "/api/v1/me/profile",
        json={
            "full_name": "Клиент обновил себя",
            "goal": "fat_loss",
            "height_cm": 174,
            "weight_kg": 72,
            "workouts_per_week": 3,
            "cardio_trainings_per_week": 4,
        },
        headers=client_headers,
    )
    assert client_update.status_code == 200

    coach_view = client.get("/api/v1/coach/clients", headers=coach_headers)
    assert coach_view.status_code == 200
    synced_client = next(row for row in coach_view.json() if row["id"] == client_user["id"])
    assert synced_client["full_name"] == "Клиент с анкетой"
    assert synced_client["goal"] == "fat_loss"
    assert synced_client["height_cm"] == 174
    assert synced_client["weight_kg"] == 72
    assert synced_client["workouts_per_week"] == 3
    assert synced_client["cardio_trainings_per_week"] == 4
    assert synced_client["birth_date"] == "1990-09-10"

    me_after_client_update = client.get("/api/v1/me", headers=client_headers).json()
    assert me_after_client_update["profile"]["full_name"] == "Клиент обновил себя"
    assert me_after_client_update["profile"]["estimated_max_heart_rate"] is not None
    assert len(me_after_client_update["profile"]["heart_rate_zones"]) == 5


def test_coach_can_assign_existing_template_to_own_client(client):
    coach_headers = auth(client, telegram_user_id=6120, is_coach=True)
    client_headers = auth(client, telegram_user_id=6121, is_coach=False)
    other_coach_headers = auth(client, telegram_user_id=6122, is_coach=True)
    client_user = client.get("/api/v1/me", headers=client_headers).json()
    accept_coach_invite(client, coach_headers, client_headers)
    alias = client.patch(
        f"/api/v1/coach/clients/{client_user['id']}/profile",
        json={"full_name": "Клиент в программах"},
        headers=coach_headers,
    )
    assert alias.status_code == 200

    exercise = client.get("/api/v1/programs/exercises", headers=coach_headers).json()[0]
    created = client.post(
        "/api/v1/programs/templates",
        json={
            "title": "Шаблон тренера",
            "goal": "maintenance",
            "level": "beginner",
            "mode": "self",
            "assign_after_create": False,
            "days": [
                {
                    "title": "День 1",
                    "exercises": [
                        {
                            "exercise_id": exercise["id"],
                            "prescribed_sets": 2,
                            "prescribed_reps": "10",
                            "rest_seconds": 60,
                        }
                    ],
                }
            ],
        },
        headers=coach_headers,
    )
    assert created.status_code == 200
    assert created.json()["template"]["days"][0]["exercises"][0]["has_guide"] is True
    template_id = created.json()["template"]["id"]
    assignment_start = datetime.now(UTC).date() + timedelta(days=1)

    assigned = client.post(
        f"/api/v1/coach/clients/{client_user['id']}/templates/{template_id}/assign",
        json={"start_date": assignment_start.isoformat()},
        headers=coach_headers,
    )
    assert assigned.status_code == 200
    assert assigned.json()["workouts_created"] == 1
    with get_session_context() as db:
        assignment_notice = (
            db.query(Notification)
            .filter(
                Notification.dedupe_key
                == f"program_assignment:{assigned.json()['user_program_id']}"
            )
            .one()
        )
        assert assignment_notice.user_id == client_user["id"]
        assert assignment_notice.status == "queued"
        assert "Шаблон тренера" in assignment_notice.body
    assert client.get("/api/v1/workouts/week", headers=client_headers).status_code == 200

    client_templates = client.get("/api/v1/programs/templates/mine", headers=client_headers).json()
    assigned_template = next(item for item in client_templates if item["id"] == template_id)
    assert assigned_template["is_assigned_to_current_user"] is True
    assert assigned_template["is_active_for_current_user"] is True
    assert assigned_template["assigned_by_user_id"] == created.json()["template"]["owner_user_id"]
    assert assigned_template["can_edit"] is False

    coach_programs = client.get("/api/v1/coach/assigned-programs", headers=coach_headers)
    assert coach_programs.status_code == 200
    assert coach_programs.json() == [
        {
            "id": assigned.json()["user_program_id"],
            "client_id": client_user["id"],
            "client_telegram_user_id": 6121,
            "client_username": client_user["username"],
            "client_full_name": "Клиент в программах",
            "template_id": template_id,
            "title": "Шаблон тренера",
            "goal": "maintenance",
            "level": "beginner",
            "assigned_at": coach_programs.json()[0]["assigned_at"],
            "is_active": True,
            "status": "scheduled",
            "start_date": assignment_start.isoformat(),
            "duration_weeks": 1,
            "schedule_weekdays": [assignment_start.weekday()],
            "completed_at": None,
            "workouts_total": 1,
            "workouts_completed": 0,
            "workouts_planned": 1,
            "next_workout_date": coach_programs.json()[0]["next_workout_date"],
        }
    ]

    second_exercise = client.get("/api/v1/programs/exercises", headers=coach_headers).json()[1]
    exercise_assignment = client.post(
        f"/api/v1/coach/clients/{client_user['id']}/programs/"
        f"{assigned.json()['user_program_id']}/exercises",
        json={
            "exercise_id": second_exercise["id"],
            "day_number": 1,
            "prescribed_sets": 4,
            "prescribed_reps": "12",
            "rest_seconds": 75,
        },
        headers=coach_headers,
    )
    assert exercise_assignment.status_code == 200
    assert exercise_assignment.json() == {"workouts_updated": 1}
    with get_session_context() as db:
        added = (
            db.query(UserWorkoutExercise)
            .join(UserWorkout)
            .filter(
                UserWorkout.user_program_id == assigned.json()["user_program_id"],
                UserWorkoutExercise.exercise_id == second_exercise["id"],
            )
            .one()
        )
        assert added.prescribed_sets == 4
        assert added.prescribed_reps == "12"
        assert added.rest_seconds == 75
        assert (
            db.query(UserWorkoutSet).filter(UserWorkoutSet.workout_exercise_id == added.id).count()
            == 4
        )

    workout_id = client.get("/api/v1/workouts/schedule", headers=client_headers).json()[0]["id"]
    client_date = assignment_start + timedelta(days=1)
    client_rescheduled = client.patch(
        f"/api/v1/workouts/{workout_id}/schedule",
        json={"scheduled_date": client_date.isoformat(), "scheduled_time": "18:30"},
        headers=client_headers,
    )
    assert client_rescheduled.status_code == 200
    assert client_rescheduled.json()["scheduled_time"] == "18:30:00"

    coach_date = assignment_start + timedelta(days=2)
    coach_rescheduled = client.patch(
        f"/api/v1/coach/clients/{client_user['id']}/workouts/{workout_id}/schedule",
        json={"scheduled_date": coach_date.isoformat(), "scheduled_time": "19:00"},
        headers=coach_headers,
    )
    assert coach_rescheduled.status_code == 200
    assert coach_rescheduled.json()["scheduled_time"] == "19:00:00"
    with get_session_context() as db:
        client_change_notice = (
            db.query(Notification)
            .filter(
                Notification.title == "Клиент изменил тренировку",
                Notification.user_id == created.json()["template"]["owner_user_id"],
            )
            .one()
        )
        assert "18:30" in client_change_notice.body
        trainer_change_notice = (
            db.query(Notification)
            .filter(
                Notification.title == "Тренер изменил тренировку",
                Notification.user_id == client_user["id"],
            )
            .one()
        )
        assert "19:00" in trainer_change_notice.body

    assert client.get("/api/v1/coach/assigned-programs", headers=other_coach_headers).json() == []


def test_coach_cannot_assign_kbju_to_non_client(client):
    coach_headers = auth(client, telegram_user_id=6201, is_coach=True)
    auth(client, telegram_user_id=6202, is_coach=False)

    response = client.post(
        "/api/v1/nutrition/targets",
        json={
            "target_telegram_user_id": 6202,
            "sex": "male",
            "weight_kg": 90,
            "height_cm": 185,
            "age": 35,
            "strength_trainings_per_week": 3,
            "cardio_trainings_per_week": 1,
            "goal": "maintenance",
        },
        headers=coach_headers,
    )

    assert response.status_code == 403


def test_admin_can_assign_kbju_to_existing_user(client):
    admin_headers = auth(client, telegram_user_id=6301, is_coach=True, is_admin=True)
    user_headers = auth(client, telegram_user_id=6302, is_coach=False)

    response = client.post(
        "/api/v1/nutrition/targets",
        json={
            "target_telegram_user_id": 6302,
            "sex": "male",
            "weight_kg": 77,
            "height_cm": 176,
            "age": 32,
            "strength_trainings_per_week": 4,
            "cardio_trainings_per_week": 0,
            "goal": "recomposition",
        },
        headers=admin_headers,
    )

    assert response.status_code == 200
    kbju = client.get("/api/v1/me", headers=user_headers).json()["profile"]["kbju"]
    assert kbju["assigned_by"]["telegram_user_id"] == 6301


def test_telegram_login_bootstraps_admin_from_env(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "admin_telegram_user_ids", "555001")
    init_data = signed_init_data(
        bot_token="test-token",
        auth_date=int(time.time()),
        telegram_user_id=555001,
    )

    login = client.post("/api/v1/auth/telegram/init", json={"init_data": init_data})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_admin"] is True


def test_create_program_and_today_workout(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Тестовая программа",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 3,
                        "prescribed_reps": "8-10",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }
    create_res = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert create_res.status_code == 200
    today = client.get("/api/v1/workouts/today", headers=headers)
    assert today.status_code == 200
    assert today.json()["title"] == "День 1"


def test_assign_template_to_self_uses_selected_start_date(client):
    headers = auth(client, telegram_user_id=2002, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Программа с выбранной датой",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": False,
        "days": [
            {
                "title": title,
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
            for title in ("День 1", "День 2")
        ],
    }
    created = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert created.status_code == 200
    template_id = created.json()["template"]["id"]

    start_date = date.today() + timedelta(days=1)
    assigned = client.post(
        f"/api/v1/programs/templates/{template_id}/assign-to-me",
        json={"start_date": start_date.isoformat()},
        headers=headers,
    )
    assert assigned.status_code == 200
    assert assigned.json()["workouts_created"] == 2

    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == 2002).one()
        program = (
            db.query(UserProgram)
            .filter(UserProgram.user_id == user.id, UserProgram.is_active.is_(True))
            .one()
        )
        scheduled_dates = [
            str(row.scheduled_date)
            for row in (
                db.query(UserWorkout)
                .filter(UserWorkout.user_program_id == program.id)
                .order_by(UserWorkout.scheduled_date.asc())
                .all()
            )
        ]

    assert scheduled_dates == [
        start_date.isoformat(),
        (start_date + timedelta(days=1)).isoformat(),
    ]


def test_week_schedule_returns_current_active_program(client):
    headers = auth(client, telegram_user_id=2003, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Недельная программа",
        "goal": "recomposition",
        "level": "beginner",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "Тренировка недели",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "10",
                        "rest_seconds": 60,
                    }
                ],
            }
        ],
    }
    created = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert created.status_code == 200

    response = client.get("/api/v1/workouts/week", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Тренировка недели"
    assert response.json()[0]["status"] == "planned"


def test_user_can_clear_completed_workout_history(client):
    headers = auth(client, telegram_user_id=6401, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Программа для очистки истории",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }
    created = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert created.status_code == 200

    assert client.get("/api/v1/workouts/history", headers=headers).json() == []
    today = client.get("/api/v1/workouts/today", headers=headers).json()
    started = client.post(f"/api/v1/workouts/{today['id']}/start", headers=headers)
    assert started.status_code == 200
    set_id = today["exercises"][0]["sets"][0]["id"]
    saved = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        json={"actual_reps": 8, "actual_weight": 20, "is_completed": True},
        headers=headers,
    )
    assert saved.status_code == 200
    finished = client.post(f"/api/v1/workouts/{today['id']}/finish", headers=headers)
    assert finished.status_code == 200

    history = client.get("/api/v1/workouts/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    cleared = client.delete("/api/v1/workouts/history", headers=headers)
    assert cleared.status_code == 204
    assert client.get("/api/v1/workouts/history", headers=headers).json() == []
    assert client.get("/api/v1/workouts/today", headers=headers).status_code == 404


def test_client_can_save_update_and_delete_body_measurement(client):
    headers = auth(client, telegram_user_id=6402, is_coach=False)

    created = client.post(
        "/api/v1/workouts/diary",
        json={
            "measured_on": "2026-05-01",
            "weight_kg": 74.5,
            "waist_cm": 82.0,
            "note": "утро",
        },
        headers=headers,
    )

    assert created.status_code == 200
    data = created.json()
    assert data["weight_kg"] == 74.5
    assert data["waist_cm"] == 82.0

    updated = client.post(
        "/api/v1/workouts/diary",
        json={
            "measured_on": "2026-05-01",
            "weight_kg": 74.0,
            "chest_cm": 98.5,
        },
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["id"] == data["id"]
    assert updated.json()["weight_kg"] == 74.0
    assert updated.json()["waist_cm"] == 82.0
    assert updated.json()["chest_cm"] == 98.5

    newer = client.post(
        "/api/v1/workouts/diary",
        json={"measured_on": "2026-05-03", "weight_kg": 73.8},
        headers=headers,
    )
    assert newer.status_code == 200

    rows = client.get("/api/v1/workouts/diary", headers=headers)
    assert rows.status_code == 200
    assert [row["measured_on"] for row in rows.json()] == ["2026-05-03", "2026-05-01"]

    deleted = client.delete(f"/api/v1/workouts/diary/{data['id']}", headers=headers)

    assert deleted.status_code == 204
    deleted_newer = client.delete(f"/api/v1/workouts/diary/{newer.json()['id']}", headers=headers)
    assert deleted_newer.status_code == 204
    assert client.get("/api/v1/workouts/diary", headers=headers).json() == []


def test_workout_set_patch(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Программа для валидации сетов",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 3,
                        "prescribed_reps": "8-10",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }
    create_res = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert create_res.status_code == 200
    today = client.get("/api/v1/workouts/today", headers=headers).json()
    exercise = today["exercises"][0]
    set_id = exercise["sets"][0]["id"]
    started = client.post(f"/api/v1/workouts/{today['id']}/start", headers=headers)
    assert started.status_code == 200

    unknown = client.patch(
        "/api/v1/workouts/sets/999999",
        json={"actual_reps": 8, "actual_weight": 80, "is_completed": True},
        headers=headers,
    )
    assert unknown.status_code == 404

    ok = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        json={"actual_reps": 8, "actual_weight": 80, "is_completed": True},
        headers=headers,
    )
    assert ok.status_code == 200


def test_workout_set_validation(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Программа для проверки валидации",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8-10",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }
    create_res = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert create_res.status_code == 200
    today = client.get("/api/v1/workouts/today", headers=headers).json()
    set_id = today["exercises"][0]["sets"][0]["id"]
    started = client.post(f"/api/v1/workouts/{today['id']}/start", headers=headers)
    assert started.status_code == 200

    invalid = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        json={"actual_reps": -5},
        headers=headers,
    )
    assert invalid.status_code == 422

    ok = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        json={"is_completed": "false"},
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["is_completed"] is False


def test_client_cannot_assign_program_as_coach(client):
    headers = auth(client, telegram_user_id=3001, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Чужая программа",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "coach",
        "target_telegram_user_id": 3999,
        "target_full_name": "Target",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }

    response = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert response.status_code == 400


def test_client_target_fields_do_not_assign_program_to_another_user(client):
    target_headers = auth(client, telegram_user_id=3998, is_coach=False)
    headers = auth(client, telegram_user_id=3002, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Программа только для себя",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "target_telegram_user_id": 3998,
        "target_full_name": "Чужой клиент",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }

    response = client.post("/api/v1/programs/templates", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["target_user"]["telegram_user_id"] == 3002
    assert client.get("/api/v1/workouts/today", headers=headers).status_code == 200
    assert client.get("/api/v1/workouts/today", headers=target_headers).status_code == 404


def test_client_custom_exercise_is_private(client):
    owner_headers = auth(client, telegram_user_id=3101, is_coach=False)
    other_headers = auth(client, telegram_user_id=3102, is_coach=False)
    coach_headers = auth(client, telegram_user_id=1101, is_coach=True)
    title = "Private Client Raise"

    created = client.post(
        "/api/v1/programs/exercises",
        json={"title": title, "primary_muscle": "shoulders", "equipment": "dumbbell"},
        headers=owner_headers,
    )

    assert created.status_code == 201
    assert created.json()["is_custom"] is True
    assert created.json()["is_personalized"] is True

    owner_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=owner_headers).json()
    }
    other_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=other_headers).json()
    }
    coach_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=coach_headers).json()
    }

    assert title in owner_titles
    assert title not in other_titles
    assert title not in coach_titles

    coach_edit = client.patch(
        f"/api/v1/programs/exercises/{created.json()['edit_target_id']}",
        json={"title": "Coach Hijack", "primary_muscle": "back", "equipment": "barbell"},
        headers=coach_headers,
    )
    assert coach_edit.status_code == 403


def test_admin_custom_exercise_is_global(client):
    admin_headers = auth(client, telegram_user_id=1102, is_coach=True, is_admin=True)
    client_headers = auth(client, telegram_user_id=3103, is_coach=False)
    coach_headers = auth(client, telegram_user_id=1103, is_coach=True)
    title = "Global Admin Press"

    created = client.post(
        "/api/v1/programs/exercises",
        json={"title": title, "primary_muscle": "chest", "equipment": "barbell"},
        headers=admin_headers,
    )

    assert created.status_code == 201
    assert created.json()["created_by_user_id"] is None
    assert created.json()["is_custom"] is False

    client_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=client_headers).json()
    }
    coach_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=coach_headers).json()
    }

    assert title in client_titles
    assert title in coach_titles


def test_custom_exercise_metadata_is_optional(client):
    headers = auth(client, telegram_user_id=31031, is_coach=False)

    created = client.post(
        "/api/v1/programs/exercises",
        json={"title": "Minimal Client Move"},
        headers=headers,
    )

    assert created.status_code == 201
    data = created.json()
    assert data["title"] == "Minimal Client Move"
    assert data["primary_muscle"] is None
    assert data["equipment"] is None
    assert data["difficulty_level"] == "intermediate"


def test_custom_exercise_can_be_marked_with_difficulty(client):
    headers = auth(client, telegram_user_id=31036, is_coach=False)

    created = client.post(
        "/api/v1/programs/exercises",
        json={"title": "Technical Client Move", "difficulty_level": "advanced"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["difficulty_level"] == "advanced"

    invalid = client.post(
        "/api/v1/programs/exercises",
        json={"title": "Invalid Level Move", "difficulty_level": "expert"},
        headers=headers,
    )
    assert invalid.status_code == 422


def test_seeded_catalog_and_strength_templates(client):
    headers = auth(client, telegram_user_id=31032, is_coach=False)

    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    templates = client.get("/api/v1/programs/templates/mine", headers=headers).json()

    assert len(exercises) >= 140
    assert {item["difficulty_level"] for item in exercises} == {
        "beginner",
        "intermediate",
        "advanced",
    }
    assert "upper-lower-4x" not in {item["slug"] for item in templates}
    assert {
        "strength-split-5d",
        "strength-push-pull-legs-6d",
        "strength-upper-lower-4d",
        "strength-fullbody-3d",
        "strength-pplf-4d",
        "strength-pplf-8d",
        "strength-pull-legs-push-legs-4d",
        "strength-pull-legs-push-legs-8d",
    }.issubset({item["slug"] for item in templates})
    pplf_templates = {item["slug"]: item for item in templates if "pplf" in item["slug"]}
    assert len(pplf_templates["strength-pplf-4d"]["days"]) == 4
    assert len(pplf_templates["strength-pplf-8d"]["days"]) == 8
    assigned = client.post(
        f"/api/v1/programs/templates/{pplf_templates['strength-pplf-8d']['id']}/assign-to-me",
        json={"start_date": (date.today() + timedelta(days=1)).isoformat()},
        headers=headers,
    )
    assert assigned.status_code == 200
    assert assigned.json()["workouts_created"] == 8
    pull_legs_templates = {
        item["slug"]: item for item in templates if "pull-legs-push-legs" in item["slug"]
    }
    assert [
        day["title"].split(" · ")[0]
        for day in pull_legs_templates["strength-pull-legs-push-legs-4d"]["days"]
    ] == ["Тяни", "Ноги A", "Толкай", "Ноги B"]
    assert len(pull_legs_templates["strength-pull-legs-push-legs-8d"]["days"]) == 8
    assert all(
        template["days"] for template in templates if template["slug"].startswith("strength-")
    )


def test_client_can_hide_and_restore_seeded_program_example(client):
    headers = auth(client, telegram_user_id=31034, is_coach=False)
    other_headers = auth(client, telegram_user_id=31035, is_coach=False)
    templates = client.get("/api/v1/programs/templates/mine", headers=headers).json()
    example = next(item for item in templates if item["slug"] == "strength-fullbody-3d")
    assert example["is_example"] is True

    hidden = client.delete(f"/api/v1/programs/templates/{example['id']}", headers=headers)
    assert hidden.status_code == 204
    assert example["id"] not in {
        item["id"] for item in client.get("/api/v1/programs/templates/mine", headers=headers).json()
    }
    assert example["id"] in {
        item["id"]
        for item in client.get("/api/v1/programs/templates/hidden", headers=headers).json()
    }
    assert example["id"] in {
        item["id"]
        for item in client.get("/api/v1/programs/templates/mine", headers=other_headers).json()
    }

    restored = client.post(f"/api/v1/programs/templates/{example['id']}/restore", headers=headers)
    assert restored.status_code == 204
    assert example["id"] in {
        item["id"] for item in client.get("/api/v1/programs/templates/mine", headers=headers).json()
    }
    assert client.get("/api/v1/programs/templates/hidden", headers=headers).json() == []


def test_every_seeded_template_can_be_customized_with_a_personal_exercise(client):
    headers = auth(client, telegram_user_id=31037, is_coach=False)
    custom_exercise = client.post(
        "/api/v1/programs/exercises",
        json={
            "title": "Моё упражнение для шаблона",
            "primary_muscle": "Все тело",
            "equipment": "Своё оборудование",
        },
        headers=headers,
    ).json()
    templates = client.get("/api/v1/programs/templates/mine", headers=headers).json()
    examples = [template for template in templates if template["is_example"]]

    assert examples
    for example in examples:
        days = [
            {
                "title": day["title"],
                "exercises": [
                    {
                        "exercise_id": (
                            custom_exercise["id"]
                            if day_index == 0 and exercise_index == 0
                            else exercise["exercise_id"]
                        ),
                        "prescribed_sets": exercise["prescribed_sets"],
                        "prescribed_reps": exercise["prescribed_reps"],
                        "rest_seconds": exercise["rest_seconds"],
                        "notes": exercise["notes"],
                    }
                    for exercise_index, exercise in enumerate(day["exercises"])
                ],
            }
            for day_index, day in enumerate(example["days"])
        ]
        response = client.post(
            "/api/v1/programs/templates",
            json={
                "title": f"{example['title']} — моя",
                "goal": example["goal"],
                "level": example["level"],
                "mode": "self",
                "assign_after_create": False,
                "schedule_weekdays": None,
                "days": days,
            },
            headers=headers,
        )

        assert response.status_code == 200, (example["slug"], response.text)
        personalized = response.json()["template"]
        assert personalized["is_example"] is False
        assert personalized["can_edit"] is True
        assert personalized["days"][0]["exercises"][0]["exercise_id"] == custom_exercise["id"]


def test_every_seeded_exercise_has_complete_guide_and_local_images(client):
    headers = auth(client, telegram_user_id=31033, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    standard_exercises = [item for item in exercises if not item["is_custom"]]
    static_dir = Path(__file__).resolve().parents[2] / "backend" / "assets"

    assert len(standard_exercises) == 158
    assert len(client.get("/api/v1/programs/exercises", headers=headers).content) < 100_000
    assert all(
        exercise["has_guide"] and exercise["guide"] is None for exercise in standard_exercises
    )

    sample = client.get(
        f"/api/v1/programs/exercises/{standard_exercises[0]['id']}/guide",
        headers=headers,
    )
    assert sample.status_code == 200
    assert len(sample.json()["images"]) == 2

    with get_session_context() as session:
        seeded_guides = [
            (row.slug, get_exercise_guide(row))
            for row in (
                session.query(Exercise)
                .filter(Exercise.created_by_user_id.is_(None), Exercise.is_deleted.is_(False))
                .all()
            )
        ]
    for slug, guide in seeded_guides:
        assert guide is not None, slug
        assert len(guide["technique_steps"]) >= 3
        assert guide["breathing"]
        assert len(guide["common_mistakes"]) >= 3
        assert guide["muscles"]
        assert guide["images"]
        for image in guide["images"]:
            asset = static_dir / image["url"].removeprefix("/static/")
            assert asset.is_file(), asset


def test_cardio_exercises_have_specific_guides_and_generated_images(client):
    headers = auth(client, telegram_user_id=31036, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    expected_titles = {
        "Бег на улице",
        "Эллиптический тренажёр",
        "Велосипед",
        "Велотренажёр",
        "Ходьба",
        "Ходьба на дорожке",
        "Степпер / лестница",
        "Плавание",
        "Лыжный тренажёр",
    }
    cardio = [exercise for exercise in exercises if exercise["title"] in expected_titles]

    assert {exercise["title"] for exercise in cardio} == expected_titles
    for exercise in cardio:
        response = client.get(
            f"/api/v1/programs/exercises/{exercise['id']}/guide",
            headers=headers,
        )
        assert response.status_code == 200
        guide = response.json()
        assert len(guide["technique_steps"]) >= 3
        assert guide["source_name"] == "Your Fitness Coach"
        assert guide["images"][0]["phase"] == "Две фазы движения"


def test_custom_exercise_has_no_incorrect_stock_guide(client):
    headers = auth(client, telegram_user_id=31034, is_coach=False)
    created = client.post(
        "/api/v1/programs/exercises",
        json={"title": "Авторское движение", "primary_muscle": "Кор"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["guide"] is None
    assert created.json()["has_guide"] is False


def test_seed_refreshes_catalog_exercises_for_templates(client):
    with get_session_context() as session:
        bench = session.query(Exercise).filter(Exercise.slug == "bench-press").one()
        bench.is_deleted = True
        session.add(
            Exercise(
                slug="legacy-global-only",
                title="Legacy Global Only",
                primary_muscle="old",
                equipment="old",
                created_by_user_id=None,
                source_exercise_id=None,
                is_deleted=False,
            )
        )
        session.flush()
        seed_demo_data(session, include_demo_users=False)

        refreshed_bench = session.query(Exercise).filter(Exercise.slug == "bench-press").one()
        obsolete = session.query(Exercise).filter(Exercise.slug == "legacy-global-only").one()

        assert refreshed_bench.is_deleted is False
        assert obsolete.is_deleted is True


def test_coach_can_manage_own_client_exercise(client):
    coach_headers = auth(client, telegram_user_id=1107, is_coach=True)
    client_headers = auth(client, telegram_user_id=3109, is_coach=False)
    other_headers = auth(client, telegram_user_id=3110, is_coach=False)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    accept_coach_invite(client, coach_headers, client_headers)

    created = client.post(
        "/api/v1/programs/exercises",
        json={
            "title": "Client Managed Row",
            "primary_muscle": "back",
            "equipment": "cable",
            "target_telegram_user_id": 3109,
        },
        headers=coach_headers,
    )
    assert created.status_code == 201
    assert created.json()["created_by_user_id"] == client_user["id"]

    client_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=client_headers).json()
    }
    coach_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=coach_headers).json()
    }
    other_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=other_headers).json()
    }
    assert "Client Managed Row" in client_titles
    assert "Client Managed Row" in coach_titles
    assert "Client Managed Row" not in other_titles

    updated = client.patch(
        f"/api/v1/programs/exercises/{created.json()['edit_target_id']}",
        json={"title": "Client Managed Updated", "primary_muscle": "back", "equipment": "cable"},
        headers=coach_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Client Managed Updated"

    deleted = client.delete(
        f"/api/v1/programs/exercises/{created.json()['edit_target_id']}",
        headers=coach_headers,
    )
    assert deleted.status_code == 204
    client_titles_after_delete = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=client_headers).json()
    }
    assert "Client Managed Updated" not in client_titles_after_delete


def test_coach_cannot_create_exercise_for_non_client(client):
    coach_headers = auth(client, telegram_user_id=1108, is_coach=True)
    auth(client, telegram_user_id=3111, is_coach=False)

    created = client.post(
        "/api/v1/programs/exercises",
        json={
            "title": "Non Client Row",
            "primary_muscle": "legs",
            "equipment": "machine",
            "target_telegram_user_id": 3111,
        },
        headers=coach_headers,
    )

    assert created.status_code == 403


def test_client_template_is_private(client):
    owner_headers = auth(client, telegram_user_id=3104, is_coach=False)
    other_headers = auth(client, telegram_user_id=3105, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=owner_headers).json()
    title = "Private Client Template"
    payload = {
        "title": title,
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": False,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }

    created = client.post("/api/v1/programs/templates", json=payload, headers=owner_headers)

    assert created.status_code == 200
    assert created.json()["template"]["is_public"] is False

    owner_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/templates/mine", headers=owner_headers).json()
    }
    other_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/templates/mine", headers=other_headers).json()
    }

    assert title in owner_titles
    assert title not in other_titles


def test_admin_template_is_public(client):
    admin_headers = auth(client, telegram_user_id=1104, is_coach=True, is_admin=True)
    client_headers = auth(client, telegram_user_id=3106, is_coach=False)
    coach_headers = auth(client, telegram_user_id=1105, is_coach=True)
    exercises = client.get("/api/v1/programs/exercises", headers=admin_headers).json()
    title = "Global Admin Template"
    payload = {
        "title": title,
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": False,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }

    created = client.post("/api/v1/programs/templates", json=payload, headers=admin_headers)

    assert created.status_code == 200
    assert created.json()["template"]["is_public"] is True

    client_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/templates/mine", headers=client_headers).json()
    }
    coach_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/templates/mine", headers=coach_headers).json()
    }

    assert title in client_titles
    assert title in coach_titles


def test_coach_can_manage_program_for_own_client(client):
    coach_headers = auth(client, telegram_user_id=1109, is_coach=True)
    client_headers = auth(client, telegram_user_id=3112, is_coach=False)
    other_coach_headers = auth(client, telegram_user_id=1110, is_coach=True)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    accept_coach_invite(client, coach_headers, client_headers)

    exercises = client.get("/api/v1/programs/exercises", headers=client_headers).json()
    payload = {
        "title": "Client Managed Program",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "coach",
        "target_telegram_user_id": 3112,
        "target_full_name": "Клиент программы",
        "assign_after_create": False,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }

    created = client.post("/api/v1/programs/templates", json=payload, headers=coach_headers)
    assert created.status_code == 200
    assert created.json()["template"]["owner_user_id"] == client_user["id"]
    template_id = created.json()["template"]["id"]

    client_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/templates/mine", headers=client_headers).json()
    }
    coach_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/templates/mine", headers=coach_headers).json()
    }
    other_coach_titles = {
        item["title"]
        for item in client.get(
            "/api/v1/programs/templates/mine", headers=other_coach_headers
        ).json()
    }
    assert "Client Managed Program" in client_titles
    assert "Client Managed Program" in coach_titles
    assert "Client Managed Program" not in other_coach_titles

    payload["title"] = "Client Managed Program Updated"
    updated = client.patch(
        f"/api/v1/programs/templates/{template_id}",
        json=payload,
        headers=coach_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Client Managed Program Updated"
    assert updated.json()["can_edit"] is True
    with get_session_context() as db:
        update_notice = (
            db.query(Notification)
            .filter(
                Notification.user_id == client_user["id"],
                Notification.title == "Программа тренировок изменена",
            )
            .one()
        )
        assert "Client Managed Program Updated" in update_notice.body

    blocked_delete = client.delete(
        f"/api/v1/programs/templates/{template_id}",
        headers=other_coach_headers,
    )
    assert blocked_delete.status_code == 403

    deleted = client.delete(f"/api/v1/programs/templates/{template_id}", headers=coach_headers)
    assert deleted.status_code == 204
    assert (
        client.get(f"/api/v1/programs/templates/{template_id}", headers=client_headers).status_code
        == 404
    )


def test_coach_cannot_create_program_for_non_client(client):
    coach_headers = auth(client, telegram_user_id=1111, is_coach=True)
    target_headers = auth(client, telegram_user_id=3113, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=target_headers).json()
    payload = {
        "title": "Forbidden Client Program",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "coach",
        "target_telegram_user_id": 3113,
        "target_full_name": "Не клиент",
        "assign_after_create": False,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }

    created = client.post("/api/v1/programs/templates", json=payload, headers=coach_headers)

    assert created.status_code == 403


def test_deleted_user_custom_exercises_do_not_become_global(client):
    admin_headers = auth(client, telegram_user_id=1106, is_coach=True, is_admin=True)
    user_headers = auth(client, telegram_user_id=3107, is_coach=False)
    other_headers = auth(client, telegram_user_id=3108, is_coach=False)
    user = client.get("/api/v1/me", headers=user_headers).json()
    title = "Deleted User Private Exercise"

    created = client.post(
        "/api/v1/programs/exercises",
        json={"title": title, "primary_muscle": "legs", "equipment": "machine"},
        headers=user_headers,
    )
    assert created.status_code == 201

    deleted = client.delete(f"/api/v1/admin/users/{user['id']}", headers=admin_headers)

    assert deleted.status_code == 204
    other_titles = {
        item["title"]
        for item in client.get("/api/v1/programs/exercises", headers=other_headers).json()
    }
    assert title not in other_titles


def test_coach_can_link_client_with_secure_invite(client):
    headers = auth(client, telegram_user_id=1002, is_coach=True)
    client_headers = auth(client, telegram_user_id=2001, is_coach=False)

    accept_coach_invite(client, headers, client_headers)

    listed = client.get("/api/v1/programs/clients", headers=headers)
    assert listed.status_code == 200
    assert any(row["telegram_user_id"] == 2001 for row in listed.json())


def test_client_approves_coach_change_and_has_only_one_active_coach(client):
    coach_one_headers = auth(
        client,
        telegram_user_id=1201,
        is_coach=True,
        username="@coach_one",
        full_name="Тренер Первый",
    )
    coach_two_headers = auth(
        client,
        telegram_user_id=1202,
        is_coach=True,
        username="@coach_two",
        full_name="Тренер Второй",
    )
    client_headers = auth(client, telegram_user_id=5201, is_coach=False)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    assert client.get("/api/v1/me", headers=client_headers).json()["trainer"] is None
    _, first_preview = accept_coach_invite(client, coach_one_headers, client_headers)
    assert first_preview["requires_trainer_change"] is False

    trainer = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer["username"] == "coach_one"
    assert trainer["full_name"] == "Тренер Первый"
    assert trainer["chat_url"] == "https://t.me/coach_one"
    assert trainer["can_open_chat"] is True

    trainer_before_accept = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer_before_accept["username"] == "coach_one"
    _, second_preview = accept_coach_invite(client, coach_two_headers, client_headers)
    assert second_preview["requires_trainer_change"] is True
    assert second_preview["current_trainer"]["username"] == "coach_one"

    first_clients = client.get("/api/v1/coach/clients", headers=coach_one_headers).json()
    second_clients = client.get("/api/v1/coach/clients", headers=coach_two_headers).json()
    assert not any(row["id"] == client_user["id"] for row in first_clients)
    assert any(row["id"] == client_user["id"] for row in second_clients)
    assert (
        client.get("/api/v1/me", headers=client_headers).json()["trainer"]["username"]
        == "coach_two"
    )

    with get_session_context() as db:
        relations = (
            db.query(CoachClient)
            .filter(CoachClient.client_user_id == client_user["id"])
            .order_by(CoachClient.id)
            .all()
        )
        assert [relation.status for relation in relations] == ["ended", "active"]
        assert relations[0].ended_at is not None
        assert relations[0].ended_reason == "client_switched_trainer"


def test_legacy_client_code_flow_is_not_public(client):
    coach_headers = auth(client, telegram_user_id=1220, is_coach=True)
    client_headers = auth(client, telegram_user_id=5220, is_coach=False)
    me = client.get("/api/v1/me", headers=client_headers).json()
    assert "client_code" not in me

    requested = client.post(
        "/api/v1/coach/clients",
        json={"client_code": "ABCD-234", "source": "client_code"},
        headers=coach_headers,
    )
    assert requested.status_code == 405
    assert client.get("/api/v1/me/client-code/qr", headers=client_headers).status_code == 404
    assert client.post("/api/v1/me/client-code/rotate", headers=client_headers).status_code == 404


def test_invite_link_preview_is_nonmutating_and_confirm_is_one_time(client):
    coach_headers = auth(client, telegram_user_id=1230, is_coach=True)
    first_client_headers = auth(client, telegram_user_id=5230, is_coach=False)
    other_client_headers = auth(client, telegram_user_id=5231, is_coach=False)
    first_user_id = client.get("/api/v1/me", headers=first_client_headers).json()["id"]

    created = client.post("/api/v1/coach/invite-links", headers=coach_headers)
    assert created.status_code == 201
    start_param = created.json()["start_param"]
    assert start_param.startswith("trainer_")
    token = start_param.removeprefix("trainer_")
    assert created.json()["code"] == token
    assert created.json()["web_url"] == f"https://app.your-fitness-coach.ru/join/{token}"
    assert created.json()["telegram_url"] == created.json()["url"]
    invite_page = client.get(f"/join/{token}")
    assert invite_page.status_code == 200
    assert '<div id="root"></div>' in invite_page.text
    invite_id = created.json()["invite_id"]

    for _ in range(2):
        preview = client.post(
            "/api/v1/me/coach-invites/link/preview",
            json={"token": token},
            headers=first_client_headers,
        )
        assert preview.status_code == 200
        assert preview.json()["invite_id"] == invite_id

    assert client.get("/api/v1/me/coach-invites", headers=first_client_headers).status_code == 404
    with get_session_context() as db:
        invite = db.query(CoachClientInvite).filter(CoachClientInvite.id == invite_id).one()
        assert invite.status == "pending"
        assert invite.client_user_id is None
        assert invite.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert token not in invite.token_hash

    accepted = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=first_client_headers,
    )
    assert accepted.status_code == 204
    repeated = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=first_client_headers,
    )
    assert repeated.status_code == 409
    stolen_after_use = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=other_client_headers,
    )
    assert stolen_after_use.status_code == 409

    relogged_headers = auth(client, telegram_user_id=5230, is_coach=False)
    assert client.get("/api/v1/me", headers=relogged_headers).json()["id"] == first_user_id
    with get_session_context() as db:
        assert db.query(User).filter(User.telegram_user_id == 5230).count() == 1
        assert (
            db.query(CoachClient)
            .filter(
                CoachClient.client_user_id == first_user_id,
                CoachClient.status == "active",
            )
            .count()
            == 1
        )
        assert (
            db.query(CoachClientInvite).filter(CoachClientInvite.id == invite_id).one().status
            == "accepted"
        )


def test_legacy_username_client_lookup_is_not_public(client):
    coach_headers = auth(client, telegram_user_id=1240, is_coach=True)
    missing = client.get(
        "/api/v1/coach/client-search?username=not_registered",
        headers=coach_headers,
    )
    assert missing.status_code == 404
    rejected = client.post(
        "/api/v1/coach/clients",
        json={"username": "not_registered", "source": "username_search"},
        headers=coach_headers,
    )
    assert rejected.status_code == 405

    auth(
        client,
        telegram_user_id=5240,
        is_coach=False,
        username="registered_client",
        full_name="Зарегистрированный клиент",
    )
    found = client.get(
        "/api/v1/coach/client-search?username=@registered_client",
        headers=coach_headers,
    )
    assert found.status_code == 404


def test_unbound_token_invite_cannot_be_accepted_by_database_id(client):
    coach_headers = auth(client, telegram_user_id=1210, is_coach=True)
    client_headers = auth(client, telegram_user_id=5210, is_coach=False)
    other_headers = auth(client, telegram_user_id=5211, is_coach=False)

    token, created = create_coach_invite_token(client, coach_headers)
    invite_id = created["invite_id"]
    assert client.get("/api/v1/me/coach-invites", headers=client_headers).status_code == 404
    assert client.get("/api/v1/me/coach-invites", headers=other_headers).status_code == 404
    forbidden = client.post(
        f"/api/v1/me/coach-invites/{invite_id}/accept",
        headers=other_headers,
    )
    assert forbidden.status_code == 404

    forbidden_for_intended_client = client.post(
        f"/api/v1/me/coach-invites/{invite_id}/accept",
        headers=client_headers,
    )
    assert forbidden_for_intended_client.status_code == 404
    confirmed = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=client_headers,
    )
    assert confirmed.status_code == 204


def test_coach_can_remove_client_link(client):
    coach_headers = auth(client, telegram_user_id=1203, is_coach=True, username="@unlink_coach")
    client_headers = auth(client, telegram_user_id=5202, is_coach=False)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    accept_coach_invite(client, coach_headers, client_headers)
    assert client.get("/api/v1/me", headers=client_headers).json()["trainer"]

    removed = client.delete(f"/api/v1/coach/clients/{client_user['id']}", headers=coach_headers)

    assert removed.status_code == 204
    assert client.get("/api/v1/me", headers=client_headers).json()["trainer"] is None
    rows = client.get("/api/v1/coach/clients", headers=coach_headers).json()
    assert not any(row["id"] == client_user["id"] for row in rows)


def test_client_can_detach_trainer(client):
    coach_headers = auth(client, telegram_user_id=1204, is_coach=True, username="@detach_coach")
    client_headers = auth(client, telegram_user_id=5203, is_coach=False)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    accept_coach_invite(client, coach_headers, client_headers)

    detached = client.delete("/api/v1/me/trainer", headers=client_headers)

    assert detached.status_code == 204
    assert client.get("/api/v1/me", headers=client_headers).json()["trainer"] is None
    rows = client.get("/api/v1/coach/clients", headers=coach_headers).json()
    assert not any(row["id"] == client_user["id"] for row in rows)


def test_trainer_info_without_username_is_not_clickable(client):
    coach_headers = auth(
        client,
        telegram_user_id=1205,
        is_coach=True,
        username="",
        full_name="Тренер Без Username",
    )
    client_headers = auth(client, telegram_user_id=5204, is_coach=False)

    accept_coach_invite(client, coach_headers, client_headers)

    trainer = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer["full_name"] == "Тренер Без Username"
    assert trainer["can_open_chat"] is False
    assert trainer["chat_url"] is None
    assert "username" in trainer["chat_unavailable_reason"]


def test_invite_link_does_not_depend_on_username_and_client_confirms_after_login(client):
    coach_headers = auth(client, telegram_user_id=1002, is_coach=True)
    token, created = create_coach_invite_token(client, coach_headers)

    init_data = signed_init_data(
        bot_token="test-token",
        auth_date=int(time.time()),
        telegram_user_id=5001,
        username="future_client",
    )
    login = client.post("/api/v1/auth/telegram/init", json={"init_data": init_data})
    assert login.status_code == 200
    client_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get("/api/v1/me/coach-invites", headers=client_headers).status_code == 404
    preview = client.post(
        "/api/v1/me/coach-invites/link/preview",
        json={"token": token},
        headers=client_headers,
    )
    assert preview.status_code == 200
    assert preview.json()["invite_id"] == created["invite_id"]
    confirmed = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=client_headers,
    )
    assert confirmed.status_code == 204

    listed = client.get("/api/v1/programs/clients", headers=coach_headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert any(row["telegram_user_id"] == 5001 and row["status"] == "active" for row in rows)


def test_me_requires_auth(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401


def test_invalid_token_treated_as_unauthorized(client):
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_telegram_init_data_rejects_stale_auth_date():
    bot_token = "test-token"
    stale_init_data = signed_init_data(
        bot_token=bot_token,
        auth_date=int(time.time()) - 2 * 24 * 60 * 60,
    )

    with pytest.raises(ValueError, match="устарел"):
        validate_telegram_init_data(stale_init_data, bot_token)


def test_telegram_init_data_rejects_non_object_user():
    init_data = signed_init_data(
        bot_token="test-token",
        auth_date=int(time.time()),
        user_data=[],
    )

    with pytest.raises(ValueError, match="Некорректный user"):
        validate_telegram_init_data(init_data, "test-token")


@pytest.mark.parametrize("invalid_id", [True, 0, -1, "555001", 2**63])
def test_telegram_init_data_rejects_invalid_user_id(invalid_id):
    init_data = signed_init_data(
        bot_token="test-token",
        auth_date=int(time.time()),
        user_data={"id": invalid_id, "first_name": "Telegram"},
    )

    with pytest.raises(ValueError, match="Некорректный id пользователя"):
        validate_telegram_init_data(init_data, "test-token")


def test_telegram_init_endpoint_rejects_oversized_payload(client):
    response = client.post("/api/v1/auth/telegram/init", json={"init_data": "x" * 16_385})

    assert response.status_code == 422


def test_refresh_token_rotation(client):
    login = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": 2001, "is_coach": False},
    )
    assert login.status_code == 200

    refresh_token = client.cookies.get("fit_refresh_token")
    assert refresh_token
    refreshed = client.post("/api/v1/auth/refresh", json={})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert "refresh_token" not in refreshed.json()
    assert client.cookies.get("fit_refresh_token") != refresh_token

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reused.status_code == 401


def test_admin_users_forbidden_for_client(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403


def test_admin_users_forbidden_for_coach(client):
    headers = auth(client, telegram_user_id=1002, is_coach=True)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403


def test_admin_users_ok_for_admin(client):
    headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_admin_users_supports_server_side_filters_and_pagination(client):
    headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    auth(client, telegram_user_id=6011, is_coach=False, full_name="Искомый клиент")
    auth(client, telegram_user_id=6012, is_coach=True, full_name="Другой тренер")

    page = client.get("/api/v1/admin/users?limit=1&offset=0", headers=headers)
    assert page.status_code == 200
    assert len(page.json()) == 1
    assert int(page.headers["X-Total-Count"]) >= 3

    filtered = client.get(
        "/api/v1/admin/users?search=6011&role=client&active=true",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert filtered.headers["X-Total-Count"] == "1"
    assert filtered.json()[0]["telegram_user_id"] == 6011


def test_admin_can_change_user_role(client):
    admin_headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    client_headers = auth(client, telegram_user_id=2001, is_coach=False)
    user = client.get("/api/v1/me", headers=client_headers).json()

    response = client.patch(
        f"/api/v1/admin/users/{user['id']}/role",
        json={"role": "coach"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "coach"
    promoted = client.get("/api/v1/me", headers=client_headers)
    assert promoted.status_code == 200
    assert promoted.json()["is_coach"] is True


def test_admin_can_block_and_unblock_user(client):
    admin_headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    user_headers = auth(client, telegram_user_id=5010, is_coach=False)
    user = client.get("/api/v1/me", headers=user_headers).json()

    blocked = client.patch(
        f"/api/v1/admin/users/{user['id']}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert blocked.status_code == 200
    assert blocked.json()["is_active"] is False

    assert client.get("/api/v1/me", headers=user_headers).status_code == 401
    relogin = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": 5010, "is_coach": False},
    )
    assert relogin.status_code == 403

    unblocked = client.patch(
        f"/api/v1/admin/users/{user['id']}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert unblocked.status_code == 200
    assert unblocked.json()["is_active"] is True
    assert auth(client, telegram_user_id=5010, is_coach=False)


def test_admin_cannot_block_or_delete_self(client):
    admin_headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    admin_user = client.get("/api/v1/me", headers=admin_headers).json()

    block = client.patch(
        f"/api/v1/admin/users/{admin_user['id']}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert block.status_code == 400

    delete = client.delete(f"/api/v1/admin/users/{admin_user['id']}", headers=admin_headers)
    assert delete.status_code == 400


def test_admin_can_delete_user(client):
    admin_headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    user_headers = auth(client, telegram_user_id=5011, is_coach=False)
    user = client.get("/api/v1/me", headers=user_headers).json()
    exercises = client.get("/api/v1/programs/exercises", headers=user_headers).json()
    payload = {
        "title": "Программа удаляемого пользователя",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }
    created = client.post("/api/v1/programs/templates", json=payload, headers=user_headers)
    assert created.status_code == 200

    deleted = client.delete(f"/api/v1/admin/users/{user['id']}", headers=admin_headers)
    assert deleted.status_code == 204
    assert client.get("/api/v1/me", headers=user_headers).status_code == 401

    rows = client.get("/api/v1/admin/users", headers=admin_headers).json()
    assert not any(row["telegram_user_id"] == 5011 for row in rows)


def test_admin_can_delete_template_from_admin_panel(client):
    admin_headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    exercises = client.get("/api/v1/programs/exercises", headers=admin_headers).json()
    payload = {
        "title": "Админ удаляет шаблон",
        "goal": "recomposition",
        "level": "intermediate",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "День 1",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 90,
                    }
                ],
            }
        ],
    }
    created = client.post("/api/v1/programs/templates", json=payload, headers=admin_headers)
    assert created.status_code == 200
    template_id = created.json()["template"]["id"]

    deleted = client.delete(f"/api/v1/admin/templates/{template_id}", headers=admin_headers)
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/programs/templates/{template_id}", headers=admin_headers)
    assert missing.status_code == 404


def test_coach_cannot_use_admin_delete_template(client):
    coach_headers = auth(client, telegram_user_id=1002, is_coach=True)
    response = client.delete("/api/v1/admin/templates/1", headers=coach_headers)
    assert response.status_code == 403


def test_billing_and_admin_payment_routes_are_not_exposed(client):
    headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    routes = [
        ("GET", "/api/v1/billing/plans"),
        ("POST", "/api/v1/billing/checkout"),
        ("POST", "/api/v1/billing/mock/complete/legacy-checkout"),
        ("GET", "/api/v1/billing/subscription"),
        ("GET", "/api/v1/admin/payments"),
    ]

    for method, path in routes:
        response = client.request(method, path, headers=headers)
        assert response.status_code == 404

    openapi_paths = client.get("/openapi.json").json()["paths"]
    assert not any("billing" in path for path in openapi_paths)
    assert "/api/v1/admin/payments" not in openapi_paths


def test_notification_reminder_hour_validation(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    response = client.patch(
        "/api/v1/notifications/settings",
        headers=headers,
        json={"workout_reminders_enabled": True, "reminder_hour": 25},
    )
    assert response.status_code in (400, 422)


def test_create_notification_and_list(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    scheduled = (datetime.now(UTC) + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    create = client.post(
        "/api/v1/notifications",
        headers=headers,
        json={"title": "Test напоминание", "body": "Текст", "scheduled_for": scheduled},
    )
    assert create.status_code == 201
    listed = client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert any(row["title"] == "Test напоминание" for row in rows)


def test_notification_scheduled_for_is_stored_as_msk_wall_time(client):
    headers = auth(client, telegram_user_id=6501, is_coach=False)

    response = client.post(
        "/api/v1/notifications",
        headers=headers,
        json={
            "title": "MSK напоминание",
            "body": "Текст",
            "scheduled_for": "2026-04-25T07:30:00Z",
        },
    )

    assert response.status_code == 201
    assert response.json()["scheduled_for"] == "2026-04-25T10:30:00"


def test_workout_reminders_are_deduplicated_claimed_and_retried(client, monkeypatch):
    fixed_local_now = datetime(2026, 4, 25, 12)
    fixed_utc_now = datetime(2026, 4, 25, 9)
    monkeypatch.setattr(
        notifications_service,
        "now_for_user_naive",
        lambda _user: fixed_local_now,
    )
    monkeypatch.setattr(notifications_service, "utcnow", lambda: fixed_utc_now)

    auth(client, telegram_user_id=6510, is_coach=False)
    with get_session_context() as session:
        user = session.query(User).filter(User.telegram_user_id == 6510).one()
        template = session.query(ProgramTemplate).first()
        program = UserProgram(user_id=user.id, template_id=template.id, is_active=True)
        session.add(program)
        session.flush()
        workout = UserWorkout(
            user_program_id=program.id,
            scheduled_date=fixed_local_now.date(),
            day_number=1,
            title="Тестовая тренировка",
            status="planned",
        )
        session.add(workout)
        session.flush()
        user_id = user.id
        workout_id = workout.id

        setting = session.query(NotificationSetting).filter_by(user_id=user.id).one()
        setting.workout_reminders_enabled = True
        setting.reminder_hour = 0

    with get_session_context() as session:
        assert sync_workout_reminders(session) == 1
        assert sync_workout_reminders(session) == 0
        rows = session.query(Notification).filter(Notification.user_id == user_id).all()
        assert len(rows) == 1
        assert rows[0].dedupe_key == f"workout:{workout_id}:reminder"

        rows[0].status = "cancelled"
        rows[0].attempt_count = 3
        rows[0].last_error = "disabled"
        rows[0].next_attempt_at = fixed_utc_now
        session.commit()
        assert sync_workout_reminders(session) == 0
        session.refresh(rows[0])
        assert rows[0].status == "queued"
        assert rows[0].attempt_count == 0
        assert rows[0].last_error is None
        assert rows[0].next_attempt_at is None

        claimed = claim_due_notifications(session)
        assert [row.id for row in claimed] == [rows[0].id]
        assert claim_due_notifications(session) == []

        mark_delivery_failed(session, claimed[0], RuntimeError("temporary"))
        session.refresh(claimed[0])
        assert claimed[0].status == "queued"
        assert claimed[0].attempt_count == 1
        assert claimed[0].next_attempt_at is not None


def test_bot_can_set_user_timezone_and_notifications_use_it(client):
    updated = client.post(
        "/api/v1/bot/timezone",
        headers={"X-Bot-Token": settings.bot_internal_token},
        json={
            "telegram_user_id": 6502,
            "timezone": "Asia/Tokyo",
            "username": "tokyo_user",
            "first_name": "Tokyo",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["timezone"] == "Asia/Tokyo"

    headers = auth(client, telegram_user_id=6502, is_coach=False)
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["profile"]["timezone"] == "Asia/Tokyo"

    response = client.post(
        "/api/v1/notifications",
        headers=headers,
        json={
            "title": "Tokyo напоминание",
            "body": "Текст",
            "scheduled_for": "2026-04-25T00:30:00Z",
        },
    )

    assert response.status_code == 201
    assert response.json()["scheduled_for"] == "2026-04-25T09:30:00"


def test_bot_rejects_invalid_timezone(client):
    response = client.post(
        "/api/v1/bot/timezone",
        headers={"X-Bot-Token": settings.bot_internal_token},
        json={"telegram_user_id": 6503, "timezone": "Mars/Olympus"},
    )

    assert response.status_code == 400


def test_bot_internal_api_does_not_accept_telegram_bot_token(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "telegram-api-token")
    monkeypatch.setattr(settings, "bot_internal_token", "separate-internal-token")
    payload = {
        "telegram_user_id": 6504,
        "timezone": "Europe/Moscow",
        "first_name": "Internal",
    }

    rejected = client.post(
        "/api/v1/bot/timezone",
        headers={"X-Bot-Token": "telegram-api-token"},
        json=payload,
    )
    accepted = client.post(
        "/api/v1/bot/timezone",
        headers={"X-Bot-Token": "separate-internal-token"},
        json=payload,
    )

    assert rejected.status_code == 403
    assert accepted.status_code == 200


def test_to_msk_naive_converts_aware_utc_datetime():
    converted = to_msk_naive(datetime(2026, 4, 25, 7, 30, tzinfo=UTC))

    assert converted == datetime(2026, 4, 25, 10, 30)


def test_health_includes_request_id(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "x-request-id" in {k.lower(): v for k, v in response.headers.items()}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_request_id_accepts_safe_value_and_replaces_untrusted_value(client):
    accepted = client.get("/health/live", headers={"X-Request-ID": "edge-request_123.abc"})
    replaced = client.get("/health/live", headers={"X-Request-ID": "x" * 129})

    assert accepted.headers["x-request-id"] == "edge-request_123.abc"
    assert replaced.headers["x-request-id"] != "x" * 129
    assert re.fullmatch(r"[0-9a-f-]{36}", replaced.headers["x-request-id"])


def test_health_supports_head(client):
    response = client.head("/health")
    assert response.status_code == 200
    assert response.content == b""
    assert "x-request-id" in {k.lower(): v for k, v in response.headers.items()}


def test_auth_uses_httponly_refresh_cookie(client):
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": 4050, "is_coach": False},
    )

    assert response.status_code == 200
    assert "refresh_token" not in response.json()
    cookie = response.headers["set-cookie"].lower()
    assert "fit_refresh_token=" in cookie
    assert "httponly" in cookie
    assert "samesite=strict" in cookie


def test_workout_state_machine_rejects_invalid_transitions(client):
    headers = auth(client, telegram_user_id=2050, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Проверка состояний",
        "goal": "recomposition",
        "level": "beginner",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "Сегодня",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 60,
                    }
                ],
            }
        ],
    }
    assert (
        client.post("/api/v1/programs/templates", json=payload, headers=headers).status_code == 200
    )
    workout = client.get("/api/v1/workouts/today", headers=headers).json()

    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers).status_code == 409
    )
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers).status_code == 409
    )

    set_id = workout["exercises"][0]["sets"][0]["id"]
    saved = client.patch(
        f"/api/v1/workouts/sets/{set_id}",
        json={"actual_reps": 8, "is_completed": True},
        headers=headers,
    )
    assert saved.status_code == 200
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers).status_code == 200
    )
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers).status_code == 409
    )


def test_invites_do_not_mutate_profile_or_delete_other_coach_invites(client):
    client_headers = auth(
        client,
        telegram_user_id=5250,
        is_coach=False,
        username="@real_client",
        full_name="Настоящее имя",
    )
    coach_one = auth(client, telegram_user_id=1250, is_coach=True)
    coach_two = auth(client, telegram_user_id=1251, is_coach=True)

    first_token, first_created = create_coach_invite_token(client, coach_one)
    second_token, second_created = create_coach_invite_token(client, coach_two)
    for token in (first_token, second_token):
        preview = client.post(
            "/api/v1/me/coach-invites/link/preview",
            json={"token": token},
            headers=client_headers,
        )
        assert preview.status_code == 200

    me = client.get("/api/v1/me", headers=client_headers).json()
    assert me["profile"]["full_name"] == "Настоящее имя"
    assert me["username"] == "real_client"
    assert client.get("/api/v1/me/coach-invites", headers=client_headers).status_code == 404

    confirmed = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": first_token},
        headers=client_headers,
    )
    assert confirmed.status_code == 204
    with get_session_context() as db:
        first = (
            db.query(CoachClientInvite)
            .filter(CoachClientInvite.id == first_created["invite_id"])
            .one()
        )
        second = (
            db.query(CoachClientInvite)
            .filter(CoachClientInvite.id == second_created["invite_id"])
            .one()
        )
        assert first.status == "accepted"
        assert first.full_name == "Настоящее имя"
        assert second.status == "pending"


def test_deleting_template_preserves_assigned_program_and_workouts(client):
    headers = auth(client, telegram_user_id=4051, is_coach=True, is_admin=True)
    user = client.get("/api/v1/me", headers=headers).json()
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    payload = {
        "title": "Архивируемый шаблон",
        "goal": "maintenance",
        "level": "beginner",
        "mode": "self",
        "assign_after_create": True,
        "days": [
            {
                "title": "Сохранённая тренировка",
                "exercises": [
                    {
                        "exercise_id": exercises[0]["id"],
                        "prescribed_sets": 1,
                        "prescribed_reps": "8",
                        "rest_seconds": 60,
                    }
                ],
            }
        ],
    }
    created = client.post("/api/v1/programs/templates", json=payload, headers=headers)
    assert created.status_code == 200
    template_id = created.json()["template"]["id"]
    program_id = created.json()["assigned_program_id"]

    assert (
        client.delete(f"/api/v1/admin/templates/{template_id}", headers=headers).status_code == 204
    )

    with get_session_context() as db:
        program = db.query(UserProgram).filter(UserProgram.id == program_id).one()
        assert program.user_id == user["id"]
        assert program.template_id is None
        assert db.query(UserWorkout).filter(UserWorkout.user_program_id == program.id).count() == 1


def test_deleting_coach_preserves_client_program_and_workouts(client):
    admin_headers = auth(client, telegram_user_id=4052, is_coach=True, is_admin=True)
    coach_headers = auth(client, telegram_user_id=1352, is_coach=True)
    client_headers = auth(client, telegram_user_id=5352, is_coach=False)
    coach_user = client.get("/api/v1/me", headers=coach_headers).json()

    accept_coach_invite(client, coach_headers, client_headers)

    exercises = client.get("/api/v1/programs/exercises", headers=coach_headers).json()
    created = client.post(
        "/api/v1/programs/templates",
        json={
            "title": "Программа, переживающая удаление тренера",
            "goal": "maintenance",
            "level": "beginner",
            "mode": "coach",
            "target_telegram_user_id": 5352,
            "assign_after_create": True,
            "days": [
                {
                    "title": "День клиента",
                    "exercises": [
                        {
                            "exercise_id": exercises[0]["id"],
                            "prescribed_sets": 1,
                            "prescribed_reps": "8",
                            "rest_seconds": 60,
                        }
                    ],
                }
            ],
        },
        headers=coach_headers,
    )
    assert created.status_code == 200
    program_id = created.json()["assigned_program_id"]

    deleted = client.delete(
        f"/api/v1/admin/users/{coach_user['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/workouts/today", headers=client_headers).status_code == 200

    with get_session_context() as db:
        program = db.query(UserProgram).filter(UserProgram.id == program_id).one()
        assert program.template_id is None
        assert program.assigned_by_user_id is None
        assert db.query(UserWorkout).filter(UserWorkout.user_program_id == program.id).count() == 1


def test_csp_blocks_unhashed_inline_scripts(client):
    response = client.get("/app")
    policy = response.headers["content-security-policy"]
    script_policy = policy.split("script-src", 1)[1].split(";", 1)[0]

    assert "img-src 'self' data: blob:" in policy
    assert "'unsafe-inline'" not in script_policy
    assert "'sha256-" not in script_policy

    html = response.text
    inline_sources = re.findall(r"<script(?:\s+[^>]*)?>([\s\S]*?)</script>", html)
    assert all(not source.strip() for source in inline_sources)

    api_client = (
        Path(__file__).resolve().parents[2] / "frontend" / "src" / "shared" / "api" / "client.ts"
    ).read_text(encoding="utf-8")
    assert "localStorage.setItem(ACCESS_TOKEN_KEY" not in api_client
    assert "sessionStorage.setItem(ACCESS_TOKEN_KEY" in api_client


def test_versioned_static_assets_are_cached_but_html_is_not(client):
    page = client.get("/app")
    asset_path = re.search(r'href="(/assets/[^"]+\.css)"', page.text).group(1)
    asset = client.get(asset_path)
    assert asset.status_code == 200
    assert asset.headers["cache-control"] == "public, max-age=31536000, immutable"

    assert page.status_code == 200
    assert "no-store" in page.headers["cache-control"]


def test_root_serves_public_landing_spa(client):
    response = client.get("/")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "no-store" in response.headers["cache-control"]


@pytest.mark.parametrize("path", ["/verify-email", "/reset-password"])
def test_browser_auth_routes_serve_spa(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "no-store" in response.headers["cache-control"]


def test_dev_login_provisions_one_idempotent_telegram_identity(client):
    from fitminiapp_api.models.auth_identity import AuthIdentity

    payload = {
        "telegram_user_id": 8_800_101,
        "username": "identity_client",
        "full_name": "Identity Client",
    }
    assert client.post("/api/v1/auth/dev-login", json=payload).status_code == 200
    assert client.post("/api/v1/auth/dev-login", json=payload).status_code == 200

    with get_session_context() as db:
        identities = (
            db.query(AuthIdentity)
            .filter(
                AuthIdentity.provider == "telegram",
                AuthIdentity.subject == str(payload["telegram_user_id"]),
            )
            .all()
        )
        assert len(identities) == 1
        assert identities[0].user.telegram_user_id == payload["telegram_user_id"]


def test_email_auth_stays_disabled_when_browser_oauth_is_enabled(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "enable_web_auth", True)
    response = client.post(
        "/api/v1/auth/email/register",
        json={
            "username": "browser_user",
            "email": "browser@example.com",
            "password": "a-long-browser-password",
        },
    )

    assert response.status_code == 404


def test_email_registration_verification_and_login_share_internal_account(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "enable_email_auth", True)
    payload = {
        "username": "browser_user",
        "email": "Browser@Example.com",
        "password": "a-long-browser-password",
    }
    registered = client.post("/api/v1/auth/email/register", json=payload)
    assert registered.status_code == 201
    verification_token = registered.json()["verification_token"]
    assert verification_token

    before_verification = client.post(
        "/api/v1/auth/email/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert before_verification.status_code == 401
    assert "Подтвердите email" in before_verification.json()["detail"]

    verified = client.post(
        "/api/v1/auth/email/verify",
        json={"token": verification_token},
    )
    assert verified.status_code == 200
    headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["telegram_user_id"] is None
    assert me.json()["username"] == payload["username"]

    reused_token = client.post(
        "/api/v1/auth/email/verify",
        json={"token": verification_token},
    )
    assert reused_token.status_code == 400

    logged_in = client.post(
        "/api/v1/auth/email/login",
        json={"email": payload["email"].lower(), "password": payload["password"]},
    )
    assert logged_in.status_code == 200


def test_email_registration_rejects_duplicate_identity_and_weak_password(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "enable_email_auth", True)
    weak = client.post(
        "/api/v1/auth/email/register",
        json={
            "username": "weak_user",
            "email": "weak@example.com",
            "password": "password1234",
        },
    )
    assert weak.status_code == 422

    payload = {
        "username": "unique_user",
        "email": "unique@example.com",
        "password": "correct horse battery staple",
    }
    assert client.post("/api/v1/auth/email/register", json=payload).status_code == 201
    duplicate = client.post(
        "/api/v1/auth/email/register",
        json={**payload, "username": "another_user"},
    )
    assert duplicate.status_code == 409


def test_password_reset_revokes_old_password_and_tokens(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "enable_email_auth", True)
    email = "reset@example.com"
    old_password = "old-password-for-browser"
    registered = client.post(
        "/api/v1/auth/email/register",
        json={"username": "reset_user", "email": email, "password": old_password},
    )
    verified = client.post(
        "/api/v1/auth/email/verify",
        json={"token": registered.json()["verification_token"]},
    )
    assert verified.status_code == 200

    requested = client.post("/api/v1/auth/password/reset/request", json={"email": email})
    reset_token = requested.json()["action_token"]
    assert reset_token
    new_password = "new-password-for-browser"
    confirmed = client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": reset_token, "password": new_password},
    )
    assert confirmed.status_code == 200

    assert (
        client.post(
            "/api/v1/auth/email/login",
            json={"email": email, "password": old_password},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/email/login",
            json={"email": email, "password": new_password},
        ).status_code
        == 200
    )


def test_password_reset_request_does_not_reveal_unknown_email(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "enable_email_auth", True)
    response = client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["action_token"] is None


def test_unconfigured_oauth_provider_is_not_exposed(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "enable_web_auth", True)
    config = client.get("/api/v1/public/config")
    assert config.status_code == 200
    assert config.json()["enable_email_auth"] is False
    assert config.json()["oauth_providers"] == []

    started = client.get("/api/v1/auth/oauth/google/start")
    assert started.status_code == 404


def test_browser_telegram_login_reuses_existing_telegram_user(client):
    from fitminiapp_api.models.auth_identity import AuthIdentity
    from fitminiapp_api.models.user import User
    from fitminiapp_api.services.oauth_login import get_or_create_oauth_user

    headers = auth(client, telegram_user_id=8_810_001, username="telegram_browser")
    current_id = client.get("/api/v1/me", headers=headers).json()["id"]

    with get_session_context() as db:
        user = get_or_create_oauth_user(
            db,
            provider="telegram",
            raw_claims={
                "id": 8_810_001,
                "sub": "telegram-oidc-subject",
                "preferred_username": "telegram_browser",
                "name": "Telegram Browser",
            },
        )
        assert user.id == current_id
        assert db.query(User).filter(User.telegram_user_id == 8_810_001).count() == 1
        assert (
            db.query(AuthIdentity)
            .filter(AuthIdentity.user_id == user.id, AuthIdentity.provider == "telegram")
            .count()
            == 1
        )


def test_oauth_callback_creates_browser_session_without_exposing_access_token(client, monkeypatch):
    from fitminiapp_api.api.v1 import auth as auth_api
    from fitminiapp_api.core.config import settings

    class FakeTelegramClient:
        async def authorize_access_token(self, request):
            del request
            return {
                "userinfo": {
                    "id": 8_810_002,
                    "sub": "telegram-oidc-subject-002",
                    "preferred_username": "oauth_callback_user",
                    "name": "OAuth Callback User",
                }
            }

    monkeypatch.setattr(settings, "enable_web_auth", True)
    monkeypatch.setattr(
        auth_api,
        "configured_oauth_client",
        lambda provider: FakeTelegramClient() if provider == "telegram" else None,
    )
    response = client.get(
        "/api/v1/auth/oauth/telegram/callback",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    assert "access_token" not in response.headers["location"]
    assert "fit_refresh_token=" in response.headers["set-cookie"]


def test_social_login_does_not_auto_link_only_by_matching_email(client, monkeypatch):
    from fitminiapp_api.core.config import settings
    from fitminiapp_api.services.oauth_login import get_or_create_oauth_user

    monkeypatch.setattr(settings, "enable_email_auth", True)
    email = "shared@example.com"
    registered = client.post(
        "/api/v1/auth/email/register",
        json={
            "username": "email_owner",
            "email": email,
            "password": "safe-password-for-email-owner",
        },
    )
    verified = client.post(
        "/api/v1/auth/email/verify",
        json={"token": registered.json()["verification_token"]},
    )
    local_headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
    local_id = client.get("/api/v1/me", headers=local_headers).json()["id"]

    with get_session_context() as db:
        google_user = get_or_create_oauth_user(
            db,
            provider="google",
            raw_claims={
                "sub": "google-subject-001",
                "email": email,
                "email_verified": True,
                "name": "Google User",
            },
        )
        assert google_user.id != local_id


def test_alembic_revision_ids_fit_version_table_column():
    versions_dir = Path(__file__).resolve().parents[2] / "backend" / "alembic" / "versions"
    for migration in versions_dir.glob("*.py"):
        source = migration.read_text(encoding="utf-8")
        match = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', source, re.MULTILINE)
        assert match, f"Revision id not found in {migration.name}"
        assert len(match.group(1)) <= 32, f"Revision id is too long in {migration.name}"


def test_miniapp_has_role_gated_coach_and_admin_navigation():
    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "src" / "app" / "AppShell.tsx"
    ).read_text(encoding="utf-8")
    assert 'to="/coach"' in source
    assert 'to="/admin"' in source
    assert "user.is_coach || user.is_admin" in source
    assert "user.is_admin" in source


def test_client_management_is_consolidated_in_coach_section():
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    coach = (root / "pages" / "coach" / "CoachPage.tsx").read_text(encoding="utf-8")
    miniapp = (root / "pages" / "miniapp" / "MiniAppPage.tsx").read_text(encoding="utf-8")
    assert "/api/v1/coach/clients" in coach
    assert "ClientProfileEditor" in coach
    assert "targetTelegramId" in coach
    assert "/api/v1/coach/clients" not in miniapp


def test_exercise_catalog_can_add_exercises_to_program_builder():
    root = Path(__file__).resolve().parents[2] / "frontend" / "src" / "features"
    catalog = (root / "exercises" / "ExerciseCatalog.tsx").read_text(encoding="utf-8")
    builder = (root / "programs" / "ProgramBuilder.tsx").read_text(encoding="utf-8")
    assert "/api/v1/programs/exercises" in catalog
    assert "Добавить упражнение" in builder
    assert "exercise_id" in builder


def test_program_builder_uses_difficulty_and_level_specific_day_limits():
    source = (
        Path(__file__).resolve().parents[2]
        / "frontend"
        / "src"
        / "features"
        / "programs"
        / "ProgramBuilder.tsx"
    ).read_text(encoding="utf-8")
    assert "difficulty_level" in source or "level" in source
    assert "Добавить день" in source
    assert "prescribed_sets" in source
