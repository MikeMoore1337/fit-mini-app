from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from fitminiapp_api.models.news import NewsSource

SOURCE_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
HOST_PATTERN = re.compile(r"[A-Za-z0-9.-]{1,253}\Z")
SOURCE_TYPES = {
    "primary_research",
    "systematic_review",
    "official_organization",
    "official_product",
    "reputable_secondary",
    "yfc",
}
FETCH_KINDS = {"rss", "json_feed", "html_metadata"}
DEFAULT_SOURCE_ALLOWLIST_PATH = (
    Path(__file__).resolve().parent.parent / "resources" / "news_sources.json"
)
type NewsSourceType = Literal[
    "primary_research",
    "systematic_review",
    "official_organization",
    "official_product",
    "reputable_secondary",
    "yfc",
]
type NewsFetchKind = Literal["rss", "json_feed", "html_metadata"]


@dataclass(frozen=True)
class NewsSourceDefinition:
    id: str
    name: str
    source_type: NewsSourceType
    fetch_kind: NewsFetchKind
    url: str
    language: str
    enabled: bool
    fetch_interval_minutes: int
    trust_notes: str
    licensing_notes: str
    allowed_redirect_hosts: tuple[str, ...] = ()
    allowed_item_hosts: tuple[str, ...] = ()


def _bounded_text(value: object, *, field: str, maximum: int, required: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = " ".join(value.split())
    if required and not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field} is too long")
    return normalized


def _source_url(value: object) -> str:
    normalized = _bounded_text(value, field="url", maximum=2048, required=True)
    parsed = urlparse(normalized)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError("url must be an absolute credential-free HTTPS URL without a fragment")
    if parsed.port not in {None, 443}:
        raise ValueError("url may only use the default HTTPS port")
    return normalized


def parse_source_definition(raw: object) -> NewsSourceDefinition:
    if not isinstance(raw, dict):
        raise ValueError("each source must be an object")
    source_id = _bounded_text(raw.get("id"), field="id", maximum=64, required=True)
    if not SOURCE_ID_PATTERN.fullmatch(source_id):
        raise ValueError("id must match [a-z0-9][a-z0-9_-]{1,63}")
    source_type = _bounded_text(raw.get("type"), field="type", maximum=32, required=True)
    if source_type not in SOURCE_TYPES:
        raise ValueError("unsupported source type")
    fetch_kind = _bounded_text(raw.get("fetch_kind"), field="fetch_kind", maximum=24, required=True)
    if fetch_kind not in FETCH_KINDS:
        raise ValueError("unsupported fetch_kind")
    language = _bounded_text(
        raw.get("language", "en"), field="language", maximum=8, required=True
    ).lower()
    if not re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", language):
        raise ValueError("language must be a two-letter locale or language-region")
    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be a boolean")
    interval = raw.get("fetch_interval_minutes", 360)
    if not isinstance(interval, int) or isinstance(interval, bool) or not 15 <= interval <= 10080:
        raise ValueError("fetch_interval_minutes must be between 15 and 10080")
    host_lists: dict[str, list[str]] = {}
    for field in ("allowed_redirect_hosts", "allowed_item_hosts"):
        raw_hosts = raw.get(field, [])
        if not isinstance(raw_hosts, list) or len(raw_hosts) > 8:
            raise ValueError(f"{field} must be a list of at most 8 hosts")
        normalized_hosts: list[str] = []
        for host in raw_hosts:
            normalized = _bounded_text(host, field=field, maximum=253, required=True).lower()
            if not HOST_PATTERN.fullmatch(normalized) or normalized.startswith("."):
                raise ValueError(f"{field} contains an invalid host")
            normalized_hosts.append(normalized)
        host_lists[field] = normalized_hosts
    return NewsSourceDefinition(
        id=source_id,
        name=_bounded_text(raw.get("name"), field="name", maximum=160, required=True),
        source_type=cast(NewsSourceType, source_type),
        fetch_kind=cast(NewsFetchKind, fetch_kind),
        url=_source_url(raw.get("url")),
        language=language,
        enabled=enabled,
        fetch_interval_minutes=interval,
        trust_notes=_bounded_text(raw.get("trust_notes", ""), field="trust_notes", maximum=2000),
        licensing_notes=_bounded_text(
            raw.get("licensing_notes", ""), field="licensing_notes", maximum=2000
        ),
        allowed_redirect_hosts=tuple(dict.fromkeys(host_lists["allowed_redirect_hosts"])),
        allowed_item_hosts=tuple(dict.fromkeys(host_lists["allowed_item_hosts"])),
    )


def parse_source_allowlist(raw: object) -> list[NewsSourceDefinition]:
    if not isinstance(raw, list):
        raise ValueError("source allowlist must be a JSON array")
    definitions = [parse_source_definition(item) for item in raw]
    ids = [item.id for item in definitions]
    if len(ids) != len(set(ids)):
        raise ValueError("source ids must be unique")
    return definitions


def load_source_allowlist(path: Path = DEFAULT_SOURCE_ALLOWLIST_PATH) -> list[NewsSourceDefinition]:
    if not path.is_file() or path.stat().st_size > 1_048_576:
        raise ValueError("source allowlist file is missing or too large")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("source allowlist file is not valid UTF-8 JSON") from exc
    return parse_source_allowlist(raw)


def apply_source_allowlist(
    db: Session,
    definitions: list[NewsSourceDefinition],
    *,
    disable_missing: bool = False,
) -> tuple[int, int]:
    existing = {row.id: row for row in db.query(NewsSource).all()}
    created = 0
    updated = 0
    for definition in definitions:
        row = existing.get(definition.id)
        values = {
            "name": definition.name,
            "source_type": definition.source_type,
            "fetch_kind": definition.fetch_kind,
            "feed_url": definition.url,
            "language": definition.language,
            "enabled": definition.enabled,
            "fetch_interval_minutes": definition.fetch_interval_minutes,
            "trust_notes": definition.trust_notes,
            "licensing_notes": definition.licensing_notes,
            "fetch_options": {
                "allowed_redirect_hosts": list(definition.allowed_redirect_hosts),
                "allowed_item_hosts": list(definition.allowed_item_hosts),
            },
        }
        if row is None:
            db.add(NewsSource(id=definition.id, **values))
            created += 1
            continue
        for key, value in values.items():
            setattr(row, key, value)
        updated += 1
    if disable_missing:
        configured_ids = {item.id for item in definitions}
        for source_id, row in existing.items():
            if source_id not in configured_ids:
                row.enabled = False
    db.flush()
    return created, updated


def bootstrap_default_news_sources(db: Session) -> int:
    """Create the versioned baseline only when an environment has no source records yet."""
    if db.query(NewsSource.id).first() is not None:
        return 0
    definitions = load_source_allowlist()
    if not any(item.enabled for item in definitions):
        raise ValueError("default source allowlist must contain an enabled source")
    created, _ = apply_source_allowlist(db, definitions)
    return created
