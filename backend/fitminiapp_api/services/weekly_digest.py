from __future__ import annotations

import hashlib
import hmac
import html
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.models.news import (
    NewsDraftRevision,
    NewsPublicationSnapshot,
)
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User
from fitminiapp_api.models.weekly_digest import (
    WeeklyDigestDelivery,
    WeeklyDigestIssue,
    WeeklyDigestIssueItem,
    WeeklyDigestPreference,
)
from fitminiapp_api.services.audit import record_audit_event
from fitminiapp_api.services.news_content import editorial_content_from_metadata
from fitminiapp_api.services.news_ingestion import utcnow
from fitminiapp_api.services.notifications import quiet_hours_retry_at
from fitminiapp_api.services.telegram_auth import (
    get_or_insert_telegram_user,
    normalize_telegram_username,
)

DIGEST_SELECTION_VERSION = "weekly-digest-usefulness-diversity-v1"
DIGEST_RENDERER_VERSION = "weekly-digest-html-v1"
DIGEST_MESSAGE_LIMIT = 4096
DIGEST_PROCESSING_TTL = timedelta(minutes=10)
DIGEST_MAX_DELIVERY_ATTEMPTS = 5
DEFAULT_DIGEST_INTRO = "Полезные материалы недели — коротко и без лишнего."


@dataclass(frozen=True)
class DigestPreferenceView:
    enabled: bool
    consent_version: str | None
    subscribed_at: datetime | None


@dataclass(frozen=True)
class DigestItemView:
    position: int
    headline: str
    takeaway: str
    category: str
    channel_permalink: str
    requires_owner_review: bool


@dataclass(frozen=True)
class DigestIssueView:
    issue_id: str
    issue_key: str
    revision: int
    status: str
    rendered_text: str
    content_hash: str
    channel_url: str
    min_items: int
    scheduled_for_utc: datetime | None
    timezone: str
    items: tuple[DigestItemView, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class DigestActionResult:
    status: str
    issue: DigestIssueView | None = None


@dataclass(frozen=True)
class DigestDeliveryPayload:
    delivery_id: int
    issue_id: str
    chat_id: int
    text: str
    channel_url: str


@dataclass
class DigestRevisionItem:
    publication_snapshot_id: str
    headline: str
    takeaway: str
    category: str
    channel_permalink: str
    source_content_hash: str
    requires_owner_review: bool
    selection_reason: str
    position: int


def _actor_ref(telegram_user_id: int) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        f"weekly-digest:{telegram_user_id}".encode("ascii"),
        hashlib.sha256,
    ).hexdigest()[:24]


def _channel_url() -> str:
    username = settings.news_channel_username.strip().removeprefix("@").lower()
    return f"https://t.me/{username}" if username else ""


def _safe_channel_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(
        parsed.scheme == "https"
        and parsed.hostname == "t.me"
        and parsed.username is None
        and parsed.password is None
        and parsed.path.strip("/")
        and not parsed.query
        and not parsed.fragment
    )


def _telegram_character_count(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def _sentence_count(value: str) -> int:
    normalized = " ".join(value.split())
    if not normalized:
        return 0
    return len([part for part in re.split(r"(?<=[.!?])\s+", normalized) if part])


def _issue_window(now: datetime) -> tuple[str, date, date, datetime, datetime]:
    timezone = ZoneInfo(settings.news_publication_timezone)
    local_now = now.replace(tzinfo=UTC).astimezone(timezone)
    week_start = local_now.date() - timedelta(days=local_now.weekday())
    week_end = week_start + timedelta(days=6)
    local_start = datetime.combine(week_start, datetime.min.time(), tzinfo=timezone)
    local_end = local_start + timedelta(days=7)
    window_start = local_start.astimezone(UTC).replace(tzinfo=None)
    window_end = min(local_end.astimezone(UTC).replace(tzinfo=None), now)
    iso_year, iso_week, _ = week_start.isocalendar()
    return f"{iso_year}-W{iso_week:02d}", week_start, week_end, window_start, window_end


def _takeaway(draft: NewsDraftRevision) -> tuple[str, bool] | None:
    content = editorial_content_from_metadata(
        draft.evidence_metadata,
        fallback_text=draft.draft_text,
    )
    if content is None:
        return None
    if content.why_it_matters and _sentence_count(content.why_it_matters) <= 2:
        return " ".join(content.why_it_matters.split()), False
    paragraphs = [
        " ".join(paragraph.split())
        for paragraph in re.split(r"\n\s*\n", content.summary)
        if paragraph.strip()
    ]
    if not paragraphs:
        return None
    first_paragraph = paragraphs[0]
    return first_paragraph, _sentence_count(first_paragraph) > 2


def _candidate_rows(
    db: Session,
    *,
    window_start: datetime,
    window_end: datetime,
) -> list[tuple[NewsPublicationSnapshot, NewsDraftRevision]]:
    rows = (
        db.query(NewsPublicationSnapshot, NewsDraftRevision)
        .join(NewsDraftRevision, NewsDraftRevision.id == NewsPublicationSnapshot.text_revision_id)
        .filter(
            NewsPublicationSnapshot.status == "published",
            NewsPublicationSnapshot.published_at >= window_start,
            NewsPublicationSnapshot.published_at < window_end,
            NewsPublicationSnapshot.telegram_deleted_at.is_(None),
            NewsPublicationSnapshot.telegram_permalink.is_not(None),
        )
        .order_by(NewsPublicationSnapshot.published_at.desc(), NewsPublicationSnapshot.id.asc())
        .all()
    )
    immutable_rows = [(snapshot, draft) for snapshot, draft in rows]
    immutable_rows.sort(
        key=lambda row: _draft_selection_metadata(row[1])[0],
        reverse=True,
    )
    selected: list[tuple[NewsPublicationSnapshot, NewsDraftRevision]] = []
    seen_topics: set[str] = set()
    for snapshot, draft in immutable_rows:
        row = (snapshot, draft)
        topic = _draft_selection_metadata(draft)[1]
        if topic not in seen_topics:
            selected.append(row)
            seen_topics.add(topic)
            if len(selected) == 5:
                return selected
    for snapshot, draft in immutable_rows:
        row = (snapshot, draft)
        if row not in selected:
            selected.append(row)
            if len(selected) == 5:
                break
    return selected


def _draft_selection_metadata(draft: NewsDraftRevision) -> tuple[int, str, str]:
    metadata = draft.evidence_metadata if isinstance(draft.evidence_metadata, dict) else {}
    raw_score = metadata.get("score")
    score = raw_score if isinstance(raw_score, int) and not isinstance(raw_score, bool) else 0
    raw_topic = metadata.get("topic")
    topic = raw_topic if isinstance(raw_topic, str) and 1 <= len(raw_topic) <= 48 else "other"
    raw_version = metadata.get("score_version")
    version = (
        raw_version if isinstance(raw_version, str) and 1 <= len(raw_version) <= 32 else "unknown"
    )
    return max(0, min(100, score)), topic, version


def _render_digest(
    *,
    week_start: date,
    week_end: date,
    intro: str,
    items: list[DigestItemView],
) -> tuple[str, str]:
    title = f"Еженедельный дайджест YFC · {week_start:%d.%m}–{week_end:%d.%m}"
    html_parts = [f"<b>{html.escape(title, quote=False)}</b>"]
    visible_parts = [title]
    clean_intro = " ".join(intro.split())
    if clean_intro:
        html_parts.append(html.escape(clean_intro, quote=False))
        visible_parts.append(clean_intro)
    for item in items:
        headline = " ".join(item.headline.split())
        takeaway = " ".join(item.takeaway.split())
        html_parts.append(
            f"<b>{item.position}. {html.escape(headline, quote=False)}</b>\n"
            f"{html.escape(takeaway, quote=False)}\n"
            f'<a href="{html.escape(item.channel_permalink, quote=True)}">Читать в канале</a>'
        )
        visible_parts.append(f"{item.position}. {headline}\n{takeaway}\nЧитать в канале")
    html_parts.append(
        "Дайджест можно отключить одним нажатием под сообщением. "
        "Это не изменит продуктовые уведомления."
    )
    visible_parts.append(
        "Дайджест можно отключить одним нажатием под сообщением. "
        "Это не изменит продуктовые уведомления."
    )
    rendered = "\n\n".join(html_parts)
    visible = "\n\n".join(visible_parts)
    return rendered, visible


def _content_hash(rendered_text: str, channel_url: str, item_ids: list[str]) -> str:
    return hashlib.sha256(
        "\x00".join([rendered_text, channel_url, DIGEST_RENDERER_VERSION, *item_ids]).encode(
            "utf-8"
        )
    ).hexdigest()


def _issue_items(db: Session, issue_id: str) -> list[WeeklyDigestIssueItem]:
    return (
        db.query(WeeklyDigestIssueItem)
        .filter(WeeklyDigestIssueItem.issue_id == issue_id)
        .order_by(WeeklyDigestIssueItem.position.asc())
        .all()
    )


def _source_blockers(db: Session, items: list[WeeklyDigestIssueItem]) -> list[str]:
    blockers: list[str] = []
    for item in items:
        snapshot = db.get(NewsPublicationSnapshot, item.publication_snapshot_id)
        if (
            snapshot is None
            or snapshot.status != "published"
            or snapshot.telegram_deleted_at is not None
            or not snapshot.telegram_permalink
        ):
            blockers.append(f"item_{item.position}_unavailable")
            continue
        current_hash = snapshot.post_edit_content_hash or snapshot.content_hash
        if current_hash != item.source_content_hash:
            blockers.append(f"item_{item.position}_changed")
        if item.requires_owner_review:
            blockers.append(f"item_{item.position}_owner_review_required")
    return blockers


def _issue_blockers(
    db: Session,
    issue: WeeklyDigestIssue,
    items: list[WeeklyDigestIssueItem],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if len(items) < issue.min_items:
        blockers.append("insufficient_content")
    if len(items) > 5:
        blockers.append("too_many_items")
    if not _safe_channel_url(issue.channel_url):
        blockers.append("channel_link_unavailable")
    visible = re.sub(r"<[^>]+>", "", issue.rendered_text)
    if _telegram_character_count(visible) > DIGEST_MESSAGE_LIMIT:
        blockers.append("telegram_message_too_long")
    blockers.extend(_source_blockers(db, items))
    return tuple(dict.fromkeys(blockers))


def _issue_view(db: Session, issue: WeeklyDigestIssue) -> DigestIssueView:
    items = _issue_items(db, issue.id)
    return DigestIssueView(
        issue_id=issue.id,
        issue_key=issue.issue_key,
        revision=issue.revision,
        status=issue.status,
        rendered_text=issue.rendered_text,
        content_hash=issue.content_hash,
        channel_url=issue.channel_url,
        min_items=issue.min_items,
        scheduled_for_utc=issue.scheduled_for_utc,
        timezone=issue.timezone,
        items=tuple(
            DigestItemView(
                position=item.position,
                headline=item.headline,
                takeaway=item.takeaway,
                category=item.category,
                channel_permalink=item.channel_permalink,
                requires_owner_review=item.requires_owner_review,
            )
            for item in items
        ),
        blockers=_issue_blockers(db, issue, items),
    )


def _preference_user(
    db: Session,
    *,
    telegram_user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    create: bool,
) -> User | None:
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if user is None and create:
        user = get_or_insert_telegram_user(
            db,
            telegram_user_id=telegram_user_id,
            username=normalize_telegram_username(username),
            first_name=first_name,
            last_name=last_name,
            photo_url=None,
        )
    return user


def get_digest_preference(
    db: Session,
    *,
    telegram_user_id: int,
) -> DigestPreferenceView:
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    preference = (
        db.query(WeeklyDigestPreference).filter(WeeklyDigestPreference.user_id == user.id).first()
        if user is not None
        else None
    )
    return DigestPreferenceView(
        enabled=bool(
            preference
            and preference.weekly_news_digest_enabled
            and preference.consent_version == settings.weekly_digest_consent_version
        ),
        consent_version=preference.consent_version if preference else None,
        subscribed_at=preference.subscribed_at if preference else None,
    )


def set_digest_preference(
    db: Session,
    *,
    telegram_user_id: int,
    enabled: bool,
    presented_consent_version: str | None = None,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> DigestPreferenceView:
    if enabled and presented_consent_version != settings.weekly_digest_consent_version:
        raise ValueError("digest_consent_version_mismatch")
    user = _preference_user(
        db,
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        create=enabled,
    )
    if user is None:
        return DigestPreferenceView(enabled=False, consent_version=None, subscribed_at=None)
    db.query(User.id).filter(User.id == user.id).with_for_update().one()
    preference = (
        db.query(WeeklyDigestPreference)
        .filter(WeeklyDigestPreference.user_id == user.id)
        .with_for_update()
        .first()
    )
    now = utcnow()
    if preference is None and not enabled:
        return DigestPreferenceView(enabled=False, consent_version=None, subscribed_at=None)
    if preference is None:
        preference = WeeklyDigestPreference(user_id=user.id)
        db.add(preference)
        db.flush()
    changed = preference.weekly_news_digest_enabled != enabled
    consent_changed = enabled and preference.consent_version != presented_consent_version
    if enabled:
        preference.weekly_news_digest_enabled = True
        preference.telegram_chat_id = telegram_user_id
        preference.consent_version = presented_consent_version
        if changed or consent_changed:
            preference.subscribed_at = now
        preference.unsubscribed_at = None
        preference.disabled_reason = None
    else:
        preference.weekly_news_digest_enabled = False
        preference.unsubscribed_at = now
        preference.disabled_reason = "user_unsubscribed"
        db.query(WeeklyDigestDelivery).filter(
            WeeklyDigestDelivery.user_id == user.id,
            WeeklyDigestDelivery.status.in_({"queued", "processing"}),
        ).update(
            {
                WeeklyDigestDelivery.status: "cancelled",
                WeeklyDigestDelivery.next_attempt_at: None,
                WeeklyDigestDelivery.processing_started_at: None,
                WeeklyDigestDelivery.last_error_code: "user_unsubscribed",
            },
            synchronize_session=False,
        )
    if changed or consent_changed:
        record_audit_event(
            db,
            action="weekly_digest.subscribed" if enabled else "weekly_digest.unsubscribed",
            resource_type="weekly_digest_preference",
            actor_user_id=user.id,
            target_user_id=user.id,
            resource_id=str(preference.id),
            details={"consent_version": preference.consent_version},
        )
    db.flush()
    return DigestPreferenceView(
        enabled=preference.weekly_news_digest_enabled,
        consent_version=preference.consent_version,
        subscribed_at=preference.subscribed_at,
    )


def disable_digest_for_unlinked_telegram(db: Session, user_id: int) -> None:
    preference = (
        db.query(WeeklyDigestPreference)
        .filter(WeeklyDigestPreference.user_id == user_id)
        .with_for_update()
        .first()
    )
    if preference is None:
        return
    preference.weekly_news_digest_enabled = False
    preference.telegram_chat_id = None
    preference.unsubscribed_at = utcnow()
    preference.disabled_reason = "telegram_identity_unlinked"
    db.query(WeeklyDigestDelivery).filter(
        WeeklyDigestDelivery.user_id == user_id,
        WeeklyDigestDelivery.status.in_({"queued", "processing"}),
    ).update(
        {
            WeeklyDigestDelivery.status: "cancelled",
            WeeklyDigestDelivery.next_attempt_at: None,
            WeeklyDigestDelivery.processing_started_at: None,
            WeeklyDigestDelivery.last_error_code: "telegram_identity_unlinked",
        },
        synchronize_session=False,
    )


def create_digest_draft(
    db: Session,
    *,
    admin_telegram_user_id: int,
    min_items: int | None = None,
    now: datetime | None = None,
) -> DigestIssueView:
    if admin_telegram_user_id not in settings.admin_telegram_id_set:
        raise PermissionError("digest_admin_required")
    current = now or utcnow()
    issue_key, week_start, week_end, window_start, window_end = _issue_window(current)
    existing = (
        db.query(WeeklyDigestIssue)
        .filter(
            WeeklyDigestIssue.issue_key == issue_key,
            WeeklyDigestIssue.status.in_({"approved", "scheduled", "sending", "sent"}),
        )
        .first()
    )
    if existing is not None:
        return _issue_view(db, existing)
    old_drafts = (
        db.query(WeeklyDigestIssue)
        .filter(
            WeeklyDigestIssue.issue_key == issue_key,
            WeeklyDigestIssue.status == "draft",
        )
        .all()
    )
    for old in old_drafts:
        old.status = "superseded"
        old.superseded_at = current
    revision = (
        db.query(func.coalesce(func.max(WeeklyDigestIssue.revision), 0))
        .filter(WeeklyDigestIssue.issue_key == issue_key)
        .scalar()
        + 1
    )
    channel_url = _channel_url()
    candidate_rows = _candidate_rows(db, window_start=window_start, window_end=window_end)
    selected: list[
        tuple[NewsPublicationSnapshot, NewsDraftRevision, str, str, bool, int, str, str]
    ] = []
    for snapshot, draft in candidate_rows:
        takeaway = _takeaway(draft)
        content = editorial_content_from_metadata(
            draft.evidence_metadata,
            fallback_text=draft.draft_text,
        )
        if takeaway is None or content is None or not snapshot.telegram_permalink:
            continue
        score, topic, score_version = _draft_selection_metadata(draft)
        selected.append(
            (
                snapshot,
                draft,
                content.headline,
                takeaway[0],
                takeaway[1],
                score,
                topic,
                score_version,
            )
        )
    requested_min = min_items if min_items is not None else settings.weekly_digest_min_items
    items = [
        DigestItemView(
            position=index,
            headline=headline,
            takeaway=takeaway,
            category=topic,
            channel_permalink=str(snapshot.telegram_permalink),
            requires_owner_review=requires_review or snapshot.telegram_edited_at is not None,
        )
        for index, (
            snapshot,
            draft,
            headline,
            takeaway,
            requires_review,
            score,
            topic,
            score_version,
        ) in enumerate(
            selected,
            start=1,
        )
    ]
    rendered, visible = _render_digest(
        week_start=week_start,
        week_end=week_end,
        intro=DEFAULT_DIGEST_INTRO,
        items=items,
    )
    while items and _telegram_character_count(visible) > DIGEST_MESSAGE_LIMIT:
        items.pop()
        selected.pop()
        for index, item in enumerate(items, start=1):
            items[index - 1] = DigestItemView(
                position=index,
                headline=item.headline,
                takeaway=item.takeaway,
                category=item.category,
                channel_permalink=item.channel_permalink,
                requires_owner_review=item.requires_owner_review,
            )
        rendered, visible = _render_digest(
            week_start=week_start,
            week_end=week_end,
            intro=DEFAULT_DIGEST_INTRO,
            items=items,
        )
    issue = WeeklyDigestIssue(
        id=secrets.token_hex(16),
        issue_key=issue_key,
        revision=revision,
        week_start=week_start,
        week_end=week_end,
        window_start_utc=window_start,
        window_end_utc=window_end,
        status="draft",
        intro=DEFAULT_DIGEST_INTRO,
        item_count=len(items),
        min_items=requested_min,
        selection_version=DIGEST_SELECTION_VERSION,
        renderer_version=DIGEST_RENDERER_VERSION,
        parse_mode="HTML",
        rendered_text=rendered,
        channel_url=channel_url,
        content_hash=_content_hash(
            rendered,
            channel_url,
            [row[0].id for row in selected],
        ),
        timezone=settings.news_publication_timezone,
    )
    db.add(issue)
    db.flush()
    for item, (
        snapshot,
        _draft,
        _headline,
        _takeaway_text,
        _requires_review,
        score,
        topic,
        score_version,
    ) in zip(items, selected, strict=True):
        db.add(
            WeeklyDigestIssueItem(
                issue_id=issue.id,
                publication_snapshot_id=snapshot.id,
                position=item.position,
                headline=item.headline,
                takeaway=item.takeaway,
                category=item.category,
                channel_permalink=item.channel_permalink,
                source_content_hash=snapshot.post_edit_content_hash or snapshot.content_hash,
                requires_owner_review=item.requires_owner_review,
                selection_reason=(f"score={score};topic={topic};version={score_version}")[:160],
            )
        )
    db.flush()
    record_audit_event(
        db,
        action="weekly_digest.draft_created",
        resource_type="weekly_digest_issue",
        resource_id=issue.id,
        details={
            "issue_key": issue.issue_key,
            "revision": issue.revision,
            "item_count": len(items),
        },
    )
    return _issue_view(db, issue)


def _clone_issue(
    db: Session,
    issue: WeeklyDigestIssue,
    items: list[DigestRevisionItem],
    *,
    intro: str | None = None,
) -> WeeklyDigestIssue:
    now = utcnow()
    issue.status = "superseded"
    issue.superseded_at = now
    db.query(WeeklyDigestDelivery).filter(
        WeeklyDigestDelivery.issue_id == issue.id,
        WeeklyDigestDelivery.status.in_({"queued", "processing"}),
    ).update(
        {
            WeeklyDigestDelivery.status: "cancelled",
            WeeklyDigestDelivery.next_attempt_at: None,
            WeeklyDigestDelivery.processing_started_at: None,
            WeeklyDigestDelivery.last_error_code: "issue_superseded",
        },
        synchronize_session=False,
    )
    clean_intro = " ".join((intro if intro is not None else issue.intro).split())
    item_views = [
        DigestItemView(
            position=index,
            headline=item.headline,
            takeaway=item.takeaway,
            category=item.category,
            channel_permalink=item.channel_permalink,
            requires_owner_review=item.requires_owner_review,
        )
        for index, item in enumerate(items, start=1)
    ]
    rendered, _visible = _render_digest(
        week_start=issue.week_start,
        week_end=issue.week_end,
        intro=clean_intro,
        items=item_views,
    )
    clone = WeeklyDigestIssue(
        id=secrets.token_hex(16),
        issue_key=issue.issue_key,
        revision=issue.revision + 1,
        week_start=issue.week_start,
        week_end=issue.week_end,
        window_start_utc=issue.window_start_utc,
        window_end_utc=issue.window_end_utc,
        status="draft",
        intro=clean_intro,
        item_count=len(items),
        min_items=issue.min_items,
        selection_version=issue.selection_version,
        renderer_version=DIGEST_RENDERER_VERSION,
        parse_mode="HTML",
        rendered_text=rendered,
        channel_url=issue.channel_url,
        content_hash=_content_hash(
            rendered,
            issue.channel_url,
            [item.publication_snapshot_id for item in items],
        ),
        timezone=issue.timezone,
    )
    db.add(clone)
    db.flush()
    for index, item in enumerate(items, start=1):
        db.add(
            WeeklyDigestIssueItem(
                issue_id=clone.id,
                publication_snapshot_id=item.publication_snapshot_id,
                position=index,
                headline=item.headline,
                takeaway=item.takeaway,
                category=item.category,
                channel_permalink=item.channel_permalink,
                source_content_hash=item.source_content_hash,
                requires_owner_review=item.requires_owner_review,
                selection_reason=item.selection_reason,
            )
        )
    db.flush()
    return clone


def edit_digest_issue(
    db: Session,
    *,
    issue_id: str,
    admin_telegram_user_id: int,
    expected_content_hash: str,
    action: Literal["remove", "move_up", "move_down", "edit_intro", "edit_item"],
    position: int | None = None,
    text_value: str | None = None,
) -> DigestActionResult:
    if admin_telegram_user_id not in settings.admin_telegram_id_set:
        return DigestActionResult(status="forbidden")
    issue = db.query(WeeklyDigestIssue).filter_by(id=issue_id).with_for_update().first()
    if issue is None or issue.status not in {"draft", "approved", "scheduled"}:
        return DigestActionResult(status="stale")
    if not hmac.compare_digest(issue.content_hash[:16], expected_content_hash):
        return DigestActionResult(status="stale")
    items = [
        DigestRevisionItem(
            publication_snapshot_id=item.publication_snapshot_id,
            headline=item.headline,
            takeaway=item.takeaway,
            category=item.category,
            channel_permalink=item.channel_permalink,
            source_content_hash=item.source_content_hash,
            requires_owner_review=item.requires_owner_review,
            selection_reason=item.selection_reason,
            position=item.position,
        )
        for item in _issue_items(db, issue.id)
    ]
    target = next((item for item in items if item.position == position), None)
    intro: str | None = None
    if action == "remove":
        if target is None:
            return DigestActionResult(status="invalid")
        items.remove(target)
    elif action in {"move_up", "move_down"}:
        if target is None:
            return DigestActionResult(status="invalid")
        other_position = target.position + (-1 if action == "move_up" else 1)
        other = next((item for item in items if item.position == other_position), None)
        if other is None:
            return DigestActionResult(status="invalid")
        target_index = items.index(target)
        other_index = items.index(other)
        items[target_index], items[other_index] = items[other_index], items[target_index]
    elif action == "edit_intro":
        intro = " ".join((text_value or "").split())
        if not 1 <= len(intro) <= 500:
            return DigestActionResult(status="invalid")
    elif action == "edit_item":
        takeaway = " ".join((text_value or "").split())
        if target is None or not 1 <= len(takeaway) <= 600 or _sentence_count(takeaway) > 2:
            return DigestActionResult(status="invalid")
        snapshot = db.get(NewsPublicationSnapshot, target.publication_snapshot_id)
        if snapshot is None or snapshot.status != "published" or snapshot.telegram_deleted_at:
            return DigestActionResult(status="stale")
        target.takeaway = takeaway
        target.source_content_hash = snapshot.post_edit_content_hash or snapshot.content_hash
        target.requires_owner_review = False
    clone = _clone_issue(db, issue, items, intro=intro)
    record_audit_event(
        db,
        action=f"weekly_digest.{action}",
        resource_type="weekly_digest_issue",
        resource_id=clone.id,
        details={"revision": clone.revision, "item_count": len(items)},
    )
    return DigestActionResult(status="updated", issue=_issue_view(db, clone))


def approve_digest_issue(
    db: Session,
    *,
    issue_id: str,
    admin_telegram_user_id: int,
    expected_content_hash: str,
) -> DigestActionResult:
    if admin_telegram_user_id not in settings.admin_telegram_id_set:
        return DigestActionResult(status="forbidden")
    issue = db.query(WeeklyDigestIssue).filter_by(id=issue_id).with_for_update().first()
    if issue is None or issue.status != "draft":
        return DigestActionResult(status="stale")
    if not hmac.compare_digest(issue.content_hash[:16], expected_content_hash):
        return DigestActionResult(status="stale")
    view = _issue_view(db, issue)
    if view.blockers:
        return DigestActionResult(status="quality_blocked", issue=view)
    issue.status = "approved"
    issue.approved_by_ref = _actor_ref(admin_telegram_user_id)
    issue.approved_at = utcnow()
    record_audit_event(
        db,
        action="weekly_digest.approved",
        resource_type="weekly_digest_issue",
        resource_id=issue.id,
        details={"revision": issue.revision, "content_hash": issue.content_hash[:16]},
    )
    db.flush()
    return DigestActionResult(status="approved", issue=_issue_view(db, issue))


def _scheduled_utc(local_value: datetime, timezone_name: str, now: datetime) -> datetime | None:
    if local_value.tzinfo is not None:
        return None
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return None
    first = local_value.replace(tzinfo=timezone, fold=0)
    second = local_value.replace(tzinfo=timezone, fold=1)
    if first.utcoffset() != second.utcoffset():
        return None
    scheduled = first.astimezone(UTC).replace(tzinfo=None)
    if scheduled.replace(tzinfo=UTC).astimezone(timezone).replace(tzinfo=None) != local_value:
        return None
    if scheduled < now + timedelta(minutes=settings.news_schedule_min_minutes):
        return None
    if scheduled > now + timedelta(days=settings.news_schedule_max_days):
        return None
    return scheduled


def schedule_digest_issue(
    db: Session,
    *,
    issue_id: str,
    admin_telegram_user_id: int,
    expected_content_hash: str,
    scheduled_local: datetime,
    timezone_name: str,
) -> DigestActionResult:
    if admin_telegram_user_id not in settings.admin_telegram_id_set:
        return DigestActionResult(status="forbidden")
    if not settings.weekly_digest_enabled:
        return DigestActionResult(status="delivery_disabled")
    issue = db.query(WeeklyDigestIssue).filter_by(id=issue_id).with_for_update().first()
    if issue is None or issue.status != "approved":
        return DigestActionResult(status="stale")
    if not hmac.compare_digest(issue.content_hash[:16], expected_content_hash):
        return DigestActionResult(status="stale")
    view = _issue_view(db, issue)
    if view.blockers:
        return DigestActionResult(status="quality_blocked", issue=view)
    now = utcnow()
    scheduled = _scheduled_utc(scheduled_local, timezone_name, now)
    if scheduled is None:
        return DigestActionResult(status="schedule_invalid", issue=view)
    recipients = (
        db.query(WeeklyDigestPreference, User)
        .join(User, User.id == WeeklyDigestPreference.user_id)
        .filter(
            WeeklyDigestPreference.weekly_news_digest_enabled.is_(True),
            WeeklyDigestPreference.consent_version == settings.weekly_digest_consent_version,
            WeeklyDigestPreference.telegram_chat_id.is_not(None),
            User.is_active.is_(True),
            User.telegram_user_id == WeeklyDigestPreference.telegram_chat_id,
        )
        .all()
    )
    if not recipients:
        return DigestActionResult(status="no_recipients", issue=view)
    for preference, user in recipients:
        db.add(
            WeeklyDigestDelivery(
                issue_id=issue.id,
                user_id=user.id,
                telegram_chat_id=int(preference.telegram_chat_id),
                status="queued",
                next_attempt_at=scheduled,
            )
        )
    db.flush()
    issue.status = "scheduled"
    issue.scheduled_for_utc = scheduled
    issue.timezone = timezone_name
    issue.recipient_count = len(recipients)
    record_audit_event(
        db,
        action="weekly_digest.scheduled",
        resource_type="weekly_digest_issue",
        resource_id=issue.id,
        details={"recipient_count": len(recipients), "revision": issue.revision},
    )
    db.flush()
    return DigestActionResult(status="scheduled", issue=_issue_view(db, issue))


def close_digest_issue(
    db: Session,
    *,
    issue_id: str,
    admin_telegram_user_id: int,
    expected_content_hash: str,
    action: Literal["cancel", "reject"],
) -> DigestActionResult:
    if admin_telegram_user_id not in settings.admin_telegram_id_set:
        return DigestActionResult(status="forbidden")
    issue = db.query(WeeklyDigestIssue).filter_by(id=issue_id).with_for_update().first()
    if issue is None or issue.status not in {"draft", "approved", "scheduled"}:
        return DigestActionResult(status="stale")
    if not hmac.compare_digest(issue.content_hash[:16], expected_content_hash):
        return DigestActionResult(status="stale")
    issue.status = "cancelled" if action == "cancel" else "rejected"
    db.query(WeeklyDigestDelivery).filter(
        WeeklyDigestDelivery.issue_id == issue.id,
        WeeklyDigestDelivery.status.in_({"queued", "processing"}),
    ).update(
        {
            WeeklyDigestDelivery.status: "cancelled",
            WeeklyDigestDelivery.next_attempt_at: None,
            WeeklyDigestDelivery.processing_started_at: None,
            WeeklyDigestDelivery.last_error_code: f"issue_{action}",
        },
        synchronize_session=False,
    )
    record_audit_event(
        db,
        action=f"weekly_digest.{action}led" if action == "cancel" else "weekly_digest.rejected",
        resource_type="weekly_digest_issue",
        resource_id=issue.id,
        details={"revision": issue.revision},
    )
    db.flush()
    return DigestActionResult(status=issue.status, issue=_issue_view(db, issue))


def claim_due_digest_deliveries(db: Session, *, limit: int = 20) -> list[int]:
    now = utcnow()
    stale_before = now - DIGEST_PROCESSING_TTL
    stale = (
        db.query(WeeklyDigestDelivery)
        .filter(
            WeeklyDigestDelivery.status == "processing",
            WeeklyDigestDelivery.processing_started_at < stale_before,
        )
        .all()
    )
    for row in stale:
        row.processing_started_at = None
        if row.attempt_count >= DIGEST_MAX_DELIVERY_ATTEMPTS:
            row.status = "failed"
            row.next_attempt_at = None
            row.last_error_code = "worker_restart_attempts_exhausted"
        else:
            row.status = "queued"
            row.next_attempt_at = now
            row.last_error_code = "worker_restart_retry"
    rows = (
        db.query(WeeklyDigestDelivery)
        .join(WeeklyDigestIssue, WeeklyDigestIssue.id == WeeklyDigestDelivery.issue_id)
        .filter(
            WeeklyDigestDelivery.status == "queued",
            WeeklyDigestDelivery.next_attempt_at <= now,
            WeeklyDigestIssue.status.in_({"scheduled", "sending"}),
        )
        .order_by(WeeklyDigestDelivery.next_attempt_at.asc(), WeeklyDigestDelivery.id.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
        .all()
    )
    claimed: list[int] = []
    for row in rows:
        row.status = "processing"
        row.processing_started_at = now
        row.attempt_count += 1
        issue = db.get(WeeklyDigestIssue, row.issue_id)
        if issue is not None and issue.status == "scheduled":
            issue.status = "sending"
        claimed.append(row.id)
    return claimed


def digest_delivery_payload(db: Session, delivery_id: int) -> DigestDeliveryPayload | None:
    row = db.get(WeeklyDigestDelivery, delivery_id)
    if row is None or row.status != "processing":
        return None
    issue = db.get(WeeklyDigestIssue, row.issue_id)
    preference = (
        db.query(WeeklyDigestPreference)
        .filter(WeeklyDigestPreference.user_id == row.user_id)
        .first()
    )
    user = db.get(User, row.user_id)
    if issue is None or issue.status not in {"scheduled", "sending"}:
        row.status = "cancelled"
        row.processing_started_at = None
        row.next_attempt_at = None
        row.last_error_code = "issue_unavailable"
        return None
    if _issue_blockers(db, issue, _issue_items(db, issue.id)):
        row.status = "cancelled"
        row.processing_started_at = None
        row.next_attempt_at = None
        row.last_error_code = "issue_source_changed"
        return None
    if (
        preference is None
        or not preference.weekly_news_digest_enabled
        or preference.consent_version != settings.weekly_digest_consent_version
        or preference.telegram_chat_id != row.telegram_chat_id
        or user is None
        or not user.is_active
        or user.telegram_user_id != row.telegram_chat_id
    ):
        row.status = "cancelled"
        row.processing_started_at = None
        row.next_attempt_at = None
        row.last_error_code = "recipient_not_opted_in"
        return None
    notification_setting = (
        db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    )
    if notification_setting is not None:
        retry_at = quiet_hours_retry_at(notification_setting, user)
        if retry_at is not None:
            row.status = "queued"
            row.processing_started_at = None
            row.next_attempt_at = retry_at
            row.last_error_code = "quiet_hours"
            return None
    return DigestDeliveryPayload(
        delivery_id=row.id,
        issue_id=issue.id,
        chat_id=row.telegram_chat_id,
        text=issue.rendered_text,
        channel_url=issue.channel_url,
    )


def mark_digest_delivery_succeeded(
    db: Session,
    delivery_id: int,
    *,
    telegram_message_id: int,
) -> None:
    row = db.get(WeeklyDigestDelivery, delivery_id)
    if row is None or row.status != "processing":
        return
    now = utcnow()
    row.status = "sent"
    row.sent_at = now
    row.telegram_message_id = telegram_message_id
    row.processing_started_at = None
    row.next_attempt_at = None
    row.last_error_code = None
    preference = (
        db.query(WeeklyDigestPreference)
        .filter(WeeklyDigestPreference.user_id == row.user_id)
        .first()
    )
    if preference is not None:
        preference.last_digest_issue_id = row.issue_id
        preference.last_sent_at = now


def mark_digest_delivery_failed(
    db: Session,
    delivery_id: int,
    *,
    error_code: str,
    retry_after: timedelta | None = None,
    terminal: bool = False,
    uncertain: bool = False,
) -> None:
    row = db.get(WeeklyDigestDelivery, delivery_id)
    if row is None or row.status != "processing":
        return
    row.processing_started_at = None
    row.last_error_code = error_code[:64]
    if uncertain:
        row.status = "uncertain"
        row.next_attempt_at = None
    elif terminal or row.attempt_count >= DIGEST_MAX_DELIVERY_ATTEMPTS:
        row.status = "cancelled" if terminal else "failed"
        row.next_attempt_at = None
    else:
        row.status = "queued"
        delay = retry_after or timedelta(minutes=min(60, 2 ** max(0, row.attempt_count - 1)))
        row.next_attempt_at = utcnow() + delay
    if terminal and error_code == "telegram_chat_unavailable":
        preference = (
            db.query(WeeklyDigestPreference)
            .filter(WeeklyDigestPreference.user_id == row.user_id)
            .first()
        )
        if preference is not None:
            preference.weekly_news_digest_enabled = False
            preference.unsubscribed_at = utcnow()
            preference.disabled_reason = "telegram_chat_unavailable"
            db.query(WeeklyDigestDelivery).filter(
                WeeklyDigestDelivery.user_id == row.user_id,
                WeeklyDigestDelivery.status == "queued",
            ).update(
                {
                    WeeklyDigestDelivery.status: "cancelled",
                    WeeklyDigestDelivery.next_attempt_at: None,
                    WeeklyDigestDelivery.last_error_code: "telegram_chat_unavailable",
                },
                synchronize_session=False,
            )


def finalize_digest_issues(db: Session, issue_ids: set[str]) -> None:
    db.flush()
    for issue_id in issue_ids:
        issue = db.get(WeeklyDigestIssue, issue_id)
        if issue is None or issue.status not in {"scheduled", "sending"}:
            continue
        active_count = (
            db.query(WeeklyDigestDelivery.id)
            .filter(
                WeeklyDigestDelivery.issue_id == issue.id,
                WeeklyDigestDelivery.status.in_({"queued", "processing"}),
            )
            .count()
        )
        if active_count:
            continue
        sent_count = (
            db.query(WeeklyDigestDelivery.id)
            .filter(
                WeeklyDigestDelivery.issue_id == issue.id,
                WeeklyDigestDelivery.status == "sent",
            )
            .count()
        )
        uncertain_count = (
            db.query(WeeklyDigestDelivery.id)
            .filter(
                WeeklyDigestDelivery.issue_id == issue.id,
                WeeklyDigestDelivery.status == "uncertain",
            )
            .count()
        )
        issue.status = "sent" if sent_count or uncertain_count else "cancelled"


def digest_delivery_counts(db: Session, issue_id: str) -> dict[str, int]:
    rows = (
        db.query(
            WeeklyDigestDelivery.status,
            func.count(WeeklyDigestDelivery.id),
        )
        .filter(WeeklyDigestDelivery.issue_id == issue_id)
        .group_by(WeeklyDigestDelivery.status)
        .all()
    )
    return {str(row[0]): int(row[1]) for row in rows}


def prune_weekly_digest(db: Session, *, retention_days: int, batch_size: int = 200) -> int:
    cutoff = utcnow() - timedelta(days=retention_days)
    issue_ids = [
        row.id
        for row in db.query(WeeklyDigestIssue.id)
        .filter(
            WeeklyDigestIssue.status.in_({"sent", "superseded", "cancelled", "rejected"}),
            WeeklyDigestIssue.created_at < cutoff,
        )
        .order_by(WeeklyDigestIssue.created_at.asc(), WeeklyDigestIssue.id.asc())
        .limit(batch_size)
        .all()
    ]
    if not issue_ids:
        return 0
    db.query(WeeklyDigestPreference).filter(
        WeeklyDigestPreference.last_digest_issue_id.in_(issue_ids)
    ).update(
        {WeeklyDigestPreference.last_digest_issue_id: None},
        synchronize_session=False,
    )
    db.query(WeeklyDigestDelivery).filter(WeeklyDigestDelivery.issue_id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    db.query(WeeklyDigestIssueItem).filter(WeeklyDigestIssueItem.issue_id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    db.query(WeeklyDigestIssue).filter(WeeklyDigestIssue.id.in_(issue_ids)).delete(
        synchronize_session=False
    )
    return len(issue_ids)
