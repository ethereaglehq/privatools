"""What this container's async job supervisor is doing, for readiness and the deploy.

    python -m backend.app.job_handover --status

Standard library only, on purpose. The zero-downtime deploy polls the status
about once a second while it hands the job queue from one container to the
other. The job package's own entry point imports FastAPI, pydantic and the
auth stack, which cost about 1 CPU-second and 100 MB per poll.

The supervisor (backend/app/api_v1/jobs/worker.py) rewrites a small state file
about once a second: its role (active, draining or standby), whether it is a
passive standby, its PID, host and build, when it wrote the file and since when
it has had that role. The file lives in the container's private /tmp (compose
mounts a per-container tmpfs), never on a shared volume. During a deploy two
containers share app-data and app-temp, and each must see its own supervisor.

The deploy depends on this command's output (deploy/README.md lists the
interfaces): the keys enabled, local.role, local.passive, local.alive,
local.ready, running_jobs and queued_jobs.
"""
from __future__ import annotations

import json
import os
import socket
import sqlite3
import sys
import time
from pathlib import Path

# The one definition of these two limits; jobs/config.py's Limits uses them.
# A heartbeat or state file older than a lease is dead. A queued job fails
# after QUEUE_SECONDS, so a standby that has waited that long for the lock
# can no longer promise to run what it accepts.
LEASE_SECONDS = 30
QUEUE_SECONDS = 900

ROLES = ("active", "draining", "standby")


def state_path() -> Path:
    return Path(os.environ.get("API_V1_JOBS_WORKER_STATE", "/tmp/privatools-job-worker.json"))


def database_path() -> Path:
    """The accounts database, derived exactly as backend/app/store.py does."""
    return Path(os.environ.get("PRIVATOOLS_DATA_DIR", "data")) / "privatools.db"


def enabled() -> bool:
    return os.environ.get("API_V1_JOBS_ENABLED", "false").lower() == "true"


def build_sha() -> str:
    return os.environ.get("PRIVATOOLS_BUILD_SHA", "unknown")


class StateReporter:
    """Written by the supervisor about once a second and on every change."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or state_path()
        self.last: tuple[str, bool, float] = ("", False, 0.0)
        self.since = 0.0

    def __call__(self, role: str, *, passive: bool = False) -> None:
        now = time.time()
        if role != self.last[0]:
            self.since = now
        elif (role, passive) == self.last[:2] and now - self.last[2] < 1:
            return
        state = {"role": role, "passive": passive, "pid": os.getpid(), "host": socket.gethostname(),
                 "build_sha": build_sha(), "updated": now, "since": self.since}
        temporary = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
        try:
            temporary.write_text(json.dumps(state), encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError:
            # Readiness then falls back to the shared heartbeat alone.
            return
        self.last = (role, passive, now)

    def clear(self) -> None:
        try:
            if json.loads(self.path.read_text(encoding="utf-8")).get("pid") == os.getpid():
                self.path.unlink()
        except (OSError, ValueError, AttributeError):
            pass


def read_state() -> dict | None:
    try:
        state = json.loads(state_path().read_text(encoding="utf-8"))
        state["pid"] = int(state["pid"])
        state["updated"] = float(state["updated"])
        state["since"] = float(state.get("since", state["updated"]))
    except (OSError, ValueError, TypeError, KeyError):
        return None
    return state if isinstance(state, dict) else None


def live_state(now: float | None = None) -> dict | None:
    """This container's supervisor, if its loop is running and runs this build.

    Live means: this host and build, a role it knows, a file rewritten within a
    lease and a living PID. A supervisor writes the file only after it has
    installed its signal handlers, so the deploy may signal a live one.
    """
    state = read_state()
    now = time.time() if now is None else now
    if (state is None or state.get("host") != socket.gethostname() or state.get("build_sha") != build_sha()
            or state.get("role") not in ROLES or state["pid"] <= 0
            or now - state["updated"] > LEASE_SECONDS):
        return None
    try:
        os.kill(state["pid"], 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        pass
    return state


def ready_state(now: float | None = None) -> dict | None:
    """live_state, except a standby that has waited more than QUEUE_SECONDS.

    A standby counts as ready so that a deploy's new container passes its
    readiness gate while the old container still owns the queue. The bound
    keeps that from lasting forever: a standby that never gets the lock turns
    /readyz to 503 and job submissions to jobs_unavailable. Pages keep serving,
    because exiting would make the launcher stop the whole container.
    """
    state = live_state(now)
    now = time.time() if now is None else now
    if state and state["role"] == "standby" and now - state["since"] > QUEUE_SECONDS:
        return None
    return state


def status(database: Path | None = None) -> dict:
    """What a deploy needs to hand the queue over: roles and counts, never job contents."""
    now = time.time()
    result: dict = {"enabled": enabled(), "build_sha": build_sha(), "local": None,
                    "active": None, "running_jobs": None, "queued_jobs": None}
    state = read_state()
    if state:
        result["local"] = {"role": state.get("role"), "passive": bool(state.get("passive")),
                           "age": round(now - state["updated"], 3),
                           "role_age": round(now - state["since"], 3),
                           "alive": live_state(now) is not None, "ready": ready_state(now) is not None}
    database = database or database_path()
    if not result["enabled"] or not database.exists():
        return result
    try:
        # Read-only: a status probe must never create or change the database.
        conn = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT * FROM api_async_worker WHERE id=1").fetchone()
            if row:
                result["active"] = {"build_sha": row["build_sha"], "accepting": bool(row["accepting"]),
                                    "age": round(now - row["heartbeat"], 3)}
            result["running_jobs"] = conn.execute(
                "SELECT COUNT(*) FROM api_async_jobs WHERE state='running' AND claim IS NOT NULL").fetchone()[0]
            result["queued_jobs"] = conn.execute(
                "SELECT COUNT(*) FROM api_async_jobs WHERE state='queued'").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        pass
    return result


def main(argv: list[str] | None = None) -> int:
    if (sys.argv[1:] if argv is None else argv) != ["--status"]:
        print("usage: python -m backend.app.job_handover --status", file=sys.stderr)
        return 2
    print(json.dumps(status(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
