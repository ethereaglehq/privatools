"""Cross-worker admission and request-scoped quota settlement."""
import multiprocessing
import time
from datetime import datetime, timezone

import pytest

from backend.app import store
from backend.app.api_v1 import quota


@pytest.fixture(autouse=True)
def database(tmp_path):
    store.reset_for_tests(tmp_path)
    yield
    store.reset_for_tests(tmp_path)


def test_reservation_refund_is_idempotent_and_uses_original_day(monkeypatch):
    first = datetime(2026, 9, 14, 23, 59, 59, tzinfo=timezone.utc)
    monkeypatch.setattr(quota, "_utcnow", lambda: first)
    allowed, state, token = quota.reserve("key", 5, 123)
    assert allowed and state.units_used == 5
    monkeypatch.setattr(quota, "_utcnow", lambda: datetime(2026, 9, 15, tzinfo=timezone.utc))
    quota.consume("key", 7, 700)
    quota.refund_reservation(token)
    quota.refund_reservation(token)
    assert quota.peek("key").units_used == 7
    assert quota.peek("key").bytes_used == 700
    with store.read() as conn:
        old = conn.execute("SELECT units, bytes FROM api_quota WHERE day='20260914'").fetchone()
    assert tuple(old) == (0, 0)


def test_admission_counts_other_keys_separately_and_releases_once():
    from backend.app.api_v1.admission import admit, release
    accepted = [admit("one", 1, 10) for _ in range(3)]
    assert all(result.allowed for result in accepted)
    rejected = admit("one", 1, 10)
    assert rejected.code == "concurrency_limit_exceeded"
    assert quota.peek("one").units_used == 3
    assert admit("two", 1, 10).allowed
    release(accepted[0].token)
    release(accepted[0].token)
    assert admit("one", 1, 10).allowed


def test_shared_rate_bucket_has_six_request_burst_and_refills():
    from backend.app.api_v1.admission import admit, release
    for _ in range(6):
        result = admit("key", 1, 0, now=1000)
        assert result.allowed
        release(result.token)
    assert admit("key", 1, 0, now=1000).code == "rate_limit_exceeded"
    assert admit("other", 1, 0, now=1000).allowed
    assert admit("key", 1, 0, now=1002).allowed


def _admit_process(directory, barrier, queue):
    from pathlib import Path
    from backend.app import store
    from backend.app.api_v1.admission import admit
    store.DATA_DIR = Path(directory)
    store.DB_PATH = Path(directory) / "privatools.db"
    store._initialised = True
    barrier.wait(timeout=10)
    result = admit("race", 1, 100)
    queue.put((result.allowed, result.token))


def test_two_worker_processes_share_three_request_capacity(tmp_path):
    quota.ensure_schema()
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(6)
    queue = context.Queue()
    workers = [context.Process(target=_admit_process, args=(str(tmp_path), barrier, queue)) for _ in range(6)]
    for worker in workers:
        worker.start()
    results = [queue.get(timeout=20) for _ in workers]
    for worker in workers:
        worker.join(timeout=10)
        assert worker.exitcode == 0
    assert sum(allowed for allowed, _ in results) == 3
    assert quota.peek("race").units_used == 3


def test_expired_live_owner_is_not_reclaimed():
    from backend.app.api_v1.admission import admit
    accepted = [admit("key", 1, 0, now=1000) for _ in range(3)]
    assert all(result.allowed for result in accepted)
    assert admit("key", 1, 0, now=time.time()).code == "concurrency_limit_exceeded"


def test_expired_dead_owner_releases_capacity_without_refunding_unknown_work(monkeypatch):
    from backend.app.api_v1 import admission
    for _ in range(3):
        assert admission.admit("key", 1, 0, now=1000).allowed
    monkeypatch.setattr(admission, "_alive", lambda pid, start: False)
    assert admission.admit("key", 1, 0, now=time.time()).allowed
    assert quota.peek("key").units_used == 4


def test_failed_atomic_job_acceptance_rolls_back_quota_receipt():
    with pytest.raises(RuntimeError):
        with store.write() as conn:
            allowed, _, _ = quota.reserve_in_transaction(conn, "job-key", 5, 500)
            assert allowed
            raise RuntimeError("queue insertion failed")
    assert quota.peek("job-key").units_used == 0
    with store.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_v1_reservations").fetchone()[0] == 0


def test_repeated_receipt_does_not_charge_again():
    with store.write() as conn:
        one = quota.reserve_in_transaction(conn, "key", 2, 300, token="unique")
        two = quota.reserve_in_transaction(conn, "key", 2, 300, token="unique")
    assert one == two
    assert quota.peek("key").units_used == 2


def test_pipeline_cost_table_matches_supported_steps():
    from backend.app.routes.developer import PIPELINE_STEP_META
    assert set(quota.PIPELINE_STEP_COSTS) == set(PIPELINE_STEP_META)


def test_global_capacity_is_shared_by_independent_keys():
    from backend.app.api_v1.admission import admit, release
    accepted = [admit(f"key-{i}", 1, 100) for i in range(quota.MAX_HTTP_REQUESTS)]
    assert all(result.allowed for result in accepted)
    rejected = admit("another-key", 1, 100)
    assert rejected.code == "server_busy"
    assert quota.peek("another-key").units_used == 0
    release(accepted[0].token)
    assert admit("another-key", 1, 100).allowed


def test_cleanup_is_bounded_and_preserves_lease_and_job_receipts():
    from backend.app.api_v1.admission import admit
    now = time.time()
    active = admit("active", 1, 20)
    _, _, job = quota.reserve("job", 1, 20)
    for _ in range(3):
        quota.reserve("old", 1, 20)
    with store.write() as conn:
        conn.execute("CREATE TABLE api_async_jobs (receipt TEXT)")
        conn.execute("INSERT INTO api_async_jobs VALUES(?)", (job,))
        conn.execute("UPDATE api_v1_reservations SET created_at=?", (now-3*86400,))
        conn.execute("INSERT INTO api_quota VALUES('past','20200101',1,1)")
    cleaned = quota.cleanup_accounting(now=now, limit=2)
    assert cleaned["receipts"] == 2
    assert cleaned["daily_counters"] == 1
    with store.read() as conn:
        tokens = {row[0] for row in conn.execute("SELECT token FROM api_v1_reservations")}
    assert active.token in tokens and job in tokens
    assert len(tokens) == 3
