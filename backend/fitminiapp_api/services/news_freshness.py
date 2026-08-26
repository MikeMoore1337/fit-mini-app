from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime


def _as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def parse_source_published_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_utc_naive(parsed)


def is_current_month_publication(
    published_at: datetime | None,
    *,
    now: datetime,
) -> bool:
    if published_at is None:
        return False
    current = _as_utc_naive(now)
    published = _as_utc_naive(published_at)
    month_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return month_start <= published <= current


def source_metadata_is_current_month(
    metadata: Mapping[str, object],
    *,
    now: datetime,
) -> bool:
    return is_current_month_publication(
        parse_source_published_at(metadata.get("source_published_at")),
        now=now,
    )
