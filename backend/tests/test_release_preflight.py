"""deploy/release-preflight.py --zero-downtime: the rollout's prerequisites, read-only.

The cut-over runbook runs it from a `git archive` export in /tmp, as ubuntu,
before anything is installed: it must not need a checkout, a compose file or
root, and must not run nginx or Docker.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_zero_downtime_preflight_runs_from_an_export_without_nginx_docker_or_git(tmp_path):
    export = tmp_path / "export" / "deploy"
    export.mkdir(parents=True)
    shutil.copy(ROOT / "deploy/release-preflight.py", export / "release-preflight.py")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name in ("nginx", "docker", "git", "sudo", "curl"):
        (fake_bin / name).write_text(f"#!/bin/sh\necho {name} \"$@\" >> {tmp_path}/called\nexit 1\n")
        (fake_bin / name).chmod(0o755)
    env = {**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run([sys.executable, str(export / "release-preflight.py"), "--zero-downtime"], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=60)
    report = json.loads(result.stdout)
    names = [check["check"] for check in report["checks"]]
    assert names == [
        "nginx upstream file names 8000 or 8001",
        "nginx site proxies only through privatools_app",
        "nginx master PID file readable (reload verification)",
        "sudo -n allows the upstream switch",
        "the rollout's check through nginx answers (curl --resolve privatools.me:443:127.0.0.1)",
        "deploy lock owned by the deploy user, or absent",
        "fs.protected_regular (informational)",
        "interim port 127.0.0.1:8001 free",
        "memory for a second container (MemAvailable >= 1536 MB)",
    ]
    called = (tmp_path / "called").read_text().split("\n") if (tmp_path / "called").exists() else []
    assert not [line for line in called if line.split(" ")[0] in ("nginx", "docker", "git")], called
    # This VM is not production: the nginx checks fail, which is the exit status.
    assert result.returncode == 1
    assert report["mode"] == "zero-downtime-read-only"
