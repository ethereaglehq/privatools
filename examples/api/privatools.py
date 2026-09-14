#!/usr/bin/env python3
"""PrivaTools async PDF starter. Python 3.10+, standard library only."""
from __future__ import annotations

import argparse
import contextlib
import email.utils
import hashlib
import http.client
import json
import os
from pathlib import Path
import random
import re
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_BASE = "https://api.privatools.me/api/v1"
MAX_INPUT = 50 * 1024 * 1024
MAX_RESULT = 100 * 1024 * 1024
OPERATIONS = ("merge", "compress", "pdf-to-text")
LEVELS = ("light", "recommended", "extreme", "email", "print", "archive", "web")
ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


class StarterError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the key to a redirected origin.


class TimedResponse(http.client.HTTPResponse):
    def close(self):
        timer = getattr(self, "starter_timer", None)
        if timer:
            timer.cancel()
        super().close()


class TimedConnection:
    """A socket inactivity timeout alone cannot stop a slow-drip response."""
    response_class = TimedResponse

    def __init__(self, *args, deadline, **kwargs):
        self.starter_deadline = deadline
        self.starter_timer = None
        super().__init__(*args, **kwargs)

    def connect(self):
        super().connect()
        sock = self.sock
        remaining = self.starter_deadline - time.monotonic()
        if remaining <= 0:
            sock.close()
            raise TimeoutError("Connection deadline reached")

        def stop_socket():
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)

        self.starter_timer = threading.Timer(remaining, stop_socket)
        self.starter_timer.daemon = True
        self.starter_timer.start()

    def getresponse(self):
        response = super().getresponse()
        response.starter_timer = self.starter_timer
        return response


class TimedHTTPConnection(TimedConnection, http.client.HTTPConnection):
    pass


class TimedHTTPSConnection(TimedConnection, http.client.HTTPSConnection):
    pass


class TimedHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, deadline):
        super().__init__()
        self.deadline = deadline

    def http_open(self, request):
        return self.do_open(TimedHTTPConnection, request, deadline=self.deadline)


class TimedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, deadline):
        super().__init__()
        self.deadline = deadline

    def https_open(self, request):
        return self.do_open(TimedHTTPSConnection, request, deadline=self.deadline, context=self._context)


def base_url(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme not in ("https", "http") or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or (parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"))):
        raise StarterError("Use an HTTPS base URL without credentials, query, or fragment (HTTP is allowed only on loopback).")
    return value.rstrip("/")


def job_id(value, key=None):
    if not isinstance(value, str) or not ID.fullmatch(value) or key and key in value:
        raise StarterError("The API returned an invalid job ID.")
    return value


def retry_delay(headers, fallback):
    raw = headers.get("Retry-After", "")
    try:
        delay = float(raw)
        if delay >= 0 and delay < float("inf"):
            return delay
    except ValueError:
        pass
    try:
        date = email.utils.parsedate_to_datetime(raw)
        return max(0, date.timestamp() - time.time())
    except (ValueError, TypeError, OverflowError):
        return fallback


class Client:
    def __init__(self, base, key, deadline_seconds=1200):
        self.base = base_url(base)
        if not key or any(ord(c) < 33 or ord(c) > 126 for c in key):
            raise StarterError("Set PRIVATOOLS_API_KEY to your API key.")
        self.key = key
        self.deadline = time.monotonic() + deadline_seconds

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise StarterError("Deadline reached. Your saved job state can be resumed; the result was not deleted.")
        return remaining

    def pause(self, seconds):
        if seconds >= self.remaining():
            raise StarterError("Retry-After exceeds the remaining deadline. Resume later using your saved state.")
        time.sleep(max(0.05, seconds))

    def request(self, method, route, body=None, headers=None):
        # All routes are built locally; status_url/result.url are never followed.
        if not re.fullmatch(r"jobs(?:/[A-Za-z0-9_-]{1,128}(?:/result)?)?", route):
            raise StarterError("Invalid local API route.")
        for attempt in range(5):
            request = urllib.request.Request(self.base + "/" + route, data=body, method=method,
                                             headers={"X-API-Key": self.key, **(headers or {})})
            try:
                timeout = min(30, self.remaining())
                deadline = time.monotonic() + timeout
                opener = urllib.request.build_opener(NoRedirect(), TimedHTTPHandler(deadline), TimedHTTPSHandler(deadline))
                return opener.open(request, timeout=timeout)
            except urllib.error.HTTPError as error:
                status = error.code
                delay = retry_delay(error.headers, 2 ** attempt + random.random() / 4)
                # Do not print response bodies, which could contain reflected secrets.
                request_id = error.headers.get("X-Request-ID", "")
                error.close()
                if status not in (429, 502, 503, 504) or attempt == 4:
                    suffix = f" Request ID: {request_id}" if ID.fullmatch(request_id) and self.key not in request_id else ""
                    raise StarterError(f"API HTTP {status}.{suffix} Saved state is available for recovery.") from None
            except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
                if attempt == 4:
                    raise StarterError("Network retry budget exhausted. Resume with the saved state.") from None
                delay = 2 ** attempt + random.random() / 4
            self.pause(delay)
        raise AssertionError("unreachable")

    def json(self, method, route, body=None, headers=None):
        with self.request(method, route, body, headers) as response:
            chunks = []
            count = 0
            while True:
                self.remaining()
                chunk = response.read1(64 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > 1024 * 1024:
                    raise StarterError("Unexpectedly large API metadata response.")
                chunks.append(chunk)
            data = b"".join(chunks)
            if len(data) > 1024 * 1024:
                raise StarterError("Unexpectedly large API metadata response.")
            try:
                value = json.loads(data)
            except (ValueError, UnicodeError):
                raise StarterError("Invalid JSON metadata response. Resume using the saved state.") from None
            if not isinstance(value, dict):
                raise StarterError("Invalid JSON metadata object. Resume using the saved state.")
            return value, response.headers


def save_state(path, state, new=False):
    # State contains IDs, options, and hashes; never the API key or document paths.
    encoded = (json.dumps(state, indent=2) + "\n").encode()
    if new:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as target:
            target.write(encoded)
            target.flush()
            os.fsync(target.fileno())
        return
    parent = Path(path).resolve().parent
    fd, tmp = tempfile.mkstemp(prefix=".priva-state-", dir=parent)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(encoded)
            target.flush()
            os.fsync(target.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


def load_state(path):
    try:
        state = json.loads(Path(path).read_text())
        if (state["version"] != 1 or state["operation"] not in OPERATIONS
                or not ID.fullmatch(state["idempotencyKey"])):
            raise ValueError()
        base_url(state["baseUrl"])
        if state.get("jobId"):
            job_id(state["jobId"])
        return state
    except (KeyError, ValueError, TypeError):
        raise StarterError("Invalid state file.") from None


def prepare_upload(operation, filenames, level):
    minimum, maximum = (2, 10) if operation == "merge" else (1, 1)
    if not minimum <= len(filenames) <= maximum:
        raise StarterError(f"{operation} requires {minimum}–{maximum} PDF inputs.")
    if sum(Path(name).stat().st_size for name in filenames) > MAX_INPUT:
        raise StarterError("Total PDF input exceeds 50 MiB.")
    blobs = [Path(name).read_bytes() for name in filenames]
    if sum(map(len, blobs)) > MAX_INPUT or any(not blob.startswith(b"%PDF-") for blob in blobs):
        raise StarterError("Inputs must be PDF files totaling at most 50 MiB.")
    options = {"level": level} if operation == "compress" else {}
    hashes = [{"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)} for blob in blobs]
    boundary = "priva-" + uuid.uuid4().hex
    chunks = []
    for name, value in (("operation", operation), ("options", json.dumps(options, sort_keys=True))):
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for index, blob in enumerate(blobs):
        chunks.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="input-{index+1}.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode(), blob, b"\r\n"])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), "multipart/form-data; boundary=" + boundary, options, hashes


def wait_for_job(client, identifier):
    for _ in range(600):
        job, headers = client.json("GET", "jobs/" + job_id(identifier))
        if job.get("id") != identifier:
            raise StarterError("Job ID mismatch.")
        state = job.get("state")
        if state == "succeeded":
            return job
        if state in ("failed", "canceled", "expired"):
            code = (job.get("error") or {}).get("code", "")
            safe_code = " (" + code + ")" if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,100}", code) and client.key not in code else ""
            raise StarterError(f"Job {state}{safe_code}. No result was deleted by this client.")
        if state not in ("queued", "running"):
            raise StarterError("Unknown job state.")
        client.pause(max(0.1, retry_delay(headers, 2)))
    raise StarterError("Polling budget exhausted. Resume using your saved state.")


def download(client, job, output):
    result = job.get("result") or {}
    expected = result.get("bytes")
    if type(expected) is not int or not 0 < expected <= MAX_RESULT:
        raise StarterError("Invalid result size metadata.")
    output = Path(output)
    if output.exists():
        raise StarterError("Output already exists. Choose another output path; the server result is retained.")
    fd, tmp = tempfile.mkstemp(prefix=".priva-download-", dir=output.resolve().parent)
    try:
        count = 0
        with os.fdopen(fd, "wb") as target, client.request("GET", "jobs/" + job_id(job["id"]) + "/result") as response:
            while True:
                client.remaining()
                chunk = response.read1(256 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > expected:
                    raise StarterError("Result exceeds expected size. The server result is retained.")
                target.write(chunk)
            if count != expected:
                raise StarterError("Result download is incomplete. Resume to download again.")
            target.flush()
            os.fsync(target.fileno())
        # Link fails if another process created the destination during download.
        os.link(tmp, output)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(*OPERATIONS, "resume", "delete"))
    parser.add_argument("files", nargs="*")
    parser.add_argument("--output", "-o", help="New local output path (.json for pdf-to-text)")
    parser.add_argument("--state", help="State JSON path; reuse it only for the same logical request")
    parser.add_argument("--base-url", help="Explicit API base; HTTPS or loopback HTTP")
    parser.add_argument("--level", choices=LEVELS, default="recommended")
    parser.add_argument("--retain", action="store_true", help="Keep server result until expiry instead of deleting after save")
    parser.add_argument("--deadline-seconds", type=float, default=1200)
    args = parser.parse_args(argv)
    if not 0 < args.deadline_seconds <= 3600:
        raise StarterError("Deadline must be positive and at most 3600 seconds.")
    if args.command != "delete" and not args.output:
        raise StarterError("Provide --output (use a .json filename for pdf-to-text).")
    if args.command in ("resume", "delete") and (not args.state or args.files):
        raise StarterError("Resume/delete requires --state and no file arguments.")
    state_path = args.state or f"privatools-job-{uuid.uuid4().hex}.json"
    existing = Path(state_path).exists()
    if args.command in ("resume", "delete") and not existing:
        raise StarterError("State file does not exist.")
    state = load_state(state_path) if existing else None
    base = base_url(args.base_url or (state["baseUrl"] if state else DEFAULT_BASE))
    if state and base != state["baseUrl"]:
        raise StarterError("The selected API base differs from the saved request. Use a new state file for a different server.")
    client = Client(base, os.environ.get("PRIVATOOLS_API_KEY", ""), args.deadline_seconds)
    if args.command in OPERATIONS:
        body, content_type, options, hashes = prepare_upload(args.command, args.files, args.level)
        if state:
            if (state["operation"], state["options"], state["inputs"]) != (args.command, options, hashes):
                raise StarterError("This state belongs to different input/options. Use a new state file for new work.")
        else:
            state = {"version": 1, "baseUrl": base, "operation": args.command, "options": options,
                     "inputs": hashes, "idempotencyKey": uuid.uuid4().hex, "jobId": None}
            save_state(state_path, state, new=True)
        print(f"State: {state_path}", flush=True)
        print(f"Idempotency key: {state['idempotencyKey']}", flush=True)
        if not state.get("jobId"):
            job, _ = client.json("POST", "jobs", body, {"Content-Type": content_type, "Idempotency-Key": state["idempotencyKey"]})
            state["jobId"] = job_id(job.get("id"), client.key)
            print(f"Job ID: {state['jobId']}", flush=True)
            save_state(state_path, state)
    if not state or not state.get("jobId"):
        raise StarterError("Submission was interrupted before saving a job ID. Repeat the original file command with this --state path.")
    job_id(state["jobId"], client.key)
    print(f"Job ID: {state['jobId']}", flush=True)
    if args.command == "delete":
        deleted, _ = client.json("DELETE", "jobs/" + state["jobId"])
        print("Cancellation requested; poll to confirm cleanup." if deleted.get("deletion_pending") else "Server result deleted.")
        return
    job = wait_for_job(client, state["jobId"])
    download(client, job, args.output)
    print(f"Saved: {args.output}", flush=True)
    if args.retain:
        print("Server result retained until its normal expiry (one hour after completion). Use delete to remove it sooner.")
    else:
        deleted, _ = client.json("DELETE", "jobs/" + state["jobId"])
        print("Deletion pending." if deleted.get("deletion_pending") else "Server result deleted after successful save.")


if __name__ == "__main__":
    try:
        main()
    except (StarterError, OSError, ValueError, http.client.HTTPException, KeyboardInterrupt) as error:
        # Local filesystem errors can include paths, but no headers or API key.
        message = str(error) if isinstance(error, StarterError) else "Local IO/response error or interruption. The server result was not automatically deleted; use saved state to recover."
        print("Error: " + message, file=sys.stderr)
        sys.exit(1)
