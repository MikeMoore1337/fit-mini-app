from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.program import UserWorkout, WorkoutAdaptation


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _assign_today_workout(
    client,
    headers: dict[str, str],
    slugs: list[str],
    *,
    prescribed_sets: int = 3,
) -> dict:
    catalog = client.get("/api/v1/programs/exercises", headers=headers).json()
    exercise_ids = {item["slug"]: item["id"] for item in catalog}
    response = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Адаптация на сегодня",
            "goal": "recomposition",
            "level": "intermediate",
            "mode": "self",
            "assign_after_create": True,
            "days": [
                {
                    "title": "Тренировка A",
                    "exercises": [
                        {
                            "exercise_id": exercise_ids[slug],
                            "prescribed_sets": prescribed_sets,
                            "prescribed_reps": "8-10",
                            "rest_seconds": 90,
                        }
                        for slug in slugs
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    today = client.get("/api/v1/workouts/today", headers=headers)
    assert today.status_code == 200
    return today.json()


def test_time_budget_preview_cancel_apply_and_history_show_actual_workout(client) -> None:
    headers = _auth(client, 93501)
    original = _assign_today_workout(
        client,
        headers,
        ["bench-press", "squat", "dumbbell-curl", "crunch", "standing-calf-raise"],
    )
    payload = {"reason": "limited_time", "time_budget_minutes": 20}

    preview = client.post(
        f"/api/v1/workouts/{original['id']}/adaptations/preview",
        headers=headers,
        json=payload,
    )
    assert preview.status_code == 200, preview.text
    preview_data = preview.json()
    assert preview_data["status"] == "preview"
    assert preview_data["original_estimated_minutes"] > 20
    assert preview_data["adapted_estimated_minutes"] <= 20
    assert {item["priority"] for item in preview_data["original_exercises"][:2]} == {"core"}
    assert all(
        change["from_title"]
        not in {item["title"] for item in preview_data["original_exercises"][:2]}
        for change in preview_data["changes"]
    )

    # Preview/cancel is read-only: without apply the materialized workout is unchanged.
    unchanged = client.get("/api/v1/workouts/today", headers=headers).json()
    assert [item["exercise_id"] for item in unchanged["exercises"]] == [
        item["exercise_id"] for item in original["exercises"]
    ]
    with get_session_context() as db:
        assert db.query(WorkoutAdaptation).count() == 0

    applied = client.post(
        f"/api/v1/workouts/{original['id']}/adaptations/apply",
        headers=headers,
        json={**payload, "preview_token": preview_data["preview_token"]},
    )
    assert applied.status_code == 200, applied.text
    applied_data = applied.json()
    assert len(applied_data["workout"]["exercises"]) == len(preview_data["adapted_exercises"])
    retried = client.post(
        f"/api/v1/workouts/{original['id']}/adaptations/apply",
        headers=headers,
        json={**payload, "preview_token": preview_data["preview_token"]},
    )
    assert retried.status_code == 200
    assert retried.json()["adaptation_id"] == applied_data["adaptation_id"]
    with get_session_context() as db:
        assert db.query(WorkoutAdaptation).count() == 1

    started = client.post(
        f"/api/v1/workouts/{original['id']}/start",
        headers=headers,
    )
    assert started.status_code == 200
    set_id = started.json()["exercises"][0]["sets"][0]["id"]
    assert (
        client.patch(
            f"/api/v1/workouts/sets/{set_id}",
            headers=headers,
            json={"actual_reps": 8, "actual_weight": 20, "is_completed": True},
        ).status_code
        == 200
    )
    finished = client.post(
        f"/api/v1/workouts/{original['id']}/finish",
        headers=headers,
        json={"confirm_incomplete": True},
    )
    assert finished.status_code == 200

    history = client.get("/api/v1/workouts/history", headers=headers).json()
    assert len(history) == 1
    assert [item["title"] for item in history[0]["exercises"]] == [
        item["title"] for item in preview_data["adapted_exercises"]
    ]
    assert history[0]["adaptations"][0]["reason"] == "limited_time"
    assert history[0]["adaptations"][0]["changes"] == preview_data["changes"]


def test_replacement_requires_curated_compatible_alternative_and_fresh_preview(client) -> None:
    headers = _auth(client, 93502)
    workout = _assign_today_workout(client, headers, ["bench-press"], prescribed_sets=1)
    workout_exercise_id = workout["exercises"][0]["id"]
    query = "available_equipment_ids=dumbbell&available_equipment_ids=bench"
    alternatives = client.get(
        f"/api/v1/workouts/{workout['id']}/exercises/{workout_exercise_id}/alternatives?{query}",
        headers=headers,
    )
    assert alternatives.status_code == 200
    replacement = next(item for item in alternatives.json() if item["title"] == "Жим гантелей лежа")
    avoided = client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={
            "training_preferences": {
                "avoided_exercises": [{"exercise_id": replacement["exercise_id"]}]
            }
        },
    )
    assert avoided.status_code == 200, avoided.text
    filtered = client.get(
        f"/api/v1/workouts/{workout['id']}/exercises/{workout_exercise_id}/alternatives?{query}",
        headers=headers,
    )
    assert replacement["exercise_id"] not in {item["exercise_id"] for item in filtered.json()}
    assert (
        client.patch(
            "/api/v1/me/profile",
            headers=headers,
            json={"training_preferences": {}},
        ).status_code
        == 200
    )
    payload = {
        "reason": "replace_exercise",
        "target_workout_exercise_id": workout_exercise_id,
        "replacement_exercise_id": replacement["exercise_id"],
        "available_equipment_ids": ["dumbbell", "bench"],
    }
    preview = client.post(
        f"/api/v1/workouts/{workout['id']}/adaptations/preview",
        headers=headers,
        json=payload,
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["changes"][0]["to_title"] == "Жим гантелей лежа"

    mismatch = client.post(
        f"/api/v1/workouts/{workout['id']}/adaptations/preview",
        headers=headers,
        json={**payload, "available_equipment_ids": ["bodyweight"]},
    )
    assert mismatch.status_code == 409
    assert "недоступное оборудование" in mismatch.json()["detail"]

    stale = client.post(
        f"/api/v1/workouts/{workout['id']}/adaptations/apply",
        headers=headers,
        json={
            **payload,
            "available_equipment_ids": ["dumbbell", "bench", "bodyweight"],
            "preview_token": preview.json()["preview_token"],
        },
    )
    assert stale.status_code == 409
    assert "preview заново" in stale.json()["detail"]


def test_unavailable_equipment_without_curated_alternative_is_controlled(client) -> None:
    headers = _auth(client, 93503)
    workout = _assign_today_workout(client, headers, ["deadlift"], prescribed_sets=1)
    target_id = workout["exercises"][0]["id"]

    preview = client.post(
        f"/api/v1/workouts/{workout['id']}/adaptations/preview",
        headers=headers,
        json={
            "reason": "unavailable_equipment",
            "target_workout_exercise_id": target_id,
            "available_equipment_ids": ["bodyweight"],
        },
    )
    assert preview.status_code == 409
    assert "нет проверенной замены" in preview.json()["detail"]


def test_pain_boundary_never_changes_workout_or_offers_medical_workaround(client) -> None:
    headers = _auth(client, 93504)
    workout = _assign_today_workout(client, headers, ["squat"], prescribed_sets=1)
    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )

    response = client.post(
        f"/api/v1/workouts/{workout['id']}/adaptations/preview",
        headers=headers,
        json={"reason": "pain_or_injury"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "safety_stop"
    assert data["changes"] == []
    assert data["preview_token"] is None
    assert "не подбирает медицинскую замену" in data["message"]
    with get_session_context() as db:
        stored = db.get(UserWorkout, workout["id"])
        assert stored is not None
        assert stored.status == "in_progress"
        assert db.query(WorkoutAdaptation).count() == 0
