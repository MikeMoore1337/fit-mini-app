import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.session import SessionLocal, get_session_context
from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.models.billing import Payment, Plan, Subscription
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.user import CoachClient, CoachClientInvite, User, UserProfile
from fitminiapp_api.services.notifications import prune_terminal_records
from fitminiapp_api.services.telegram_auth import get_or_create_user_from_init_data


def _auth(client, telegram_user_id: int, *, is_coach: bool, is_admin: bool = False):
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


def _create_invite(client, coach_headers) -> tuple[str, int]:
    response = client.post("/api/v1/coach/invite-links", headers=coach_headers)
    assert response.status_code == 201
    return response.json()["code"], response.json()["invite_id"]


def _accept_invite(client, coach_headers, client_headers) -> int:
    token, invite_id = _create_invite(client, coach_headers)
    preview = client.post(
        "/api/v1/me/coach-invites/link/preview",
        json={"token": token},
        headers=client_headers,
    )
    assert preview.status_code == 200
    confirmed = client.post(
        "/api/v1/me/coach-invites/link/confirm",
        json={"token": token},
        headers=client_headers,
    )
    assert confirmed.status_code == 204
    return invite_id


def test_concurrent_telegram_first_login_is_an_idempotent_upsert():
    barrier = Barrier(2)
    init_data = {
        "user": {
            "id": 880_001,
            "username": "race_user",
            "first_name": "Race",
            "last_name": "User",
        }
    }

    def login() -> int:
        db = SessionLocal()
        try:
            barrier.wait(timeout=5)
            return get_or_create_user_from_init_data(db, init_data).id
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        user_ids = list(executor.map(lambda _: login(), range(2)))

    assert user_ids[0] == user_ids[1]
    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == 880_001).one()
        assert db.query(User).filter(User.telegram_user_id == 880_001).count() == 1
        assert db.query(UserProfile).filter(UserProfile.user_id == user.id).count() == 1
        assert (
            db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).count()
            == 1
        )


def test_admin_deactivation_ends_both_relationship_roles_and_revokes_invites(client):
    admin_headers = _auth(client, 881_000, is_coach=True, is_admin=True)
    target_headers = _auth(client, 881_001, is_coach=True)
    other_coach_headers = _auth(client, 881_002, is_coach=True)
    client_headers = _auth(client, 881_003, is_coach=False)

    _accept_invite(client, other_coach_headers, target_headers)
    _accept_invite(client, target_headers, client_headers)
    outbound_token, outbound_invite_id = _create_invite(client, target_headers)
    assert outbound_token

    with get_session_context() as db:
        target = db.query(User).filter(User.telegram_user_id == 881_001).one()
        other_coach = db.query(User).filter(User.telegram_user_id == 881_002).one()
        inbound = CoachClientInvite(
            coach_user_id=other_coach.id,
            client_user_id=target.id,
            telegram_user_id=target.telegram_user_id,
            token_hash=hashlib.sha256(b"legacy-bound-proof").hexdigest(),
            source="invite_link",
            status="pending",
            expires_at=now_msk_naive() + timedelta(days=1),
        )
        db.add(inbound)
        db.flush()
        inbound_invite_id = inbound.id
        db.add(
            Notification(
                user_id=target.id,
                channel="telegram",
                title="Trainer request",
                body="Confirm in app",
                scheduled_for=now_msk_naive(),
                scheduled_for_utc=datetime.now(UTC).replace(tzinfo=None),
                status="queued",
                dedupe_key=f"trainer_request:{inbound.id}",
            )
        )
        target_id = target.id

    blocked = client.patch(
        f"/api/v1/admin/users/{target_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert blocked.status_code == 200
    assert client.get("/api/v1/me", headers=target_headers).status_code == 401

    with get_session_context() as db:
        relations = (
            db.query(CoachClient)
            .filter(
                (CoachClient.coach_user_id == target_id) | (CoachClient.client_user_id == target_id)
            )
            .all()
        )
        assert len(relations) == 2
        assert {row.status for row in relations} == {"ended"}
        assert {row.ended_reason for row in relations} == {"user_deactivated"}

        invites = (
            db.query(CoachClientInvite)
            .filter(CoachClientInvite.id.in_((outbound_invite_id, inbound_invite_id)))
            .all()
        )
        assert {row.status for row in invites} == {"revoked"}
        notification = (
            db.query(Notification)
            .filter(Notification.dedupe_key == f"trainer_request:{inbound_invite_id}")
            .one()
        )
        assert notification.status == "cancelled"

        audit_actions = {
            row.action
            for row in db.query(AuditEvent).filter(AuditEvent.target_user_id == target_id).all()
        }
        assert {
            "admin.user_status_updated",
            "coach.relation_ended",
            "coach.invite_revoked",
        }.issubset(audit_actions)

    assert client.get("/api/v1/coach/clients", headers=other_coach_headers).json() == []


def test_terminal_retention_prunes_only_old_operational_rows(client):
    headers = _auth(client, 882_001, is_coach=True)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    old = now_msk_naive() - timedelta(days=91)
    now_utc = datetime.now(UTC).replace(tzinfo=None)

    with get_session_context() as db:
        old_notification = Notification(
            user_id=user_id,
            channel="telegram",
            title="Old",
            body="Old terminal row",
            scheduled_for=old,
            scheduled_for_utc=old,
            status="sent",
            created_at=old,
        )
        fresh_notification = Notification(
            user_id=user_id,
            channel="telegram",
            title="Fresh",
            body="Fresh terminal row",
            scheduled_for=now_msk_naive(),
            scheduled_for_utc=now_utc,
            status="cancelled",
        )
        revoked_invite = CoachClientInvite(
            coach_user_id=user_id,
            token_hash=hashlib.sha256(b"old-revoked").hexdigest(),
            source="invite_link",
            status="revoked",
            created_at=old,
        )
        accepted_invite = CoachClientInvite(
            coach_user_id=user_id,
            token_hash=hashlib.sha256(b"old-accepted").hexdigest(),
            source="invite_link",
            status="accepted",
            created_at=old,
        )
        relation = CoachClient(
            coach_user_id=user_id,
            client_user_id=db.query(User).filter(User.id != user_id).first().id,
            status="ended",
            ended_reason="historical",
            created_at=old,
        )
        db.add_all(
            [
                old_notification,
                fresh_notification,
                revoked_invite,
                accepted_invite,
                relation,
            ]
        )
        db.flush()
        ids = {
            "old_notification": old_notification.id,
            "fresh_notification": fresh_notification.id,
            "revoked_invite": revoked_invite.id,
            "accepted_invite": accepted_invite.id,
            "relation": relation.id,
        }

    with get_session_context() as db:
        assert prune_terminal_records(db) == 2
        assert db.get(Notification, ids["old_notification"]) is None
        assert db.get(Notification, ids["fresh_notification"]) is not None
        assert db.get(CoachClientInvite, ids["revoked_invite"]) is None
        assert db.get(CoachClientInvite, ids["accepted_invite"]) is not None
        assert db.get(CoachClient, ids["relation"]) is not None


def test_account_export_omits_secrets_and_self_delete_removes_account(client):
    headers = _auth(client, 883_001, is_coach=False)
    me = client.get("/api/v1/me", headers=headers).json()
    saved = client.post(
        "/api/v1/workouts/diary",
        headers=headers,
        json={"weight_kg": 74.5, "note": "Контрольная запись"},
    )
    assert saved.status_code == 200

    exported = client.get("/api/v1/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.headers["cache-control"] == "no-store"
    assert exported.json()["account"]["telegram_user_id"] == 883_001
    assert exported.json()["measurements"][0]["weight_kg"] == 74.5
    serialized = exported.text.lower()
    assert "token_hash" not in serialized
    assert "refresh_token" not in serialized

    invalid = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "NO"},
    )
    assert invalid.status_code == 422
    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    with get_session_context() as db:
        assert db.query(User).filter(User.id == me["id"]).first() is None


def test_account_deletion_cleans_legacy_billing_foreign_keys(client):
    headers = _auth(client, 883_002, is_coach=False)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]

    with get_session_context() as db:
        plan = Plan(
            code="legacy-account-delete",
            title="Legacy",
            price=1,
            currency="RUB",
            period_days=1,
        )
        db.add(plan)
        db.flush()
        db.add_all(
            [
                Payment(
                    user_id=user_id,
                    plan_id=plan.id,
                    provider="legacy",
                    provider_payment_id="legacy-account-delete",
                    amount=1,
                    currency="RUB",
                    status="legacy",
                ),
                Subscription(
                    user_id=user_id,
                    plan_id=plan.id,
                    status="legacy",
                ),
            ]
        )

    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204

    with get_session_context() as db:
        assert db.query(Payment).filter(Payment.user_id == user_id).count() == 0
        assert db.query(Subscription).filter(Subscription.user_id == user_id).count() == 0
