from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Literal

import httpx
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.news import (
    NewsDraftRevision,
    NewsImageRevision,
    NewsPublicationSnapshot,
)
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.news_content import parse_editorial_content
from fitminiapp_api.services.news_ingestion import utcnow
from fitminiapp_api.services.news_publication import compose_editorial_artifact

logger = logging.getLogger(__name__)

PostAction = Literal["edit", "delete"]


@dataclass(frozen=True)
class PostActionResult:
    status: Literal["updated", "deleted", "stale", "unavailable", "invalid"]


async def manage_published_post(
    db: Session,
    *,
    snapshot_id: str,
    admin_telegram_user_id: int,
    action: PostAction,
    text: str | None,
    client: httpx.AsyncClient,
) -> PostActionResult:
    if admin_telegram_user_id not in settings.admin_telegram_id_set:
        return PostActionResult(status="unavailable")
    row = db.query(NewsPublicationSnapshot).filter_by(id=snapshot_id).with_for_update().first()
    if (
        row is None
        or row.status != "published"
        or row.telegram_message_id is None
        or row.target_channel_id != settings.news_channel_id
    ):
        return PostActionResult(status="stale")
    if action == "delete" and row.telegram_deleted_at is not None:
        return PostActionResult(status="deleted")
    endpoint: str
    payload: dict[str, object]
    if action == "edit":
        clean_text = (text or "").strip()
        content = parse_editorial_content(clean_text)
        draft = db.get(NewsDraftRevision, row.text_revision_id)
        image = (
            db.get(NewsImageRevision, row.image_revision_id)
            if row.image_revision_id is not None
            else None
        )
        if content is None or draft is None:
            return PostActionResult(status="invalid")
        trusted_source_url = str(draft.evidence_metadata.get("trusted_source_url", ""))
        composition = compose_editorial_artifact(
            content,
            image,
            trusted_source_url=trusted_source_url,
        )
        if composition.artifact is None:
            return PostActionResult(status="invalid")
        artifact = composition.artifact
        clean_text = artifact.text
        endpoint = "editMessageCaption" if row.image_revision_id is not None else "editMessageText"
        payload = {
            "chat_id": row.target_channel_id,
            "message_id": row.telegram_message_id,
            "caption" if row.image_revision_id is not None else "text": clean_text,
            "parse_mode": artifact.parse_mode,
        }
        if row.image_revision_id is None:
            payload["link_preview_options"] = {"is_disabled": True}
    else:
        clean_text = ""
        endpoint = "deleteMessage"
        payload = {"chat_id": row.target_channel_id, "message_id": row.telegram_message_id}
    try:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/{endpoint}",
            json=payload,
        )
    except httpx.HTTPError:
        return PostActionResult(status="unavailable")
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = None
    if (
        not response.is_success
        or not isinstance(response_payload, dict)
        or response_payload.get("ok") is not True
    ):
        logger.error(
            "news_post_management_failed",
            extra={
                "pipeline_stage": "post_management",
                "outcome": action,
                "telegram_status": response.status_code,
            },
        )
        return PostActionResult(status="unavailable")
    now = utcnow()
    if action == "edit":
        row.telegram_edited_at = now
        row.post_edit_content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        result_status: Literal["updated", "deleted"] = "updated"
    else:
        row.telegram_deleted_at = now
        result_status = "deleted"
    record_audit_event(
        db,
        action=f"news.post_{action}",
        resource_type="news_publication_snapshot",
        resource_id=row.id,
        details={"message_id": row.telegram_message_id},
    )
    return PostActionResult(status=result_status)
