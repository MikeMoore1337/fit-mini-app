from datetime import UTC, datetime, timedelta


def auth(client, telegram_user_id=1001, is_coach=True):
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": is_coach},
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


def test_me_requires_auth(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401


def test_invalid_token_treated_as_unauthorized(client):
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_admin_users_forbidden_for_client(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403


def test_admin_users_ok_for_coach(client):
    headers = auth(client, telegram_user_id=1001, is_coach=True)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


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
