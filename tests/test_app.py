import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import pytest

from app.core.timezone import to_msk_naive
from app.services.telegram_auth import validate_telegram_init_data


def signed_init_data(
    bot_token: str,
    auth_date: int,
    telegram_user_id: int = 555001,
    username: str | None = None,
) -> str:
    user = {"id": telegram_user_id, "first_name": "Telegram"}
    if username:
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


def test_dev_login_and_me(client):
    headers = auth(client)
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_user_id"] == 1001
    assert data["is_coach"] is True


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
    assert data["calories"] == 3035
    assert data["protein_g"] == 144
    assert data["fat_g"] == 72
    assert data["carbs_g"] == 453

    me = client.get("/api/v1/me", headers=headers).json()
    kbju = me["profile"]["kbju"]
    assert kbju["calories"] == 3035
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
    from app.core.config import settings

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
    finished = client.post(f"/api/v1/workouts/{today['id']}/finish", headers=headers)
    assert finished.status_code == 200

    history = client.get("/api/v1/workouts/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    cleared = client.delete("/api/v1/workouts/history", headers=headers)
    assert cleared.status_code == 204
    assert client.get("/api/v1/workouts/history", headers=headers).json() == []
    assert client.get("/api/v1/workouts/today", headers=headers).status_code == 404


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


def test_seeded_catalog_and_strength_templates(client):
    headers = auth(client, telegram_user_id=31032, is_coach=False)

    exercises = client.get("/api/v1/programs/exercises", headers=headers).json()
    templates = client.get("/api/v1/programs/templates/mine", headers=headers).json()

    assert len(exercises) >= 140
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

    created = client.post(
        "/api/v1/programs/clients",
        json={"telegram_user_id": 2001, "full_name": "Клиент тренера"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["status"] == "active"
    assert created.json()["telegram_user_id"] == 2001

    listed = client.get("/api/v1/programs/clients", headers=headers)
    assert listed.status_code == 200
    assert any(row["telegram_user_id"] == 2001 for row in listed.json())


def test_client_has_only_one_active_coach_and_trainer_info(client):
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

    first_clients = client.get("/api/v1/coach/clients", headers=coach_one_headers).json()
    second_clients = client.get("/api/v1/coach/clients", headers=coach_two_headers).json()
    assert not any(row["id"] == client_user["id"] for row in first_clients)
    assert any(row["id"] == client_user["id"] for row in second_clients)
    assert (
        client.get("/api/v1/me", headers=client_headers).json()["trainer"]["username"]
        == "coach_two"
    )


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

    trainer = client.get("/api/v1/me", headers=client_headers).json()["trainer"]
    assert trainer["full_name"] == "Тренер Без Username"
    assert trainer["can_open_chat"] is False
    assert trainer["chat_url"] is None
    assert "username" in trainer["chat_unavailable_reason"]


def test_coach_can_invite_client_by_username_and_link_on_login(client):
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


def test_refresh_token_rotation(client):
    login = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": 2001, "is_coach": False},
    )
    assert login.status_code == 200

    refresh_token = login.json()["refresh_token"]
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert refreshed.json()["refresh_token"] != refresh_token

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


def test_to_msk_naive_converts_aware_utc_datetime():
    converted = to_msk_naive(datetime(2026, 4, 25, 7, 30, tzinfo=UTC))

    assert converted == datetime(2026, 4, 25, 10, 30)


def test_health_includes_request_id(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "x-request-id" in {k.lower(): v for k, v in response.headers.items()}


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
    complete = client.post(f"/api/v1/billing/mock/complete/{checkout_id}")
    assert complete.status_code == 200
    sub = client.get("/api/v1/billing/subscription", headers=headers)
    assert sub.status_code == 200
    assert sub.json()["plan_code"] == "premium"


def test_billing_checkout_falls_back_to_frontend_base_url(client, monkeypatch):
    from app.core.config import settings

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
