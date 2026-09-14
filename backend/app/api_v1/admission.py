"""Shared SQLite admission for HTTP requests, not native compute cancellation."""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from pathlib import Path

from .. import store
from . import quota

REQUESTS_PER_MINUTE = 30
BURST = 6
LEASE_SECONDS = max(120, int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "300")) + 60)


@dataclass(frozen=True)
class Admission:
    allowed: bool
    state: quota.QuotaState
    token: str | None = None
    code: str | None = None
    retry_after: int = 0


def _process_start(pid: int) -> str:
    try:
        # Linux start ticks distinguish a dead worker from a reused PID.
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return ""


def _alive(pid: int, start: str) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    current = _process_start(pid)
    return not (start and current and start != current)


def _reap(conn, now: float) -> None:
    for row in conn.execute("SELECT token,owner_pid,owner_start FROM api_v1_leases WHERE expires_at<=?", (now,)):
        # A paused but living request must not lose its slot merely due to TTL.
        if not _alive(row["owner_pid"], row["owner_start"]):
            conn.execute("DELETE FROM api_v1_leases WHERE token=?", (row["token"],))


def admit(key_id: str, units: int, size_bytes: int, *, now: float | None = None) -> Admission:
    quota.ensure_schema()
    now = time.time() if now is None else now
    with store.write() as conn:
        day = quota._today()
        state = quota._state(conn, key_id, day)
        _reap(conn, now)
        active = conn.execute("SELECT COUNT(*) FROM api_v1_leases WHERE key_id=?", (key_id,)).fetchone()[0]
        if active >= quota.MAX_JOBS_PER_KEY:
            return Admission(False, state, code="concurrency_limit_exceeded", retry_after=2)
        total = conn.execute("SELECT COUNT(*) FROM api_v1_leases").fetchone()[0]
        if total >= quota.MAX_HTTP_REQUESTS:
            return Admission(False, state, code="server_busy", retry_after=2)
        row = conn.execute("SELECT tokens,updated_at FROM api_v1_rate_buckets WHERE key_id=?", (key_id,)).fetchone()
        available = min(BURST, row["tokens"] + max(0, now-row["updated_at"])*REQUESTS_PER_MINUTE/60) if row else BURST
        if available < 1:
            return Admission(False, state, code="rate_limit_exceeded", retry_after=max(1, math.ceil((1-available)*60/REQUESTS_PER_MINUTE)))
        allowed, state, token = quota.reserve_in_transaction(conn, key_id, units, size_bytes, day=day, now=now)
        if not allowed:
            return Admission(False, state, code="quota_exceeded", retry_after=state.retry_after)
        conn.execute("INSERT INTO api_v1_rate_buckets VALUES(?,?,?) ON CONFLICT(key_id) DO UPDATE SET tokens=excluded.tokens,updated_at=excluded.updated_at", (key_id, available-1, now))
        conn.execute("INSERT INTO api_v1_leases VALUES(?,?,?,?,?)", (token, key_id, os.getpid(), _process_start(os.getpid()), now+LEASE_SECONDS))
        return Admission(True, state, token)


def renew(token: str) -> None:
    with store.write() as conn:
        conn.execute("UPDATE api_v1_leases SET expires_at=? WHERE token=?", (time.time()+LEASE_SECONDS, token))


def release(token: str) -> None:
    with store.write() as conn:
        conn.execute("DELETE FROM api_v1_leases WHERE token=?", (token,))
