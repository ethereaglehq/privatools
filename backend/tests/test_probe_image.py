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
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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


class _HostEcho(BaseHTTPRequestHandler):
    """Answers like TrustedHostMiddleware: 400 unless the Host header is allowed."""

    allowed = "privatools.me"

    def do_GET(self):  # noqa: N802 (http.server's name)
        ok = self.headers.get("Host") == self.allowed
        body = self.headers.get("Host", "").encode()
        self.send_response(200 if ok else 400)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


@pytest.mark.parametrize("host_header,expected", [(None, 400), ("privatools.me", 200)])
def test_the_deploy_probe_asks_for_the_public_host_name(probe, monkeypatch, host_header, expected):
    # The rollout sets PRIVATOOLS_PROBE_HOST, so a release whose TRUSTED_HOSTS
    # rejects the public name fails the page probe instead of the check through
    # nginx after a switch. Unset (CI), requests go to 127.0.0.1 as before.
    if host_header:
        monkeypatch.setenv("PRIVATOOLS_PROBE_HOST", host_header)
    else:
        monkeypatch.delenv("PRIVATOOLS_PROBE_HOST", raising=False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HostEcho)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = probe.fetch(f"http://127.0.0.1:{server.server_address[1]}", "/")
    finally:
        server.shutdown()
        server.server_close()
    assert status == expected, body
