"""The page can read every response header it asks for.

privatools.me calls api.privatools.me (deploy/api-subdomain-split.md), so every
answer the page reads is a cross-origin one. A browser then hands the page only
the CORS-safelisted response headers and those the answer names in
Access-Control-Expose-Headers: any other header reads as null, and the page
carries on without it. Content-Disposition was missing for that reason, so
downloads lost the server's file name and Redact never showed its report.

These tests read frontend/src for the headers it reads off an answer and ask
the app which headers it exposes, both ways: a header the page reads must be
exposed, and a header exposed must be one the page reads. The public API,
which has its own policy (middleware/v1_cors.py), must expose every header the
tools' answers carry to the page, since the same handlers answer it.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"

# A browser always lets a cross-origin page read these (Fetch standard,
# "CORS-safelisted response-header name").
SAFELISTED = {
    "cache-control", "content-language", "content-length", "content-type",
    "expires", "last-modified", "pragma",
}

_NAME = r"""(["'`])([A-Za-z0-9-]+)\1"""
# res.headers.get("X"), headers?.get("X"), xhr.getResponseHeader("X"),
# headers.has("X"), and a record of headers indexed by name: headers?.["x"]
# (but not headers["X"] = value, which builds a request).
_READS = [
    re.compile(r"\bheaders\??\.(?:get|has)\(\s*" + _NAME),
    re.compile(r"\bgetResponseHeader\(\s*" + _NAME),
    re.compile(r"\bheaders\??\.?\[\s*" + _NAME + r"\s*\](?!\s*=(?!=))"),
]
# A file that calls the public API reads its answers under that API's policy.
_CALLS_V1 = re.compile(r"""apiUrl\(\s*[`"']/v1/|["'`]/api/v1/""")


def _sources() -> list[Path]:
    return [
        path for path in FRONTEND.rglob("*")
        if path.suffix in {".ts", ".tsx"}
        and not re.search(r"\.test\.tsx?$", path.name)
        and "test" not in path.relative_to(FRONTEND).parts
    ]


def headers_read() -> dict[str, dict[str, set[str]]]:
    """{"site" | "v1": {header name, lower case: {files that read it}}}."""
    found: dict[str, dict[str, set[str]]] = {"site": {}, "v1": {}}
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        surface = "v1" if _CALLS_V1.search(text) else "site"
        for pattern in _READS:
            for match in pattern.finditer(text):
                name = match.group(2).lower()
                found[surface].setdefault(name, set()).add(str(path.relative_to(FRONTEND)))
    return found


def exposed(response) -> set[str]:
    value = response.headers.get("access-control-expose-headers", "")
    return {name.strip().lower() for name in value.split(",") if name.strip()}


def _allowed_origin() -> str:
    from backend.app.main import _origins

    return _origins[0]


def site_exposed(client) -> set[str]:
    return exposed(client.get("/api/health", headers={"Origin": _allowed_origin()}))


def v1_exposed(client) -> set[str]:
    # Any answer from /api/v1 carries its policy; this one needs no key.
    return exposed(client.get("/api/v1/whoami", headers={"Origin": "https://developer.example"}))


def test_every_header_the_pages_read_from_the_api_is_exposed(client):
    reads = headers_read()["site"]
    missing = {name: sorted(files) for name, files in reads.items()
               if name not in SAFELISTED and name not in site_exposed(client)}
    assert not missing, (
        "The page reads these headers, but a cross-origin page cannot see them: add each "
        f"to SITE_EXPOSED_HEADERS in backend/app/middleware/cors.py. {missing}"
    )


def test_the_api_exposes_only_headers_the_pages_read(client):
    reads = headers_read()["site"]
    unread = sorted(site_exposed(client) - set(reads))
    assert not unread, (
        "Exposed, but no page reads them (or this test no longer finds the read): "
        f"remove them from SITE_EXPOSED_HEADERS, or fix the reader patterns here. {unread}"
    )


def test_the_api_playground_can_read_what_it_asks_the_public_api_for(client):
    reads = headers_read()["v1"]
    assert reads, "no file reads /api/v1 answers any more: update _CALLS_V1"
    missing = {name: sorted(files) for name, files in reads.items()
               if name not in SAFELISTED and name not in v1_exposed(client)}
    assert not missing, f"add these to EXPOSED_HEADERS in backend/app/middleware/v1_cors.py: {missing}"


def test_the_public_api_exposes_what_the_tools_answers_carry(client):
    # Both surfaces run the same handlers, so an answer from /api/v1/redact
    # carries the same X-Redaction-Report as one from /api/redact.
    missing = sorted(site_exposed(client) - v1_exposed(client))
    assert not missing, f"add these to EXPOSED_HEADERS in backend/app/middleware/v1_cors.py: {missing}"
