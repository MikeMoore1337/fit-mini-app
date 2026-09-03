import hashlib
import json
import time
from datetime import UTC, datetime

from pydantic import SecretStr

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.news import HermesEditorialSubmission, NewsSource
from fitminiapp_api.services.news_hermes import _canonical_source_hash, hermes_signature


def _payload() -> dict:
    published_at = datetime.now(UTC).replace(tzinfo=None, microsecond=0)
    source = {
        "source_id": "journal-one",
        "external_id": "hermes-1",
        "canonical_url": "https://example.com/story",
        "primary_url": None,
        "title": "Исследование связало силовые тренировки с восстановлением",
        "summary": "Авторы изучили силовые тренировки и восстановление у взрослых.",
        "author": None,
        "publisher": "Journal One",
        "published_at": published_at.isoformat(),
        "updated_at": None,
        "doi": None,
    }
    source["content_hash"] = _canonical_source_hash(
        title=source["title"],
        summary=source["summary"],
        canonical_url=source["canonical_url"],
        published_at=published_at,
    )
    return {
        "schema_version": "hermes-editorial-intake-v1",
        "idempotency_key": "hermes-test-idempotency-1",
        "request_nonce": "hermes-test-nonce-1",
        "source": source,
        "draft": {
            "headline": "Силовые тренировки и восстановление: что показало исследование",
            "summary": "Авторы изучили связь силовых тренировок с восстановлением у взрослых. "
            "Результат относится к исследованной группе и не заменяет индивидуальную оценку.",
            "why_it_matters": "Данные помогают точнее обсуждать восстановление после нагрузки.",
        },
        "provenance": {
            "provider": "hermes",
            "model": "test-model",
            "prompt_version": "hermes-editorial-v1",
            "skill_version": "yfc-hermes-editorial-v1",
        },
    }


def _signed_headers(body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    nonce = "hermes-test-nonce-1"
    return {
        "X-Hermes-Key-Id": "hermes-test",
        "X-Hermes-Timestamp": timestamp,
        "X-Hermes-Nonce": nonce,
        "X-Hermes-Signature": hermes_signature(
            "test-hermes-shared-secret-that-is-long-enough",
            timestamp=timestamp,
            nonce=nonce,
            body=body,
        ),
    }


def test_signed_hermes_intake_creates_preview_and_is_idempotent(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "hermes_intake_enabled", True)
    monkeypatch.setattr(settings, "hermes_intake_key_id", "hermes-test")
    monkeypatch.setattr(
        settings,
        "hermes_intake_shared_secret",
        SecretStr("test-hermes-shared-secret-that-is-long-enough"),
    )
    with get_session_context() as db:
        db.add(
            NewsSource(
                id="journal-one",
                name="Journal One",
                source_type="primary_research",
                fetch_kind="rss",
                feed_url="https://example.com/feed",
                language="en",
                enabled=True,
            )
        )

    body = json.dumps(_payload(), ensure_ascii=False, separators=(",", ":")).encode()
    headers = _signed_headers(body)
    first = client.post("/api/v1/hermes/editorial/intake", content=body, headers=headers)
    assert first.status_code == 200, first.text
    first_payload = first.json()
    assert first_payload["status"] == "accepted"
    assert first_payload["publication_policy"] == "manual_required"
    assert "силовые тренировки" in first_payload["preview_text"].lower()

    second = client.post("/api/v1/hermes/editorial/intake", content=body, headers=headers)
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "duplicate"
    assert second.json()["draft_id"] == first_payload["draft_id"]
    with get_session_context() as db:
        assert db.query(HermesEditorialSubmission).count() == 1


def test_hermes_intake_rejects_bad_signature_without_source_processing(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "hermes_intake_enabled", True)
    monkeypatch.setattr(settings, "hermes_intake_key_id", "hermes-test")
    monkeypatch.setattr(
        settings,
        "hermes_intake_shared_secret",
        SecretStr("test-hermes-shared-secret-that-is-long-enough"),
    )
    body = json.dumps(_payload(), ensure_ascii=False).encode()
    headers = _signed_headers(body)
    headers["X-Hermes-Signature"] = "sha256=" + hashlib.sha256(b"wrong").hexdigest()

    response = client.post("/api/v1/hermes/editorial/intake", content=body, headers=headers)

    assert response.status_code == 403
