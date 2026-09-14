"""One same-host supervisor; each transformation has its own killable process.

Run: python -m backend.app.api_v1.jobs.worker
Health: python -m backend.app.api_v1.jobs.worker --healthcheck
SIGTERM stops claims, terminates/reaps the active process group, and exits. Its
durable claim is eligible for bounded recovery on the next supervisor start.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import threading
import time

from . import config, storage
from .adapters import execute


def terminate_group(process: subprocess.Popen, grace: float = 1.0) -> None:
    """Kill the session including native grandchildren, then reap its leader."""
    try:
        os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    # A leader can exit while a native child ignores SIGTERM.
    try:
        os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def child_environment(scratch: Path) -> dict[str,str]:
    allowed = ("PATH","LANG","LC_ALL","SYSTEMROOT","U2NET_HOME","XDG_CACHE_HOME","NUMBA_DISABLE_JIT")
    env = {key:os.environ[key] for key in allowed if key in os.environ}
    env.update({"TEMP_DIR":str(scratch),"TMPDIR":str(scratch),"PYTHONPATH":str(Path(__file__).resolve().parents[4]),
                "OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1",
                "PRIVATOOLS_JOB_SUPERVISOR_PID":str(os.getpid())})
    return env


def run_job(row: dict, stop: threading.Event) -> None:
    identifier,token = row["id"],row["claim"]
    directory = storage.job_dir(identifier).resolve()
    scratch = directory/token
    scratch.mkdir(mode=0o700)
    spec = {"operation":row["operation"],"options":json.loads(row["options"]),
            "inputs":[str(directory/"inputs"/item["name"]) for item in json.loads(row["inputs"])],
            "max_result_bytes":config.LIMITS.result_bytes,"runtime_seconds":config.LIMITS.runtime_seconds}
    request_file = scratch/"request.json"
    request_file.write_text(json.dumps(spec),encoding="utf-8")
    process = subprocess.Popen([sys.executable,"-m","backend.app.api_v1.jobs.worker","--execute",str(request_file)],
                               env=child_environment(scratch),start_new_session=True,
                               stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    deadline = time.monotonic()+config.LIMITS.runtime_seconds
    error = None
    interrupted = False
    try:
        while process.poll() is None:
            if stop.is_set():
                interrupted = True
                break
            if not storage.renew(identifier,token):
                error = "job_canceled"
                break
            storage.heartbeat()
            if time.monotonic()>=deadline:
                error = "job_timeout"
                break
            stop.wait(0.5)
    finally:
        # Also kills lingering grandchildren if the Python leader exited.
        terminate_group(process)
    if interrupted:
        # The process group has been reaped; only the durable original inputs
        # are needed for a retry. Never accumulate one scratch tree per deploy.
        shutil.rmtree(scratch,ignore_errors=True)
        with storage.connection(write=True) as conn:
            conn.execute("UPDATE api_async_jobs SET state=CASE WHEN state='running' THEN 'queued' ELSE state END, "
                         "claim=NULL,lease_until=NULL WHERE id=? AND claim=?",(identifier,token))
        return
    if error or process.returncode:
        storage.finish(identifier,token,error=error or "job_processing_failed")
    else:
        try:
            manifest = json.loads((scratch/"manifest.json").read_text(encoding="utf-8"))
            storage.finish(identifier,token,output=Path(manifest["output"]))
        except (OSError,ValueError,KeyError,storage.JobError):
            storage.finish(identifier,token,error="job_processing_failed")
    # Cancellation keeps files until this function has killed/reaped the child.
    current = storage.lookup(identifier,row["key_id"])
    if current["state"] != "succeeded" and current["claim"] is None:
        storage.purge_files(identifier)


def execute_child(request_file: Path) -> int:
    """No API credentials or database path are passed into the transformation."""
    import resource
    # Linux immediately kills the direct child if a supervisor dies abruptly.
    # The first adapters do not spawn external programs. Process-group cleanup
    # remains mandatory before adding OCR/Office/media adapters.
    if sys.platform.startswith("linux"):
        import ctypes
        parent = int(os.environ.get("PRIVATOOLS_JOB_SUPERVISOR_PID","0"))
        if not parent or os.getppid()!=parent:
            return 1
        ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGKILL)
        if os.getppid()!=parent:
            return 1
    spec = json.loads(request_file.read_text(encoding="utf-8"))
    resource.setrlimit(resource.RLIMIT_FSIZE,(spec["max_result_bytes"],spec["max_result_bytes"]))
    resource.setrlimit(resource.RLIMIT_CPU,(spec["runtime_seconds"],spec["runtime_seconds"]+1))
    # Address-space limit is Linux-only: Darwin maps shared libraries much more
    # sparsely. Production also inherits the existing aggregate container cap.
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS,(1024*1024*1024,1024*1024*1024))
    scratch = request_file.parent.resolve()
    output = execute(spec["operation"],spec["options"],spec["inputs"],scratch)
    (scratch/"manifest.json").write_text(json.dumps({"output":str(output.resolve())}),encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--healthcheck",action="store_true")
    parser.add_argument("--execute",type=Path)
    args = parser.parse_args()
    if args.execute:
        return execute_child(args.execute)
    if args.healthcheck:
        return 0 if storage.capability()["available"] else 1
    if not config.enabled():
        return 0
    storage.init_schema()
    stop = threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,lambda _sig,_frame:stop.set())
    with (config.root()/"worker.lock").open("a") as lock:
        # Web retention maintenance may briefly own this same lock while no
        # supervisor exists. Wait for that sweep instead of failing startup.
        lock_deadline = time.monotonic()+config.LIMITS.lease_seconds
        while not stop.is_set():
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic()>=lock_deadline:
                    return 1
                stop.wait(0.05)
        else:
            return 0
        try:
            while not stop.is_set():
                storage.recover_and_sweep()
                storage.heartbeat()
                row = storage.claim()
                if row:
                    run_job(row,stop)
                else:
                    stop.wait(1)
        finally:
            storage.heartbeat(accepting=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
