#!/usr/bin/env python3
"""Finite synthetic benchmark, run INSIDE an isolated PrivaTools candidate container.

Requires PRIVATOOLS_CAPACITY_SANDBOX=1 and a loopback API. Creates two temporary
keys, measures 1/3/6 concurrent synchronous requests without retries or quota
changes, and deletes its synthetic account. Never prints credentials or files.
This measures these fixtures under the configured cgroup, not a throughput SLA.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import io
import json
import logging
import math
import os
from pathlib import Path
import secrets
import statistics
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(len(values) * p) - 1)]


def multipart(operation, data):
    boundary = "capacity-" + secrets.token_hex(12)
    parts = []
    field = "file" if operation == "pdf-to-text" else "files"
    for _ in range(2 if operation == "merge" else 1):
        parts += [f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="sample.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode(), data, b"\r\n"]
    parts += [f"--{boundary}--\r\n".encode()]
    return b"".join(parts), "multipart/form-data; boundary=" + boundary


def fixtures():
    import pymupdf as fitz
    from PIL import Image
    # Deterministic RGB texture, rather than an unrealistically empty scanned page.
    image = Image.frombytes("RGB", (640, 640), bytes((index * 31 + index // 640) % 256 for index in range(640 * 640 * 3)))
    output = {}
    for name, pages, scanned in (("text-2-pages", 2, False), ("text-40-pages", 40, False), ("image-20-pages", 20, True)):
        with fitz.open() as document:
            for index in range(pages):
                page = document.new_page()
                page.insert_text((40, 40), f"Synthetic capacity sample. Page {index + 1}.")
                if scanned:
                    # Different images on each page defeat PDF deduplication,
                    # representing a multipage scan rather than one reused icon.
                    scanned_page = image.copy()
                    scanned_page.paste(((index * 13) % 256, (index * 31) % 256, (index * 47) % 256), (0, 0, 96, 96))
                    encoded = io.BytesIO()
                    scanned_page.save(encoded, format="JPEG", quality=90)
                    page.insert_image(fitz.Rect(40, 70, 550, 780), stream=encoded.getvalue())
                else:
                    page.insert_textbox(fitz.Rect(40, 70, 550, 780), "A sample paragraph for document automation. " * 150, fontsize=10)
            output[name] = document.tobytes(garbage=4, deflate=True)
    return output


def cgroup_value(name):
    try:
        return (Path("/sys/fs/cgroup") / name).read_text().strip()
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--repeats", type=int, choices=range(1, 4), default=2)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if os.environ.get("PRIVATOOLS_CAPACITY_SANDBOX") != "1":
        parser.error("Run only inside an isolated candidate with PRIVATOOLS_CAPACITY_SANDBOX=1")
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path.rstrip("/") != "/api/v1":
        parser.error("base-url must be a loopback /api/v1 endpoint without credentials or query")
    for root in (Path.cwd(), Path(__file__).resolve().parents[2], Path("/app")):
        if (root / "backend/app/store.py").is_file():
            sys.path.insert(0, str(root))
            break
    from backend.app.auth import accounts
    logging.disable(logging.CRITICAL)
    samples = fixtures()
    user = accounts.create_user(f"capacity-{secrets.token_hex(12)}@example.test", secrets.token_urlsafe(36))
    keys = [accounts.issue_api_key(user.id, f"Capacity sample {index}")[0] for index in range(2)]
    peak_memory = [0]
    stop = threading.Event()

    def sample_resources():
        while not stop.wait(.1):
            memory = cgroup_value("memory.current")
            if memory and memory.isdigit():
                peak_memory[0] = max(peak_memory[0], int(memory))

    sampler = threading.Thread(target=sample_resources, daemon=True)
    sampler.start()
    evidence = {"started_at": datetime.now(timezone.utc).isoformat(), "fixture_bytes": {name: len(data) for name, data in samples.items()}, "cpu_max": cgroup_value("cpu.max"), "memory_max": cgroup_value("memory.max"), "cpu_before": cgroup_value("cpu.stat"), "memory_events_before": cgroup_value("memory.events"), "cases": [], "cleanup_complete": False}

    def request_once(operation, body, content_type, index):
        started = time.perf_counter()
        req = Request(args.base_url.rstrip("/") + "/" + operation, data=body, headers={"X-API-Key": keys[index % 2], "Content-Type": content_type}, method="POST")
        try:
            with build_opener(NoRedirect()).open(req, timeout=60) as response:
                payload = response.read(100 * 1024 * 1024 + 1)
                valid = len(payload) <= 100 * 1024 * 1024
                if operation == "pdf-to-text":
                    valid = valid and "Synthetic capacity sample" in payload.decode("utf-8")
                else:
                    import pymupdf as fitz
                    with fitz.open(stream=payload, filetype="pdf") as document:
                        valid = valid and document.page_count > 0
                return {"status": response.status, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "valid_result": valid}
        except HTTPError as exc:
            status = exc.code
            exc.close()
            return {"status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "valid_result": False}
        except Exception as exc:
            return {"status": 0, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "valid_result": False, "error_type": type(exc).__name__}

    try:
        # A total of 30 * repeats requests; pause between bursts to refill fair limits.
        for operation, name in (("merge", "text-2-pages"), ("pdf-to-text", "text-40-pages"), ("compress", "image-20-pages")):
            body, content_type = multipart(operation, samples[name])
            for concurrency in (1, 3, 6):
                results = []
                for _ in range(args.repeats):
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        results.extend(pool.map(lambda index: request_once(operation, body, content_type, index), range(concurrency)))
                    time.sleep(6)
                values = [result["duration_ms"] for result in results]
                evidence["cases"].append({"operation": operation, "fixture": name, "concurrency": concurrency, "requests": len(results), "p50_ms": round(statistics.median(values), 2), "p95_ms": percentile(values, .95), "results": results})
    finally:
        stop.set()
        sampler.join(timeout=1)
        accounts.delete_user(user.id)
        evidence["cleanup_complete"] = accounts.get_user(user.id) is None
        evidence.update({"peak_memory_bytes": peak_memory[0] or None, "cpu_after": cgroup_value("cpu.stat"), "memory_events_after": cgroup_value("memory.events"), "finished_at": datetime.now(timezone.utc).isoformat()})
        evidence["all_results_valid"] = bool(evidence["cases"]) and all(row["valid_result"] for case in evidence["cases"] for row in case["results"])
        print(json.dumps(evidence, indent=2))
    return 0 if evidence["cleanup_complete"] and evidence["all_results_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
