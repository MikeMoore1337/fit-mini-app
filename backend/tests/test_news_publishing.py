from __future__ import annotations

import asyncio
import base64
import io
from datetime import UTC, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
from PIL import Image

from fitminiapp_api.core.config import Settings, settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.models.news import (
    NewsCluster,
    NewsDraftRevision,
    NewsImageRevision,
    NewsItem,
    NewsPublicationSnapshot,
    NewsSource,
)
from fitminiapp_api.services import news_publication
from fitminiapp_api.services.news_content import parse_editorial_content
from fitminiapp_api.services.news_drafts import create_draft_revision
from fitminiapp_api.services.news_editorial import (
    edit_text_revision,
    enqueue_review_deliveries,
)
from fitminiapp_api.services.news_images import (
    NewsImageError,
    create_image_revision,
    create_uploaded_image_revision,
)
from fitminiapp_api.services.news_ingestion import ParsedNewsItem, ingest_items, utcnow
from fitminiapp_api.services.news_post_management import manage_published_post
from fitminiapp_api.services.news_publication import (
    approve_publication,
    claim_due_publications,
    mark_publication_failed,
    mark_publication_succeeded,
    publication_payload,
    reconcile_uncertain_publication,
    retry_uncertain_publication,
)
from fitminiapp_api.services.news_sources import apply_source_allowlist, parse_source_allowlist
from fitminiapp_api.services.worker import (
    TelegramPublicationError,
    check_news_channel_rights,
    send_telegram_publication,
)


def _source_and_candidate(*, external_id: str = "publication-1") -> str:
    title = "Resistance training changed a measured strength outcome"
    summary = "A controlled study reported a specific strength outcome."
    if external_id == "daily-0":
        title = "Dietary protein review changed nutrition context"
        summary = "A nutrition review compared dietary protein contexts."
    elif external_id == "daily-1":
        title = "Sleep duration cohort reported recovery associations"
        summary = "A sleep cohort reported recovery associations."
    definitions = parse_source_allowlist(
        [
            {
                "id": "publishing-journal",
                "name": "Publishing Journal",
                "type": "primary_research",
                "fetch_kind": "rss",
                "url": "https://publishing-journal.example/feed",
                "language": "en",
                "enabled": True,
                "fetch_interval_minutes": 60,
                "trust_notes": "Primary publisher",
                "licensing_notes": "Metadata and short excerpt only",
            }
        ]
    )
    with get_session_context() as db:
        apply_source_allowlist(db, definitions)
        source = db.get(NewsSource, "publishing-journal")
        assert source is not None
        counts = ingest_items(
            db,
            source,
            [
                ParsedNewsItem(
                    external_id=external_id,
                    canonical_url=f"https://publishing-journal.example/{external_id}",
                    primary_url=f"https://publishing-journal.example/{external_id}",
                    title=title,
                    summary=summary,
                    publisher="Publishing Journal",
                    published_at=utcnow() - timedelta(hours=8),
                    doi=f"10.1000/{external_id}",
                )
            ],
            candidate_threshold=55,
        )
        assert counts["candidate"] == 1
        item = db.query(NewsItem).filter(NewsItem.external_id == external_id).one()
        assert item.cluster_id is not None
        return item.cluster_id


def _jpeg_bytes(*, exif: bool = False) -> bytes:
    image = Image.new("RGB", (900, 600), "#345221")
    output = io.BytesIO()
    kwargs = {"exif": Image.Exif()} if exif else {}
    if exif:
        kwargs["exif"][0x010E] = "private editorial metadata"
    image.save(output, format="JPEG", **kwargs)
    return output.getvalue()


def _draft(cluster_id: str) -> tuple[str, str]:
    with get_session_context() as db:
        cluster = db.get(NewsCluster, cluster_id)
        assert cluster is not None
        draft = asyncio.run(create_draft_revision(db, cluster))
        return draft.id, cluster.id


def test_image_provider_is_free_only_and_requires_explicit_free_plan() -> None:
    base = {
        "_env_file": None,
        "app_env": "test",
        "secret_key": "task-89-free-provider-secret-key",
        "database_url": "sqlite://",
        "telegram_bot_token": "test",
        "news_image_provider": "cloudflare_workers_ai",
        "news_image_cloudflare_account_id": "account",
        "news_image_cloudflare_api_token": "token",
    }
    with pytest.raises(ValueError, match="FREE_PLAN_CONFIRMED"):
        Settings(**base)
    configured = Settings(**base, news_image_cloudflare_free_plan_confirmed=True)
    assert configured.news_image_model == "@cf/black-forest-labs/flux-1-schnell"
    assert configured.news_image_steps == 4
    with pytest.raises(ValueError):
        Settings(**{**base, "news_image_provider": "openai"})


def test_task88_editorial_contract_is_structured_and_source_bound() -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    with get_session_context() as db:
        cluster = db.get(NewsCluster, cluster_id)
        draft = db.get(NewsDraftRevision, draft_id)
        assert cluster is not None and draft is not None
        assert draft.evidence_metadata["editorial_contract_version"] == "news-editorial-v2"
        assert draft.evidence_metadata["editorial_fields"]["headline"]
        assert draft.evidence_metadata["trusted_source_url"] == (
            "https://publishing-journal.example/publication-1"
        )
        parsed = parse_editorial_content(draft.draft_text)
        assert parsed is not None
        assert parsed.fields() == draft.evidence_metadata["editorial_fields"]
        asyncio.run(create_image_revision(db, cluster, draft, client=None))
        enqueue_review_deliveries(db, {7001})
        changed_source = edit_text_revision(
            db,
            draft_id=draft.id,
            expected_image_revision=cluster.current_image_revision,
            admin_telegram_user_id=7001,
            draft_text=draft.draft_text.replace(
                "https://publishing-journal.example/publication-1",
                "https://untrusted.example/replacement",
            ),
        )
        assert changed_source.status == "unavailable"
        assert cluster.latest_draft_revision == 1


def test_legacy_task88_revision_remains_parseable_for_existing_rows() -> None:
    legacy_text = (
        "Рубрика: Силовые тренировки\n\n"
        "Заголовок: Исследование уточнило контекст силовой адаптации\n\n"
        "Что произошло\nИсследователи сравнили две группы и описали ограничения выборки.\n\n"
        "Почему это важно\nКонтекст помогает корректно интерпретировать результат.\n\n"
        "Как применять / что не меняется\nНе менять программу только по одной публикации.\n\n"
        "Ограничения\nРезультат не является медицинской рекомендацией.\n\n"
        "Источник: Publishing Journal, 2026-08-25\n"
        "https://publishing-journal.example/legacy-publication"
    )

    parsed = parse_editorial_content(legacy_text)

    assert parsed is not None
    assert parsed.headline == "Исследование уточнило контекст силовой адаптации"
    assert parsed.summary.startswith("Исследователи сравнили две группы")
    assert parsed.why_it_matters == "Контекст помогает корректно интерпретировать результат."
    assert parsed.source_url == "https://publishing-journal.example/legacy-publication"


def test_provisional_task89_renderer_cannot_publish_in_production() -> None:
    values = {
        "_env_file": None,
        "app_debug": False,
        "secret_key": "task-89-production-secret-key-long-enough",
        "database_url": "sqlite://",
        "enable_dev_auth": False,
        "enable_web_auth": False,
        "enable_email_auth": False,
        "telegram_bot_token": "123456:configured-token",
        "bot_internal_token": "task-89-internal-token-that-is-long-enough",
        "frontend_base_url": "https://example.test",
        "admin_telegram_user_ids": "7001",
        "news_channel_id": -1001234567890,
        "news_channel_environment": "production",
        "news_ingestion_enabled": True,
        "news_publication_enabled": True,
    }
    for app_env in ("dev", "prod"):
        with pytest.raises(ValueError, match="task 89A renderer"):
            Settings(
                **values,
                app_env=app_env,
            )


def test_cloudflare_free_generation_is_news_specific_and_stores_provenance(monkeypatch) -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    monkeypatch.setattr(settings, "news_image_provider", "cloudflare_workers_ai")
    monkeypatch.setattr(settings, "news_image_cloudflare_account_id", "account")
    monkeypatch.setattr(settings, "news_image_cloudflare_api_token", "token")
    raw = _jpeg_bytes()

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/@cf/black-forest-labs/flux-1-schnell")
        body = request.content.decode()
        assert "Resistance training changed" in body
        assert "Topic category: strength" in body
        assert "publishing-journal.example" not in body
        return httpx.Response(
            200,
            json={"success": True, "result": {"image": base64.b64encode(raw).decode()}},
        )

    async def generate() -> str:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with get_session_context() as db:
                cluster = db.get(NewsCluster, cluster_id)
                draft = db.get(NewsDraftRevision, draft_id)
                assert cluster is not None and draft is not None
                image = await create_image_revision(db, cluster, draft, client=client)
                return image.id

    image_id = asyncio.run(generate())
    with get_session_context() as db:
        image = db.get(NewsImageRevision, image_id)
        assert image is not None
        assert image.kind == "generated"
        assert image.provider == "cloudflare_workers_ai_free"
        assert image.generation_cost_microunits == 0
        assert image.safety_status == "generated_pending_review"
        assert image.provenance["source"] == "safe_editorial_summary"


def test_provider_failure_uses_template_and_upload_is_normalized(monkeypatch) -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    monkeypatch.setattr(settings, "news_image_provider", "cloudflare_workers_ai")
    monkeypatch.setattr(settings, "news_image_cloudflare_account_id", "account")
    monkeypatch.setattr(settings, "news_image_cloudflare_api_token", "token")

    async def generate() -> str:
        transport = httpx.MockTransport(lambda _: httpx.Response(503))
        async with httpx.AsyncClient(transport=transport) as client:
            with get_session_context() as db:
                cluster = db.get(NewsCluster, cluster_id)
                draft = db.get(NewsDraftRevision, draft_id)
                assert cluster is not None and draft is not None
                image = await create_image_revision(db, cluster, draft, client=client)
                return image.id

    image_id = asyncio.run(generate())
    with get_session_context() as db:
        image = db.get(NewsImageRevision, image_id)
        assert image is not None
        assert image.kind == "template"
        assert image.warnings == ["image_provider_unavailable"]
        cluster = db.get(NewsCluster, cluster_id)
        draft = db.get(NewsDraftRevision, draft_id)
        assert cluster is not None and draft is not None
        uploaded = create_uploaded_image_revision(db, cluster, draft, _jpeg_bytes(exif=True))
        with Image.open(io.BytesIO(uploaded.image_data)) as normalized:
            assert normalized.getexif() == {}
            assert normalized.size == (1200, 800)
        with pytest.raises(NewsImageError, match="image_decode_invalid"):
            create_uploaded_image_revision(db, cluster, draft, b"not-an-image")
        monkeypatch.setattr(settings, "news_image_upload_max_bytes", 32)
        with pytest.raises(NewsImageError, match="image_size_invalid"):
            create_uploaded_image_revision(db, cluster, draft, _jpeg_bytes())
        monkeypatch.setattr(settings, "news_image_upload_max_bytes", 8_388_608)
        too_small = io.BytesIO()
        Image.new("RGB", (120, 80), "white").save(too_small, format="JPEG")
        with pytest.raises(NewsImageError, match="image_dimensions_invalid"):
            create_uploaded_image_revision(db, cluster, draft, too_small.getvalue())


def test_exact_approval_is_idempotent_and_edit_revokes_schedule(monkeypatch) -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    monkeypatch.setattr(settings, "news_image_provider", "disabled")
    monkeypatch.setattr(settings, "news_publication_enabled", True)
    monkeypatch.setattr(settings, "news_channel_id", -1001234567890)
    monkeypatch.setattr(settings, "news_channel_username", "yfc_test_news")
    monkeypatch.setattr(settings, "admin_telegram_user_ids", "7001")
    with get_session_context() as db:
        cluster = db.get(NewsCluster, cluster_id)
        draft = db.get(NewsDraftRevision, draft_id)
        assert cluster is not None and draft is not None
        draft.warnings = []
        asyncio.run(create_image_revision(db, cluster, draft, client=None))
        enqueue_review_deliveries(db, {7001})
        image_revision = cluster.current_image_revision
        approved = approve_publication(
            db,
            draft_id=draft.id,
            expected_image_revision=image_revision,
            admin_telegram_user_id=7001,
            mode="immediate",
        )
        assert approved.status == "queued"
        repeated = approve_publication(
            db,
            draft_id=draft.id,
            expected_image_revision=image_revision,
            admin_telegram_user_id=7001,
            mode="immediate",
        )
        assert repeated.status == "already_queued"
        snapshot = db.get(NewsPublicationSnapshot, approved.snapshot_id)
        assert snapshot is not None
        payload = publication_payload(db, snapshot.id)
        assert payload is None  # Snapshot is immutable but not claimed yet.
        edited = edit_text_revision(
            db,
            draft_id=draft.id,
            expected_image_revision=image_revision,
            admin_telegram_user_id=7001,
            draft_text=draft.draft_text.replace(
                "Новый материал о силовых тренировках требует редакторской проверки",
                "Проверенный материал о силовых тренировках",
            ),
        )
        assert edited.status == "queued"
        assert snapshot.status == "cancelled"
        assert snapshot.publication_text == draft.draft_text
        assert snapshot.renderer_version == "news-publication-plain-v0"
        assert snapshot.transport == "photo"
        assert snapshot.parse_mode is None
        assert snapshot.link_preview_disabled is False
        latest = (
            db.query(NewsDraftRevision)
            .filter(NewsDraftRevision.cluster_id == cluster.id)
            .order_by(NewsDraftRevision.revision.desc())
            .first()
        )
        assert latest is not None
        assert latest.evidence_metadata["editorial_fields"]["headline"] == (
            "Проверенный материал о силовых тренировках"
        )
        assert latest.evidence_metadata["trusted_source_url"] == (
            "https://publishing-journal.example/publication-1"
        )


def test_no_image_snapshot_and_daily_cap_are_checked_when_claimed(monkeypatch) -> None:
    monkeypatch.setattr(settings, "news_publication_enabled", True)
    monkeypatch.setattr(settings, "news_channel_id", -1001234567890)
    monkeypatch.setattr(settings, "news_channel_username", "yfc_test_news")
    monkeypatch.setattr(settings, "news_daily_publication_limit", 1)
    snapshot_ids: list[str] = []
    for index in range(2):
        cluster_id = _source_and_candidate(external_id=f"daily-{index}")
        draft_id, _ = _draft(cluster_id)
        with get_session_context() as db:
            cluster = db.get(NewsCluster, cluster_id)
            draft = db.get(NewsDraftRevision, draft_id)
            assert cluster is not None and draft is not None
            draft.warnings = []
            enqueue_review_deliveries(db, {7001})
            assert cluster.current_image_revision == 0
            approved = approve_publication(
                db,
                draft_id=draft.id,
                expected_image_revision=0,
                admin_telegram_user_id=7001,
                mode="immediate",
            )
            assert approved.status == "queued"
            assert approved.snapshot_id is not None
            snapshot_ids.append(approved.snapshot_id)
    with get_session_context() as db:
        first_claim = claim_due_publications(db, limit=1)
        assert len(first_claim) == 1
        claimed_id = first_claim[0]
        assert claimed_id in snapshot_ids
        payload = publication_payload(db, claimed_id)
        assert payload is not None
        assert payload.renderer_version == "news-publication-plain-v0"
        assert payload.transport == "message"
        assert payload.parse_mode is None
        assert payload.link_preview_disabled is False
    with get_session_context() as db:
        second_claim = claim_due_publications(db, limit=5)
        assert second_claim == []
        rejected_id = next(value for value in snapshot_ids if value != claimed_id)
        second = db.get(NewsPublicationSnapshot, rejected_id)
        assert second is not None
        assert second.status == "failed"
        assert second.last_error_code == "daily_cap_reached"


def test_channel_preflight_and_plain_telegram_publication(monkeypatch) -> None:
    monkeypatch.setattr(settings, "news_publication_enabled", True)
    monkeypatch.setattr(settings, "news_channel_id", -1001234567890)
    monkeypatch.setattr(settings, "telegram_bot_token", "bot-token")
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/getMe"):
            return httpx.Response(200, json={"ok": True, "result": {"id": 44}})
        if request.url.path.endswith("/getChatMember"):
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": {"status": "administrator", "can_post_messages": True},
                },
            )
        return httpx.Response(
            200,
            json={"ok": True, "result": {"message_id": 91, "date": 1_787_600_000}},
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            assert await check_news_channel_rights(client) is True
            result = await send_telegram_publication(
                client,
                -1001234567890,
                "Источник: https://example.test?a=1&b=<safe>",
                None,
            )
            assert result.message_id == 91
            html_result = await send_telegram_publication(
                client,
                -1001234567890,
                "<b>Проверенный заголовок</b>",
                None,
                parse_mode="HTML",
                link_preview_disabled=True,
            )
            assert html_result.message_id == 91

    asyncio.run(exercise())
    sent = requests[-2]
    assert sent.url.path.endswith("/sendMessage")
    body = sent.content.decode()
    assert "parse_mode" not in body
    assert "<safe>" in body
    html_body = requests[-1].content.decode()
    assert '"parse_mode":"HTML"' in html_body
    assert '"link_preview_options":{"is_disabled":true}' in html_body

    async def malformed_success() -> None:
        transport = httpx.MockTransport(
            lambda _: httpx.Response(200, json={"ok": False, "result": {}})
        )
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(TelegramPublicationError) as raised:
                await send_telegram_publication(
                    client,
                    -1001234567890,
                    "Источник: https://example.test",
                    None,
                )
            assert raised.value.uncertain is True

    asyncio.run(malformed_success())


def test_post_edit_and_delete_are_owner_only_and_audited(monkeypatch) -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    monkeypatch.setattr(settings, "news_publication_enabled", True)
    monkeypatch.setattr(settings, "news_channel_id", -1001234567890)
    monkeypatch.setattr(settings, "news_channel_username", "yfc_test_news")
    monkeypatch.setattr(settings, "admin_telegram_user_ids", "7001")
    with get_session_context() as db:
        cluster = db.get(NewsCluster, cluster_id)
        draft = db.get(NewsDraftRevision, draft_id)
        assert cluster is not None and draft is not None
        draft.warnings = []
        enqueue_review_deliveries(db, {7001})
        invalid_schedule = approve_publication(
            db,
            draft_id=draft.id,
            expected_image_revision=0,
            admin_telegram_user_id=7001,
            mode="scheduled",
            scheduled_local=utcnow(),
            timezone_name="Europe/Moscow",
        )
        assert invalid_schedule.status == "schedule_invalid"
        approved = approve_publication(
            db,
            draft_id=draft.id,
            expected_image_revision=0,
            admin_telegram_user_id=7001,
            mode="immediate",
        )
        assert approved.snapshot_id is not None
        assert claim_due_publications(db) == [approved.snapshot_id]
        mark_publication_succeeded(
            db,
            approved.snapshot_id,
            message_id=77,
            message_date=utcnow(),
        )
        snapshot_id = approved.snapshot_id

    edited_text = (
        "ЗАГОЛОВОК\nПроверенная редакционная версия\n\n"
        "КРАТКО\nРедактор уточнил контекст новости, ограничения и границы применимости.\n\n"
        "ПОЧЕМУ ЭТО ВАЖНО\nКонтекст влияет на интерпретацию результата.\n\n"
        "ИСТОЧНИК\nPublishing Journal, 2026-08-25\n"
        "https://publishing-journal.example/publication-1"
    )

    async def exercise() -> None:
        malformed_transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"ok": False}))
        async with httpx.AsyncClient(transport=malformed_transport) as malformed_client:
            with get_session_context() as db:
                malformed = await manage_published_post(
                    db,
                    snapshot_id=snapshot_id,
                    admin_telegram_user_id=7001,
                    action="edit",
                    text=edited_text,
                    client=malformed_client,
                )
                assert malformed.status == "unavailable"
        transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"ok": True}))
        async with httpx.AsyncClient(transport=transport) as client:
            with get_session_context() as db:
                forbidden = await manage_published_post(
                    db,
                    snapshot_id=snapshot_id,
                    admin_telegram_user_id=7999,
                    action="edit",
                    text=edited_text,
                    client=client,
                )
                assert forbidden.status == "unavailable"
            with get_session_context() as db:
                edited = await manage_published_post(
                    db,
                    snapshot_id=snapshot_id,
                    admin_telegram_user_id=7001,
                    action="edit",
                    text=edited_text,
                    client=client,
                )
                assert edited.status == "updated"
            with get_session_context() as db:
                deleted = await manage_published_post(
                    db,
                    snapshot_id=snapshot_id,
                    admin_telegram_user_id=7001,
                    action="delete",
                    text=None,
                    client=client,
                )
                assert deleted.status == "deleted"

    asyncio.run(exercise())
    with get_session_context() as db:
        snapshot = db.get(NewsPublicationSnapshot, snapshot_id)
        assert snapshot is not None
        assert snapshot.telegram_edited_at is not None
        assert snapshot.telegram_deleted_at is not None
        assert snapshot.post_edit_content_hash is not None
        actions = {
            row.action
            for row in db.query(AuditEvent).filter(AuditEvent.resource_id == snapshot_id).all()
        }
        assert {"news.post_edit", "news.post_delete"}.issubset(actions)


def test_uncertain_send_never_retries_until_owner_reconciles(monkeypatch) -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    monkeypatch.setattr(settings, "news_publication_enabled", True)
    monkeypatch.setattr(settings, "news_channel_id", -1001234567890)
    monkeypatch.setattr(settings, "news_channel_username", "yfc_test_news")
    monkeypatch.setattr(settings, "admin_telegram_user_ids", "7001")
    with get_session_context() as db:
        cluster = db.get(NewsCluster, cluster_id)
        draft = db.get(NewsDraftRevision, draft_id)
        assert cluster is not None and draft is not None
        draft.warnings = []
        enqueue_review_deliveries(db, {7001})
        approved = approve_publication(
            db,
            draft_id=draft.id,
            expected_image_revision=0,
            admin_telegram_user_id=7001,
            mode="immediate",
        )
        assert approved.snapshot_id is not None
        assert claim_due_publications(db) == [approved.snapshot_id]
        mark_publication_failed(
            db,
            approved.snapshot_id,
            error_code="telegram_send_timeout",
            uncertain=True,
        )
        assert claim_due_publications(db) == []
        assert retry_uncertain_publication(
            db,
            snapshot_id=approved.snapshot_id,
            admin_telegram_user_id=7001,
        )
        assert claim_due_publications(db) == [approved.snapshot_id]
        mark_publication_failed(
            db,
            approved.snapshot_id,
            error_code="telegram_send_timeout",
            uncertain=True,
        )
        assert reconcile_uncertain_publication(
            db,
            snapshot_id=approved.snapshot_id,
            admin_telegram_user_id=7001,
            channel_message_id=501,
        )
        snapshot = db.get(NewsPublicationSnapshot, approved.snapshot_id)
        assert snapshot is not None
        assert snapshot.status == "published"
        assert snapshot.telegram_permalink == "https://t.me/yfc_test_news/501"


def test_immediate_daily_cap_date_is_recomputed_at_claim_time(monkeypatch) -> None:
    cluster_id = _source_and_candidate()
    draft_id, _ = _draft(cluster_id)
    monkeypatch.setattr(settings, "news_publication_enabled", True)
    monkeypatch.setattr(settings, "news_channel_id", -1001234567890)
    monkeypatch.setattr(settings, "news_channel_username", "yfc_test_news")
    with get_session_context() as db:
        cluster = db.get(NewsCluster, cluster_id)
        draft = db.get(NewsDraftRevision, draft_id)
        assert cluster is not None and draft is not None
        draft.warnings = []
        enqueue_review_deliveries(db, {7001})
        approved = approve_publication(
            db,
            draft_id=draft.id,
            expected_image_revision=0,
            admin_telegram_user_id=7001,
            mode="immediate",
        )
        assert approved.snapshot_id is not None
        snapshot = db.get(NewsPublicationSnapshot, approved.snapshot_id)
        assert snapshot is not None
        fixed_now = utcnow() + timedelta(days=1)
        snapshot.next_attempt_at = fixed_now - timedelta(seconds=1)
        snapshot.publication_local_date = (fixed_now - timedelta(days=2)).date()
        monkeypatch.setattr(news_publication, "utcnow", lambda: fixed_now)
        assert claim_due_publications(db) == [approved.snapshot_id]
        expected_date = fixed_now.replace(tzinfo=UTC).astimezone(ZoneInfo(snapshot.timezone)).date()
        assert snapshot.publication_local_date == expected_date
