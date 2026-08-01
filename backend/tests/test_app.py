import hashlib
import hmac
import json
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pytest
from pydantic import ValidationError

from fitminiapp_api.core.config import Settings
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


def accept_latest_coach_invite(client, headers):
    invites = client.get("/api/v1/me/coach-invites", headers=headers)
    assert invites.status_code == 200
    assert invites.json()
    invite_id = invites.json()[0]["id"]
    accepted = client.post(
        f"/api/v1/me/coach-invites/{invite_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 204


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
            app_name="FitMiniApp",
            app_host="0.0.0.0",
            app_port=8000,
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
            app_name="FitMiniApp",
            app_host="0.0.0.0",
            app_port=8000,
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


def test_coach_can_assign_kbju_to_own_client(client):
    coach_headers = auth(
        client,
        telegram_user_id=6101,
        is_coach=True,
        username="@nutrition_coach",
        full_name="КБЖУ Тренер",
    )
    client_headers = auth(client, telegram_user_id=6102, is_coach=False)
    client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 6102},
        headers=coach_headers,
    )
    accept_latest_coach_invite(client, client_headers)

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


def test_coach_can_update_own_client_profile_and_measurements(client):
    coach_headers = auth(client, telegram_user_id=6110, is_coach=True)
    client_headers = auth(client, telegram_user_id=6111, is_coach=False)
    other_coach_headers = auth(client, telegram_user_id=6112, is_coach=True)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    invited = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 6111, "full_name": "Новый клиент"},
        headers=coach_headers,
    )
    assert invited.status_code == 201
    accept_latest_coach_invite(client, client_headers)

    profile = client.patch(
        f"/api/v1/coach/clients/{client_user['id']}/profile",
        json={
            "full_name": "Клиент с анкетой",
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
    assert me["profile"]["full_name"] == "Клиент с анкетой"
    assert me["profile"]["weight_kg"] == 74
    assert me["profile"]["cardio_trainings_per_week"] == 2


def test_coach_can_assign_existing_template_to_own_client(client):
    coach_headers = auth(client, telegram_user_id=6120, is_coach=True)
    client_headers = auth(client, telegram_user_id=6121, is_coach=False)
    other_coach_headers = auth(client, telegram_user_id=6122, is_coach=True)
    client_user = client.get("/api/v1/me", headers=client_headers).json()
    client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 6121},
        headers=coach_headers,
    )
    accept_latest_coach_invite(client, client_headers)

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
    template_id = created.json()["template"]["id"]

    assigned = client.post(
        f"/api/v1/coach/clients/{client_user['id']}/templates/{template_id}/assign",
        json={"start_date": "2026-07-31"},
        headers=coach_headers,
    )
    assert assigned.status_code == 200
    assert assigned.json()["workouts_created"] == 1
    assert client.get("/api/v1/workouts/week", headers=client_headers).status_code == 200

    client_templates = client.get("/api/v1/programs/templates/mine", headers=client_headers).json()
    assigned_template = next(item for item in client_templates if item["id"] == template_id)
    assert assigned_template["is_assigned_to_current_user"] is True
    assert assigned_template["is_active_for_current_user"] is True
    assert assigned_template["assigned_by_user_id"] == created.json()["template"]["owner_user_id"]

    coach_programs = client.get("/api/v1/coach/assigned-programs", headers=coach_headers)
    assert coach_programs.status_code == 200
    assert coach_programs.json() == [
        {
            "id": assigned.json()["user_program_id"],
            "client_id": client_user["id"],
            "client_telegram_user_id": 6121,
            "client_username": client_user["username"],
            "client_full_name": client_user["profile"]["full_name"],
            "template_id": template_id,
            "title": "Шаблон тренера",
            "goal": "maintenance",
            "level": "beginner",
            "assigned_at": coach_programs.json()[0]["assigned_at"],
            "is_active": True,
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

    assigned = client.post(
        f"/api/v1/programs/templates/{template_id}/assign-to-me",
        json={"start_date": "2026-08-10"},
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

    assert scheduled_dates == ["2026-08-10", "2026-08-11"]


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
    }.issubset({item["slug"] for item in templates})
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


def test_every_seeded_exercise_has_complete_guide_and_local_images(client):
    headers = auth(client, telegram_user_id=31033, is_coach=False)
    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    standard_exercises = [item for item in exercises if not item["is_custom"]]
    static_dir = Path(__file__).resolve().parents[2] / "backend" / "assets"

    assert len(standard_exercises) == 149
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
        assert len(guide["images"]) == 2
        assert [image["phase"] for image in guide["images"]] == [
            "Исходное положение",
            "Активная фаза",
        ]
        for image in guide["images"]:
            asset = static_dir / image["url"].removeprefix("/static/")
            assert asset.is_file(), asset


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

    linked = client.post(
        "/api/v1/programs/clients",
        json={"telegram_user_id": 3109, "full_name": "Клиент тренера"},
        headers=coach_headers,
    )
    assert linked.status_code == 201
    assert linked.json()["status"] == "pending"
    accept_latest_coach_invite(client, client_headers)

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

    linked = client.post(
        "/api/v1/programs/clients",
        json={"telegram_user_id": 3112, "full_name": "Клиент программы"},
        headers=coach_headers,
    )
    assert linked.status_code == 201
    accept_latest_coach_invite(client, client_headers)

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


def test_coach_can_add_client_by_telegram_id(client):
    headers = auth(client, telegram_user_id=1002, is_coach=True)
    client_headers = auth(client, telegram_user_id=2001, is_coach=False)

    created = client.post(
        "/api/v1/programs/clients",
        json={"telegram_user_id": 2001, "full_name": "Клиент тренера"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    assert created.json()["telegram_user_id"] == 2001

    accept_latest_coach_invite(client, client_headers)

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

    first_link = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5201, "full_name": "Клиент с тренером"},
        headers=coach_one_headers,
    )
    assert first_link.status_code == 201
    assert client.get("/api/v1/me", headers=client_headers).json()["trainer"] is None
    accept_latest_coach_invite(client, client_headers)

    trainer = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer["username"] == "coach_one"
    assert trainer["full_name"] == "Тренер Первый"
    assert trainer["chat_url"] == "https://t.me/coach_one"
    assert trainer["can_open_chat"] is True

    second_link = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5201, "full_name": "Клиент с тренером"},
        headers=coach_two_headers,
    )
    assert second_link.status_code == 201

    trainer_before_accept = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer_before_accept["username"] == "coach_one"
    accept_latest_coach_invite(client, client_headers)

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


def test_client_code_request_rotation_and_qr(client):
    coach_headers = auth(client, telegram_user_id=1220, is_coach=True)
    client_headers = auth(client, telegram_user_id=5220, is_coach=False)
    me = client.get("/api/v1/me", headers=client_headers).json()
    original_code = me["client_code"]
    assert re.fullmatch(r"[A-Z2-9]{4}-[A-Z2-9]{3}", original_code)

    requested = client.post(
        "/api/v1/coach/clients",
        json={"client_code": original_code, "source": "client_code"},
        headers=coach_headers,
    )
    assert requested.status_code == 201
    assert requested.json()["status"] == "pending"
    invites = client.get("/api/v1/me/coach-invites", headers=client_headers).json()
    assert invites[0]["source"] == "client_code"
    with get_session_context() as db:
        notification = (
            db.query(Notification)
            .filter(Notification.dedupe_key == f"trainer_request:{invites[0]['id']}")
            .one()
        )
        assert notification.status == "queued"
        assert "хочет добавить вас" in notification.title

    qr = client.get("/api/v1/me/client-code/qr", headers=client_headers)
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert qr.content.startswith(b"\x89PNG")

    rotated = client.post("/api/v1/me/client-code/rotate", headers=client_headers)
    assert rotated.status_code == 200
    assert rotated.json()["client_code"] != original_code
    old_code = client.post(
        "/api/v1/coach/clients",
        json={"client_code": original_code, "source": "client_code"},
        headers=coach_headers,
    )
    assert old_code.status_code == 400


def test_invite_link_claim_is_bound_to_verified_existing_user_and_idempotent(client):
    coach_headers = auth(client, telegram_user_id=1230, is_coach=True)
    first_client_headers = auth(client, telegram_user_id=5230, is_coach=False)
    first_user_id = client.get("/api/v1/me", headers=first_client_headers).json()["id"]

    created = client.post("/api/v1/coach/invite-links", headers=coach_headers)
    assert created.status_code == 201
    start_param = created.json()["start_param"]
    assert start_param.startswith("trainer_")
    token = start_param.removeprefix("trainer_")

    for _ in range(2):
        claimed = client.post(
            f"/api/v1/me/coach-invites/link/{token}/claim",
            headers=first_client_headers,
        )
        assert claimed.status_code == 200

    invite_id = client.get("/api/v1/me/coach-invites", headers=first_client_headers).json()[0]["id"]
    for _ in range(2):
        accepted = client.post(
            f"/api/v1/me/coach-invites/{invite_id}/accept",
            headers=first_client_headers,
        )
        assert accepted.status_code == 204

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


def test_username_search_only_finds_registered_local_users(client):
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
    assert rejected.status_code == 400

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
    assert found.status_code == 200
    assert found.json() == {
        "username": "registered_client",
        "full_name": "Зарегистрированный клиент",
        "photo_url": None,
    }


def test_only_invited_client_can_respond_to_coach_invite(client):
    coach_headers = auth(client, telegram_user_id=1210, is_coach=True)
    client_headers = auth(client, telegram_user_id=5210, is_coach=False)
    other_headers = auth(client, telegram_user_id=5211, is_coach=False)

    invited = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5210},
        headers=coach_headers,
    )
    assert invited.status_code == 201

    invite_id = client.get("/api/v1/me/coach-invites", headers=client_headers).json()[0]["id"]
    assert client.get("/api/v1/me/coach-invites", headers=other_headers).json() == []
    forbidden = client.post(
        f"/api/v1/me/coach-invites/{invite_id}/accept",
        headers=other_headers,
    )
    assert forbidden.status_code == 404

    declined = client.post(
        f"/api/v1/me/coach-invites/{invite_id}/decline",
        headers=client_headers,
    )
    assert declined.status_code == 204
    assert client.get("/api/v1/me", headers=client_headers).json()["trainer"] is None


def test_coach_can_remove_client_link(client):
    coach_headers = auth(client, telegram_user_id=1203, is_coach=True, username="@unlink_coach")
    client_headers = auth(client, telegram_user_id=5202, is_coach=False)
    client_user = client.get("/api/v1/me", headers=client_headers).json()

    linked = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5202, "full_name": "Клиент на удаление"},
        headers=coach_headers,
    )
    assert linked.status_code == 201
    accept_latest_coach_invite(client, client_headers)
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

    linked = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5203, "full_name": "Самостоятельный клиент"},
        headers=coach_headers,
    )
    assert linked.status_code == 201
    accept_latest_coach_invite(client, client_headers)

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

    linked = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5204, "full_name": "Клиент без ссылки"},
        headers=coach_headers,
    )
    assert linked.status_code == 201
    accept_latest_coach_invite(client, client_headers)

    trainer = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer["full_name"] == "Тренер Без Username"
    assert trainer["can_open_chat"] is False
    assert trainer["chat_url"] is None
    assert "username" in trainer["chat_unavailable_reason"]


def test_coach_can_invite_client_by_username_and_client_accepts_on_login(client):
    coach_headers = auth(client, telegram_user_id=1002, is_coach=True)

    invited = client.post(
        "/api/v1/programs/clients",
        json={"username": "@future_client", "full_name": "Будущий клиент"},
        headers=coach_headers,
    )

    assert invited.status_code == 201
    assert invited.json()["status"] == "pending"
    assert invited.json()["username"] == "future_client"

    init_data = signed_init_data(
        bot_token="test-token",
        auth_date=int(time.time()),
        telegram_user_id=5001,
        username="future_client",
    )
    login = client.post("/api/v1/auth/telegram/init", json={"init_data": init_data})
    assert login.status_code == 200
    client_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    listed = client.get("/api/v1/programs/clients", headers=coach_headers)
    assert listed.status_code == 200
    assert any(
        row["telegram_user_id"] == 5001 and row["status"] == "pending" for row in listed.json()
    )

    accept_latest_coach_invite(client, client_headers)

    listed = client.get("/api/v1/programs/clients", headers=coach_headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert any(row["telegram_user_id"] == 5001 and row["status"] == "active" for row in rows)
    assert not any(
        row["username"] == "future_client" and row["status"] == "pending" for row in rows
    )


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


def test_admin_payments_ok_for_admin(client):
    headers = auth(client, telegram_user_id=1001, is_coach=True, is_admin=True)
    plans = client.get("/api/v1/billing/plans", headers=headers).json()
    premium = next(p for p in plans if p["code"] == "premium")
    checkout = client.post(
        "/api/v1/billing/checkout",
        json={"plan_code": premium["code"]},
        headers=headers,
    )
    assert checkout.status_code == 200

    response = client.get("/api/v1/admin/payments", headers=headers)
    assert response.status_code == 200
    rows = response.json()
    assert any(row["plan_code"] == "premium" for row in rows)


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
        headers={"X-Bot-Token": "test-token"},
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
        headers={"X-Bot-Token": "test-token"},
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


def test_mock_billing_activation(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    plans = client.get("/api/v1/billing/plans", headers=headers).json()
    premium = next(p for p in plans if p["code"] == "premium")
    checkout = client.post(
        "/api/v1/billing/checkout", json={"plan_code": premium["code"]}, headers=headers
    )
    assert checkout.status_code == 200
    checkout_id = checkout.json()["checkout_id"]
    assert client.post(f"/api/v1/billing/mock/complete/{checkout_id}").status_code == 401
    other_headers = auth(client, telegram_user_id=2999, is_coach=False)
    assert (
        client.post(
            f"/api/v1/billing/mock/complete/{checkout_id}", headers=other_headers
        ).status_code
        == 404
    )
    complete = client.post(f"/api/v1/billing/mock/complete/{checkout_id}", headers=headers)
    assert complete.status_code == 200
    sub = client.get("/api/v1/billing/subscription", headers=headers)
    assert sub.status_code == 200
    assert sub.json()["plan_code"] == "premium"


def test_billing_checkout_falls_back_to_frontend_base_url(client, monkeypatch):
    from fitminiapp_api.core.config import settings

    monkeypatch.setattr(settings, "payment_public_url", "")
    monkeypatch.setattr(settings, "frontend_base_url", "https://app.your-fitness-coach.ru")

    headers = auth(client, telegram_user_id=2001, is_coach=False)
    plans = client.get("/api/v1/billing/plans", headers=headers).json()
    premium = next(p for p in plans if p["code"] == "premium")

    checkout = client.post(
        "/api/v1/billing/checkout",
        json={"plan_code": premium["code"]},
        headers=headers,
    )

    assert checkout.status_code == 200
    assert checkout.json()["checkout_url"].startswith("https://app.your-fitness-coach.ru/app?")


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

    for coach_headers, supplied_name in (
        (coach_one, "Имя от первого тренера"),
        (coach_two, "Имя от второго тренера"),
    ):
        invited = client.post(
            "/api/v1/coach/clients",
            json={"username": "real_client", "full_name": supplied_name},
            headers=coach_headers,
        )
        assert invited.status_code == 201

    me = client.get("/api/v1/me", headers=client_headers).json()
    assert me["profile"]["full_name"] == "Настоящее имя"
    assert me["username"] == "real_client"
    invites = client.get("/api/v1/me/coach-invites", headers=client_headers).json()
    assert len(invites) == 2


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

    invited = client.post(
        "/api/v1/coach/clients",
        json={"telegram_user_id": 5352},
        headers=coach_headers,
    )
    assert invited.status_code == 201
    accept_latest_coach_invite(client, client_headers)

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
