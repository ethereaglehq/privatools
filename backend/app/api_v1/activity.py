"""Bounded, best-effort HTTP metadata on the existing SQLite database.

Never accepts file names, URLs, headers, content, or exception messages. The
daily chart is independent of recent-row eviction. A failed telemetry write
must not affect processing, quota accounting, or the response.
"""
from __future__ import annotations

import logging
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import anyio

from .. import store
from . import catalog, quota

logger = logging.getLogger(__name__)
RETENTION_DAYS = 7
RECENT_LIMIT = 50
MAX_RECENT_PER_KEY = 1000
MAX_RECENT_GLOBAL = 100000
CLEANUP_BATCH = 1000
CLEANUP_INTERVAL = 60
_last_warning = 0.0

# This reviewed route inventory prevents a URL/path parameter from becoming
# stored metadata. Discovery and non-processing job endpoints are excluded.
_PROCESSING_PATHS = frozenset(
    catalog.PREFIX + short for short in catalog._METADATA["operations"]
    if quota.cost_for(catalog.PREFIX + short) > 0
) | {"/api/v1/jobs"}
_ERROR_CODES = frozenset({
    "invalid_request", "unauthorized", "forbidden", "not_found", "method_not_allowed",
    "conflict", "gone", "payload_too_large", "unsupported_media_type", "validation_error",
    "rate_limited", "processing_failed", "not_implemented", "service_unavailable",
    "processing_timeout", "request_failed", "request_cancelled", "request_too_large",
    "missing_api_key", "invalid_api_key", "admission_unavailable", "quota_exceeded",
    "concurrency_limit_exceeded", "rate_limit_exceeded", "server_busy",
    "idempotency_conflict", "idempotency_expired", "invalid_job_result",
    "job_admission_limit", "job_queue_full", "job_rate_limited", "job_storage_full",
    "job_upload_expired", "jobs_unavailable", "invalid_idempotency_key",
    "invalid_job_fields", "invalid_job_files", "invalid_job_options",
    "job_input_too_large", "unsupported_async_operation",
})
_STATUS_CODES = {
    400: "invalid_request", 401: "unauthorized", 403: "forbidden", 404: "not_found",
    405: "method_not_allowed", 409: "conflict", 410: "gone", 413: "payload_too_large",
    415: "unsupported_media_type", 422: "validation_error", 429: "rate_limited",
    499: "request_cancelled", 500: "processing_failed", 501: "not_implemented",
    503: "service_unavailable", 504: "processing_timeout",
}
_OPERATIONS = frozenset(catalog.operation_id(method, path)
                        for path in _PROCESSING_PATHS for method in ("GET", "POST", "PUT", "PATCH", "DELETE"))


def operation_for(scope: dict) -> str | None:
    path = scope.get("path", "")
    method = scope.get("method", "")
    if path not in _PROCESSING_PATHS or method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return None
    if path == "/api/v1/jobs" and method != "POST":
        return None
    return catalog.operation_id(method, path)


def error_code(status: int, code: object = None) -> str | None:
    if status < 400:
        return None
    return code if isinstance(code, str) and code in _ERROR_CODES else _STATUS_CODES.get(status, "request_failed")


async def finish(scope: dict, status: int) -> None:
    """Observe the HTTP result without reading or buffering response/upload data."""
    state = scope.get("state", {})
    operation = operation_for(scope)
    if not operation or state.get("v1_activity_recorded"):
        return
    state["v1_activity_recorded"] = True
    duration = round((time.perf_counter() - state.get("v1_activity_started", time.perf_counter())) * 1000)

    def save():
        try:
            key_id = state.get("v1_key_id")
            if not key_id and status >= 400:
                # Multipart/JSON parsing can reject before authentication
                # dependencies run. Resolve only those failed calls; the raw
                # credential remains local to this function and is not stored.
                from starlette.datastructures import Headers
                headers = Headers(scope=scope)
                raw = headers.get("x-api-key")
                if not raw:
                    scheme, _, token = headers.get("authorization", "").partition(" ")
                    raw = token.strip() if scheme.lower() == "bearer" else ""
                key_id = _known_key(raw) if raw else None
            if key_id:
                record(key_id, state.get("request_id", ""), operation, scope["method"], status,
                       state.get("v1_error_code"), duration)
        except Exception:
            _warn_unavailable()

    try:
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(save)
    except Exception:
        _warn_unavailable()


def _window(now: float) -> tuple[datetime, datetime]:
    today = datetime.fromtimestamp(now, timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return today, today - timedelta(days=RETENTION_DAYS - 1)


def _known_key(raw: str) -> str | None:
    """Reuse verified-key authentication with the optional telemetry lock budget."""
    from ..auth import accounts
    record = accounts.resolve_key(raw, read_timeout=0.025)
    return record.key_id if record else None


@contextmanager
def _write():
    # Do not wait behind the quota store's process lock or its ten-second busy
    # timeout. Telemetry is optional; admission has priority under contention.
    conn = sqlite3.connect(store.DB_PATH, timeout=0.025, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def _cleanup(conn, now: float, *, force: bool = False) -> int:
    last = conn.execute("SELECT cleaned_at FROM api_activity_maintenance WHERE singleton=1").fetchone()[0]
    if not force and now - last < CLEANUP_INTERVAL:
        return 0
    _, first = _window(now)
    # Every iteration has a fixed bound, including after a long downtime. Read
    # queries independently exclude expired rows while the janitor catches up.
    recent = conn.execute("DELETE FROM api_activity_recent WHERE id IN (SELECT id FROM api_activity_recent WHERE created_at<? ORDER BY created_at,id LIMIT ?)", (first.timestamp(), CLEANUP_BATCH)).rowcount
    daily = conn.execute("DELETE FROM api_activity_daily WHERE rowid IN (SELECT rowid FROM api_activity_daily WHERE day<? ORDER BY day LIMIT ?)", (first.date().isoformat(), CLEANUP_BATCH)).rowcount
    conn.execute("UPDATE api_activity_maintenance SET cleaned_at=? WHERE singleton=1", (now,))
    return max(recent, daily)


def cleanup() -> None:
    """Called by the existing janitor, including when there is no API traffic."""
    try:
        # Drain a full recent-history capacity after downtime, in short
        # transactions so admission can interleave. Work has a fixed maximum;
        # no single transaction deletes more than CLEANUP_BATCH rows/table.
        for _ in range((MAX_RECENT_GLOBAL + CLEANUP_BATCH - 1) // CLEANUP_BATCH):
            with _write() as conn:
                removed = _cleanup(conn, time.time(), force=True)
            if removed < CLEANUP_BATCH:
                break
    except Exception:
        _warn_unavailable()


def _warn_unavailable() -> None:
    global _last_warning
    now = time.monotonic()
    if now - _last_warning > 60:
        _last_warning = now
        logger.warning("API activity storage is temporarily unavailable")


def record(key_id: str, request_id: str, operation: str, method: str,
           status_code: int, code: object, duration_ms: int, *, now: float | None = None) -> None:
    """Persist one completed HTTP attempt; all failures are deliberately swallowed."""
    try:
        # Require server-minted IDs. An inbound client ID can contain private
        # text even when it is syntactically safe for an HTTP header.
        if not re.fullmatch(r"[0-9a-f]{12}", request_id) or operation not in _OPERATIONS:
            return
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"} or not 100 <= status_code <= 599:
            return
        moment = time.time() if now is None else now
        duration = max(0, min(int(duration_ms), 86400000))
        day = datetime.fromtimestamp(moment, timezone.utc).date().isoformat()
        succeeded = int(status_code < 400)
        with _write() as conn:
            # A deleted account/key must not be recreated by an in-flight call.
            if not conn.execute("SELECT 1 FROM api_keys WHERE key_id=?", (key_id,)).fetchone():
                return
            conn.execute("INSERT INTO api_activity_recent(key_id,request_id,operation,method,status_code,error_code,duration_ms,created_at) VALUES(?,?,?,?,?,?,?,?)",
                         (key_id, request_id, operation, method, status_code, error_code(status_code, code), duration, moment))
            conn.execute("INSERT INTO api_activity_daily(key_id,day,requests,succeeded,failed,duration_ms) VALUES(?,?,1,?,?,?) ON CONFLICT(key_id,day) DO UPDATE SET requests=requests+1,succeeded=succeeded+excluded.succeeded,failed=failed+excluded.failed,duration_ms=duration_ms+excluded.duration_ms",
                         (key_id, day, succeeded, 1 - succeeded, duration))
            # At steady state each cap removes at most the one inserted row.
            # Indexed key lookup is bounded by 1,001; the trigger-maintained
            # global count avoids scanning 100,000 rows for every request.
            conn.execute("DELETE FROM api_activity_recent WHERE id IN (SELECT id FROM api_activity_recent WHERE key_id=? ORDER BY id DESC LIMIT ? OFFSET ?)", (key_id, CLEANUP_BATCH, MAX_RECENT_PER_KEY))
            total = conn.execute("SELECT recent_count FROM api_activity_maintenance WHERE singleton=1").fetchone()[0]
            overflow = min(CLEANUP_BATCH, max(0, total - MAX_RECENT_GLOBAL))
            if overflow:
                conn.execute("DELETE FROM api_activity_recent WHERE id IN (SELECT id FROM api_activity_recent ORDER BY id LIMIT ?)", (overflow,))
            _cleanup(conn, moment)
    except Exception:
        _warn_unavailable()


def summary(user_id: str, key_id: str | None = None, *, now: float | None = None) -> dict:
    """A consistent account-scoped snapshot; a foreign key filter is never trusted."""
    moment = time.time() if now is None else now
    today, first = _window(moment)
    store.init()
    with store.read() as conn:
        conn.execute("BEGIN")
        rows = conn.execute("SELECT key_id,label,revoked_at FROM api_keys WHERE user_id=? ORDER BY created_at DESC,key_id", (user_id,)).fetchall()
        if key_id is not None:
            rows = [row for row in rows if row["key_id"] == key_id]
            if not rows:
                raise KeyError("No such key")
        keys = []
        for row in rows:
            standing = quota._state(conn, row["key_id"], today.strftime("%Y%m%d"))
            keys.append({"key_id": row["key_id"], "label": row["label"], "revoked": row["revoked_at"] is not None,
                         "units": {"used": standing.units_used, "limit": standing.units_limit, "remaining": standing.units_remaining},
                         "bytes": {"used": standing.bytes_used, "limit": standing.bytes_limit}})
        daily = conn.execute("SELECT d.day,SUM(d.requests) requests,SUM(d.succeeded) succeeded,SUM(d.failed) failed,SUM(d.duration_ms) duration_ms FROM api_activity_daily d JOIN api_keys k ON k.key_id=d.key_id WHERE k.user_id=? AND (? IS NULL OR k.key_id=?) AND d.day>=? AND d.day<=? GROUP BY d.day",
                             (user_id, key_id, key_id, first.date().isoformat(), today.date().isoformat())).fetchall()
        by_day = {row["day"]: row for row in daily}
        days = []
        for offset in range(RETENTION_DAYS):
            date = (first + timedelta(days=offset)).date().isoformat()
            row = by_day.get(date)
            days.append({"date": date, "requests": row["requests"] if row else 0,
                         "succeeded": row["succeeded"] if row else 0, "failed": row["failed"] if row else 0,
                         "avg_duration_ms": round(row["duration_ms"] / row["requests"], 1) if row else 0})
        recent = conn.execute("SELECT r.* FROM api_activity_recent r JOIN api_keys k ON k.key_id=r.key_id WHERE k.user_id=? AND (? IS NULL OR k.key_id=?) AND r.created_at>=? AND r.created_at<=? ORDER BY r.id DESC LIMIT ?",
                              (user_id, key_id, key_id, first.timestamp(), moment, RECENT_LIMIT)).fetchall()
        public_recent = [{name: row[name] for name in ("request_id", "key_id", "operation", "method", "status_code", "error_code", "duration_ms")} |
                         {"created_at": datetime.fromtimestamp(row["created_at"], timezone.utc).isoformat(timespec="milliseconds")} for row in recent]
    return {"retention_days": RETENTION_DAYS, "recent_limit": RECENT_LIMIT, "keys": keys,
            "resets_at": (today + timedelta(days=1)).isoformat(), "days": days, "recent": public_recent}
