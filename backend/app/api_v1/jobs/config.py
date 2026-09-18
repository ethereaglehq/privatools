"""Conservative, same-host async job limits (no background threads at import)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ... import store


@dataclass(frozen=True)
class Limits:
    input_bytes: int = 50 * 1024 * 1024
    result_bytes: int = 100 * 1024 * 1024
    storage_bytes: int = 1024 * 1024 * 1024
    disk_headroom: int = 512 * 1024 * 1024
    max_pending: int = 24
    per_key: int = 3
    per_account: int = 6
    submissions_per_minute: int = 30
    upload_seconds: int = 300
    queue_seconds: int = 900
    runtime_seconds: int = 300
    lease_seconds: int = 30
    heartbeat_seconds: int = 5
    result_seconds: int = 3600
    tombstone_seconds: int = 86400
    attempts: int = 2

    @property
    def reservation_bytes(self) -> int:
        # Inputs + scratch output + a published result during atomic promotion.
        return self.input_bytes + 2 * self.result_bytes


LIMITS = Limits()


def enabled() -> bool:
    return os.environ.get("API_V1_JOBS_ENABLED", "false").lower() == "true"


def root() -> Path:
    return store.DATA_DIR / "jobs"


def build_sha() -> str:
    return os.environ.get("PRIVATOOLS_BUILD_SHA", "unknown")


def worker_state_path() -> Path:
    """Where this container's supervisor reports its role to its own web workers.

    It must be private to one container, never on a shared volume: during a
    deploy two containers share app-data and app-temp, and each web process
    has to see its own supervisor, not the other container's. Compose mounts
    /tmp as a per-container tmpfs, which is exactly that scope.
    """
    return Path(os.environ.get("API_V1_JOBS_WORKER_STATE", "/tmp/privatools-job-worker.json"))
