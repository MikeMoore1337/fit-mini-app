from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from time import monotonic

import httpx

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.news import (
    NewsCluster,
    NewsDraftRevision,
    NewsReviewDelivery,
    NewsSource,
)
from fitminiapp_api.services.news_drafts import create_draft_revision
from fitminiapp_api.services.news_editorial import (
    editorial_actor_ref,
    enqueue_review_deliveries,
    prune_news_editorial,
    review_message,
)
from fitminiapp_api.services.news_ingestion import (
    SafeNewsFetcher,
    SourceFetchError,
    ingest_items,
    utcnow,
)
from fitminiapp_api.services.notifications import safe_delivery_error

logger = logging.getLogger(__name__)
MAX_GENERATIONS_PER_CYCLE = 10
MAX_DELIVERIES_PER_CYCLE = 20
MAX_DELIVERY_ATTEMPTS = 5
PROCESSING_TTL = timedelta(minutes=10)

SendMessage = Callable[
    [httpx.AsyncClient, int, str],
    Awaitable[int | None],
]


def _source_ref(source_id: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        f"news-source:{source_id}".encode(),
        hashlib.sha256,
    ).hexdigest()[:16]


async def _fetch_source(
    source_id: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> dict[str, int]:
    started = monotonic()
    async with semaphore:
        with get_session_context() as db:
            source = db.get(NewsSource, source_id)
            if source is None or not source.enabled:
                return {"new": 0, "duplicate": 0, "candidate": 0}
            fetcher = SafeNewsFetcher(client, max_bytes=settings.news_source_max_bytes)
            try:
                result = await fetcher.fetch(source)
            except SourceFetchError as exc:
                current = utcnow()
                source.last_error_code = exc.code
                source.last_error_at = current
                source.consecutive_error_count += 1
                backoff_minutes = min(
                    source.fetch_interval_minutes,
                    5 * (2 ** min(source.consecutive_error_count - 1, 6)),
                )
                source.next_fetch_at = current + timedelta(minutes=backoff_minutes)
                logger.error(
                    "news_source_fetch_failed",
                    extra={
                        "source_ref": _source_ref(source.id),
                        "reason": exc.code,
                        "pipeline_stage": "fetch",
                        "latency_ms": round((monotonic() - started) * 1000, 2),
                    },
                )
                return {"new": 0, "duplicate": 0, "candidate": 0}
            current = utcnow()
            source.last_success_at = current
            source.last_error_code = None
            source.last_error_at = None
            source.consecutive_error_count = 0
            source.next_fetch_at = current + timedelta(minutes=source.fetch_interval_minutes)
            if result.status == "not_modified":
                counts = {"new": 0, "duplicate": 0, "candidate": 0}
            else:
                source.etag = result.etag
                source.last_modified = result.last_modified
                counts = ingest_items(
                    db,
                    source,
                    result.items,
                    candidate_threshold=settings.news_candidate_score_threshold,
                    fetched_at=current,
                )
            logger.info(
                "news_source_fetch_succeeded",
                extra={
                    "source_ref": _source_ref(source.id),
                    "outcome": result.status,
                    "pipeline_stage": "fetch",
                    "items_count": counts.get("new", 0),
                    "duplicate_count": counts.get("duplicate", 0),
                    "candidate_count": counts.get("candidate", 0),
                    "latency_ms": round((monotonic() - started) * 1000, 2),
                },
            )
            return counts


async def fetch_due_sources(client: httpx.AsyncClient) -> dict[str, int]:
    current = utcnow()
    with get_session_context() as db:
        source_ids = [
            row.id
            for row in db.query(NewsSource.id)
            .filter(
                NewsSource.enabled.is_(True),
                (NewsSource.next_fetch_at.is_(None) | (NewsSource.next_fetch_at <= current)),
            )
            .order_by(NewsSource.next_fetch_at.asc(), NewsSource.id.asc())
            .limit(40)
            .all()
        ]
    semaphore = asyncio.Semaphore(settings.news_fetch_concurrency)
    results = await asyncio.gather(
        *(_fetch_source(source_id, client, semaphore) for source_id in source_ids)
    )
    return {
        key: sum(item.get(key, 0) for item in results) for key in ("new", "duplicate", "candidate")
    }


async def generate_candidate_drafts(client: httpx.AsyncClient) -> int:
    with get_session_context() as db:
        generated_since = utcnow() - timedelta(days=1)
        generated_last_day = (
            db.query(NewsDraftRevision.id)
            .filter(NewsDraftRevision.created_at >= generated_since)
            .count()
        )
        remaining_daily = max(0, settings.news_daily_draft_limit - generated_last_day)
        if remaining_daily == 0:
            return 0
        cluster_ids = [
            row.id
            for row in db.query(NewsCluster.id)
            .filter(NewsCluster.status == "candidate")
            .order_by(NewsCluster.score.desc(), NewsCluster.created_at.asc())
            .limit(min(MAX_GENERATIONS_PER_CYCLE, remaining_daily))
            .all()
        ]
    generated = 0
    for cluster_id in cluster_ids:
        started = monotonic()
        with get_session_context() as db:
            cluster = (
                db.query(NewsCluster)
                .filter(NewsCluster.id == cluster_id, NewsCluster.status == "candidate")
                .with_for_update()
                .first()
            )
            if cluster is None:
                continue
            try:
                draft = await create_draft_revision(db, cluster, client=client)
            except Exception as exc:
                logger.error(
                    "news_draft_generation_failed",
                    extra={
                        "pipeline_stage": "generation",
                        "reason": getattr(exc, "code", type(exc).__name__),
                        "latency_ms": round((monotonic() - started) * 1000, 2),
                    },
                )
                continue
            generated += 1
            logger.info(
                "news_draft_generation_succeeded",
                extra={
                    "pipeline_stage": "generation",
                    "provider": draft.provider,
                    "outcome": "fallback" if draft.provider == "deterministic" else "generated",
                    "latency_ms": draft.generation_latency_ms,
                },
            )
    return generated


def _claim_deliveries() -> list[int]:
    now = utcnow()
    stale_before = now - PROCESSING_TTL
    with get_session_context() as db:
        db.query(NewsReviewDelivery).filter(
            NewsReviewDelivery.status == "processing",
            NewsReviewDelivery.processing_started_at < stale_before,
        ).update(
            {
                NewsReviewDelivery.status: "queued",
                NewsReviewDelivery.processing_started_at: None,
                NewsReviewDelivery.next_attempt_at: now,
            },
            synchronize_session=False,
        )
        rows = (
            db.query(NewsReviewDelivery)
            .filter(
                NewsReviewDelivery.status == "queued",
                NewsReviewDelivery.next_attempt_at <= now,
            )
            .order_by(NewsReviewDelivery.next_attempt_at.asc(), NewsReviewDelivery.id.asc())
            .limit(MAX_DELIVERIES_PER_CYCLE)
            .with_for_update(skip_locked=True)
            .all()
        )
        result = []
        for row in rows:
            row.status = "processing"
            row.processing_started_at = now
            row.attempt_count += 1
            result.append(row.id)
        return result


async def deliver_review_queue(
    client: httpx.AsyncClient,
    send_message: Callable[..., Awaitable[int | None]],
) -> int:
    recipient_ids = {
        editorial_actor_ref(telegram_id): telegram_id
        for telegram_id in settings.admin_telegram_id_set
    }
    delivered = 0
    for delivery_id in _claim_deliveries():
        with get_session_context() as db:
            delivery = db.get(NewsReviewDelivery, delivery_id)
            if delivery is None or delivery.status != "processing":
                continue
            draft = db.get(NewsDraftRevision, delivery.draft_id)
            cluster = db.get(NewsCluster, draft.cluster_id) if draft is not None else None
            chat_id = recipient_ids.get(delivery.recipient_ref)
            if (
                draft is None
                or cluster is None
                or cluster.status != "awaiting_review"
                or draft.revision != cluster.latest_draft_revision
                or chat_id is None
            ):
                delivery.status = "cancelled"
                delivery.processing_started_at = None
                continue
            message, _, markup = review_message(db, draft)
            attempt_count = delivery.attempt_count
            queue_age = max(0, round((utcnow() - delivery.created_at).total_seconds()))
        try:
            message_id = await send_message(
                client,
                chat_id,
                message,
                reply_markup=markup,
            )
        except Exception as exc:
            error_code = safe_delivery_error(exc)
            with get_session_context() as db:
                delivery = db.get(NewsReviewDelivery, delivery_id)
                if delivery is None or delivery.status != "processing":
                    continue
                terminal_status = getattr(exc, "terminal_status", None)
                if terminal_status or delivery.attempt_count >= MAX_DELIVERY_ATTEMPTS:
                    delivery.status = "failed"
                else:
                    delivery.status = "queued"
                    delivery.next_attempt_at = utcnow() + timedelta(
                        minutes=min(60, 2**delivery.attempt_count)
                    )
                delivery.processing_started_at = None
                delivery.last_error_code = error_code
            logger.error(
                "news_review_delivery_failed",
                extra={
                    "pipeline_stage": "owner_delivery",
                    "delivery_error": error_code,
                    "attempt_count": attempt_count,
                    "queue_age_seconds": queue_age,
                },
            )
            continue
        with get_session_context() as db:
            delivery = db.get(NewsReviewDelivery, delivery_id)
            if delivery is None or delivery.status != "processing":
                continue
            delivery.status = "sent"
            delivery.sent_at = utcnow()
            delivery.telegram_message_id = message_id
            delivery.processing_started_at = None
            delivery.last_error_code = None
        delivered += 1
        logger.info(
            "news_review_delivery_succeeded",
            extra={
                "pipeline_stage": "owner_delivery",
                "outcome": "sent",
                "attempt_count": attempt_count,
                "queue_age_seconds": queue_age,
            },
        )
    return delivered


async def run_news_pipeline_once(
    *,
    send_message: Callable[..., Awaitable[int | None]],
    fetch_sources: bool,
) -> None:
    started = monotonic()
    with get_session_context() as db:
        prune_news_editorial(db, retention_days=settings.news_retention_days)
    timeout = httpx.Timeout(settings.news_source_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        counts = (
            await fetch_due_sources(client)
            if fetch_sources
            else {"new": 0, "duplicate": 0, "candidate": 0}
        )
        await generate_candidate_drafts(client)
        with get_session_context() as db:
            enqueue_review_deliveries(db, settings.admin_telegram_id_set)
        delivered = await deliver_review_queue(client, send_message)
    logger.info(
        "news_pipeline_cycle_completed",
        extra={
            "pipeline_stage": "cycle",
            "outcome": "completed",
            "items_count": counts["new"],
            "duplicate_count": counts["duplicate"],
            "candidate_count": counts["candidate"],
            "attempt_count": delivered,
            "latency_ms": round((monotonic() - started) * 1000, 2),
        },
    )
