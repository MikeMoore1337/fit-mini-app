from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta


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
    """Return whether a source date is inside the current or previous calendar month.

    The legacy function name is kept because it is part of the existing news pipeline
    contract. The accepted freshness window now intentionally spans two calendar months.
    """
    if published_at is None:
        return False
    current = _as_utc_naive(now)
    published = _as_utc_naive(published_at)
    current_month_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return previous_month_start <= published <= current


def source_metadata_is_current_month(
    metadata: Mapping[str, object],
    *,
    now: datetime,
) -> bool:
    return is_current_month_publication(
        parse_source_published_at(metadata.get("source_published_at")),
        now=now,
    )
