from fitminiapp_api.core.config import settings
from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.user import User


def _auth(
    client,
    telegram_user_id: int,
    *,
    is_coach: bool = False,
    is_admin: bool = False,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={
            "telegram_user_id": telegram_user_id,
            "is_coach": is_coach,
            "is_admin": is_admin,
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_only_verified_root_manages_admin_capability_and_preserves_trainer(client, monkeypatch):
    root_telegram_user_id = 46_100
    monkeypatch.setattr(settings, "admin_telegram_user_ids", str(root_telegram_user_id))
    root_headers = _auth(client, root_telegram_user_id, is_admin=True)
    delegated_admin_headers = _auth(client, 46_101, is_admin=True)
    trainer_headers = _auth(client, 46_102, is_coach=True)
    trainer = client.get("/api/v1/me", headers=trainer_headers).json()

    delegated = client.patch(
        f"/api/v1/admin/users/{trainer['id']}/admin-capability",
        json={"is_admin": True},
        headers=delegated_admin_headers,
    )
    assert delegated.status_code == 403

    granted = client.patch(
        f"/api/v1/admin/users/{trainer['id']}/admin-capability",
        json={"is_admin": True},
        headers=root_headers,
    )
    assert granted.status_code == 200
    assert granted.json()["is_coach"] is True
    assert granted.json()["is_admin"] is True

    revoked = client.patch(
        f"/api/v1/admin/users/{trainer['id']}/admin-capability",
        json={"is_admin": False},
        headers=root_headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["is_coach"] is True
    assert revoked.json()["is_admin"] is False

    with get_session_context() as db:
        events = (
            db.query(AuditEvent)
            .filter(AuditEvent.action == "root.user_admin_capability_updated")
            .all()
        )
        assert len(events) == 2
        assert all(event.details == {"is_admin": event.details["is_admin"]} for event in events)


def test_root_is_protected_from_admin_mutations_and_self_delete(client, monkeypatch):
    root_telegram_user_id = 46_200
    monkeypatch.setattr(settings, "admin_telegram_user_ids", str(root_telegram_user_id))
    root_headers = _auth(client, root_telegram_user_id, is_admin=True)
    delegated_admin_headers = _auth(client, 46_201, is_admin=True)
    root = client.get("/api/v1/me", headers=root_headers).json()

    for path, payload in (
        (f"/api/v1/admin/users/{root['id']}/admin-capability", {"is_admin": False}),
        (f"/api/v1/admin/users/{root['id']}/status", {"is_active": False}),
    ):
        assert client.patch(path, json=payload, headers=delegated_admin_headers).status_code == 403
    assert (
        client.delete(
            f"/api/v1/admin/users/{root['id']}", headers=delegated_admin_headers
        ).status_code
        == 403
    )
    assert (
        client.request(
            "DELETE",
            "/api/v1/me/account",
            json={"confirmation": "DELETE"},
            headers=root_headers,
        ).status_code
        == 403
    )

    with get_session_context() as db:
        protected_root = db.query(User).filter(User.id == root["id"]).one()
        assert protected_root.is_active is True
        assert protected_root.is_admin is True


def test_admin_without_trainer_cannot_access_coach_or_private_notification_content(client):
    admin_headers = _auth(client, 46_300, is_admin=True)
    target_headers = _auth(client, 46_301)
    target = client.get("/api/v1/me", headers=target_headers).json()
    with get_session_context() as db:
        db.add(
            Notification(
                user_id=target["id"],
                channel="telegram",
                title="Private title",
                body="Private notification content",
                scheduled_for=now_msk_naive(),
                scheduled_for_utc=now_msk_naive(),
                status="queued",
            )
        )
        db.commit()

    assert client.get("/api/v1/coach/clients", headers=admin_headers).status_code == 403
    notifications = client.get("/api/v1/admin/notifications", headers=admin_headers)
    assert notifications.status_code == 200
    assert notifications.json()[0].keys() == {
        "id",
        "user_id",
        "timezone",
        "status",
        "scheduled_for",
        "sent_at",
    }
    assert "Private" not in notifications.text


def test_trainer_admin_still_requires_an_active_client_relation(client):
    trainer_admin_headers = _auth(client, 46_400, is_coach=True, is_admin=True)
    target_headers = _auth(client, 46_401)
    target = client.get("/api/v1/me", headers=target_headers).json()

    coach_measurements = client.get(
        f"/api/v1/coach/clients/{target['id']}/measurements",
        headers=trainer_admin_headers,
    )
    assert coach_measurements.status_code == 404

    nutrition = client.post(
        "/api/v1/nutrition/targets",
        headers=trainer_admin_headers,
        json={
            "target_telegram_user_id": 46_401,
            "sex": "male",
            "weight_kg": 80,
            "height_cm": 180,
            "age": 30,
            "strength_trainings_per_week": 3,
            "cardio_trainings_per_week": 0,
            "goal": "maintenance",
        },
    )
    assert nutrition.status_code == 403
