from __future__ import annotations

from datetime import UTC, datetime

from fitminiapp_api.services.news_freshness import is_current_month_publication


def test_freshness_window_accepts_current_and_previous_calendar_month() -> None:
    now = datetime(2026, 8, 30, 12, 0, 0)

    assert is_current_month_publication(datetime(2026, 7, 1, 0, 0, 0), now=now)
    assert is_current_month_publication(datetime(2026, 7, 31, 23, 59, 59), now=now)
    assert is_current_month_publication(datetime(2026, 8, 1, 0, 0, 0), now=now)
    assert is_current_month_publication(now, now=now)


def test_freshness_window_rejects_older_missing_and_future_dates() -> None:
    now = datetime(2026, 8, 30, 12, 0, 0)

    assert not is_current_month_publication(datetime(2026, 6, 30, 23, 59, 59), now=now)
    assert not is_current_month_publication(None, now=now)
    assert not is_current_month_publication(datetime(2026, 8, 30, 12, 0, 1), now=now)


def test_freshness_window_handles_year_boundary_and_timezone() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    assert is_current_month_publication(
        datetime(2025, 12, 1, 0, 0, 0, tzinfo=UTC),
        now=now,
    )
    assert not is_current_month_publication(
        datetime(2025, 11, 30, 23, 59, 59, tzinfo=UTC),
        now=now,
    )
