from __future__ import annotations

from datetime import timedelta

from fitminiapp_api.core.timezone import today_for_user
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.user import User


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _today(telegram_user_id: int):
    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).one()
        return today_for_user(user)


def test_summary_and_training_analytics_share_inclusive_preset_bounds(client) -> None:
    telegram_user_id = 111_001
    headers = _auth(client, telegram_user_id)
    today = _today(telegram_user_id)

    for period_days in (1, 7, 30, 90, 365):
        summary_response = client.get(
            "/api/v1/workouts/progress/summary",
            params={"period_days": period_days},
            headers=headers,
        )
        analytics_response = client.get(
            "/api/v1/workouts/progress/training-analytics",
            params={"period_days": period_days},
            headers=headers,
        )

        assert summary_response.status_code == 200, summary_response.text
        assert analytics_response.status_code == 200, analytics_response.text
        summary = summary_response.json()
        analytics = analytics_response.json()
        expected_start = (today - timedelta(days=period_days - 1)).isoformat()
        assert (summary["period_start"], summary["period_end"], summary["period_days"]) == (
            expected_start,
            today.isoformat(),
            period_days,
        )
        assert (analytics["period_start"], analytics["period_end"], analytics["period_days"]) == (
            expected_start,
            today.isoformat(),
            period_days,
        )


def test_custom_period_is_shared_and_counts_leap_day_inclusively(client) -> None:
    telegram_user_id = 111_002
    headers = _auth(client, telegram_user_id)
    params = {"date_from": "2024-02-28", "date_to": "2024-03-01"}

    summary_response = client.get(
        "/api/v1/workouts/progress/summary",
        params=params,
        headers=headers,
    )
    analytics_response = client.get(
        "/api/v1/workouts/progress/training-analytics",
        params=params,
        headers=headers,
    )

    assert summary_response.status_code == 200, summary_response.text
    assert analytics_response.status_code == 200, analytics_response.text
    assert summary_response.json()["period_days"] == 3
    assert analytics_response.json()["period_days"] == 3
    assert summary_response.json()["period_start"] == "2024-02-28"
    assert summary_response.json()["period_end"] == "2024-03-01"
    assert analytics_response.json()["period_start"] == "2024-02-28"
    assert analytics_response.json()["period_end"] == "2024-03-01"


def test_progress_period_validation_rejects_partial_invalid_and_future_ranges(client) -> None:
    telegram_user_id = 111_003
    headers = _auth(client, telegram_user_id)
    today = _today(telegram_user_id)

    invalid_requests = (
        {"date_from": "2024-01-01"},
        {"date_from": "2024-02-01", "date_to": "2024-01-31"},
        {
            "date_from": (today - timedelta(days=366)).isoformat(),
            "date_to": today.isoformat(),
        },
        {
            "date_from": today.isoformat(),
            "date_to": (today + timedelta(days=1)).isoformat(),
        },
        {
            "period_days": 30,
            "date_from": (today - timedelta(days=2)).isoformat(),
            "date_to": today.isoformat(),
        },
    )

    for params in invalid_requests:
        response = client.get(
            "/api/v1/workouts/progress/summary",
            params=params,
            headers=headers,
        )
        assert response.status_code == 422, (params, response.text)

    unsupported = client.get(
        "/api/v1/workouts/progress/training-analytics",
        params={"period_days": 14},
        headers=headers,
    )
    assert unsupported.status_code == 422


def test_custom_period_with_no_data_keeps_factual_empty_payload(client) -> None:
    telegram_user_id = 111_004
    headers = _auth(client, telegram_user_id)
    response = client.get(
        "/api/v1/workouts/progress/summary",
        params={"date_from": "2024-01-01", "date_to": "2024-01-01"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["period_days"] == 1
    assert payload["training"]["completed_workouts"] == 0
    assert payload["body"]["trends"] == []
    assert payload["nutrition"]["average_calories"] is None
