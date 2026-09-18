"""Conservative, same-host async job limits (no background threads at import)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ... import job_handover, store


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
    queue_seconds: int = job_handover.QUEUE_SECONDS
    runtime_seconds: int = 300
    lease_seconds: int = job_handover.LEASE_SECONDS
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
    """Where this container's supervisor reports its role (see backend/app/job_handover.py)."""
    return job_handover.state_path()
