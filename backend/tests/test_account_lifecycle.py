from __future__ import annotations

import io
import json
import zipfile
from datetime import timedelta

from fastapi.encoders import jsonable_encoder

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.account import AccountDataExport
from fitminiapp_api.models.auth_identity import AuthIdentity
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.token import RefreshToken
from fitminiapp_api.models.user import BodyMeasurement, CoachClient, User
from fitminiapp_api.models.weekly_digest import WeeklyDigestPreference
from fitminiapp_api.services import account_exports


def _login(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_export_job_is_current_user_only_zip_and_replaces_previous_artifact(client) -> None:
    owner_headers = _login(client, 9_650_001)
    other_headers = _login(client, 9_650_002)
    owner_id = client.get("/api/v1/me", headers=owner_headers).json()["id"]
    other_id = client.get("/api/v1/me", headers=other_headers).json()["id"]
    with get_session_context() as db:
        db.add_all(
            [
                BodyMeasurement(
                    user_id=owner_id,
                    measured_on=now_msk_naive().date(),
                    weight_kg=75.2,
                    note='=HYPERLINK("https://example.test", "Личная запись владельца")',
                ),
                BodyMeasurement(
                    user_id=other_id,
                    measured_on=now_msk_naive().date(),
                    weight_kg=91.4,
                    note="Чужая запись",
                ),
            ]
        )

    assert client.get("/api/v1/me/exports/current", headers=owner_headers).json() == {
        "status": "none",
        "export_id": None,
        "created_at": None,
        "completed_at": None,
        "expires_at": None,
        "filename": None,
        "content_size_bytes": None,
        "error_code": None,
    }
    created = client.post("/api/v1/me/exports", headers=owner_headers)
    assert created.status_code == 201
    status = created.json()
    assert status["status"] == "ready"
    assert status["export_id"]
    assert status["filename"].endswith(".zip")
    assert status["content_size_bytes"] > 0

    denied = client.get(
        f"/api/v1/me/exports/{status['export_id']}/download",
        headers=other_headers,
    )
    assert denied.status_code == 404
    downloaded = client.get(
        f"/api/v1/me/exports/{status['export_id']}/download",
        headers=owner_headers,
    )
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/zip"
    assert downloaded.headers["cache-control"] == "no-store, private"
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        assert set(archive.namelist()) == {
            "account.json",
            "food-diary.csv",
            "manifest.json",
            "measurements.csv",
            "nutrition-target-history.csv",
            "weekly-check-ins.csv",
            "workout-history.csv",
        }
        payload = json.loads(archive.read("account.json"))
        measurements_csv = archive.read("measurements.csv").decode("utf-8-sig")
    assert payload["account"]["id"] == owner_id
    assert payload["measurements"][0]["note"].startswith("=HYPERLINK")
    assert "Чужая запись" not in json.dumps(payload, ensure_ascii=False)
    assert "'=HYPERLINK" in measurements_csv
    assert "91.4" not in measurements_csv
    assert "token_hash" not in json.dumps(jsonable_encoder(payload)).lower()

    replaced = client.post("/api/v1/me/exports", headers=owner_headers).json()
    assert replaced["status"] == "ready"
    assert replaced["export_id"] != status["export_id"]
    assert (
        client.get(
            f"/api/v1/me/exports/{status['export_id']}/download",
            headers=owner_headers,
        ).status_code
        == 404
    )
    with get_session_context() as db:
        assert db.query(AccountDataExport).filter_by(user_id=owner_id).count() == 1


def test_export_expiry_purges_bytes_and_tma_link_is_short_lived(client) -> None:
    headers = _login(client, 9_650_003)
    ready = client.post("/api/v1/me/exports", headers=headers).json()
    link = client.post(
        f"/api/v1/me/exports/{ready['export_id']}/download-link",
        headers=headers,
    )
    assert link.status_code == 200
    public_path = link.json()["url"].split("/api/v1", 1)[1]
    public_download = client.get(f"/api/v1{public_path}")
    assert public_download.status_code == 200
    assert public_download.headers["access-control-allow-origin"] == "https://web.telegram.org"

    with get_session_context() as db:
        row = db.query(AccountDataExport).filter_by(export_id=ready["export_id"]).one()
        row.expires_at = now_msk_naive() - timedelta(seconds=1)

    expired = client.get("/api/v1/me/exports/current", headers=headers)
    assert expired.status_code == 200
    assert expired.json()["status"] == "expired"
    assert expired.json()["content_size_bytes"] is None
    assert (
        client.get(
            f"/api/v1/me/exports/{ready['export_id']}/download",
            headers=headers,
        ).status_code
        == 410
    )
    assert client.get(f"/api/v1{public_path}").status_code == 404
    with get_session_context() as db:
        row = db.query(AccountDataExport).filter_by(export_id=ready["export_id"]).one()
        assert row.archive_bytes is None
        assert row.download_token_hash is None


def test_export_handles_empty_account_and_bounded_generation_error(client, monkeypatch) -> None:
    headers = _login(client, 9_650_007)
    ready = client.post("/api/v1/me/exports", headers=headers)
    assert ready.status_code == 201
    assert ready.json()["status"] == "ready"

    monkeypatch.setattr(account_exports, "ACCOUNT_EXPORT_MAX_SOURCE_BYTES", 1)
    bounded = client.post("/api/v1/me/exports", headers=headers)
    assert bounded.status_code == 201
    assert bounded.json()["status"] == "error"
    assert bounded.json()["error_code"] == "archive_too_large"
    with get_session_context() as db:
        row = (
            db.query(AccountDataExport)
            .filter_by(user_id=client.get("/api/v1/me", headers=headers).json()["id"])
            .one()
        )
        assert row.archive_bytes is None


def test_superseded_export_generation_cannot_lock_the_newer_job(client) -> None:
    headers = _login(client, 9_650_008)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    with get_session_context() as db:
        user = db.get(User, user_id)
        assert user is not None
        first = account_exports.start_account_export(db, user)
        first_id = first.export_id

    with get_session_context() as db:
        user = db.get(User, user_id)
        assert user is not None
        second = account_exports.start_account_export(db, user)
        second_id = second.export_id

    assert second_id != first_id
    with get_session_context() as db:
        assert account_exports.lock_account_export_generation(db, user_id, first_id) is None
        current = account_exports.lock_account_export_generation(db, user_id, second_id)
        assert current is not None
        assert current.export_id == second_id


def test_unlink_preserves_account_guards_last_identity_and_disables_telegram(client) -> None:
    headers = _login(client, 9_650_004)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    now = now_msk_naive()
    with get_session_context() as db:
        db.add(
            AuthIdentity(
                user_id=user_id,
                provider="google",
                subject="task-65-google",
                email="task65@example.test",
                email_verified=True,
            )
        )
        setting = db.query(NotificationSetting).filter_by(user_id=user_id).one()
        setting.telegram_enabled = True
        db.add(
            WeeklyDigestPreference(
                user_id=user_id,
                telegram_chat_id=9_650_004,
                weekly_news_digest_enabled=True,
                consent_version="weekly-news-v1",
                subscribed_at=now,
            )
        )
        db.add(
            Notification(
                user_id=user_id,
                channel="telegram",
                category="workout_reminder",
                event_kind="reminder",
                title="Напоминание",
                body="Личный текст",
                scheduled_for=now + timedelta(hours=1),
                scheduled_for_utc=now + timedelta(hours=1),
                status="queued",
            )
        )
        db.add(
            BodyMeasurement(
                user_id=user_id,
                measured_on=now.date(),
                weight_kg=70,
            )
        )

    unlinked = client.delete("/api/v1/me/auth/identities/telegram", headers=headers)
    assert unlinked.status_code == 200
    assert unlinked.json()["telegram_user_id"] is None
    assert unlinked.json()["auth_providers"] == ["google"]
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    with get_session_context() as db:
        assert db.get(User, user_id) is not None
        assert db.query(BodyMeasurement).filter_by(user_id=user_id).count() == 1
        setting = db.query(NotificationSetting).filter_by(user_id=user_id).one()
        notification = db.query(Notification).filter_by(user_id=user_id).one()
        assert setting.telegram_enabled is False
        assert notification.status == "cancelled"
        assert notification.last_error == "telegram_identity_unlinked"
        digest_preference = db.query(WeeklyDigestPreference).filter_by(user_id=user_id).one()
        assert digest_preference.weekly_news_digest_enabled is False
        assert digest_preference.telegram_chat_id is None
        assert digest_preference.disabled_reason == "telegram_identity_unlinked"

    blocked = client.delete("/api/v1/me/auth/identities/google", headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "Нельзя отключить последний способ входа"


def test_delete_revokes_sessions_relationships_and_export_but_keeps_shared_catalog(client) -> None:
    headers = _login(client, 9_650_005)
    other_headers = _login(client, 9_650_006)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    other_id = client.get("/api/v1/me", headers=other_headers).json()["id"]
    ready = client.post("/api/v1/me/exports", headers=headers).json()
    with get_session_context() as db:
        shared_exercise_id = (
            db.query(Exercise.id).filter(Exercise.created_by_user_id.is_(None)).first()[0]
        )
        db.add(CoachClient(coach_user_id=other_id, client_user_id=user_id, status="active"))

    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    with get_session_context() as db:
        assert db.get(User, user_id) is None
        assert db.get(User, other_id) is not None
        assert db.get(Exercise, shared_exercise_id) is not None
        assert db.query(CoachClient).filter_by(client_user_id=user_id).count() == 0
        assert db.query(AccountDataExport).filter_by(export_id=ready["export_id"]).count() == 0
        assert db.query(RefreshToken).filter_by(user_id=user_id).count() == 0
