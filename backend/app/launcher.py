"""Run web and optional job processing inside one existing resource envelope.

The disabled path execs Uvicorn directly. Enabled jobs add exactly one worker
supervisor, not one per Uvicorn process. Docker still applies the same combined
CPU, memory and process limits to the complete process tree.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time


def web_command() -> list[str]:
    return [
        sys.executable, "-m", "uvicorn", "backend.app.main:app",
        "--host", "0.0.0.0", "--port", "8000", "--workers", "2",
        "--timeout-keep-alive", "30", "--limit-concurrency", "50",
        "--timeout-graceful-shutdown", "30",
    ]


def _signal_group(process: subprocess.Popen, signum: int) -> None:
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        pass


def supervise(commands: list[list[str]], *, grace_seconds: float = 35,
              relay_to: int | None = None) -> int:
    """Stop both services on shutdown or failure, reaping all direct children.

    ``relay_to`` names the child that receives SIGUSR1 and SIGUSR2. The deploy
    sends them to the container (this process is its PID 1) to drain or resume
    the job supervisor during a zero-downtime handover; the web server never
    sees them.
    """
    stopping = False
    children: list[subprocess.Popen] = []

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    def relay(signum, _frame):
        if relay_to is not None and relay_to < len(children):
            _signal_group(children[relay_to], signum)

    deploy_signals = (signal.SIGUSR1, signal.SIGUSR2)
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    # Children start with the deploy signals ignored (an ignored disposition
    # survives exec). Their default action is to terminate, and the worker
    # installs its handlers only after its imports, so a drain relayed in that
    # window would otherwise kill it and, below, the whole container.
    previous.update({sig: signal.signal(sig, signal.SIG_IGN) for sig in deploy_signals})
    result = 0
    try:
        for command in commands:
            children.append(subprocess.Popen(command, start_new_session=True))
        for sig in deploy_signals:
            signal.signal(sig, relay)
        while not stopping:
            for child in children:
                code = child.poll()
                if code is not None:
                    # An unexpected clean exit is still a service failure.
                    result = code if code > 0 else 1
                    stopping = True
                    break
            if not stopping:
                time.sleep(0.1)
    finally:
        # Worker stops admission and reaps its isolated native job child.
        # Uvicorn drains HTTP requests concurrently within the same deadline.
        for child in children:
            _signal_group(child, signal.SIGTERM)
        deadline = time.monotonic() + grace_seconds
        for child in children:
            try:
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                _signal_group(child, signal.SIGKILL)
                child.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return result


def main() -> int:
    web = web_command()
    if os.environ.get("API_V1_JOBS_ENABLED", "false").lower() != "true":
        os.execv(web[0], web)
    return supervise([
        [sys.executable, "-m", "backend.app.api_v1.jobs.worker"],
        web,
    ], relay_to=0)


if __name__ == "__main__":
    raise SystemExit(main())
