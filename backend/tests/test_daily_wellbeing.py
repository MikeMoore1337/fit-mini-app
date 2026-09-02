from __future__ import annotations

import io
import zipfile
from datetime import timedelta

from fitminiapp_api.core.timezone import today_in_timezone, today_msk
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.daily_wellbeing import DailyWellbeingCheckIn
from fitminiapp_api.models.user import CoachClient, User
from fitminiapp_api.schemas.progress import NutritionReportPeriod
from fitminiapp_api.services.account_export import build_account_export
from fitminiapp_api.services.progress_report_pdf import build_progress_report_pdf
from fitminiapp_api.services.progress_reports import build_progress_report


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


def test_daily_wellbeing_is_optional_editable_and_isolated(client) -> None:
    headers = _auth(client, 82_001)
    other_headers = _auth(client, 82_002)
    local_date = today_msk()

    empty = client.get(
        "/api/v1/check-ins/daily",
        params={"local_date": local_date},
        headers=headers,
    )
    assert empty.status_code == 200
    assert empty.json()["record"] is None

    no_observation = client.put(
        f"/api/v1/check-ins/daily/{local_date}",
        json={"note": "Заметка без наблюдения"},
        headers=headers,
    )
    assert no_observation.status_code == 422

    saved = client.put(
        f"/api/v1/check-ins/daily/{local_date}",
        json={"sleep_quality": 4, "note": "Личная заметка не для отчёта"},
        headers=headers,
    )
    assert saved.status_code == 200, saved.text
    saved_payload = saved.json()
    assert saved_payload["sleep_quality"] == 4
    assert saved_payload["mood"] is None
    assert saved_payload["note"] == "Личная заметка не для отчёта"
    row_id = saved_payload["id"]
    original_timezone = saved_payload["timezone_at_entry"]

    with get_session_context() as db:
        user = db.get(User, _user_id(82_001))
        assert user is not None and user.profile is not None
        user.profile.timezone = "UTC"
        db.commit()

    edited = client.put(
        f"/api/v1/check-ins/daily/{local_date}",
        json={"sleep_duration_minutes": 420, "mood": 3, "note": "Обновлено"},
        headers=headers,
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["id"] == row_id
    assert edited.json()["sleep_quality"] is None
    assert edited.json()["sleep_duration_minutes"] == 420
    assert edited.json()["mood"] == 3
    assert edited.json()["timezone_at_entry"] == original_timezone

    foreign_view = client.get(
        "/api/v1/check-ins/daily",
        params={"local_date": local_date},
        headers=other_headers,
    )
    assert foreign_view.status_code == 200
    assert foreign_view.json()["record"] is None

    future = client.put(
        f"/api/v1/check-ins/daily/{local_date + timedelta(days=1)}",
        json={"mood": 3},
        headers=headers,
    )
    assert future.status_code == 422

    deleted = client.delete(f"/api/v1/check-ins/daily/{local_date}", headers=headers)
    assert deleted.status_code == 204
    assert (
        client.get(
            "/api/v1/check-ins/daily",
            params={"local_date": local_date},
            headers=headers,
        ).json()["record"]
        is None
    )


def test_daily_wellbeing_report_uses_actual_points_and_excludes_notes(client) -> None:
    headers = _auth(client, 82_003)
    user_id = _user_id(82_003)
    today = today_msk()
    entries = (
        (today - timedelta(days=5), {"sleep_quality": 2, "mood": 2}),
        (today - timedelta(days=3), {"sleep_duration_minutes": 390, "mood": 3}),
        (today, {"sleep_quality": 5, "sleep_duration_minutes": 480, "mood": 5}),
    )
    for local_date, payload in entries:
        response = client.put(
            f"/api/v1/check-ins/daily/{local_date}",
            json={**payload, "note": "Скрытая заметка пользователя"},
            headers=headers,
        )
        assert response.status_code == 200, response.text

    report_response = client.get(
        "/api/v1/workouts/progress/report",
        params={
            "period": "custom",
            "date_from": (today - timedelta(days=6)).isoformat(),
            "date_to": today.isoformat(),
        },
        headers=headers,
    )
    assert report_response.status_code == 200, report_response.text
    report = report_response.json()
    wellbeing = report["wellbeing"]
    assert wellbeing["eligible_days"] == 7
    assert wellbeing["recorded_days"] == 3
    assert wellbeing["coverage_percent"] == 42.9
    assert wellbeing["sleep"]["recorded_days"] == 2
    assert wellbeing["mood"]["recorded_days"] == 3
    assert wellbeing["mood"]["trend"] == "improving"
    assert len(wellbeing["daily"]) == 3
    assert "note" not in report_response.text
    assert "Скрытая заметка пользователя" not in report_response.text

    with get_session_context() as db:
        user = db.get(User, user_id)
        assert user is not None
        internal_report = build_progress_report(
            db,
            user,
            NutritionReportPeriod.CUSTOM,
            date_from=today - timedelta(days=6),
            date_to=today,
        )
        exported = build_account_export(db, user)
    assert (
        internal_report["wellbeing"]["daily"][0]["local_date"]
        == (today - timedelta(days=5)).isoformat()
    )
    assert exported["daily_wellbeing_check_ins"][0]["note"] == "Скрытая заметка пользователя"

    pdf = build_progress_report_pdf(internal_report)
    assert pdf.startswith(b"%PDF-")


def test_daily_wellbeing_is_exported_and_removed_with_account(client) -> None:
    headers = _auth(client, 82_004)
    user_id = _user_id(82_004)
    local_date = today_in_timezone("Europe/Moscow")
    saved = client.put(
        f"/api/v1/check-ins/daily/{local_date}",
        json={"sleep_quality": 3, "mood": 4, "note": "Экспортируемая заметка"},
        headers=headers,
    )
    assert saved.status_code == 200

    created = client.post("/api/v1/me/exports", headers=headers)
    assert created.status_code == 201, created.text
    export_id = created.json()["export_id"]
    downloaded = client.get(f"/api/v1/me/exports/{export_id}/download", headers=headers)
    assert downloaded.status_code == 200
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        payload = archive.read("account.json").decode("utf-8")
        daily_csv = archive.read("daily-wellbeing-check-ins.csv").decode("utf-8-sig")
    assert "Экспортируемая заметка" in payload
    assert "Экспортируемая заметка" in daily_csv

    deleted = client.request(
        "DELETE", "/api/v1/me/account", headers=headers, json={"confirmation": "DELETE"}
    )
    assert deleted.status_code == 204
    with get_session_context() as db:
        assert db.query(DailyWellbeingCheckIn).filter_by(user_id=user_id).count() == 0


def test_coach_progress_report_keeps_daily_wellbeing_permission_boundary(client) -> None:
    client_headers = _auth(client, 82_005)
    coach_headers = _auth(client, 82_006, is_coach=True)
    other_coach_headers = _auth(client, 82_007, is_coach=True)
    client_id = _user_id(82_005)
    coach_id = _user_id(82_006)
    today = today_msk()
    with get_session_context() as db:
        db.add(CoachClient(coach_user_id=coach_id, client_user_id=client_id, status="active"))

    saved = client.put(
        f"/api/v1/check-ins/daily/{today}",
        json={"mood": 4, "note": "Тренер не должен видеть эту заметку"},
        headers=client_headers,
    )
    assert saved.status_code == 200
    allowed = client.get(
        f"/api/v1/coach/clients/{client_id}/progress-report?period=days_7",
        headers=coach_headers,
    )
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["wellbeing"]["recorded_days"] == 1
    assert "Тренер не должен видеть эту заметку" not in allowed.text

    denied = client.get(
        f"/api/v1/coach/clients/{client_id}/progress-report?period=days_7",
        headers=other_coach_headers,
    )
    assert denied.status_code == 404
