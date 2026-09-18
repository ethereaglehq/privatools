"""Execute deploy/oracle-vm/rollout.sh against inert command doubles.

A small simulated host (containers, their readiness and pages, the nginx
upstream file, job supervisor roles) stands in for docker, curl, the nginx
switch and the page probe, so these prove sequencing and failure handling:
the new release takes traffic only after it is ready and serves real pages,
every failure leaves a serving release behind nginx, and the job queue is
handed over rather than interrupted. They never run Docker, nginx or the
network; deploy/README.md records the live load test on a real stand-in.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
ROLLOUT = ROOT / "deploy/oracle-vm/rollout.sh"
OLD, NEW = "b" * 40, "a" * 40

FAKE = r'''
import json, os, pathlib, sys
root = pathlib.Path(os.environ["FAKE_ROOT"])
world_path = root / "world.json"
world = json.loads(world_path.read_text())
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]

def save():
    world_path.write_text(json.dumps(world))

def event(*item):
    with (root / "events.jsonl").open("a") as f:
        f.write(json.dumps(list(item)) + "\n")

def by_port(port):
    for cid, c in world["containers"].items():
        if c["port"] == port and c["status"] == "running":
            return cid, c
    return None, None

def answer_readyz(port):
    cid, c = by_port(port)
    image = world["images"].get(c["image"], {}) if c else {}
    if not c or not image.get("ready", True):
        sys.exit(22)
    print(json.dumps({"status": "ready", "build_sha": c["sha"], "checks": {}}))

def upstream_port():
    text = pathlib.Path(os.environ["UPSTREAM_FILE"]).read_text()
    return int(text.split("server 127.0.0.1:")[1].split(";")[0])

if name == "curl":
    url = next(a for a in args if a.startswith("http"))
    if url == os.environ["PUBLIC_READY_URL"]:
        if world.get("public_stuck_on"):
            port = world["public_stuck_on"]
        else:
            port = upstream_port()
        answer_readyz(port)
    else:
        answer_readyz(int(url.split(":")[2].split("/")[0]))

elif name == "nginx-switch":
    port = int(args[-1])
    event("switch", port)
    if world.get("switch_fails"):
        sys.exit(3)
    pathlib.Path(os.environ["UPSTREAM_FILE"]).write_text(f"upstream privatools_app {{\n    server 127.0.0.1:{port};\n}}\n")

elif name == "probe":
    container = args[args.index("--running") + 1]
    c = world["containers"][container]
    event("probe", c["project"])
    sys.exit(0 if world["images"].get(c["image"], {}).get("pages", True) else 1)

elif name == "docker":
    if args[0] == "compose":
        project = args[args.index("-p") + 1]
        rest = args[args.index("-p") + 2:]
        while rest and rest[0] == "-f":
            rest = rest[2:]
        command = rest[0]
        event("compose", project, command, os.environ.get("PRIVATOOLS_IMAGE"), os.environ.get("GIT_SHA"),
              os.environ.get("PRIVATOOLS_HOST_PORT"), os.environ.get("PRIVATOOLS_DATA_VOLUME"))
        mine = [cid for cid, c in world["containers"].items() if c["project"] == project]
        if command == "up":
            if project in world.get("up_fails", []):
                sys.exit(1)
            for cid in mine:
                del world["containers"][cid]
            ref = os.environ["PRIVATOOLS_IMAGE"]
            image = world["refs"].get(ref, ref)
            world["next"] += 1
            cid = f"c{world['next']:02d}{project.replace('-', '')}"
            world["containers"][cid] = {"project": project, "image": image, "sha": os.environ["GIT_SHA"],
                                        "port": int(os.environ["PRIVATOOLS_HOST_PORT"]), "status": "running",
                                        "role": "standby"}
        elif command == "down":
            for cid in mine:
                del world["containers"][cid]
        elif command == "stop":
            for cid in mine:
                world["containers"][cid]["status"] = "exited"
        save()
    elif args[0] == "ps":
        project = next(a.split("=", 2)[2] for a in args if a.startswith("label=com.docker.compose.project="))
        for cid, c in world["containers"].items():
            if c["project"] == project:
                print(cid)
    elif args[0] == "inspect":
        form, cid = args[2], args[3]
        c = world["containers"].get(cid)
        if c is None:
            sys.exit(1)
        if form == "{{.Image}}":
            print(c["image"])
        elif ".Config.Env" in form:
            print(f"PRIVATOOLS_BUILD_SHA={c['sha']}")
        elif ".Mounts" in form:
            print("privatools_app-data" if "/app/data" in form else "privatools_app-temp")
        elif form == "{{.State.Running}}":
            print("true" if c["status"] == "running" else "false")
        else:
            print(c["status"], 0)
    elif args[0] == "image":
        ref = args[-1]
        print(world["refs"].get(ref, ref))
    elif args[0] == "exec":
        cid = args[1]
        c = world["containers"].get(cid)
        if not c or c["status"] != "running":
            sys.exit(1)  # like docker exec on a stopped or missing container
        if "--status" in args:
            if not c or world["images"].get(c["image"], {}).get("legacy"):
                sys.exit(2)
            print(json.dumps({"enabled": world.get("jobs", True), "local": {"role": c["role"]},
                              "running_jobs": 0, "queued_jobs": 0}))
        else:
            print("  sl  local_address rem_address   st")
    elif args[0] == "kill":
        signal, cid = args[2], args[3]
        event("kill", signal, world["containers"][cid]["project"])
        c = world["containers"][cid]
        if signal == "SIGUSR1" and c["role"] == "active":
            # The drained supervisor releases the lock; the eager standby of
            # the other container takes it.
            c["role"] = "standby"
            for other in world["containers"].values():
                if other is not c and other["status"] == "running" and not world["images"].get(other["image"], {}).get("legacy"):
                    other["role"] = "active"
                    break
        elif signal == "SIGUSR2" and not any(o["role"] == "active" for o in world["containers"].values()):
            c["role"] = "active"
        save()
    elif args[0] == "stop":
        event("stop", world["containers"][args[-1]]["project"])
        world["containers"][args[-1]]["status"] = "exited"
        save()
    elif args[0] == "rm":
        world["containers"].pop(args[-1], None)
        save()
'''


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def bash() -> str:
    found = shutil.which("bash") or "/bin/bash"
    major = subprocess.run([found, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True).stdout.strip()
    if not major.isdigit() or int(major) < 4:
        pytest.skip("rollout.sh needs bash 4 (the VM's bash); this host has an older one")
    return found


class Host:
    """The simulated VM: one canonical container on OLD, nginx pointing at it."""

    def __init__(self, tmp_path: Path):
        self.root = tmp_path
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        for name in ("docker", "curl", "nginx-switch", "probe"):
            script = self.bin / name
            script.write_text(f"#!{sys.executable}\n" + FAKE)
            script.chmod(0o755)
        self.canonical_port, self.interim_port = free_port(), free_port()
        self.upstream = tmp_path / "privatools-upstream.conf"
        self.set_upstream(self.canonical_port)
        self.site = tmp_path / "site.conf"
        self.site.write_text("location / { proxy_pass http://privatools_app; }\n")
        self.meminfo = tmp_path / "meminfo"
        self.meminfo.write_text("MemTotal: 12000000 kB\nMemAvailable: 6000000 kB\n")
        self.world = {
            "next": 1,
            "refs": {"ghcr.io/x@sha256:new": "sha256:new", "ghcr.io/x@sha256:old": "sha256:old"},
            "images": {"sha256:new": {}, "sha256:old": {}},
            "containers": {"c01privatools": {"project": "privatools", "image": "sha256:old", "sha": OLD,
                                              "port": self.canonical_port, "status": "running", "role": "active"}},
        }
        self.save()

    def save(self):
        (self.root / "world.json").write_text(json.dumps(self.world))

    def load(self) -> dict:
        return json.loads((self.root / "world.json").read_text())

    def set_upstream(self, port: int):
        self.upstream.write_text(f"upstream privatools_app {{\n    server 127.0.0.1:{port};\n}}\n")

    def live_port(self) -> int:
        return int(self.upstream.read_text().split("server 127.0.0.1:")[1].split(";")[0])

    def events(self) -> list[list]:
        path = self.root / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def run(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        environment = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_ROOT": str(self.root),
            "REPO_DIR": str(ROOT),
            "STATE_DIR": str(self.root),
            "UPSTREAM_FILE": str(self.upstream),
            "NGINX_SITE": str(self.site),
            "NGINX_SWITCH": "nginx-switch set",
            "NGINX_PID_FILE": str(self.root / "no-nginx.pid"),
            "PUBLIC_READY_URL": "http://public.test/readyz",
            "PUBLIC_RESOLVE": "",
            "PROBE_SCRIPT": str(self.bin / "probe"),
            "CANONICAL_PORT": str(self.canonical_port),
            "INTERIM_PORT": str(self.interim_port),
            "MEMINFO": str(self.meminfo),
            "PRIVATOOLS_DEPLOY_LOCK_HELD": "1",
            "READY_TIMEOUT": "2", "DRAIN_MAX": "1", "DRAIN_EXTRA": "1", "DRAIN_QUIET": "0",
            "HANDOVER_MAX": "3", "HANDOVER_IDLE_WAIT": "1", "POLL": "0.05",
            **env,
        }
        environment.pop("COMPOSE_PROJECT", None)
        return subprocess.run([bash(), str(ROLLOUT), *args], env=environment, capture_output=True, text=True,
                              timeout=120)

    def containers(self, project: str) -> list[dict]:
        return [c for c in self.load()["containers"].values() if c["project"] == project]


@pytest.fixture
def host(tmp_path):
    return Host(tmp_path)


def steps(events: list[list]) -> list[tuple]:
    """The externally visible actions, in order, without their details."""
    out = []
    for item in events:
        if item[0] == "compose":
            out.append(("compose", item[1], item[2]))
        elif item[0] in ("switch", "probe"):
            out.append((item[0], item[1]))
        elif item[0] in ("kill", "stop"):
            out.append(tuple(item))
    return out


def test_good_release_moves_through_the_interim_and_back_to_the_canonical_port(host):
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 0, result.stdout + result.stderr
    assert steps(host.events()) == [
        ("compose", "privatools-interim", "up"),
        ("probe", "privatools-interim"),
        ("kill", "SIGUSR2", "privatools-interim"),  # the successor may take the queue...
        ("kill", "SIGUSR1", "privatools"),          # ...when the old one finishes its job; before any switch
        ("switch", host.interim_port),
        ("compose", "privatools", "up"),            # only after the old container drained
        ("probe", "privatools"),
        ("kill", "SIGUSR2", "privatools"),
        ("kill", "SIGUSR1", "privatools-interim"),
        ("switch", host.canonical_port),
        ("compose", "privatools-interim", "down"),
    ]
    up = next(e for e in host.events() if e[:3] == ["compose", "privatools-interim", "up"])
    # The verified image and its revision, on the interim port, on the live data volume.
    assert up[3:] == ["ghcr.io/x@sha256:new", NEW, str(host.interim_port), "privatools_app-data"]
    assert host.live_port() == host.canonical_port
    [canonical] = host.containers("privatools")
    assert (canonical["image"], canonical["sha"], canonical["role"]) == ("sha256:new", NEW, "active")
    assert not host.containers("privatools-interim")
    assert (host.root / ".privatools-deploy.previous").read_text().split() == ["sha256:old", OLD]


@pytest.mark.parametrize("fault,message", [("ready", "never became ready"), ("pages", "failed the real-page probe")])
def test_rejected_release_never_takes_traffic_and_is_removed(host, fault, message):
    host.world["images"]["sha256:new"] = {fault: False}
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 1, result.stdout + result.stderr
    assert message in result.stdout
    actions = steps(host.events())
    assert not [a for a in actions if a[0] == "switch"]
    assert not [a for a in actions if a[0] == "kill"], "the old supervisor must keep the queue"
    assert actions[-1] == ("compose", "privatools-interim", "down")
    assert host.live_port() == host.canonical_port
    assert [c["sha"] for c in host.containers("privatools")] == [OLD]
    assert not host.containers("privatools-interim")
    assert not (host.root / ".privatools-deploy.previous").exists()


def test_failed_switch_returns_the_queue_and_removes_the_interim(host):
    host.world["switch_fails"] = True
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 1, result.stdout + result.stderr
    actions = steps(host.events())
    assert ("switch", host.interim_port) in actions
    # The drained old supervisor is resumed, the interim (which took the queue
    # when the old one released it) drains back to it, and then it is removed.
    after = actions[actions.index(("switch", host.interim_port)) + 1:]
    assert after == [("kill", "SIGUSR2", "privatools"), ("kill", "SIGUSR2", "privatools"),
                     ("kill", "SIGUSR1", "privatools-interim"), ("compose", "privatools-interim", "down")]
    assert host.live_port() == host.canonical_port
    assert [c["role"] for c in host.containers("privatools")] == ["active"]


def test_switch_that_does_not_reach_the_new_build_is_undone(host):
    # nginx reloaded but still answers from the old container.
    host.world["public_stuck_on"] = host.canonical_port
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 1, result.stdout + result.stderr
    switches = [a for a in steps(host.events()) if a[0] == "switch"]
    assert switches == [("switch", host.interim_port), ("switch", host.canonical_port)]
    assert host.live_port() == host.canonical_port
    assert [c["sha"] for c in host.containers("privatools")] == [OLD]
    assert not host.containers("privatools-interim")


def test_canonical_that_will_not_start_leaves_the_new_release_serving_from_the_interim(host):
    host.world["up_fails"] = ["privatools"]
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 3, result.stdout + result.stderr
    assert "DEGRADED" in result.stdout
    assert host.live_port() == host.interim_port
    [interim] = host.containers("privatools-interim")
    assert interim["sha"] == NEW and interim["status"] == "running"
    assert (host.root / ".privatools-deploy.resume").exists()

    # The next run backs off instead of rebooting a failing container every minute...
    again = host.run("ghcr.io/x@sha256:new", NEW)
    assert again.returncode == 3 and "failed less than" in again.stdout
    # ...and after the backoff finishes the move once the canonical can start.
    host.world = host.load()
    host.world["up_fails"] = []
    host.save()
    past = time.time() - 3600
    os.utime(host.root / ".privatools-deploy.resume", (past, past))
    resumed = host.run("ghcr.io/x@sha256:new", NEW)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "resuming" in resumed.stdout
    assert host.live_port() == host.canonical_port
    assert [c["sha"] for c in host.containers("privatools")] == [NEW]
    assert not host.containers("privatools-interim")
    assert not (host.root / ".privatools-deploy.resume").exists()


def test_leftover_interim_is_drained_and_removed_before_a_new_deploy(host):
    host.world["containers"]["c09privatoolsinterim"] = {
        "project": "privatools-interim", "image": "sha256:old", "sha": OLD, "port": host.interim_port,
        "status": "running", "role": "standby"}
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "left an interim container behind" in result.stdout
    assert steps(host.events())[0] == ("kill", "SIGUSR2", "privatools")
    assert steps(host.events())[2] == ("compose", "privatools-interim", "down")


def test_run_killed_after_its_switch_is_finished_by_the_next_run(host):
    # A previous run switched nginx to the interim and died before draining
    # the old canonical container, whose supervisor still holds the queue.
    host.set_upstream(host.interim_port)
    host.world["containers"]["c09privatoolsinterim"] = {
        "project": "privatools-interim", "image": "sha256:new", "sha": NEW, "port": host.interim_port,
        "status": "running", "role": "standby"}
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "resuming" in result.stdout
    assert steps(host.events()) == [
        ("kill", "SIGUSR2", "privatools-interim"),  # the old canonical hands the queue over...
        ("kill", "SIGUSR1", "privatools"),
        ("compose", "privatools", "up"),            # ...before compose stops it
        ("probe", "privatools"),
        ("kill", "SIGUSR2", "privatools"),
        ("kill", "SIGUSR1", "privatools-interim"),
        ("switch", host.canonical_port),
        ("compose", "privatools-interim", "down"),
    ]
    assert host.live_port() == host.canonical_port
    assert [(c["sha"], c["role"]) for c in host.containers("privatools")] == [(NEW, "active")]
    assert not host.containers("privatools-interim")


def test_interim_that_stopped_serving_is_replaced_by_a_serving_canonical(host):
    # nginx still names the interim port, but the interim no longer answers;
    # the canonical container does. Go back to it and retire the interim
    # through a queue handover rather than killing it.
    host.set_upstream(host.interim_port)
    host.world["images"]["sha256:broken"] = {"ready": False}
    host.world["containers"]["c09privatoolsinterim"] = {
        "project": "privatools-interim", "image": "sha256:broken", "sha": NEW, "port": host.interim_port,
        "status": "running", "role": "active"}
    host.world["containers"]["c01privatools"]["role"] = "standby"
    host.save()
    result = host.run("ghcr.io/x@sha256:old", OLD)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "switched nginx back to the canonical container" in result.stdout
    assert steps(host.events()) == [
        ("switch", host.canonical_port),
        ("kill", "SIGUSR2", "privatools"),
        ("kill", "SIGUSR1", "privatools-interim"),
        ("compose", "privatools-interim", "down"),
    ]
    assert host.live_port() == host.canonical_port
    assert [c["role"] for c in host.containers("privatools")] == ["active"]


def test_stopped_canonical_container_is_replaced_without_drain_or_signals(host):
    host.world["containers"]["c01privatools"]["status"] = "exited"
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "is not running" in result.stdout
    assert "predates handover" not in result.stdout
    actions = steps(host.events())
    assert not [a for a in actions if a[0] in ("kill", "stop") and a[-1] == "privatools"
                and actions.index(a) < actions.index(("compose", "privatools", "up"))]
    assert [c["sha"] for c in host.containers("privatools")] == [NEW]
    # The stopped release is still recorded for rollback.
    assert (host.root / ".privatools-deploy.previous").read_text().split() == ["sha256:old", OLD]


def test_same_image_and_build_is_a_no_op(host):
    result = host.run("ghcr.io/x@sha256:old", OLD)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "already serves" in result.stdout
    assert not host.events()


@pytest.mark.parametrize("breakage,message", [
    ("memory", "refusing to start a second container"),
    ("upstream", "install the nginx switch first"),
    ("site", "does not proxy only through"),
])
def test_unmet_preconditions_change_nothing(host, breakage, message):
    if breakage == "memory":
        host.meminfo.write_text("MemAvailable: 1000000 kB\n")
    elif breakage == "upstream":
        host.upstream.unlink()
    else:
        host.site.write_text("location / { proxy_pass http://127.0.0.1:8000; }\n")
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 2, result.stdout + result.stderr
    assert message in result.stdout
    assert not host.events()


def test_supervisor_that_cannot_drain_is_stopped_only_when_idle(host):
    # The first deploy after the cut-over replaces a release without --status.
    host.world["images"]["sha256:old"] = {"legacy": True}
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 0, result.stdout + result.stderr
    actions = steps(host.events())
    assert ("kill", "SIGUSR1", "privatools") not in actions
    assert "predates handover" in result.stdout
    stop = actions.index(("stop", "privatools"))
    assert actions.index(("switch", host.interim_port)) < stop < actions.index(("compose", "privatools", "up"))


def test_rollback_redeploys_the_recorded_previous_release(host):
    assert host.run("ghcr.io/x@sha256:new", NEW).returncode == 0
    (host.root / "events.jsonl").unlink()
    result = host.run("--rollback")
    assert result.returncode == 0, result.stdout + result.stderr
    assert [c["sha"] for c in host.containers("privatools")] == [OLD]
    assert (host.root / ".privatools-deploy.previous").read_text().split() == ["sha256:new", NEW]
    assert steps(host.events())[0] == ("compose", "privatools-interim", "up")


def test_disabled_jobs_send_no_supervisor_signals(host):
    host.world["jobs"] = False
    host.save()
    result = host.run("ghcr.io/x@sha256:new", NEW)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not [a for a in steps(host.events()) if a[0] == "kill"]


def test_ports_and_privilege_are_consistent_across_the_deploy_files():
    rollout = ROLLOUT.read_text()
    helper = (ROOT / "deploy/oracle-vm/nginx-upstream.sh").read_text()
    sudoers = (ROOT / "deploy/oracle-vm/privatools-deploy.sudoers").read_text()
    assert 'CANONICAL_PORT="${CANONICAL_PORT:-8000}"' in rollout
    assert 'INTERIM_PORT="${INTERIM_PORT:-8001}"' in rollout
    assert 'ALLOWED_PORTS="8000 8001"' in helper
    rule = next(line for line in sudoers.splitlines() if line.startswith("ubuntu "))
    assert rule == ("ubuntu ALL=(root) NOPASSWD: /usr/local/sbin/privatools-nginx-upstream set 8000, "
                    "/usr/local/sbin/privatools-nginx-upstream set 8001")
    assert 'NGINX_SWITCH="${NGINX_SWITCH:-sudo -n /usr/local/sbin/privatools-nginx-upstream set}"' in rollout
    unit = (ROOT / "deploy/oracle-vm/privatools-auto-deploy.service").read_text()
    assert "NoNewPrivileges" not in unit.replace("NoNewPrivileges=:", "")
    # Never an image prune: the replaced image is the rollback image.
    for path in ("rollout.sh", "auto-deploy.sh", "deploy.sh"):
        code = [line for line in (ROOT / "deploy/oracle-vm" / path).read_text().splitlines()
                if not line.lstrip().startswith("#")]
        assert not [line for line in code if "docker" in line and "prune" in line], path


def test_compose_defaults_to_the_steady_state_port_and_the_interim_cannot_own_data():
    compose = (ROOT / "docker-compose.yml").read_text()
    assert '- "127.0.0.1:${PRIVATOOLS_HOST_PORT:-8000}:8000"' in compose
    interim = (ROOT / "deploy/oracle-vm/compose.interim.yml").read_text()
    for volume in ("app-temp", "app-data"):
        block = interim.split(f"  {volume}:\n", 1)[1].split("\n  app-", 1)[0]
        assert "external: true" in block
    assert "${PRIVATOOLS_DATA_VOLUME:?" in interim and "${PRIVATOOLS_TEMP_VOLUME:?" in interim


# ── the root helper, through its unprivileged testing hook ───────────────────

def run_helper(tmp_path, *args, test="true", reload="true"):
    env = {**os.environ, "PRIVATOOLS_UPSTREAM_FILE": str(tmp_path / "up.conf"),
           "PRIVATOOLS_ALLOWED_PORTS": "8000 8001", "PRIVATOOLS_NGINX_TEST": test,
           "PRIVATOOLS_NGINX_RELOAD": reload}
    return subprocess.run([bash(), str(ROOT / "deploy/oracle-vm/nginx-upstream.sh"), *args], env=env,
                          capture_output=True, text=True, timeout=30)


def test_helper_switches_only_to_privatools_ports_and_restores_on_failure(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("the testing hook is ignored as root, by design")
    shipped = (ROOT / "deploy/oracle-vm/privatools-upstream.conf").read_text()
    (tmp_path / "up.conf").write_text(shipped)

    assert run_helper(tmp_path, "set", "8001").returncode == 0
    assert "server 127.0.0.1:8001;" in (tmp_path / "up.conf").read_text()
    assert run_helper(tmp_path, "show").stdout.strip() == "8001"

    for port in ("22", "8002", "8001;", "80 01"):
        assert run_helper(tmp_path, "set", port).returncode == 2
    assert run_helper(tmp_path, "show").stdout.strip() == "8001"

    # nginx -t rejects the result: the previous file is back and nothing reloads.
    marker = tmp_path / "reloaded"
    failed = run_helper(tmp_path, "set", "8000", test="false", reload=f"touch {marker}")
    assert failed.returncode == 3 and not marker.exists()
    assert run_helper(tmp_path, "show").stdout.strip() == "8001"

    # The reload itself fails: the file matches what nginx still runs.
    failed = run_helper(tmp_path, "set", "8000", reload="false")
    assert failed.returncode == 4
    assert run_helper(tmp_path, "show").stdout.strip() == "8001"

    assert run_helper(tmp_path, "set", "8000").returncode == 0
    assert (tmp_path / "up.conf").read_text() == shipped
    assert sorted(p.name for p in tmp_path.iterdir()) == ["up.conf", "up.conf.previous"]
