import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import pytest

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


def auth(client, telegram_user_id=1001, is_coach=True, is_admin=False):
    response = client.post(
        "/api/v1/auth/dev-login",
        json={
            "telegram_user_id": telegram_user_id,
            "is_coach": is_coach,
            "is_admin": is_admin,
        },
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
