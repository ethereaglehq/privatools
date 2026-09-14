"""Real ASGI streams, validation provenance, and verified-key rate isolation."""
import asyncio
import threading

import httpx
import pytest
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile

from backend.app import store
from backend.app.api_v1 import quota
from backend.app.api_v1.body_accounting import V1AccountingMiddleware
from backend.app.api_v1.deps import enforce_quota
from backend.app.auth import accounts
from backend.app.middleware.error_handlers import register_error_handlers
from backend.app.rate_limit import WebsiteLimiter


@pytest.fixture()
def environment(tmp_path):
    store.reset_for_tests(tmp_path)
    user = accounts.create_user("body@example.com", "a-long-enough-password")
    raw, key = accounts.issue_api_key(user.id, "body")
    app = FastAPI()
    register_error_handlers(app)
    app.add_middleware(V1AccountingMiddleware)
    called = []

    @app.post("/api/v1/body", dependencies=[Depends(enforce_quota)])
    async def body(request: Request):
        called.append(True)
        return {"bytes": request.state.v1_received_bytes}

    @app.post("/api/v1/file", dependencies=[Depends(enforce_quota)])
    async def file(file: UploadFile = File(...)):
        called.append(True)
        return {"ok": True}

    @app.post("/api/v1/after-work", dependencies=[Depends(enforce_quota)])
    async def after_work():
        called.append(True)
        raise HTTPException(422, "Service rejected after doing work")

    return app, raw, key, called


def request(app, raw, path, **kwargs):
    async def perform():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
            return await client.post(path, headers={"X-API-Key": raw, **kwargs.pop("headers", {})}, **kwargs)
    return asyncio.run(perform())


def test_chunked_body_is_charged_by_actual_count(environment):
    app, raw, key, called = environment
    async def chunks():
        yield b"abc"
        yield b"defgh"
    response = request(app, raw, "/api/v1/body", content=chunks())
    assert response.status_code == 200
    assert response.json()["bytes"] == 8
    assert quota.peek(key.key_id).bytes_used == 8
    assert called == [True]


def test_declared_size_does_not_replace_actual_body_count(environment):
    app, raw, key, _ = environment
    response = request(app, raw, "/api/v1/body", content=b"abcdefgh", headers={"Content-Length": "1"})
    assert response.status_code == 200
    assert quota.peek(key.key_id).bytes_used == 8


def test_over_quota_chunked_request_never_calls_service(environment, monkeypatch):
    app, raw, key, called = environment
    monkeypatch.setattr(quota, "DAILY_BYTES", 5)
    async def chunks():
        yield b"abc"
        yield b"def"
    response = request(app, raw, "/api/v1/body", content=chunks())
    assert response.status_code == 429
    assert response.json()["code"] == "quota_exceeded"
    assert called == []
    assert quota.peek(key.key_id).bytes_used == 0


def test_multipart_overhead_is_counted_and_validation_refund_is_explicit(environment):
    app, raw, key, called = environment
    response = request(app, raw, "/api/v1/file", files={"file": ("tiny.pdf", b"pdf", "application/pdf")})
    assert response.status_code == 200
    assert quota.peek(key.key_id).bytes_used == int(response.request.headers["Content-Length"])
    before = quota.peek(key.key_id)
    invalid = request(app, raw, "/api/v1/file", files={"wrong": ("tiny.pdf", b"pdf", "application/pdf")})
    assert invalid.status_code == 422
    assert quota.peek(key.key_id) == before
    after_work = request(app, raw, "/api/v1/after-work")
    assert after_work.status_code == 422
    assert quota.peek(key.key_id).units_used == before.units_used + 1


def test_slots_release_after_success_and_error(environment):
    app, raw, key, _ = environment
    request(app, raw, "/api/v1/body", content=b"abc")
    request(app, raw, "/api/v1/after-work")
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_leases WHERE key_id=?", (key.key_id,)).fetchone()[0] == 0


def test_two_keys_behind_same_ip_do_not_share_legacy_ip_limit(environment):
    app, raw, key, _ = environment
    another, _ = accounts.issue_api_key(key.user_id, "second")
    limiter = WebsiteLimiter(key_func=lambda request: "same-ip")

    @app.post("/api/v1/limited", dependencies=[Depends(enforce_quota)])
    @limiter.limit("1/minute")
    async def limited(request: Request):
        return {"ok": True}

    assert request(app, raw, "/api/v1/limited").status_code == 200
    assert request(app, another, "/api/v1/limited").status_code == 200
    assert request(app, "forged", "/api/v1/limited").status_code == 401


def test_unverified_and_legacy_calls_keep_ip_protection():
    limiter = WebsiteLimiter(key_func=lambda request: "same-ip")
    from slowapi.errors import RateLimitExceeded
    def probe(path):
        return Request({"type": "http", "method": "POST", "path": path, "headers": [(b"x-api-key", b"forged")], "client": ("127.0.0.1", 1)})
    @limiter.limit("1/minute")
    async def expensive(request: Request):
        return {"ok": True}
    for path in ["/api/expensive", "/api/v1/expensive"]:
        asyncio.run(expensive(request=probe(path)))
        with pytest.raises(RateLimitExceeded):
            asyncio.run(expensive(request=probe(path)))


def test_schema_auth_alternatives_are_distinct(environment):
    app, _, _, _ = environment
    schema = app.openapi()
    assert set(schema["components"]["securitySchemes"]) == {"XAPIKey", "BearerAuth"}
    assert schema["paths"]["/api/v1/file"]["post"]["security"] == [{"XAPIKey": []}, {"BearerAuth": []}]


def test_pipeline_reserves_the_sum_of_validated_steps(environment):
    app, raw, key, _ = environment
    @app.post("/api/v1/pipeline", dependencies=[Depends(enforce_quota)])
    async def pipeline(file: UploadFile = File(...), steps: str = Form(...)):
        return {"ok": True}
    response = request(app, raw, "/api/v1/pipeline", data={"steps": '["compress-pdf","pdf-to-pdfa"]'}, files={"file": ("tiny.pdf", b"pdf", "application/pdf")})
    assert response.status_code == 200
    assert quota.peek(key.key_id).units_used == 6
    before = quota.peek(key.key_id)
    invalid = request(app, raw, "/api/v1/pipeline", data={"steps": '["not-supported"]'}, files={"file": ("tiny.pdf", b"pdf", "application/pdf")})
    assert invalid.status_code == 400
    assert quota.peek(key.key_id) == before


def test_information_calls_do_not_spend_quota_or_request_burst(environment):
    app, raw, key, _ = environment
    @app.post("/api/v1/pipeline/validate", dependencies=[Depends(enforce_quota)])
    async def validate():
        return {"ok": True}
    for _ in range(8):
        assert request(app, raw, "/api/v1/pipeline/validate").status_code == 200
    assert quota.peek(key.key_id).units_used == 0
    assert request(app, raw, "/api/v1/body", content=b"abc").status_code == 200


def test_http_requests_hold_slots_until_completion(environment):
    app, raw, key, _ = environment
    async def run():
        release = asyncio.Event()
        entered = asyncio.Event()
        active = 0
        @app.post("/api/v1/slow", dependencies=[Depends(enforce_quota)])
        async def slow():
            nonlocal active
            active += 1
            if active == 3:
                entered.set()
            await release.wait()
            return {"ok": True}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost", headers={"X-API-Key": raw}) as client:
            requests = [asyncio.create_task(client.post("/api/v1/slow")) for _ in range(3)]
            try:
                await asyncio.wait_for(entered.wait(), 5)
                denied = await client.post("/api/v1/slow")
                assert denied.status_code == 429
                assert denied.json()["code"] == "concurrency_limit_exceeded"
            finally:
                release.set()
                await asyncio.gather(*requests)
    asyncio.run(run())
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_leases").fetchone()[0] == 0
    assert quota.peek(key.key_id).units_used == 3


def test_cancelled_http_request_releases_its_admitted_request_slot(environment):
    app, raw, key, _ = environment
    async def run():
        entered = asyncio.Event()
        @app.post("/api/v1/cancel", dependencies=[Depends(enforce_quota)])
        async def cancel():
            entered.set()
            await asyncio.Event().wait()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost", headers={"X-API-Key": raw}) as client:
            task = asyncio.create_task(client.post("/api/v1/cancel"))
            await asyncio.wait_for(entered.wait(), 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
    asyncio.run(run())
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_leases").fetchone()[0] == 0
    # The HTTP lifecycle alone cannot establish that processing cost was zero.
    assert quota.peek(key.key_id).units_used == 1


def test_cancellation_during_database_commit_does_not_lose_reservation(environment, monkeypatch):
    from backend.app.api_v1 import admission
    app, raw, key, called = environment
    committed = threading.Event()
    complete = threading.Event()
    real_admit = admission.admit
    def delayed(*args):
        result = real_admit(*args)
        committed.set()
        complete.wait(timeout=5)
        return result
    monkeypatch.setattr(admission, "admit", delayed)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost", headers={"X-API-Key": raw}) as client:
            task = asyncio.create_task(client.post("/api/v1/body", content=b"abc"))
            try:
                assert await asyncio.to_thread(committed.wait, 5)
                task.cancel()
            finally:
                complete.set()
            with pytest.raises(asyncio.CancelledError):
                await task
    asyncio.run(run())
    assert called == []
    assert quota.peek(key.key_id).units_used == 0
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_leases").fetchone()[0] == 0


def test_global_capacity_returns_retryable_503_without_charging(environment):
    from backend.app.api_v1.admission import admit
    app, raw, key, _ = environment
    for i in range(quota.MAX_HTTP_REQUESTS):
        assert admit(f"other-{i}", 1, 0).allowed
    response = request(app, raw, "/api/v1/body", content=b"abc")
    assert response.status_code == 503
    assert response.json()["code"] == "server_busy"
    assert response.headers["Retry-After"] == "2"
    assert quota.peek(key.key_id).units_used == 0
