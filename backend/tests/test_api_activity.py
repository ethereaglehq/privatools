"""Account-scoped metadata, privacy, retention, and telemetry failure isolation."""
from __future__ import annotations

import json
import hashlib
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from backend.app import store
from backend.app.api_v1 import activity, quota
from backend.app.api_v1.body_accounting import V1AccountingMiddleware
from backend.app.api_v1.deps import enforce_quota
from backend.app.auth import accounts
from backend.app.middleware.error_handlers import register_error_handlers
from backend.app.middleware.request_id import RequestIDMiddleware
from backend.app.routes import accounts as account_routes


@pytest.fixture()
def environment(tmp_path, monkeypatch):
    store.reset_for_tests(tmp_path)
    monkeypatch.setattr(account_routes.clerk_session, "is_configured", lambda: False)
    user = accounts.create_user_with_hash("activity@example.com", "unused", "unused")
    raw, key = accounts.issue_api_key(user.id, "Synthetic integration")
    other_user = accounts.create_user_with_hash("other@example.com", "unused", "unused")
    other_raw, other_key = accounts.issue_api_key(other_user.id, "Other account")
    app = FastAPI()
    register_error_handlers(app)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(V1AccountingMiddleware)
    app.include_router(account_routes.router, prefix="/api")

    @app.post("/api/v1/compress", dependencies=[Depends(enforce_quota)])
    async def process(request: Request, file: UploadFile = File(...), mode: str = Form("ok")):
        if mode == "error":
            raise HTTPException(422, {"code": "private-customer-filename.pdf", "message": "Private text"})
        return {"result": "private-document-content", "bytes": request.state.v1_received_bytes}

    @app.post("/api/v1/grayscale", dependencies=[Depends(enforce_quota)])
    async def unexpected():
        raise ValueError("private-path-and-message")

    @app.post("/api/v1/merge", dependencies=[Depends(enforce_quota)])
    async def broken_stream():
        async def chunks():
            yield b"private-stream-content"
            raise RuntimeError("private-stream-error")
        return StreamingResponse(chunks(), media_type="application/pdf")

    @app.get("/api/v1/usage", dependencies=[Depends(enforce_quota)])
    async def usage():
        return {"ok": True}

    from backend.app.api_v1.jobs.router import router as jobs
    app.include_router(jobs, prefix="/api/v1")
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set(account_routes.SESSION_COOKIE, accounts.create_session(user.id))
    return client, user, raw, key, other_user, other_raw, other_key


def _record(key, *, now=None, status=200, duration=100, index=1):
    activity.record(key.key_id, f"{index:012x}", "v1_post_compress", "POST", status,
                    "validation_error" if status == 422 else None, duration, now=now)


def _process(client, raw, *, mode="ok", **kwargs):
    return client.post("/api/v1/compress?file=private-query-filename.pdf", headers={"X-API-Key": raw, "X-Request-ID": "private-header-filename.pdf"},
                       files={"file": ("private-upload-filename.pdf", b"private-document-content", "application/pdf")}, data={"mode": mode}, **kwargs)


def test_success_and_validation_metadata_contains_no_document_or_client_values(environment):
    client, user, raw, key, *_ = environment
    success = _process(client, raw)
    failed = _process(client, raw, mode="error")
    assert success.status_code == 200
    assert failed.status_code == 422
    assert re.fullmatch(r"[0-9a-f]{12}", success.headers["X-Request-ID"])
    result = client.get("/api/account/api-activity")
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-store"
    data = result.json()
    assert data["retention_days"] == 7 and data["recent_limit"] == 50
    assert len(data["days"]) == 7
    assert data["days"][-1]["requests"] == 2
    assert data["days"][-1]["succeeded"] == 1
    assert data["days"][-1]["failed"] == 1
    assert data["recent"][0]["error_code"] == "validation_error"
    assert data["recent"][1]["error_code"] is None
    assert data["recent"][1]["request_id"] == success.headers["X-Request-ID"]
    assert all(row["operation"] == "v1_post_compress" for row in data["recent"])
    assert data["keys"][0]["units"]["used"] == 2
    assert data["keys"][0]["bytes"]["used"] == int(success.request.headers["content-length"]) + int(failed.request.headers["content-length"])
    with store.read() as conn:
        saved = json.dumps([dict(row) for row in conn.execute("SELECT * FROM api_activity_recent")])
    for private in (raw, "private-document-content", "private-upload-filename.pdf", "private-query-filename.pdf", "private-header-filename.pdf", "private-customer-filename.pdf", "Private text"):
        assert private not in saved and private not in result.text


def test_known_key_framework_validation_and_admission_failures_are_recorded_without_charging(environment, monkeypatch):
    client, user, raw, key, *_ = environment
    invalid = client.post("/api/v1/compress", headers={"X-API-Key": raw})
    assert invalid.status_code == 422
    assert quota.peek(key.key_id).units_used == 0
    monkeypatch.setattr(quota, "DAILY_UNITS", 0)
    denied = _process(client, raw)
    assert denied.status_code == 429
    result = activity.summary(user.id)
    assert [r["error_code"] for r in result["recent"]] == ["quota_exceeded", "validation_error"]
    assert quota.peek(key.key_id).bytes_used == 0


def test_known_key_multipart_parse_failure_before_auth_dependency_is_recorded(environment):
    client, user, raw, key, *_ = environment
    response = client.post("/api/v1/compress", content=b"invalid multipart", headers={"X-API-Key": raw, "Content-Type": "multipart/form-data"})
    assert response.status_code == 400
    assert activity.summary(user.id)["recent"][0]["status_code"] == 400
    assert quota.peek(key.key_id).units_used == 0


def test_final_translated_status_of_unhandled_exception_is_recorded(environment):
    client, user, raw, key, *_ = environment
    response = client.post("/api/v1/grayscale", headers={"X-API-Key": raw})
    assert response.status_code == 400
    recent = activity.summary(user.id)["recent"]
    assert len(recent) == 1
    assert recent[0]["status_code"] == 400
    assert recent[0]["error_code"] == "invalid_request"
    assert recent[0]["request_id"] == response.headers["X-Request-ID"]


def test_stream_failure_preserves_already_sent_status_and_records_only_once(environment):
    client, user, raw, key, *_ = environment
    response = client.post("/api/v1/merge", headers={"X-API-Key": raw})
    assert response.status_code == 200
    recent = activity.summary(user.id)["recent"]
    assert len(recent) == 1 and recent[0]["status_code"] == 200
    assert recent[0]["request_id"] == response.headers["X-Request-ID"]
    assert quota.peek(key.key_id).units_used == 1
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_leases").fetchone()[0] == 0


def test_unknown_failure_preserves_500_and_safe_code(environment):
    client, user, raw, key, *_ = environment
    @client.app.post("/api/v1/rotate", dependencies=[Depends(enforce_quota)])
    async def unknown_failure():
        raise RuntimeError("private-unknown-error")
    response = client.post("/api/v1/rotate", headers={"X-API-Key": raw})
    assert response.status_code == 500
    recent = activity.summary(user.id)["recent"]
    assert len(recent) == 1 and recent[0]["status_code"] == 500
    assert recent[0]["error_code"] == "processing_failed"


def test_async_submission_errors_are_recorded_but_usage_and_job_polling_are_not(environment, monkeypatch):
    client, user, raw, key, *_ = environment
    from backend.app.api_v1.jobs import config, storage
    storage.init_schema()
    monkeypatch.setattr(config, "enabled", lambda: False)
    submission = client.post("/api/v1/jobs", headers={"X-API-Key": raw})
    assert submission.status_code == 503
    assert client.get("/api/v1/usage", headers={"X-API-Key": raw}).status_code == 200
    assert client.get("/api/v1/jobs/missing", headers={"X-API-Key": raw}).status_code == 404
    assert client.get("/api/v1/jobs/missing/result", headers={"X-API-Key": raw}).status_code == 404
    assert client.delete("/api/v1/jobs/missing", headers={"X-API-Key": raw}).status_code == 404
    recent = activity.summary(user.id)["recent"]
    assert len(recent) == 1
    assert recent[0]["operation"] == "v1_post_jobs"
    assert recent[0]["error_code"] == "jobs_unavailable"
    assert quota.peek(key.key_id).units_used == 0


def test_unrecognised_or_revoked_credentials_do_not_create_history(environment):
    client, user, raw, key, *_ = environment
    assert _process(client, "invalid-key").status_code == 401
    accounts.revoke_key(user.id, key.key_id)
    assert _process(client, raw).status_code == 401
    assert activity.summary(user.id)["recent"] == []


def test_account_and_key_filter_are_owned_and_revoked_keys_remain_visible(environment):
    client, user, raw, key, other_user, other_raw, other_key = environment
    _record(key)
    _record(other_key)
    raw2, key2 = accounts.issue_api_key(user.id, "Second key")
    _record(key2, status=422)
    accounts.revoke_key(user.id, key2.key_id)
    own = client.get("/api/account/api-activity", params={"key_id": key2.key_id}).json()
    assert len(own["keys"]) == 1 and own["keys"][0]["revoked"] is True
    assert len(own["recent"]) == 1 and own["days"][-1]["failed"] == 1
    assert client.get("/api/account/api-activity", params={"key_id": other_key.key_id}).status_code == 404
    assert client.get("/api/account/api-activity", params={"key_id": "missing"}).status_code == 404
    all_keys = client.get("/api/account/api-activity").json()
    assert {r["key_id"] for r in all_keys["recent"]} == {key.key_id, key2.key_id}
    client.cookies.clear()
    assert client.get("/api/account/api-activity", headers={"X-API-Key": raw}).status_code == 401


def test_clerk_identity_owns_history_and_does_not_fall_back_to_native_cookie(environment, monkeypatch):
    client, user, raw, key, other_user, other_raw, other_key = environment
    _record(key)
    _record(other_key)
    monkeypatch.setattr(account_routes.clerk_session, "is_configured", lambda: True)
    monkeypatch.setattr(account_routes.clerk_session, "verify", lambda token: SimpleNamespace(user_id=other_user.id) if token == "synthetic-clerk-session" else None)
    assert client.get("/api/account/api-activity").status_code == 401
    headers = {"Authorization": "Bearer synthetic-clerk-session"}
    result = client.get("/api/account/api-activity", headers=headers).json()
    assert [r["key_id"] for r in result["recent"]] == [other_key.key_id]
    assert client.get("/api/account/api-activity", params={"key_id": key.key_id}, headers=headers).status_code == 404


def test_daily_chart_survives_per_key_and_global_eviction(environment, monkeypatch):
    _, user, _, key, other_user, _, other_key = environment
    monkeypatch.setattr(activity, "MAX_RECENT_PER_KEY", 3)
    monkeypatch.setattr(activity, "MAX_RECENT_GLOBAL", 5)
    for i in range(6):
        _record(key, index=i, duration=100)
    for i in range(4):
        _record(other_key, index=100+i, status=422, duration=300)
    result = activity.summary(user.id)
    assert len(result["recent"]) == 2
    assert result["days"][-1] == {"date": result["days"][-1]["date"], "requests": 6, "succeeded": 6, "failed": 0, "avg_duration_ms": 100}
    assert activity.summary(other_user.id)["days"][-1]["requests"] == 4
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_activity_recent").fetchone()[0] == 5
        assert conn.execute("SELECT recent_count FROM api_activity_maintenance").fetchone()[0] == 5


def test_seven_utc_dates_expire_in_history_and_daily_chart(environment, monkeypatch):
    _, user, _, key, *_ = environment
    now = datetime(2026, 9, 14, 12, 30, tzinfo=timezone.utc)
    _record(key, now=(now - timedelta(days=7)).timestamp(), index=1)
    _record(key, now=(now - timedelta(days=6)).timestamp(), index=2)
    _record(key, now=now.timestamp(), index=3)
    result = activity.summary(user.id, now=now.timestamp())
    assert [r["request_id"] for r in result["recent"]] == ["000000000003", "000000000002"]
    assert result["days"][0]["date"] == "2026-09-08"
    assert result["resets_at"] == "2026-09-15T00:00:00+00:00"
    assert sum(day["requests"] for day in result["days"]) == 2
    monkeypatch.setattr(activity.time, "time", lambda: (now + timedelta(days=7)).timestamp())
    activity.cleanup()
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_activity_recent").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM api_activity_daily").fetchone()[0] == 0


def test_deleting_account_cascades_history_and_aggregate_count(environment):
    _, user, _, key, _, _, other_key = environment
    _record(key)
    _record(other_key)
    accounts.delete_user(user.id)
    _record(key)  # A request completing after deletion cannot resurrect rows.
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_activity_recent WHERE key_id=?", (key.key_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM api_activity_daily WHERE key_id=?", (key.key_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT recent_count FROM api_activity_maintenance").fetchone()[0] == 1


def test_telemetry_outage_preserves_response_body_quota_and_slot_release(environment, monkeypatch):
    client, user, raw, key, *_ = environment
    def unavailable():
        raise sqlite3.OperationalError("synthetic telemetry database outage")
    monkeypatch.setattr(activity, "_write", unavailable)
    response = _process(client, raw)
    assert response.status_code == 200
    assert response.json()["result"] == "private-document-content"
    assert quota.peek(key.key_id).units_used == 1
    assert quota.peek(key.key_id).bytes_used == int(response.request.headers["content-length"])
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_leases").fetchone()[0] == 0


def test_busy_database_drops_optional_write_promptly_and_fallback_auth_is_read_only(environment):
    _, user, raw, key, *_ = environment
    conn = sqlite3.connect(store.DB_PATH, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        started = time.monotonic()
        _record(key)
        assert time.monotonic() - started < 0.5
        assert activity._known_key(raw) == key.key_id
        assert activity._known_key("invalid-raw-key") is None
    finally:
        conn.execute("ROLLBACK")
        conn.close()
    assert activity.summary(user.id)["recent"] == []
    _record(key)
    assert len(activity.summary(user.id)["recent"]) == 1


def test_optional_key_lookup_reuses_authentication_and_revocation_without_touching_usage(environment):
    _, user, raw, key, *_ = environment
    assert accounts.resolve_key(raw, read_timeout=0.025) == accounts.resolve_key(raw)
    assert activity._known_key(raw) == key.key_id
    assert accounts.list_keys(user.id)[0].last_used_at is None
    assert quota.peek(key.key_id).units_used == 0
    assert accounts.resolve_key("invalid-key", read_timeout=0.025) is None
    accounts.revoke_key(user.id, key.key_id)
    assert accounts.resolve_key(raw, read_timeout=0.025) is None
    assert activity._known_key(raw) is None


def test_optional_key_lookup_never_initializes_or_creates_a_missing_store(tmp_path, monkeypatch):
    missing = tmp_path / "no-existing-store.db"
    monkeypatch.setattr(store, "DB_PATH", missing)
    def no_init():
        pytest.fail("Optional key lookup must not initialize a database")
    monkeypatch.setattr(store, "init", no_init)
    with pytest.raises(sqlite3.OperationalError):
        accounts.resolve_key("synthetic-random-api-key", read_timeout=0.025)
    assert not missing.exists()


def test_janitor_drains_expired_capacity_in_separate_bounded_transactions(environment, monkeypatch):
    _, user, _, key, *_ = environment
    monkeypatch.setattr(activity, "MAX_RECENT_PER_KEY", 10)
    monkeypatch.setattr(activity, "MAX_RECENT_GLOBAL", 10)
    monkeypatch.setattr(activity, "CLEANUP_BATCH", 2)
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc).timestamp()
    for i in range(10):
        _record(key, now=now - 8 * 86400, index=i)
    monkeypatch.setattr(activity.time, "time", lambda: now)
    activity.cleanup()
    with store.read() as conn:
        assert conn.execute("SELECT recent_count FROM api_activity_maintenance").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM api_activity_daily").fetchone()[0] == 0


def test_activity_dashboard_database_failure_is_retryable(environment, monkeypatch):
    client, *_ = environment
    def unavailable(*args):
        raise sqlite3.OperationalError("private-db-path")
    monkeypatch.setattr(activity, "summary", unavailable)
    response = client.get("/api/account/api-activity")
    assert response.status_code == 503 and response.headers["Retry-After"] == "5"
    assert response.headers["Cache-Control"] == "no-store"
    assert "private-db-path" not in response.text


def test_concurrent_writers_keep_daily_and_recent_counts_atomic(environment, monkeypatch):
    _, user, _, key, *_ = environment
    monkeypatch.setattr(activity, "MAX_RECENT_PER_KEY", 5)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: _record(key, index=i), range(32)))
    result = activity.summary(user.id)
    # Optional writes may be dropped on a busy database, but a committed daily
    # event and recent row are one transaction and cannot partially commit.
    assert 5 <= result["days"][-1]["requests"] <= 32
    assert len(result["recent"]) == 5
    assert result["days"][-1]["succeeded"] == result["days"][-1]["requests"]
    with store.read() as conn:
        assert conn.execute("SELECT recent_count FROM api_activity_maintenance").fetchone()[0] == 5


def test_storage_rejects_arbitrary_identifiers_and_bounds_error_fields(environment):
    _, user, _, key, *_ = environment
    activity.record(key.key_id, "private-client-id", "v1_post_compress", "POST", 200, None, 1)
    activity.record(key.key_id, "000000000000", "private-path", "POST", 200, None, 1)
    activity.record(key.key_id, "000000000001", "v1_post_compress", "POST", 400, {"secret": "private"}, -5)
    result = activity.summary(user.id)
    assert len(result["recent"]) == 1
    assert result["recent"][0]["error_code"] == "invalid_request"
    assert result["recent"][0]["duration_ms"] == 0


def test_schema_three_upgrade_and_rollback_preserve_accounts_quota_and_completed_job(tmp_path, monkeypatch, sample_pdf):
    """The additive migration must not strand a saved result during deployment.

    Historical migrations are immutable. Limiting init to versions 1–3 models
    the previous release without making the regression depend on git history
    being available inside a CI checkout or container.
    """
    from backend.app.api_v1.jobs import config, storage
    from backend.app.api_v1.jobs.router import router as jobs_router

    monkeypatch.setenv("API_V1_JOBS_ENABLED", "true")
    monkeypatch.setenv("PRIVATOOLS_BUILD_SHA", "synthetic-upgrade-build")
    historical = [entry for entry in store.MIGRATIONS if entry[0] <= 3]
    assert [version for version, _ in historical] == [1, 2, 3]
    with monkeypatch.context() as old:
        old.setattr(store, "MIGRATIONS", historical)
        store.reset_for_tests(tmp_path)
        storage.init_schema()
        storage.heartbeat()
        user = accounts.create_user_with_hash("upgrade@example.test", "unused", "unused")
        raw, key = accounts.issue_api_key(user.id, "Preserved integration")
        session = accounts.create_session(user.id)
        assert quota.consume(key.key_id, 7, 2048)[0]
        identifier = storage.begin_ingest(key.key_id, user.id)
        manifest = [{"name": "0.pdf", "sha256": hashlib.sha256(sample_pdf).hexdigest(), "bytes": len(sample_pdf)}]
        (storage.job_dir(identifier) / "inputs" / "0.pdf").write_bytes(sample_pdf)
        accepted, _, replayed = storage.accept(identifier, key.key_id, user.id,
                                                "synthetic-pre-upgrade-job", "grayscale", {}, manifest, 4096)
        assert accepted["state"] == "queued" and not replayed
        claimed = storage.claim()
        assert claimed and claimed["id"] == identifier
        scratch = storage.job_dir(identifier) / claimed["claim"]
        scratch.mkdir()
        output = scratch / "converted.pdf"
        output.write_bytes(sample_pdf)
        assert storage.finish(identifier, claimed["claim"], output=output)
        saved = storage.lookup(identifier, key.key_id)
        standing = quota.peek(key.key_id)
        assert saved["state"] == "succeeded" and standing.units_used == 8
        assert standing.bytes_used == 6144
        with store.read() as conn:
            assert [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")] == [1, 2, 3]
            assert not conn.execute("SELECT 1 FROM sqlite_master WHERE name='api_activity_recent'").fetchone()

    # A new process initializes the current schema; repeated init is harmless.
    monkeypatch.setattr(store, "_initialised", False)
    store.init()
    store.init()
    assert accounts.resolve_session(session) == user
    assert accounts.resolve_key(raw).key_id == key.key_id
    assert quota.peek(key.key_id) == standing
    assert storage.lookup(identifier, key.key_id) == saved
    assert (storage.job_dir(identifier) / "result").read_bytes() == sample_pdf
    assert activity.summary(user.id)["recent"] == []
    _record(key)
    assert activity.summary(user.id)["days"][-1]["requests"] == 1
    with store.read() as conn:
        assert [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")] == [1, 2, 3, 4]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    app = FastAPI()
    app.include_router(jobs_router, prefix="/api/v1")
    app.add_middleware(V1AccountingMiddleware)
    with TestClient(app) as client:
        # A rollout may temporarily disable new submissions; saved results
        # must remain downloadable using the original key regardless.
        monkeypatch.setattr(config, "enabled", lambda: False)
        result = client.get(f"/api/v1/jobs/{identifier}/result", headers={"X-API-Key": raw})
        assert result.status_code == 200 and result.content == sample_pdf
        assert quota.peek(key.key_id) == standing

        with monkeypatch.context() as rollback:
            rollback.setattr(store, "MIGRATIONS", historical)
            rollback.setattr(store, "_initialised", False)
            store.init()  # Old releases ignore the extra version/table entries.
            assert accounts.resolve_session(session) == user
            assert accounts.resolve_key(raw).key_id == key.key_id
            assert storage.lookup(identifier, key.key_id) == saved
            result = client.get(f"/api/v1/jobs/{identifier}/result", headers={"X-API-Key": raw})
            assert result.status_code == 200 and result.content == sample_pdf
            assert quota.peek(key.key_id) == standing
            # An old release can continue metering while the new tables exist.
            assert quota.consume(key.key_id, 1, 32)[0]

    monkeypatch.setattr(store, "_initialised", False)
    store.init()
    summary = activity.summary(user.id)
    assert summary["keys"][0]["units"]["used"] == 9
    assert summary["keys"][0]["bytes"]["used"] == 6176
    assert len(summary["recent"]) == 1
    assert storage.delete(identifier, key.key_id)["deletion_pending"] is False
    assert not storage.job_dir(identifier).exists()
