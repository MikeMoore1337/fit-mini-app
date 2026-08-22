from datetime import timedelta

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.models.support import BotSupportCase
from fitminiapp_api.models.user import User
from fitminiapp_api.services.accounts import delete_user_cascade
from fitminiapp_api.services.bot_support import prune_support_cases, utcnow


def _headers() -> dict[str, str]:
    return {"X-Bot-Token": settings.bot_internal_token}


def _create_case(client, *, user_id: int = 9001, message_id: int = 101, category: str = "bug"):
    return client.post(
        "/api/v1/bot/support/cases",
        headers=_headers(),
        json={
            "telegram_user_id": user_id,
            "request_message_id": message_id,
            "category": category,
        },
    )


def test_support_case_flow_is_idempotent_private_and_admin_bound(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_telegram_user_ids", "7001,7002")

    created = _create_case(client)
    assert created.status_code == 200
    assert created.json()["status"] == "created"
    assert created.json()["case_status"] == "pending_relay"
    case_id = created.json()["case_id"]

    duplicate = _create_case(client)
    assert duplicate.status_code == 200
    assert duplicate.json() == {
        "case_id": case_id,
        "status": "duplicate",
        "case_status": "pending_relay",
    }

    relayed = client.post(
        f"/api/v1/bot/support/cases/{case_id}/relay-result",
        headers=_headers(),
        json={"delivered": True},
    )
    assert relayed.status_code == 200
    assert relayed.json() == {"status": "open"}

    unauthorized = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7999, "reply_message_id": 201},
    )
    assert unauthorized.status_code == 403

    claimed = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7001, "reply_message_id": 201},
    )
    assert claimed.status_code == 200
    assert claimed.json() == {"status": "claimed", "telegram_user_id": 9001}

    competing = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7002, "reply_message_id": 301},
    )
    assert competing.status_code == 200
    assert competing.json() == {"status": "unavailable", "telegram_user_id": None}

    completed = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-result",
        headers=_headers(),
        json={
            "admin_telegram_user_id": 7001,
            "reply_message_id": 201,
            "outcome": "delivered",
        },
    )
    assert completed.status_code == 200
    assert completed.json() == {"status": "recorded"}

    repeated = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7001, "reply_message_id": 201},
    )
    assert repeated.json() == {"status": "already_processed", "telegram_user_id": None}

    with get_session_context() as db:
        case = db.get(BotSupportCase, case_id)
        assert case is not None
        assert case.status == "replied"
        assert not hasattr(case, "text")
        audit_events = (
            db.query(AuditEvent)
            .filter(AuditEvent.resource_type == "bot_support_case")
            .order_by(AuditEvent.id.asc())
            .all()
        )
        assert [event.action for event in audit_events] == [
            "support.case_created",
            "support.relay_succeeded",
            "support.reply_claimed",
            "support.reply_delivered",
        ]
        assert all(event.details == {"category": "bug"} for event in audit_events)


def test_support_rate_limit_is_per_user_and_category(client) -> None:
    for message_id in range(1, 4):
        assert _create_case(client, message_id=message_id).status_code == 200

    limited = _create_case(client, message_id=4)
    assert limited.status_code == 429
    assert _create_case(client, message_id=5, category="idea").status_code == 200
    assert _create_case(client, user_id=9002, message_id=4).status_code == 200


def test_support_internal_api_rejects_wrong_token_and_invalid_case_id(client) -> None:
    forbidden = client.post(
        "/api/v1/bot/support/cases",
        headers={"X-Bot-Token": "wrong-token"},
        json={"telegram_user_id": 9001, "request_message_id": 1, "category": "bug"},
    )
    assert forbidden.status_code == 403
    invalid_case = client.post(
        "/api/v1/bot/support/cases/not-a-case/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7001, "reply_message_id": 1},
    )
    assert invalid_case.status_code == 422


def test_expired_and_blocked_support_cases_are_terminal(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_telegram_user_ids", "7001")
    created = _create_case(client, user_id=9010)
    case_id = created.json()["case_id"]
    with get_session_context() as db:
        case = db.get(BotSupportCase, case_id)
        assert case is not None
        case.status = "open"
        case.expires_at = utcnow() - timedelta(seconds=1)

    expired = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7001, "reply_message_id": 202},
    )
    assert expired.json() == {"status": "expired", "telegram_user_id": None}

    blocked_case = _create_case(client, user_id=9011, message_id=102).json()["case_id"]
    claim = client.post(
        f"/api/v1/bot/support/cases/{blocked_case}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7001, "reply_message_id": 203},
    )
    assert claim.json()["status"] == "claimed"
    result = client.post(
        f"/api/v1/bot/support/cases/{blocked_case}/reply-result",
        headers=_headers(),
        json={
            "admin_telegram_user_id": 7001,
            "reply_message_id": 203,
            "outcome": "blocked",
        },
    )
    assert result.status_code == 200
    with get_session_context() as db:
        assert db.get(BotSupportCase, blocked_case).status == "undeliverable"


def test_uncertain_reply_claim_remains_locked_against_duplicate_delivery(
    client, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "admin_telegram_user_ids", "7001,7002")
    case_id = _create_case(client, user_id=9012, message_id=103).json()["case_id"]
    with get_session_context() as db:
        case = db.get(BotSupportCase, case_id)
        assert case is not None
        case.status = "replying"
        case.reply_admin_telegram_user_id = 7001
        case.reply_message_id = 204
        case.reply_claimed_at = utcnow() - timedelta(minutes=6)

    competing = client.post(
        f"/api/v1/bot/support/cases/{case_id}/reply-claim",
        headers=_headers(),
        json={"admin_telegram_user_id": 7002, "reply_message_id": 205},
    )
    assert competing.json() == {"status": "unavailable", "telegram_user_id": None}
    with get_session_context() as db:
        case = db.get(BotSupportCase, case_id)
        assert case is not None
        assert case.status == "replying"
        assert case.reply_admin_telegram_user_id == 7001
        assert case.reply_message_id == 204


def test_account_deletion_removes_support_routing_metadata() -> None:
    telegram_user_id = 9020
    with get_session_context() as db:
        user = User(telegram_user_id=telegram_user_id, is_active=True)
        db.add(user)
        db.flush()
        case = BotSupportCase(
            id="a" * 32,
            telegram_user_id=telegram_user_id,
            request_message_id=404,
            category="account",
            status="open",
            created_at=utcnow(),
            expires_at=utcnow() + timedelta(days=7),
        )
        db.add(case)
        db.flush()
        delete_user_cascade(db, user)

    with get_session_context() as db:
        assert db.get(BotSupportCase, "a" * 32) is None


def test_support_metadata_retention_is_bounded() -> None:
    with get_session_context() as db:
        db.add_all(
            [
                BotSupportCase(
                    id="b" * 32,
                    telegram_user_id=9030,
                    request_message_id=405,
                    category="other",
                    status="expired",
                    created_at=utcnow() - timedelta(days=31),
                    expires_at=utcnow() - timedelta(days=24),
                ),
                BotSupportCase(
                    id="c" * 32,
                    telegram_user_id=9030,
                    request_message_id=406,
                    category="other",
                    status="open",
                    created_at=utcnow(),
                    expires_at=utcnow() + timedelta(days=7),
                ),
            ]
        )
        db.flush()
        assert prune_support_cases(db) == 1

    with get_session_context() as db:
        assert db.get(BotSupportCase, "b" * 32) is None
        assert db.get(BotSupportCase, "c" * 32) is not None
