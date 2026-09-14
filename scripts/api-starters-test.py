#!/usr/bin/env python3
"""Exercise both real CLI processes against a synthetic local HTTP API."""
from __future__ import annotations

import contextlib
import email.parser
import email.policy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("api_starters_build", ROOT / "scripts/api-starters-build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
KEY = "synthetic-starter-test-key"
JOB_ID = "synthetic-job-001"


class MockAPI:
    def __init__(self, mode="happy"):
        self.mode = mode
        self.calls = []
        self.submissions = []
        self.state = "succeeded"
        self.deleted = False
        self.result = builder.sample_pdf("Synthetic converted result")
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def send(self, status, body, extra=None, media="application/json"):
                body = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", media)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Retry-After", "0")
                for name, value in (extra or {}).items():
                    self.send_header(name, value)
                self.end_headers()
                with contextlib.suppress(BrokenPipeError):
                    self.wfile.write(body)

            def record(self):
                api.calls.append((self.command, self.path))
                if self.headers.get("X-API-Key") != KEY:
                    self.send(401, {"code": "invalid_key"})
                    return False
                return True

            def do_POST(self):
                if not self.record():
                    return
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                message = email.parser.BytesParser(policy=email.policy.default).parsebytes(
                    b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + raw)
                parts = [(part.get_param("name", header="content-disposition"), part.get_payload(decode=True)) for part in message.iter_parts()]
                api.submissions.append({"key": self.headers.get("Idempotency-Key"), "parts": parts})
                if api.mode == "retry" and len(api.submissions) == 1:
                    self.send(429, {"code": "rate_limited"})
                    return
                if api.mode == "lost_ack" and len(api.submissions) == 1:
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if api.mode == "rejected":
                    self.send(422, {"message": KEY, "code": "invalid_input"})
                    return
                if api.mode == "reflected_request_id":
                    self.send(422, {"message": KEY}, {"X-Request-ID": KEY})
                    return
                if api.mode == "reflected_job_id":
                    self.send(202, {"id": KEY})
                    return
                if api.mode == "redirect":
                    self.send(307, {}, {"Location": api.base + "/unexpected-secret-destination"})
                    return
                if api.mode == "quota":
                    self.send_response(429)
                    self.send_header("Retry-After", "3600")
                    self.send_header("Content-Length", "2")
                    self.end_headers()
                    self.wfile.write(b"{}")
                    return
                if dict(parts).get("operation") == b"pdf-to-text":
                    api.result = b'{"text":"sample","pages":[{"page":1,"text":"sample"}],"characters":6}'
                self.send(202, api.job())

            def do_GET(self):
                if not self.record():
                    return
                if self.path.endswith("/result"):
                    result = api.result[:-2] if api.mode == "truncated" else api.result
                    if api.mode == "slow_download":
                        self.drip(result)
                        return
                    self.send(200, result, media="application/pdf")
                    return
                if api.mode == "slow_metadata":
                    self.drip(json.dumps(api.job()).encode())
                    return
                if api.mode == "slow_headers":
                    with contextlib.suppress(OSError):
                        for byte in b'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n{}':
                            self.connection.sendall(bytes([byte]))
                            time.sleep(0.05)
                    return
                if api.mode in ("failed", "canceled", "expired"):
                    api.state = api.mode
                if api.mode == "deadline":
                    api.state = "running"
                    self.send_response(200)
                    data = json.dumps(api.job()).encode()
                    self.send_header("Retry-After", "3600")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                self.send(200, api.job())

            def drip(self, body):
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                with contextlib.suppress(OSError):
                    for byte in body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.05)

            def do_DELETE(self):
                if not self.record():
                    return
                api.deleted = True
                api.state = "canceled"
                self.send(200, {"id": JOB_ID, "state": "canceled", "deletion_pending": False})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_port}/api/v1"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def job(self):
        return {"id": JOB_ID, "operation": "compress", "state": self.state,
                "result": {"bytes": len(self.result), "url": "https://attacker.invalid/steal", "media_type": "application/pdf"},
                "status_url": "https://attacker.invalid/steal", "expires_at": KEY if self.mode == "reflected_expiry" else "2099-01-01T00:00:00Z",
                "error": {"code": "synthetic_failure", "message": KEY} if self.state != "succeeded" else None}

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise RuntimeError("Node.js 22+ is required to test both advertised runtimes.")

    def setup_case(self, runtime):
        temporary = tempfile.TemporaryDirectory(prefix="priva-starter-test-")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        (directory / "first.pdf").write_bytes(builder.sample_pdf("First synthetic input"))
        (directory / "second.pdf").write_bytes(builder.sample_pdf("Second synthetic input"))
        cli = ([sys.executable, str(ROOT / "examples/api/privatools.py")] if runtime == "python"
               else [shutil.which("node"), str(ROOT / "examples/api/privatools.mjs")])
        return directory, cli

    def run_cli(self, cli, directory, api, args, success=True, deadline="5"):
        process = subprocess.run([*cli, *args, "--base-url", api.base, "--deadline-seconds", deadline],
                                 cwd=directory, env={**os.environ, "PRIVATOOLS_API_KEY": KEY}, capture_output=True, text=True, timeout=10)
        self.assertNotIn(KEY, process.stdout + process.stderr)
        if success:
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        else:
            self.assertNotEqual(process.returncode, 0, process.stdout + process.stderr)
        return process

    def arguments(self, operation="compress", output="result.pdf", extra=()):
        inputs = ["first.pdf", "second.pdf"] if operation == "merge" else ["first.pdf"]
        return [operation, *inputs, "--state", "job.json", "--output", output, *extra]

    def test_three_recipes_save_complete_file_then_delete(self):
        for runtime in ("python", "node"):
            for operation in builder.OPERATIONS:
                with self.subTest(runtime=runtime, operation=operation), MockAPI() as api:
                    directory, cli = self.setup_case(runtime)
                    self.run_cli(cli, directory, api, self.arguments(operation))
                    self.assertEqual((directory / "result.pdf").read_bytes(), api.result)
                    self.assertTrue(api.deleted)
                    self.assertEqual(api.calls[-1], ("DELETE", "/api/v1/jobs/" + JOB_ID))
                    state = json.loads((directory / "job.json").read_text())
                    self.assertEqual(state["jobId"], JOB_ID)
                    self.assertEqual(state["operation"], operation)
                    self.assertNotIn(KEY, json.dumps(state))
                    self.assertNotIn("first.pdf", json.dumps(state))
                    parts = api.submissions[0]["parts"]
                    self.assertEqual(dict(parts)["operation"], operation.encode())
                    self.assertEqual(sum(name == "files" for name, _ in parts), 2 if operation == "merge" else 1)

    def test_retries_preserve_logical_idempotency_and_file_bytes(self):
        for runtime in ("python", "node"):
            for mode in ("retry", "lost_ack"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    self.run_cli(cli, directory, api, self.arguments())
                    self.assertEqual(len(api.submissions), 2)
                    self.assertEqual(api.submissions[0], api.submissions[1])

    def test_retain_resume_cross_runtime_and_explicit_delete(self):
        with MockAPI() as api:
            directory, cli = self.setup_case("python")
            self.run_cli(cli, directory, api, self.arguments(extra=["--retain"]))
            self.assertFalse(api.deleted)
            node_cli = [shutil.which("node"), str(ROOT / "examples/api/privatools.mjs")]
            self.run_cli(node_cli, directory, api, ["resume", "--state", "job.json", "--output", "copy.pdf", "--retain"])
            self.assertEqual((directory / "copy.pdf").read_bytes(), api.result)
            self.assertEqual(len(api.submissions), 1)
            self.run_cli(node_cli, directory, api, ["delete", "--state", "job.json"])
            self.assertTrue(api.deleted)

    def test_terminal_failures_do_not_download_or_delete(self):
        for runtime in ("python", "node"):
            for mode in ("failed", "canceled", "expired"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    self.run_cli(cli, directory, api, self.arguments(), success=False)
                    self.assertFalse(api.deleted)
                    self.assertFalse((directory / "result.pdf").exists())
                    self.assertFalse(any(route.endswith("/result") for _, route in api.calls))

    def test_deadline_and_daily_quota_do_not_retry_early(self):
        for runtime in ("python", "node"):
            for mode in ("deadline", "quota"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    self.run_cli(cli, directory, api, self.arguments(), success=False)
                    self.assertEqual(len(api.submissions), 1)
                    self.assertFalse(api.deleted)
                    self.assertTrue((directory / "job.json").exists())

    def test_save_failure_or_truncation_keeps_result(self):
        for runtime in ("python", "node"):
            for mode in ("existing", "missing_dir", "truncated"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    output = "missing/result.pdf" if mode == "missing_dir" else "result.pdf"
                    if mode == "existing":
                        (directory / "result.pdf").write_bytes(b"DO NOT REPLACE")
                    self.run_cli(cli, directory, api, self.arguments(output=output), success=False)
                    self.assertFalse(api.deleted)
                    if mode == "existing":
                        self.assertEqual((directory / "result.pdf").read_bytes(), b"DO NOT REPLACE")
                    else:
                        self.assertFalse((directory / output).exists())
                    self.assertEqual(list(directory.glob(".priva-download-*")), [])

    def test_redirect_and_input_error_stop_without_retries_or_secret_echo(self):
        for runtime in ("python", "node"):
            for mode in ("redirect", "rejected"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    self.run_cli(cli, directory, api, self.arguments(), success=False)
                    self.assertEqual(len(api.submissions), 1)
                    self.assertEqual(len(api.calls), 1)
                    self.assertFalse(api.deleted)

    def test_changed_input_cannot_reuse_saved_idempotency(self):
        for runtime in ("python", "node"):
            with self.subTest(runtime=runtime), MockAPI() as api:
                directory, cli = self.setup_case(runtime)
                self.run_cli(cli, directory, api, self.arguments(extra=["--retain"]))
                (directory / "first.pdf").write_bytes(builder.sample_pdf("Changed contents"))
                before = len(api.calls)
                self.run_cli(cli, directory, api, self.arguments(output="another.pdf", extra=["--retain"]), success=False)
                self.assertEqual(len(api.calls), before)
                self.assertFalse(api.deleted)

    def test_accepted_state_skips_resubmission(self):
        for runtime in ("python", "node"):
            with self.subTest(runtime=runtime), MockAPI() as api:
                directory, cli = self.setup_case(runtime)
                self.run_cli(cli, directory, api, self.arguments(extra=["--retain"]))
                self.run_cli(cli, directory, api, self.arguments(output="another.pdf"))
                self.assertEqual(len(api.submissions), 1)
                self.assertTrue(api.deleted)

    def test_slow_drip_headers_and_bodies_respect_wall_clock_deadline(self):
        for runtime in ("python", "node"):
            for mode in ("slow_metadata", "slow_download", "slow_headers"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    started = time.monotonic()
                    self.run_cli(cli, directory, api, self.arguments(), success=False, deadline="0.35")
                    self.assertLess(time.monotonic() - started, 1.5)
                    self.assertFalse(api.deleted)
                    self.assertFalse((directory / "result.pdf").exists())

    def test_reflected_credentials_are_not_printed_or_saved(self):
        for runtime in ("python", "node"):
            for mode in ("reflected_request_id", "reflected_job_id", "reflected_expiry"):
                with self.subTest(runtime=runtime, mode=mode), MockAPI(mode) as api:
                    directory, cli = self.setup_case(runtime)
                    self.run_cli(cli, directory, api, self.arguments(extra=["--retain"]), success=mode == "reflected_expiry")
                    self.assertNotIn(KEY, (directory / "job.json").read_text())
                    self.assertFalse(api.deleted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
