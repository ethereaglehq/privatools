"""Durable application state.

Everything else in this backend is stateless by design — the container is
destroyed and recreated on every release, and ``TEMP_DIR`` is swept by a
janitor. Accounts cannot live like that: a user must survive a deploy. So this
module owns the one piece of durable state the service has.

**SQLite, deliberately.** The deployment is a 2-core VM running two uvicorn
workers in one container for a free, owner-funded product. A separate database
server would be more operational surface than the data justifies. SQLite in WAL
mode handles multi-process readers with a single writer safely, which is the
exact shape of this workload — reads on every authenticated request, writes only
on registration, login and key management.

**Zero new dependencies.** Dependencies here are hash-pinned with
``--require-hashes``; adding an ORM or a password library means lockfile churn
and new supply-chain surface for something the standard library already does
well. ``sqlite3`` and ``hashlib.scrypt`` are both stdlib.

The file lives in ``PRIVATOOLS_DATA_DIR`` (default ``data/``), which is a
*different* volume from ``TEMP_DIR`` — putting it in the temp volume would hand
the cleanup janitor the user table.
"""
from __future__ import annotations

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("PRIVATOOLS_DATA_DIR", "data"))
DB_PATH = DATA_DIR / "privatools.db"

# Serialises writers inside a process. SQLite itself serialises across
# processes; this just avoids the two workers of one container queueing on
# lock timeouts for no reason.
_write_lock = threading.Lock()
_initialised = False


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")      # concurrent readers with a writer
    conn.execute("PRAGMA busy_timeout=10000")    # wait rather than fail under contention
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")    # WAL makes FULL unnecessary for this workload
    return conn


@contextmanager
def read() -> Iterator[sqlite3.Connection]:
    """A read-only-by-convention connection. Cheap; no lock held."""
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def write() -> Iterator[sqlite3.Connection]:
    """A writing connection inside a transaction, committed on clean exit."""
    with _write_lock:
        conn = _connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            # `executescript` commits implicitly and opens no new transaction,
            # so an unconditional COMMIT here fails with "no transaction is
            # active" on any migration that uses it.
            if conn.in_transaction:
                conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            raise
        finally:
            conn.close()


# ── schema ────────────────────────────────────────────────────────────────
#
# Migrations are a plain ordered list. Each entry runs once and is recorded in
# `schema_version`. Never edit an entry that has shipped — append a new one.

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE users (
            id            TEXT PRIMARY KEY,
            email         TEXT NOT NULL,
            email_lower   TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            last_login_at TEXT
        );

        CREATE TABLE sessions (
            token_hash TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
        CREATE INDEX idx_sessions_user ON sessions(user_id);
        CREATE INDEX idx_sessions_expiry ON sessions(expires_at);

        -- Raw API keys are never stored. `key_id` is the lookup handle that
        -- appears in quotas, logs and metrics; `key_hash` verifies the secret.
        CREATE TABLE api_keys (
            key_id      TEXT PRIMARY KEY,
            key_hash    TEXT NOT NULL,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            label       TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            last_used_at TEXT,
            revoked_at  TEXT
        );
        CREATE INDEX idx_api_keys_user ON api_keys(user_id);
        """,
    ),
    (
        2,
        """
        -- A recovery code is the only way back into an account, because there
        -- is no email to send a reset link to. Stored as a hash like any other
        -- secret; shown to the user exactly once.
        ALTER TABLE users ADD COLUMN recovery_hash TEXT;
        ALTER TABLE users ADD COLUMN recovery_used_at TEXT;

        -- Per-account login throttling. The per-IP limiter does not stop
        -- someone spreading guesses for one account across many addresses.
        CREATE TABLE login_attempts (
            email_lower TEXT PRIMARY KEY,
            failures    INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT
        );
        """,
    ),
    (
        3,
        """
        CREATE TABLE IF NOT EXISTS api_quota (
            key_id TEXT NOT NULL, day TEXT NOT NULL,
            units INTEGER NOT NULL DEFAULT 0, bytes INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (key_id, day)
        );
        CREATE TABLE api_v1_reservations (
            token TEXT PRIMARY KEY, key_id TEXT NOT NULL, day TEXT NOT NULL,
            units INTEGER NOT NULL, bytes INTEGER NOT NULL, created_at REAL NOT NULL,
            refunded INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX api_v1_reservations_created ON api_v1_reservations(created_at);
        CREATE TABLE api_v1_leases (
            token TEXT PRIMARY KEY REFERENCES api_v1_reservations(token),
            key_id TEXT NOT NULL, owner_pid INTEGER NOT NULL, owner_start TEXT NOT NULL,
            expires_at REAL NOT NULL
        );
        CREATE INDEX api_v1_leases_key ON api_v1_leases(key_id);
        CREATE TABLE api_v1_rate_buckets (
            key_id TEXT PRIMARY KEY, tokens REAL NOT NULL, updated_at REAL NOT NULL
        );
        """,
    ),
    (
        4,
        """
        -- API activity contains identifiers and HTTP outcomes only. Daily
        -- aggregates survive eviction from the bounded recent-request list.
        CREATE TABLE api_activity_recent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT NOT NULL REFERENCES api_keys(key_id) ON DELETE CASCADE,
            request_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            error_code TEXT,
            duration_ms INTEGER NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX api_activity_recent_key ON api_activity_recent(key_id, id DESC);
        CREATE INDEX api_activity_recent_created ON api_activity_recent(created_at, id);
        CREATE TABLE api_activity_daily (
            key_id TEXT NOT NULL REFERENCES api_keys(key_id) ON DELETE CASCADE,
            day TEXT NOT NULL,
            requests INTEGER NOT NULL DEFAULT 0,
            succeeded INTEGER NOT NULL DEFAULT 0,
            failed INTEGER NOT NULL DEFAULT 0,
            duration_ms INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (key_id, day)
        );
        CREATE INDEX api_activity_daily_day ON api_activity_daily(day);
        CREATE TABLE api_activity_maintenance (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
            recent_count INTEGER NOT NULL DEFAULT 0,
            cleaned_at REAL NOT NULL DEFAULT 0
        );
        INSERT INTO api_activity_maintenance(singleton) VALUES(1);
        CREATE TRIGGER api_activity_insert_count AFTER INSERT ON api_activity_recent
        BEGIN
            UPDATE api_activity_maintenance SET recent_count=recent_count+1 WHERE singleton=1;
        END;
        CREATE TRIGGER api_activity_delete_count AFTER DELETE ON api_activity_recent
        BEGIN
            UPDATE api_activity_maintenance SET recent_count=recent_count-1 WHERE singleton=1;
        END;
        """,
    ),
]


def init() -> None:
    """Create or upgrade the schema. Idempotent; safe to call from every worker."""
    global _initialised
    if _initialised:
        return
    with write() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "  version INTEGER PRIMARY KEY,"
            "  applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        applied = {row["version"] for row in conn.execute("SELECT version FROM schema_version")}
        for version, ddl in MIGRATIONS:
            if version in applied:
                continue
            # executescript implicitly commits the write transaction first,
            # allowing a second worker to race the same migration. Execute
            # complete statements inside the existing BEGIN IMMEDIATE instead.
            statement = ""
            for line in ddl.splitlines(keepends=True):
                statement += line
                if sqlite3.complete_statement(statement):
                    conn.execute(statement)
                    statement = ""
            if statement.strip():
                conn.execute(statement)
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            logger.info("store: applied migration %d", version)
    _initialised = True


def reset_for_tests(tmp_dir: Path) -> None:
    """Point the store at a throwaway directory. Tests only."""
    global DATA_DIR, DB_PATH, _initialised
    DATA_DIR = tmp_dir
    DB_PATH = tmp_dir / "privatools.db"
    _initialised = False
    init()
