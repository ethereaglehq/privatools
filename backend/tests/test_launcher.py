"""Exercise supervisor failure and shutdown using real, inert child processes."""

import json
from pathlib import Path
import signal
import subprocess
import sys
import time

from backend.app import launcher


def child_commands(tmp_path: Path, *, fail: bool) -> list[list[str]]:
    waiting = (
        "import pathlib,signal,time,sys; "
        f"p=pathlib.Path({str(tmp_path / 'web-state')!r}); "
        "signal.signal(signal.SIGTERM, lambda *_: (p.write_text('stopped'),sys.exit(0))); "
        "p.write_text('started'); time.sleep(15)"
    )
    worker = "import time,sys; time.sleep(0.5); sys.exit(7)" if fail else waiting.replace("web-state", "worker-state")
    return [[sys.executable, "-c", worker], [sys.executable, "-c", waiting]]


def start_supervisor(tmp_path, *, fail):
    code = (
        "from backend.app.launcher import supervise; "
        f"raise SystemExit(supervise({child_commands(tmp_path, fail=fail)!r}, grace_seconds=2))"
    )
    return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_worker_failure_stops_web_and_returns_failure(tmp_path):
    process = start_supervisor(tmp_path, fail=True)
    _, stderr = process.communicate(timeout=6)
    assert process.returncode == 7, stderr.decode()
    assert (tmp_path / "web-state").read_text() == "stopped"


def test_sigterm_drains_both_children(tmp_path):
    process = start_supervisor(tmp_path, fail=False)
    try:
        deadline = time.monotonic() + 4
        while not all((tmp_path / name).exists() for name in ("web-state", "worker-state")):
            assert time.monotonic() < deadline
            time.sleep(0.02)
        process.send_signal(signal.SIGTERM)
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr.decode()
        assert (tmp_path / "web-state").read_text() == "stopped"
        assert (tmp_path / "worker-state").read_text() == "stopped"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_disabled_jobs_exec_the_existing_web_command(monkeypatch):
    monkeypatch.setenv("API_V1_JOBS_ENABLED", "false")
    calls = []

    def execv(binary, args):
        calls.append((binary, args))
        raise SystemExit(0)

    monkeypatch.setattr(launcher.os, "execv", execv)
    try:
        launcher.main()
    except SystemExit:
        pass
    assert calls == [(sys.executable, launcher.web_command())]
    assert calls[0][1][calls[0][1].index("--workers") + 1] == "2"


def test_container_uses_launcher_and_preserves_combined_resource_limits():
    root = Path(__file__).resolve().parents[2]
    dockerfile = (root / "Dockerfile").read_text()
    command = next(line[4:] for line in dockerfile.splitlines() if line.startswith("CMD "))
    assert json.loads(command) == ["python", "-m", "backend.app.launcher"]
    compose = (root / "docker-compose.yml").read_text()
    assert "memory: 4G" in compose and "cpus: '1.8'" in compose
    assert "stop_grace_period: 45s" in compose
