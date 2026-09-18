"""Run deploy/oracle-vm/backup-app-data.sh against a Docker double; no Docker, no production.

The installed script is what the nightly backup timer runs. It must keep
working while a zero-downtime deploy is in flight or has left the new release
on the interim container, and must not race a deploy's container replacement.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deploy/oracle-vm/backup-app-data.sh"
CANONICAL, INTERIM = "privatools-privatools-1", "privatools-interim-privatools-1"

FAKE_DOCKER = r'''
import json, os, pathlib, sqlite3, sys
root = pathlib.Path(os.environ["FAKE_ROOT"])
running = json.loads((root / "running.json").read_text())
args = sys.argv[1:]
with (root / "docker.jsonl").open("a") as f:
    f.write(json.dumps(args) + "\n")
if args[0] == "inspect":
    name = args[-1]
    if name not in running:
        sys.exit(1)
    print("true" if running[name] else "false")
elif args[0] == "exec":
    if not running.get(args[1]):
        sys.exit(1)
elif args[0] == "cp":
    source, destination = args[1], args[2]
    if not running.get(source.split(":")[0]):
        sys.exit(1)
    connection = sqlite3.connect(destination)
    connection.execute("CREATE TABLE users (id TEXT)")
    connection.commit()
    connection.close()
'''


def run_backup(tmp_path, running: dict, **env):
    fake_bin = tmp_path / "bin"
    if not fake_bin.exists():
        fake_bin.mkdir()
        docker = fake_bin / "docker"
        docker.write_text(f"#!{sys.executable}\n" + FAKE_DOCKER)
        docker.chmod(0o755)
    (tmp_path / "running.json").write_text(json.dumps(running))
    (tmp_path / "docker.jsonl").unlink(missing_ok=True)
    environment = {**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}", "FAKE_ROOT": str(tmp_path),
                   "DEST_DIR": str(tmp_path / "backups"), "LOCK_FILE": str(tmp_path / "deploy.lock"),
                   "LOCK_WAIT": "1", "BACKUP_PING_URL": "", **env}
    environment.pop("CONTAINER", None)
    environment.update({key: value for key, value in env.items()})
    result = subprocess.run(["/bin/bash", str(SCRIPT)], env=environment, capture_output=True, text=True, timeout=60)
    calls = [json.loads(line) for line in (tmp_path / "docker.jsonl").read_text().splitlines()] \
        if (tmp_path / "docker.jsonl").exists() else []
    return result, calls


def backed_up_from(calls) -> set[str]:
    return {args[1] for args in calls if args[0] == "exec" and "python3" in args}


def written(tmp_path) -> list[Path]:
    return sorted((tmp_path / "backups").glob("privatools-*.db"))


def test_backup_prefers_the_canonical_container(tmp_path):
    result, calls = run_backup(tmp_path, {CANONICAL: True, INTERIM: True})
    assert result.returncode == 0, result.stdout + result.stderr
    assert backed_up_from(calls) == {CANONICAL}
    [snapshot] = written(tmp_path)
    assert sqlite3.connect(snapshot).execute("SELECT name FROM sqlite_master").fetchone() == ("users",)


def test_backup_uses_the_interim_container_while_a_deploy_left_it_serving(tmp_path):
    # Degraded: the new release serves from the interim; the canonical
    # container is stopped. Both mount the same accounts volume.
    result, calls = run_backup(tmp_path, {CANONICAL: False, INTERIM: True})
    assert result.returncode == 0, result.stdout + result.stderr
    assert backed_up_from(calls) == {INTERIM}
    assert len(written(tmp_path)) == 1


def test_backup_fails_loudly_when_no_container_runs(tmp_path):
    result, _ = run_backup(tmp_path, {CANONICAL: False})
    assert result.returncode == 1
    assert "no PrivaTools container is running" in result.stdout
    assert not written(tmp_path)


def test_backup_waits_for_a_deploy_holding_the_lock(tmp_path):
    lock = (tmp_path / "deploy.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        started = time.monotonic()
        result, calls = run_backup(tmp_path, {CANONICAL: True})
        waited = time.monotonic() - started
    finally:
        lock.close()
    assert result.returncode == 0, result.stdout + result.stderr
    assert waited >= 1 and "deploy lock" in result.stdout
    assert backed_up_from(calls) == {CANONICAL}

    # A free lock is taken without comment.
    result, _ = run_backup(tmp_path, {CANONICAL: True})
    assert result.returncode == 0 and "deploy lock" not in result.stdout


def test_explicit_container_is_still_honoured(tmp_path):
    result, calls = run_backup(tmp_path, {CANONICAL: True, "other": True}, CONTAINER="other")
    assert result.returncode == 0, result.stdout + result.stderr
    assert backed_up_from(calls) == {"other"}
