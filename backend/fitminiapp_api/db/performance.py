from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from time import perf_counter

from sqlalchemy import event
from sqlalchemy.engine import Engine


@dataclass
class SqlMetrics:
    query_count: int = 0
    duration_ms: float = 0.0


_sql_metrics: ContextVar[SqlMetrics | None] = ContextVar("sql_metrics", default=None)
_LISTENERS_INSTALLED_ATTR = "_fitminiapp_performance_listeners_installed"


def begin_sql_metrics() -> Token[SqlMetrics | None]:
    return _sql_metrics.set(SqlMetrics())


def current_sql_metrics() -> SqlMetrics:
    metrics = _sql_metrics.get()
    return metrics if metrics is not None else SqlMetrics()


def reset_sql_metrics(token: Token[SqlMetrics | None]) -> None:
    _sql_metrics.reset(token)


def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:
    del cursor, statement, parameters, executemany
    metrics = _sql_metrics.get()
    if metrics is None:
        context._fitminiapp_query_started_at = None
        return
    context._fitminiapp_query_started_at = perf_counter()
    metrics.query_count += 1


def _record_query_duration(context) -> None:
    started_at = getattr(context, "_fitminiapp_query_started_at", None)
    metrics = _sql_metrics.get()
    if started_at is not None and metrics is not None:
        metrics.duration_ms += (perf_counter() - started_at) * 1000


def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:
    del conn, cursor, statement, parameters, executemany
    _record_query_duration(context)


def install_sql_metrics(engine: Engine) -> None:
    if getattr(engine, _LISTENERS_INSTALLED_ATTR, False):
        return
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)
    setattr(engine, _LISTENERS_INSTALLED_ATTR, True)


def pool_snapshot(engine: Engine) -> dict[str, int]:
    pool = engine.pool
    result: dict[str, int] = {}
    for field, method_name in (
        ("db_pool_size", "size"),
        ("db_pool_checked_out", "checkedout"),
        ("db_pool_overflow", "overflow"),
    ):
        method = getattr(pool, method_name, None)
        if callable(method):
            try:
                value = int(method())
                result[field] = max(0, value) if field == "db_pool_overflow" else value
            except NotImplementedError, TypeError:
                continue
    return result
