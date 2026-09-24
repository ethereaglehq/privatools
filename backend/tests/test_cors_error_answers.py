"""An error answer carries the same CORS headers as a success.

The page (https://privatools.me) reads the API (https://api.privatools.me)
cross-origin, and a browser hands a cross-origin page nothing from an answer
without Access-Control-Allow-Origin: not the status, not the JSON detail. The
page then reports a network failure and sends the upload again.

Starlette runs the catch-all exception handler in ServerErrorMiddleware,
outside every add_middleware layer, CORS included, so its answers (an
unhandled exception's 500, and the 413, 400 and 501 it maps some exceptions
to) went out without CORS headers. The 413 and 504 from the upload-size and
timeout middlewares answer inside the CORS layer and always had them.

An origin the app does not allow gets no CORS header on any answer. Starlette
used to send it the list of exposed headers anyway, which a browser ignores
without an Access-Control-Allow-Origin.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.auth import accounts
from backend.app.services import url_to_pdf_service

DISALLOWED = "https://evil.example"
ORIGINS = ["allowed", "disallowed"]


def _allowed() -> str:
    return main._origins[0]


def cors(response) -> dict[str, str]:
    """The CORS part of an answer: its Access-Control-* headers, and whether
    it says it varies by Origin."""
    headers = {k.lower(): v for k, v in response.headers.items() if k.lower().startswith("access-control-")}
    vary = {token.strip().lower() for token in response.headers.get("vary", "").split(",")}
    if "origin" in vary:
        headers["vary"] = "Origin"
    return headers


@pytest.fixture
def quiet_client():
    # The catch-all re-raises after answering; keep the answer.
    return TestClient(main.app, raise_server_exceptions=False)


@pytest.fixture
def expected(client, request):
    """What every answer to the test's origin must carry: a success's CORS
    headers for the allowed origin, none for any other. Taken before the test
    patches anything, since a patched timeout would end this request too."""
    success = client.get("/api/health", headers={"Origin": _allowed()})
    assert success.status_code == 200
    allowed = cors(success)
    assert allowed["access-control-allow-origin"] == _allowed()
    assert allowed["vary"] == "Origin"
    assert "x-request-id" in allowed["access-control-expose-headers"].lower()
    return (_allowed(), allowed) if request.param == "allowed" else (DISALLOWED, {})


@pytest.mark.parametrize("expected", ORIGINS, indirect=True)
def test_a_success(client, expected):
    origin, headers = expected
    assert cors(client.get("/api/health", headers={"Origin": origin})) == headers


@pytest.mark.parametrize("expected", ORIGINS, indirect=True)
def test_413_from_the_upload_size_limit(client, expected):
    origin, headers = expected
    response = client.post("/api/compress", content=b"x", headers={
        "Origin": origin, "content-type": "application/octet-stream",
        "content-length": str(600 * 1024 * 1024),
    })
    assert response.status_code == 413
    assert cors(response) == headers


@pytest.mark.parametrize("expected", ORIGINS, indirect=True)
def test_504_from_the_request_timeout(quiet_client, monkeypatch, tmp_path, expected):
    origin, headers = expected
    page = tmp_path / "page.pdf"
    page.write_bytes(b"%PDF-1.4\n")

    # The request only completes once the route ends, even after the 504 has
    # gone out, so the slow conversion ends on its own.
    def slow(url):
        time.sleep(0.5)
        return str(page)

    monkeypatch.setattr(url_to_pdf_service, "url_to_pdf", slow)
    monkeypatch.setattr(main, "_REQUEST_TIMEOUT", 0.1)
    response = quiet_client.post("/api/url-to-pdf", data={"url": "https://example.com/"}, headers={"Origin": origin})
    assert response.status_code == 504
    assert cors(response) == headers


def _named(name: str) -> type[Exception]:
    # The catch-all matches some libraries' exceptions by class name.
    return type(name, (Exception,), {})


@pytest.mark.parametrize("error,status", [
    (lambda: RuntimeError("an unhandled failure"), 500),
    (lambda: _named("DecompressionBombError")("too many pixels"), 413),
    (lambda: _named("PasswordError")("encrypted"), 400),
    (lambda: NotImplementedError(), 501),
])
@pytest.mark.parametrize("expected", ORIGINS, indirect=True)
def test_answers_from_the_catch_all_handler(quiet_client, monkeypatch, expected, error, status):
    origin, headers = expected
    from PIL import Image

    def fail(*_args, **_kwargs):
        raise error()

    # Image Compressor catches nothing, so whatever Image.open raises reaches
    # the catch-all handler. (A TimeoutError would not: on Python 3.11 it is
    # asyncio.TimeoutError, which RequestTimeoutMiddleware answers itself.)
    monkeypatch.setattr(Image, "open", fail)
    response = quiet_client.post(
        "/api/image-compressor",
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        headers={"Origin": origin},
    )
    assert response.status_code == status
    assert cors(response) == headers
    # The page reads the request id off a failure for its error report.
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


@pytest.mark.parametrize("origin", ["https://developer.example", "allowed"])
def test_public_api_answers_from_the_catch_all_handler(client, quiet_client, monkeypatch, origin):
    origin = _allowed() if origin == "allowed" else origin
    # Any other /api/v1 answer: this one is refused inside the stack.
    refused = client.get("/api/v1/whoami", headers={"Origin": origin})
    assert refused.status_code == 401

    def fail(_key):
        raise RuntimeError("the key store failed")

    monkeypatch.setattr(accounts, "resolve_key", fail)
    failed = quiet_client.get("/api/v1/whoami", headers={"Origin": origin, "X-API-Key": "pk_test_anything"})
    assert failed.status_code == 500
    assert cors(failed) == cors(refused)
    assert cors(failed)["access-control-allow-origin"] == "*"
