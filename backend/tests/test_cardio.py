from datetime import datetime, time, timedelta

from fitminiapp_api.core.timezone import today_msk
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.cardio import CardioSession
from fitminiapp_api.models.nutrition import NutritionTarget
from fitminiapp_api.models.user import User


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _user_id(telegram_user_id: int) -> int:
    with get_session_context() as db:
        return db.query(User.id).filter(User.telegram_user_id == telegram_user_id).scalar()


def _payload(*, request_id: str, status: str = "completed", day_offset: int = -1) -> dict:
    scheduled_at = datetime.combine(today_msk() + timedelta(days=day_offset), time(hour=12))
    return {
        "client_request_id": request_id,
        "activity_type": "running",
        "duration_minutes": 35,
        "distance_km": 5.25,
        "average_heart_rate_bpm": 148,
        "heart_rate_zone": 3,
        "note": "  Ровный темп  ",
        "scheduled_at": scheduled_at.isoformat(timespec="minutes"),
        "status": status,
    }


def _target(user_id: int, cardio_per_week: int = 2) -> NutritionTarget:
    effective_from = today_msk() - timedelta(days=30)
    return NutritionTarget(
        user_id=user_id,
        sex="male",
        weight_kg=80,
        height_cm=180,
        age=30,
        strength_trainings_per_week=3,
        cardio_trainings_per_week=cardio_per_week,
        cardio_training_duration_minutes=30,
        cardio_trainings=[],
        goal="maintenance",
        bmr=1800,
        tdee=2400,
        calories=2200,
        protein_g=150,
        fat_g=75,
        carbs_g=230,
        effective_from=effective_from,
        source="calculated",
        saved_at=datetime.combine(effective_from, time()),
    )


def test_cardio_crud_is_owned_validated_and_create_is_idempotent(client) -> None:
    owner_headers = _auth(client, 66_001)
    other_headers = _auth(client, 66_002)
    payload = _payload(request_id="00000000-0000-4000-8000-000000000066")

    created = client.post("/api/v1/workouts/cardio", headers=owner_headers, json=payload)
    replayed = client.post("/api/v1/workouts/cardio", headers=owner_headers, json=payload)

    assert created.status_code == 201
    assert replayed.status_code == 201
    assert replayed.json()["id"] == created.json()["id"]
    assert created.json()["note"] == "Ровный темп"
    assert created.json()["source"] == "manual"
    assert created.json()["completed_at"] is not None

    owner_rows = client.get("/api/v1/workouts/cardio", headers=owner_headers)
    other_rows = client.get("/api/v1/workouts/cardio", headers=other_headers)
    assert [row["id"] for row in owner_rows.json()] == [created.json()["id"]]
    assert other_rows.json() == []

    forbidden = client.patch(
        f"/api/v1/workouts/cardio/{created.json()['id']}",
        headers=other_headers,
        json={"duration_minutes": 50},
    )
    assert forbidden.status_code == 404

    updated = client.patch(
        f"/api/v1/workouts/cardio/{created.json()['id']}",
        headers=owner_headers,
        json={"duration_minutes": 42, "distance_km": None, "note": ""},
    )
    assert updated.status_code == 200
    assert updated.json()["duration_minutes"] == 42
    assert updated.json()["distance_km"] is None
    assert updated.json()["note"] is None

    null_required = client.patch(
        f"/api/v1/workouts/cardio/{created.json()['id']}",
        headers=owner_headers,
        json={"duration_minutes": None},
    )
    assert null_required.status_code == 422

    invalid = client.post(
        "/api/v1/workouts/cardio",
        headers=owner_headers,
        json={
            **payload,
            "client_request_id": "00000000-0000-4000-8000-000000000067",
            "duration_minutes": 0,
            "average_heart_rate_bpm": 251,
        },
    )
    assert invalid.status_code == 422

    future = client.post(
        "/api/v1/workouts/cardio",
        headers=owner_headers,
        json=_payload(
            request_id="00000000-0000-4000-8000-000000000068",
            day_offset=1,
        ),
    )
    assert future.status_code == 400
    assert future.json()["detail"] == "Завершённую активность нельзя записать в будущем"

    deleted = client.delete(
        f"/api/v1/workouts/cardio/{created.json()['id']}", headers=owner_headers
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/workouts/cardio", headers=owner_headers).json() == []


def test_planned_cardio_completion_is_duplicate_safe(client) -> None:
    headers = _auth(client, 66_010)
    created = client.post(
        "/api/v1/workouts/cardio",
        headers=headers,
        json=_payload(
            request_id="00000000-0000-4000-8000-000000000069",
            status="planned",
        ),
    )
    assert created.status_code == 201
    assert created.json()["completed_at"] is None

    first = client.post(f"/api/v1/workouts/cardio/{created.json()['id']}/complete", headers=headers)
    replay = client.post(
        f"/api/v1/workouts/cardio/{created.json()['id']}/complete", headers=headers
    )
    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json()["completed_at"] == replay.json()["completed_at"]


def test_cardio_uses_profile_timezone_for_storage_filters_and_response(client) -> None:
    headers = _auth(client, 66_011)
    user_id = _user_id(66_011)
    with get_session_context() as db:
        user = db.get(User, user_id)
        assert user is not None and user.profile is not None
        user.profile.timezone = "America/Los_Angeles"

    local_time = "2026-01-10T23:30:00"
    created = client.post(
        "/api/v1/workouts/cardio",
        headers=headers,
        json={
            **_payload(
                request_id="00000000-0000-4000-8000-000000000073",
                status="planned",
            ),
            "scheduled_at": local_time,
        },
    )
    assert created.status_code == 201
    assert created.json()["scheduled_at"] == local_time

    with get_session_context() as db:
        stored = db.query(CardioSession).filter(CardioSession.user_id == user_id).one()
        assert stored.scheduled_at.isoformat() == "2026-01-11T07:30:00"

    local_day = client.get(
        "/api/v1/workouts/cardio?date_from=2026-01-10&date_to=2026-01-10",
        headers=headers,
    )
    utc_day = client.get(
        "/api/v1/workouts/cardio?date_from=2026-01-11&date_to=2026-01-11",
        headers=headers,
    )
    assert [row["id"] for row in local_day.json()] == [created.json()["id"]]
    assert utc_day.json() == []


def test_cardio_progress_adherence_uses_completed_manual_sessions(client) -> None:
    headers = _auth(client, 66_020)
    user_id = _user_id(66_020)
    with get_session_context() as db:
        db.add(_target(user_id))

    first = _payload(
        request_id="00000000-0000-4000-8000-000000000070",
        day_offset=-2,
    )
    second = {
        **_payload(
            request_id="00000000-0000-4000-8000-000000000071",
            day_offset=-1,
        ),
        "activity_type": "walking",
        "duration_minutes": 45,
        "distance_km": None,
        "heart_rate_zone": None,
    }
    assert client.post("/api/v1/workouts/cardio", headers=headers, json=first).status_code == 201
    assert client.post("/api/v1/workouts/cardio", headers=headers, json=second).status_code == 201

    summary = client.get("/api/v1/workouts/progress/summary?period_days=7", headers=headers)
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["cardio"] == {
        "completed_sessions": 2,
        "planned_sessions": 0,
        "frequency_per_week": 2.0,
        "duration_minutes": 80,
        "distance_km": 5.25,
        "zone_duration": [{"zone": 3, "duration_minutes": 35}],
    }
    assert payload["adherence"]["cardio"] == {
        "status": "available",
        "percent": 100.0,
        "achieved": 2,
        "evaluated": 2,
        "weight": 0.2,
        "reason": None,
    }
    assert "cardio" in payload["adherence"]["included_components"]


def test_cardio_is_in_account_export_and_account_deletion(client) -> None:
    headers = _auth(client, 66_030)
    user_id = _user_id(66_030)
    created = client.post(
        "/api/v1/workouts/cardio",
        headers=headers,
        json=_payload(request_id="00000000-0000-4000-8000-000000000072"),
    )
    assert created.status_code == 201

    exported = client.get("/api/v1/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["schema_version"] == 3
    assert exported.json()["cardio_sessions"][0]["average_heart_rate_bpm"] == 148
    assert exported.json()["cardio_sessions"][0]["note"] == "Ровный темп"

    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    with get_session_context() as db:
        assert db.query(CardioSession).filter(CardioSession.user_id == user_id).count() == 0
