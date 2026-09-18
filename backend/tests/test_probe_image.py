"""The CI image probe boots releases the way production runs them.

Production runs async jobs. The deploy's first deploy after the cut-over
makes a release's job supervisor take the queue only after traffic has moved
(the old supervisor cannot hand over), so CI must have seen that supervisor
take the lock in a booted image before any release is tagged.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def probe(monkeypatch):
    spec = importlib.util.spec_from_file_location("probe_image", ROOT / "scripts/ci/probe-image.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ci_boots_the_image_with_async_jobs_enabled(probe, monkeypatch):
    monkeypatch.setenv("API_V1_JOBS_ENABLED", "false")
    probe.isolate_environment("some-image", "some-sha")
    assert os.environ["API_V1_JOBS_ENABLED"] == "true"
    assert (os.environ["PRIVATOOLS_IMAGE"], os.environ["GIT_SHA"]) == ("some-image", "some-sha")


@pytest.mark.parametrize("local,ok", [
    ({"role": "active", "alive": True}, True),
    ({"role": "standby", "alive": True}, False),
    ({"role": "active", "alive": False}, False),
    (None, False),
])
def test_ci_requires_the_job_supervisor_to_hold_the_queue(probe, local, ok):
    status = {"enabled": True, "local": local}
    if ok:
        assert "holds the job queue" in probe.check_supervisor_status(status)
    else:
        with pytest.raises(probe.CheckFailed):
            probe.check_supervisor_status(status)
    with pytest.raises(probe.CheckFailed):
        probe.check_supervisor_status({"enabled": False, "local": None})
