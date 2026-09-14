"""O4/O7: /readyz free-disk check + build_sha in the readiness response."""

import collections
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.utils import health

_Usage = collections.namedtuple("Usage", "total used free")


def test_free_disk_in_checks_list():
    assert "free_disk" in [name for name, _ in health._CHECKS]


def test_free_disk_passes_with_ample_space():
    # The CI runner / dev box always has well over the 250 MB threshold free.
    assert health._check_free_disk() is True


def test_free_disk_fails_below_threshold(monkeypatch):
    monkeypatch.setattr(health, "_FREE_DISK_MIN_MB", 250)
    monkeypatch.setattr(
        health.shutil, "disk_usage", lambda _p: _Usage(10 * 1024**3, 0, 1024 * 1024)
    )  # 1 MB free
    assert health._check_free_disk() is False


def test_free_disk_fails_on_oserror(monkeypatch):
    def boom(_p):
        raise OSError("no such path")

    monkeypatch.setattr(health.shutil, "disk_usage", boom)
    assert health._check_free_disk() is False


def test_readyz_response_includes_build_sha(client):
    body = client.get("/readyz").json()
    assert "build_sha" in body
    assert "checks" in body
    assert "free_disk" in body["checks"]


def test_enabled_jobs_require_a_healthy_worker(client, monkeypatch):
    from backend.app import main
    from backend.app.api_v1 import jobs

    monkeypatch.setenv("API_V1_JOBS_ENABLED", "true")
    monkeypatch.setattr(main, "run_readiness_checks", lambda: (True, {}))
    monkeypatch.setattr(jobs, "capability", lambda: {"available": False})
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["checks"]["api_job_worker"] is False

    monkeypatch.setattr(jobs, "capability", lambda: {"available": True})
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["checks"]["api_job_worker"] is True


def test_disabled_jobs_do_not_block_existing_api_readiness(client, monkeypatch):
    from backend.app import main
    from backend.app.api_v1 import jobs

    monkeypatch.setenv("API_V1_JOBS_ENABLED", "false")
    monkeypatch.setattr(main, "run_readiness_checks", lambda: (True, {}))

    def unexpected_probe():
        raise AssertionError("disabled jobs must not require a worker")

    monkeypatch.setattr(jobs, "capability", unexpected_probe)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert "api_job_worker" not in response.json()["checks"]
