from __future__ import annotations

from datetime import timedelta

from fitminiapp_api.core.timezone import today_msk
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.user import (
    BodyMeasurement,
    CoachClient,
    User,
    UserProfilePriorityMuscle,
)


def _auth(client, telegram_user_id: int, *, is_coach: bool = False) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": is_coach},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _user_id(telegram_user_id: int) -> int:
    with get_session_context() as db:
        return db.query(User.id).filter(User.telegram_user_id == telegram_user_id).scalar()


def test_body_priorities_validate_canonical_taxonomy_and_optional_modes(client) -> None:
    headers = _auth(client, 31_001)

    options = client.get("/api/v1/me/profile/body-priority-options", headers=headers)
    assert options.status_code == 200
    option_ids = {item["id"] for item in options.json()["items"]}
    assert {"chest", "back", "quadriceps", "biceps"}.issubset(option_ids)
    assert {"cardio", "conditioning", "full_body"}.isdisjoint(option_ids)

    selected = client.patch(
        "/api/v1/me/profile",
        json={
            "body_priority": {
                "mode": "muscle_groups",
                "muscle_group_ids": ["back", "biceps"],
            }
        },
        headers=headers,
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["profile"]["body_priority"] == {
        "mode": "muscle_groups",
        "muscle_group_ids": ["back", "biceps"],
    }

    empty_groups = client.patch(
        "/api/v1/me/profile",
        json={"body_priority": {"mode": "muscle_groups", "muscle_group_ids": []}},
        headers=headers,
    )
    assert empty_groups.status_code == 422
    duplicate_groups = client.patch(
        "/api/v1/me/profile",
        json={
            "body_priority": {
                "mode": "muscle_groups",
                "muscle_group_ids": ["back", "back"],
            }
        },
        headers=headers,
    )
    assert duplicate_groups.status_code == 422
    unknown_group = client.patch(
        "/api/v1/me/profile",
        json={
            "body_priority": {
                "mode": "muscle_groups",
                "muscle_group_ids": ["cardio"],
            }
        },
        headers=headers,
    )
    assert unknown_group.status_code == 400

    balanced = client.patch(
        "/api/v1/me/profile",
        json={"body_priority": {"mode": "balanced", "muscle_group_ids": []}},
        headers=headers,
    )
    assert balanced.status_code == 200
    assert balanced.json()["profile"]["body_priority"] == {
        "mode": "balanced",
        "muscle_group_ids": [],
    }

    cleared = client.patch(
        "/api/v1/me/profile",
        json={"body_priority": None},
        headers=headers,
    )
    assert cleared.status_code == 200
    assert cleared.json()["profile"]["body_priority"] is None

    client.patch(
        "/api/v1/me/profile",
        json={
            "body_priority": {
                "mode": "muscle_groups",
                "muscle_group_ids": ["back"],
            }
        },
        headers=headers,
    )
    exported = client.get("/api/v1/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["profile"]["body_priority"]["muscle_group_ids"] == ["back"]
    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    with get_session_context() as db:
        assert db.query(UserProfilePriorityMuscle).count() == 0


def test_anthropometry_trends_are_chronological_guarded_and_user_isolated(client) -> None:
    headers = _auth(client, 31_101)
    other_headers = _auth(client, 31_102)
    user_id = _user_id(31_101)
    other_user_id = _user_id(31_102)
    today = today_msk()

    client.patch(
        "/api/v1/me/profile",
        json={
            "body_priority": {
                "mode": "muscle_groups",
                "muscle_group_ids": ["quadriceps"],
            }
        },
        headers=headers,
    )
    with get_session_context() as db:
        db.add_all(
            [
                BodyMeasurement(
                    user_id=user_id,
                    measured_on=today - timedelta(days=20),
                    weight_kg=80,
                    waist_cm=90,
                    biceps_cm=35,
                ),
                BodyMeasurement(
                    user_id=user_id,
                    measured_on=today - timedelta(days=10),
                    weight_kg=79.5,
                    biceps_cm=35.2,
                ),
                BodyMeasurement(
                    user_id=user_id,
                    measured_on=today - timedelta(days=3),
                    chest_cm=100,
                ),
                BodyMeasurement(
                    user_id=user_id,
                    measured_on=today - timedelta(days=2),
                    chest_cm=100.5,
                ),
                BodyMeasurement(
                    user_id=user_id,
                    measured_on=today - timedelta(days=1),
                    weight_kg=79,
                    chest_cm=101,
                ),
                BodyMeasurement(
                    user_id=other_user_id,
                    measured_on=today - timedelta(days=1),
                    weight_kg=250,
                ),
            ]
        )

    response = client.get(
        "/api/v1/workouts/progress/summary?period_days=30",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()["body"]
    assert body["priority"] == {
        "mode": "muscle_groups",
        "muscle_group_ids": ["quadriceps"],
    }
    assert body["guidance"]["comparison_basis"] == "self"
    assert body["guidance"]["minimum_points_for_interpretation"] == 3
    assert body["guidance"]["minimum_span_days_for_interpretation"] == 14
    assert "250" not in response.text

    trends = {trend["metric"]: trend for trend in body["trends"]}
    weight = trends["weight_kg"]
    assert weight["interpretation_status"] == "available"
    assert weight["point_count"] == 3
    assert weight["span_days"] == 19
    assert weight["change"] == -1
    assert [point["measured_on"] for point in weight["points"]] == [
        (today - timedelta(days=20)).isoformat(),
        (today - timedelta(days=10)).isoformat(),
        (today - timedelta(days=1)).isoformat(),
    ]
    assert trends["waist_cm"]["interpretation_status"] == "single_point"
    assert trends["waist_cm"]["change"] is None
    assert trends["biceps_cm"]["interpretation_status"] == "insufficient_points"
    assert trends["chest_cm"]["interpretation_status"] == "insufficient_period"

    short_period = client.get(
        "/api/v1/workouts/progress/summary?period_days=7",
        headers=headers,
    ).json()["body"]
    assert short_period["trends"][0]["interpretation_status"] == "single_point"
    assert (
        short_period["trends"][0]["points"][0]["measured_on"]
        == (today - timedelta(days=1)).isoformat()
    )
    short_trends = {trend["metric"]: trend for trend in short_period["trends"]}
    assert short_trends["chest_cm"]["interpretation_status"] == "insufficient_period"

    other = client.get(
        "/api/v1/workouts/progress/summary?period_days=30",
        headers=other_headers,
    )
    assert other.status_code == 200
    assert other.json()["body"]["latest_measurement"]["weight_kg"] == 250


def test_trainer_reads_and_updates_only_active_clients_body_priority(client) -> None:
    coach_headers = _auth(client, 31_201, is_coach=True)
    client_headers = _auth(client, 31_202)
    other_coach_headers = _auth(client, 31_203, is_coach=True)
    coach_id = _user_id(31_201)
    client_id = _user_id(31_202)

    with get_session_context() as db:
        db.add(
            CoachClient(
                coach_user_id=coach_id,
                client_user_id=client_id,
                status="active",
            )
        )

    updated = client.patch(
        f"/api/v1/coach/clients/{client_id}/profile",
        json={
            "body_priority": {
                "mode": "muscle_groups",
                "muscle_group_ids": ["chest", "triceps"],
            }
        },
        headers=coach_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["body_priority"]["muscle_group_ids"] == ["chest", "triceps"]

    summary = client.get(
        f"/api/v1/coach/clients/{client_id}/summary?period_days=30",
        headers=coach_headers,
    )
    assert summary.status_code == 200
    assert summary.json()["body"]["priority"]["muscle_group_ids"] == ["chest", "triceps"]

    denied_patch = client.patch(
        f"/api/v1/coach/clients/{client_id}/profile",
        json={"body_priority": {"mode": "balanced", "muscle_group_ids": []}},
        headers=other_coach_headers,
    )
    assert denied_patch.status_code == 404
    denied_summary = client.get(
        f"/api/v1/coach/clients/{client_id}/summary?period_days=30",
        headers=other_coach_headers,
    )
    assert denied_summary.status_code == 404

    own_profile = client.get("/api/v1/me", headers=client_headers)
    assert own_profile.status_code == 200
    assert own_profile.json()["profile"]["body_priority"]["muscle_group_ids"] == [
        "chest",
        "triceps",
    ]
