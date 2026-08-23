from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.program import UserProgram
from fitminiapp_api.models.user import CoachClient


def _auth(client, telegram_user_id: int, *, is_coach: bool = False) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": is_coach},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _exercise_by_slug(client, headers: dict[str, str], slug: str) -> dict:
    catalog = client.get("/api/v1/programs/exercises", headers=headers)
    assert catalog.status_code == 200
    return next(item for item in catalog.json() if item["slug"] == slug)


def test_training_preferences_none_some_all_and_custom_exercise(client) -> None:
    headers = _auth(client, 95401)
    empty = client.get("/api/v1/me", headers=headers).json()["profile"]
    assert empty["training_preferences"]["preferred_weekdays"] == []
    assert empty["training_preferences"]["conflict"]["status"] == "none"

    custom = client.post(
        "/api/v1/programs/exercises",
        headers=headers,
        json={
            "title": "Моё контрольное движение",
            "primary_muscle": "Спина",
            "equipment": "Собственный вес",
            "difficulty_level": "beginner",
        },
    )
    assert custom.status_code == 201, custom.text
    bench = _exercise_by_slug(client, headers, "bench-press")
    payload = {
        "preferred_duration_min": 35,
        "preferred_duration_max": 70,
        "preferred_weekdays": [0, 2, 4],
        "preferred_time": "18:30",
        "location_profiles": [
            {
                "location": "gym",
                "equipment_ids": ["bodyweight", "dumbbell", "barbell", "bench"],
            },
            {"location": "home", "equipment_ids": ["bodyweight", "dumbbell"]},
        ],
        "preferred_exercise_ids": [custom.json()["id"]],
        "avoided_exercises": [{"exercise_id": bench["id"], "reason": "not_enjoyable"}],
        "note": "  Не ставить два тяжёлых жима подряд.  ",
    }
    saved = client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={"training_preferences": payload},
    )
    assert saved.status_code == 200, saved.text
    preferences = saved.json()["profile"]["training_preferences"]
    assert preferences["preferred_weekdays"] == [0, 2, 4]
    assert preferences["preferred_time"] == "18:30:00"
    assert preferences["note"] == "Не ставить два тяжёлых жима подряд."
    assert preferences["updated_by"]["role"] == "self"
    assert preferences["conflict"] == {
        "status": "none",
        "active_program_id": None,
        "reasons": [],
    }

    overlap = client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={
            "training_preferences": {
                "preferred_exercise_ids": [bench["id"]],
                "avoided_exercises": [{"exercise_id": bench["id"]}],
            }
        },
    )
    assert overlap.status_code == 422

    cleared = client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={"training_preferences": {}},
    )
    assert cleared.status_code == 200
    assert cleared.json()["profile"]["training_preferences"]["preferred_weekdays"] == []


def test_active_program_is_preserved_and_conflict_requires_explicit_review(client) -> None:
    headers = _auth(client, 95402)
    bench = _exercise_by_slug(client, headers, "bench-press")
    created = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Конфликтная программа",
            "goal": "recomposition",
            "level": "beginner",
            "mode": "self",
            "assign_after_create": True,
            "days": [
                {
                    "title": "Жимовой день",
                    "exercises": [
                        {
                            "exercise_id": bench["id"],
                            "prescribed_sets": 4,
                            "prescribed_reps": "8-10",
                            "rest_seconds": 120,
                        }
                    ],
                }
            ],
        },
    )
    assert created.status_code == 200, created.text
    with get_session_context() as db:
        active_before = db.query(UserProgram).filter(UserProgram.is_active.is_(True)).one()
        active_id = active_before.id

    response = client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={
            "training_preferences": {
                "preferred_duration_max": 10,
                "preferred_weekdays": [6],
                "location_profiles": [{"location": "home", "equipment_ids": ["bodyweight"]}],
                "avoided_exercises": [{"exercise_id": bench["id"]}],
            }
        },
    )
    assert response.status_code == 200, response.text
    conflict = response.json()["profile"]["training_preferences"]["conflict"]
    assert conflict["status"] == "review_required"
    assert conflict["active_program_id"] == active_id
    assert any("списка «избегать»" in reason for reason in conflict["reasons"])
    with get_session_context() as db:
        assert db.get(UserProgram, active_id).is_active is True


def test_active_trainer_can_edit_and_revoked_trainer_cannot(client) -> None:
    coach_headers = _auth(client, 95403, is_coach=True)
    client_headers = _auth(client, 95404)
    coach_id = client.get("/api/v1/me", headers=coach_headers).json()["id"]
    client_id = client.get("/api/v1/me", headers=client_headers).json()["id"]
    with get_session_context() as db:
        db.add(CoachClient(coach_user_id=coach_id, client_user_id=client_id, status="active"))
        db.commit()

    saved = client.patch(
        f"/api/v1/coach/clients/{client_id}/profile",
        headers=coach_headers,
        json={
            "training_preferences": {
                "preferred_duration_min": 40,
                "note": "Клиент просит короткую разминку.",
            }
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["training_preferences"]["updated_by"]["role"] == "trainer"
    own_view = client.get("/api/v1/me", headers=client_headers).json()
    assert own_view["profile"]["training_preferences"]["updated_by"]["user_id"] == coach_id

    cleared = client.patch(
        f"/api/v1/coach/clients/{client_id}/profile",
        headers=coach_headers,
        json={"training_preferences": {}},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["training_preferences"]["updated_by"]["role"] == "trainer"
    own_cleared = client.get("/api/v1/me", headers=client_headers).json()
    cleared_preferences = own_cleared["profile"]["training_preferences"]
    assert cleared_preferences["preferred_duration_min"] is None
    assert cleared_preferences["updated_by"]["user_id"] == coach_id

    restored = client.patch(
        f"/api/v1/coach/clients/{client_id}/profile",
        headers=coach_headers,
        json={"training_preferences": {"preferred_duration_min": 40}},
    )
    assert restored.status_code == 200, restored.text

    removed = client.delete(f"/api/v1/coach/clients/{client_id}", headers=coach_headers)
    assert removed.status_code == 204
    denied = client.patch(
        f"/api/v1/coach/clients/{client_id}/profile",
        headers=coach_headers,
        json={"training_preferences": {"preferred_duration_min": 50}},
    )
    assert denied.status_code == 404

    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=coach_headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    after_editor_deletion = client.get("/api/v1/me", headers=client_headers).json()
    retained = after_editor_deletion["profile"]["training_preferences"]
    assert retained["preferred_duration_min"] == 40
    assert retained["updated_by"] is None


def test_profile_preferences_feed_recommendation_and_account_export(client) -> None:
    headers = _auth(client, 95405)
    bench = _exercise_by_slug(client, headers, "bench-press")
    saved = client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={
            "goal": "recomposition",
            "level": "intermediate",
            "workouts_per_week": 4,
            "training_preferences": {
                "location_profiles": [
                    {
                        "location": "gym",
                        "equipment_ids": [
                            "bodyweight",
                            "dumbbell",
                            "barbell",
                            "bench",
                            "cable",
                            "machine",
                        ],
                    }
                ],
                "avoided_exercises": [{"exercise_id": bench["id"], "reason": "other"}],
            },
        },
    )
    assert saved.status_code == 200, saved.text
    recommendation = client.post(
        "/api/v1/programs/templates/recommendation", headers=headers, json={}
    )
    assert recommendation.status_code == 200, recommendation.text
    fields = recommendation.json()["criteria"]["profile_fields_used"]
    assert "training_location" in fields
    assert "available_equipment" in fields
    assert "avoided_exercises" in fields
    if recommendation.json()["status"] == "recommended":
        exercise_ids = {
            exercise["exercise_id"]
            for day in recommendation.json()["recommendation"]["template"]["days"]
            for exercise in day["exercises"]
        }
        assert bench["id"] not in exercise_ids

    exported = client.get("/api/v1/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["profile"]["training_preferences"]["avoided_exercises"] == [
        {"exercise_id": bench["id"], "reason": "other"}
    ]
