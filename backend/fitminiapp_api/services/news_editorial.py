from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.news import (
    NewsCluster,
    NewsDraftRevision,
    NewsEditorialAction,
    NewsItem,
    NewsReviewDelivery,
    NewsStateTransition,
)
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.news_ingestion import utcnow
from fitminiapp_api.services.news_state import transition_news_cluster

EditorialAction = Literal["skip", "defer", "regenerate", "accept_for_design"]
type ModerationStatus = Literal[
    "accepted",
    "queued",
    "deferred",
    "already_processed",
    "stale",
    "limit_reached",
    "unavailable",
]
TERMINAL_CLUSTER_STATUSES = {"rejected", "accepted_for_design", "rejected_by_rules"}
MAX_REVIEW_MESSAGE_CHARS = 4000


@dataclass(frozen=True)
class ModerationResult:
    status: ModerationStatus
    cluster_status: str | None = None


def editorial_actor_ref(telegram_user_id: int) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        f"news-admin:{telegram_user_id}".encode("ascii"),
        hashlib.sha256,
    ).hexdigest()[:24]


def callback_data(action: EditorialAction, draft_id: str) -> str:
    code = {
        "skip": "s",
        "defer": "d",
        "regenerate": "r",
        "accept_for_design": "a",
    }[action]
    value = f"news:{code}:{draft_id}"
    if len(value.encode("utf-8")) > 64:
        raise ValueError("callback_data_too_long")
    return value


def latest_draft(db: Session, cluster: NewsCluster) -> NewsDraftRevision | None:
    if cluster.latest_draft_revision < 1:
        return None
    return (
        db.query(NewsDraftRevision)
        .filter(
            NewsDraftRevision.cluster_id == cluster.id,
            NewsDraftRevision.revision == cluster.latest_draft_revision,
        )
        .first()
    )


def _cancel_pending_deliveries(db: Session, draft_id: str) -> None:
    db.flush()
    db.query(NewsReviewDelivery).filter(
        NewsReviewDelivery.draft_id == draft_id,
        NewsReviewDelivery.status.in_({"queued", "processing"}),
    ).update(
        {
            NewsReviewDelivery.status: "cancelled",
            NewsReviewDelivery.processing_started_at: None,
        },
        synchronize_session=False,
    )


def moderate_draft(
    db: Session,
    *,
    draft_id: str,
    admin_telegram_user_id: int,
    action: EditorialAction,
) -> ModerationResult:
    draft = db.get(NewsDraftRevision, draft_id)
    if draft is None:
        return ModerationResult(status="unavailable")
    cluster = (
        db.query(NewsCluster).filter(NewsCluster.id == draft.cluster_id).with_for_update().first()
    )
    if cluster is None:
        return ModerationResult(status="unavailable")
    actor_ref = editorial_actor_ref(admin_telegram_user_id)
    prior = (
        db.query(NewsEditorialAction)
        .filter(
            NewsEditorialAction.draft_id == draft.id,
            NewsEditorialAction.actor_ref == actor_ref,
            NewsEditorialAction.action == action,
        )
        .first()
    )
    if prior is not None:
        return ModerationResult(status="already_processed", cluster_status=cluster.status)
    if (
        draft.revision != cluster.latest_draft_revision
        or cluster.status in TERMINAL_CLUSTER_STATUSES
        or cluster.status != "awaiting_review"
    ):
        return ModerationResult(status="stale", cluster_status=cluster.status)

    result_status: ModerationStatus
    outcome = "applied"
    if action == "skip":
        transition_news_cluster(
            db, cluster, "rejected", reason_code="owner_skip", actor_ref=actor_ref
        )
        result_status = "accepted"
    elif action == "accept_for_design":
        transition_news_cluster(
            db,
            cluster,
            "accepted_for_design",
            reason_code="owner_accept_for_design",
            actor_ref=actor_ref,
        )
        result_status = "accepted"
    elif action == "defer":
        transition_news_cluster(
            db, cluster, "deferred", reason_code="owner_defer", actor_ref=actor_ref
        )
        cluster.deferred_until = utcnow() + timedelta(hours=settings.news_defer_hours)
        cluster.delivery_round += 1
        result_status = "deferred"
    else:
        if cluster.generation_attempt_count > settings.news_max_regenerations:
            result_status = "limit_reached"
            outcome = "limit_reached"
        else:
            transition_news_cluster(
                db,
                cluster,
                "candidate",
                reason_code="owner_regenerate",
                actor_ref=actor_ref,
            )
            cluster.deferred_until = None
            result_status = "queued"
    db.add(
        NewsEditorialAction(
            cluster_id=cluster.id,
            draft_id=draft.id,
            actor_ref=actor_ref,
            action=action,
            outcome=outcome,
        )
    )
    if outcome == "applied":
        _cancel_pending_deliveries(db, draft.id)
    record_audit_event(
        db,
        action=f"news.editorial_{action}",
        resource_type="news_cluster",
        resource_id=cluster.id,
        details={"outcome": outcome, "topic": cluster.topic, "revision": draft.revision},
    )
    return ModerationResult(status=result_status, cluster_status=cluster.status)


def enqueue_review_deliveries(db: Session, admin_telegram_user_ids: set[int]) -> int:
    now = utcnow()
    deferred = (
        db.query(NewsCluster)
        .filter(
            NewsCluster.status == "deferred",
            NewsCluster.deferred_until.is_not(None),
            NewsCluster.deferred_until <= now,
        )
        .all()
    )
    for cluster in deferred:
        transition_news_cluster(
            db,
            cluster,
            "draft_ready",
            reason_code="defer_period_elapsed",
        )
        cluster.deferred_until = None
    db.flush()
    clusters = db.query(NewsCluster).filter(NewsCluster.status == "draft_ready").all()
    created = 0
    for cluster in clusters:
        draft = latest_draft(db, cluster)
        if draft is None:
            continue
        for telegram_user_id in sorted(admin_telegram_user_ids):
            recipient_ref = editorial_actor_ref(telegram_user_id)
            existing = (
                db.query(NewsReviewDelivery)
                .filter(
                    NewsReviewDelivery.draft_id == draft.id,
                    NewsReviewDelivery.recipient_ref == recipient_ref,
                    NewsReviewDelivery.delivery_round == cluster.delivery_round,
                )
                .first()
            )
            if existing is None:
                db.add(
                    NewsReviewDelivery(
                        draft_id=draft.id,
                        recipient_ref=recipient_ref,
                        delivery_round=cluster.delivery_round,
                        status="queued",
                        next_attempt_at=now,
                    )
                )
                created += 1
        if admin_telegram_user_ids:
            transition_news_cluster(
                db,
                cluster,
                "awaiting_review",
                reason_code="owner_delivery_queued",
            )
    db.flush()
    return created


def review_message(db: Session, draft: NewsDraftRevision) -> tuple[str, str, dict]:
    cluster = db.get(NewsCluster, draft.cluster_id)
    if cluster is None:
        raise ValueError("cluster_missing")
    primary = db.get(NewsItem, draft.primary_item_id)
    if primary is None or primary.id not in draft.evidence_item_ids:
        raise ValueError("primary_source_missing")
    metadata = draft.evidence_metadata
    warnings = ", ".join(draft.warnings) if draft.warnings else "нет автоматических флагов"
    score_reasons = ", ".join(metadata.get("score_reasons", [])[:6])
    supporting_count = metadata.get("supporting_source_count", 0)
    if not isinstance(supporting_count, int):
        supporting_count = 0
    prefix = (
        f"Редакционный черновик · revision {draft.revision}\n"
        f"Topic: {metadata.get('topic', 'other')} · score {metadata.get('score', 0)}/100 "
        f"({metadata.get('score_version', 'unknown')})\n"
        f"Причины: {score_reasons}\n"
        f"Supporting sources: {max(0, supporting_count)}\n"
        f"Warnings: {warnings}\n\n"
    )
    message = prefix + draft.draft_text
    if len(message) > MAX_REVIEW_MESSAGE_CHARS:
        message = (
            message[: MAX_REVIEW_MESSAGE_CHARS - 40].rstrip()
            + "\n\n[черновик сокращён для Telegram]"
        )
    markup = {
        "inline_keyboard": [
            [{"text": "Открыть источник", "url": primary.primary_url or primary.canonical_url}],
            [
                {"text": "Пропустить", "callback_data": callback_data("skip", draft.id)},
                {"text": "Отложить", "callback_data": callback_data("defer", draft.id)},
            ],
            [
                {
                    "text": "Перегенерировать текст",
                    "callback_data": callback_data("regenerate", draft.id),
                }
            ],
            [
                {
                    "text": "Передать к оформлению",
                    "callback_data": callback_data("accept_for_design", draft.id),
                }
            ],
        ]
    }
    return message, primary.primary_url or primary.canonical_url, markup


def prune_news_editorial(db: Session, *, retention_days: int, batch_size: int = 200) -> int:
    cutoff = utcnow() - timedelta(days=retention_days)
    cluster_ids = [
        row.id
        for row in db.query(NewsCluster.id)
        .filter(
            NewsCluster.status.in_(TERMINAL_CLUSTER_STATUSES),
            NewsCluster.updated_at < cutoff,
        )
        .order_by(NewsCluster.updated_at.asc(), NewsCluster.id.asc())
        .limit(batch_size)
        .all()
    ]
    if cluster_ids:
        draft_ids = [
            row.id
            for row in db.query(NewsDraftRevision.id)
            .filter(NewsDraftRevision.cluster_id.in_(cluster_ids))
            .all()
        ]
        if draft_ids:
            db.query(NewsReviewDelivery).filter(NewsReviewDelivery.draft_id.in_(draft_ids)).delete(
                synchronize_session=False
            )
            db.query(NewsEditorialAction).filter(
                NewsEditorialAction.draft_id.in_(draft_ids)
            ).delete(synchronize_session=False)
            db.query(NewsDraftRevision).filter(NewsDraftRevision.id.in_(draft_ids)).delete(
                synchronize_session=False
            )
        db.query(NewsStateTransition).filter(
            NewsStateTransition.cluster_id.in_(cluster_ids)
        ).delete(synchronize_session=False)
        db.query(NewsItem).filter(NewsItem.cluster_id.in_(cluster_ids)).delete(
            synchronize_session=False
        )
        db.query(NewsCluster).filter(NewsCluster.id.in_(cluster_ids)).delete(
            synchronize_session=False
        )
    return len(cluster_ids)
