"""Durable jobs use synthetic identities and PDFs; never production resources."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app import store
from backend.app.api_v1 import quota
from backend.app.api_v1.body_accounting import V1AccountingMiddleware
from backend.app.api_v1.jobs import config, storage
from backend.app.api_v1.jobs.router import router
from backend.app.api_v1.jobs.worker import child_environment, run_job, terminate_group
from backend.app.api_v1.jobs import worker
from backend.app.auth import accounts


@pytest.fixture
def jobs(tmp_path,monkeypatch):
    store.reset_for_tests(tmp_path)
    monkeypatch.setenv("API_V1_JOBS_ENABLED","true")
    monkeypatch.setenv("PRIVATOOLS_BUILD_SHA","jobs-test-build")
    storage.init_schema()
    storage.heartbeat()
    user = accounts.create_user("job-tests@example.com","synthetic-long-password")
    raw,key = accounts.issue_api_key(user.id,"synthetic job tests")
    app = FastAPI()
    app.include_router(router,prefix="/api/v1")
    app.add_middleware(V1AccountingMiddleware)
    with TestClient(app) as client:
        yield client,raw,key
    store.reset_for_tests(tmp_path)


def submit(jobs,pdf,*,operation="grayscale",options="{}",idempotency="request-1",raw=None):
    client,secret,_ = jobs
    files = [("files",("input.pdf",pdf,"application/pdf"))]
    if operation=="merge":
        files *= 2
    return client.post("/api/v1/jobs",headers={"X-API-Key":raw or secret,"Idempotency-Key":idempotency},
                       data={"operation":operation,"options":options},files=files)


def headers(jobs):
    return {"X-API-Key":jobs[1]}


def test_feature_and_worker_must_be_ready(jobs,sample_pdf,monkeypatch):
    monkeypatch.setenv("API_V1_JOBS_ENABLED","false")
    assert submit(jobs,sample_pdf).status_code==503
    monkeypatch.setenv("API_V1_JOBS_ENABLED","true")
    storage.heartbeat(now=time.time()-100)
    assert submit(jobs,sample_pdf).json()["code"]=="jobs_unavailable"
    storage.heartbeat()
    monkeypatch.setenv("PRIVATOOLS_BUILD_SHA","different-build")
    assert not storage.capability()["available"]


def test_validated_submission_is_durable_and_charges_actual_multipart(jobs,sample_pdf):
    response = submit(jobs,sample_pdf)
    assert response.status_code==202,response.text
    body = response.json()
    row = storage.lookup(body["id"],jobs[2].key_id)
    assert row["state"]=="queued"
    assert (storage.job_dir(row["id"])/"inputs"/"0.pdf").read_bytes()==sample_pdf
    usage = quota.peek(jobs[2].key_id)
    assert usage.units_used==quota.cost_for("/api/v1/grayscale")
    assert usage.bytes_used>len(sample_pdf)
    with storage.connection() as conn:
        assert conn.execute("PRAGMA synchronous").fetchone()[0]==2
        assert conn.execute("SELECT COUNT(*) FROM api_async_ingest").fetchone()[0]==0


def test_invalid_options_or_unsupported_operation_never_charge(jobs,sample_pdf):
    for operation,options in [("ocr","{}"),("grayscale",'{"anything":true}'),("compress",'{"level":"custom"}')]:
        assert submit(jobs,sample_pdf,operation=operation,options=options).status_code in (400,422)
    assert quota.peek(jobs[2].key_id).units_used==0
    assert not [p for p in config.root().iterdir() if p.is_dir()]


def test_duplicate_and_conflict_are_scoped_to_fingerprint(jobs,sample_pdf):
    first = submit(jobs,sample_pdf)
    before = quota.peek(jobs[2].key_id)
    again = submit(jobs,sample_pdf)
    assert again.status_code==202,again.text
    assert again.json()["id"]==first.json()["id"]
    assert again.headers["Idempotency-Replayed"]=="true"
    assert quota.peek(jobs[2].key_id)==before
    conflict = submit(jobs,sample_pdf,operation="compress")
    assert conflict.status_code==409
    assert conflict.json()["code"]=="idempotency_conflict"


def test_duplicate_replay_works_when_key_queue_is_full_or_worker_is_down(jobs,sample_pdf,monkeypatch):
    monkeypatch.setattr(config,"LIMITS",replace(config.LIMITS,per_key=1))
    first = submit(jobs,sample_pdf)
    before = quota.peek(jobs[2].key_id)
    assert submit(jobs,sample_pdf,idempotency="different-job").status_code==429
    storage.heartbeat(accepting=False)
    replay = submit(jobs,sample_pdf)
    assert replay.status_code==202,replay.text
    assert replay.json()["id"]==first.json()["id"]
    assert quota.peek(jobs[2].key_id)==before


def test_duplicate_acceptance_race_has_one_job_and_receipt(jobs,sample_pdf):
    key = jobs[2]
    identifiers = [storage.begin_ingest(key.key_id,key.user_id) for _ in range(2)]
    inputs = [{"name":"0.pdf","sha256":hashlib.sha256(sample_pdf).hexdigest(),"bytes":len(sample_pdf)}]
    barrier = threading.Barrier(2)
    def accept(identifier):
        barrier.wait()
        return storage.accept(identifier,key.key_id,key.user_id,"concurrent-key","grayscale",{},inputs,1234)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(accept,identifiers))
    assert len({r[0]["id"] for r in results})==1
    assert sorted(r[2] for r in results)==[False,True]
    assert quota.peek(key.key_id).units_used==1
    assert quota.peek(key.key_id).bytes_used==1234
    for identifier in identifiers:
        storage.abandon_ingest(identifier)


def test_all_job_access_is_key_scoped_and_status_is_free(jobs,sample_pdf):
    client,raw,key = jobs
    other_raw,_ = accounts.issue_api_key(key.user_id,"different key same account")
    job_id = submit(jobs,sample_pdf).json()["id"]
    before = quota.peek(key.key_id)
    assert client.get(f"/api/v1/jobs/{job_id}",headers=headers(jobs)).status_code==200
    for method,suffix in [("get",""),("get","/result"),("delete","")]:
        response = getattr(client,method)(f"/api/v1/jobs/{job_id}{suffix}",headers={"X-API-Key":other_raw})
        assert response.status_code==404,response.text
    assert quota.peek(key.key_id)==before
    assert client.get(f"/api/v1/jobs/{job_id}").status_code==401


@pytest.mark.parametrize("operation",["grayscale","compress","merge","pdf-to-text"])
def test_process_adapters_publish_retrievable_results_and_remove_inputs(jobs,sample_pdf,operation):
    response = submit(jobs,sample_pdf,operation=operation)
    assert response.status_code==202,response.text
    row = storage.claim()
    assert row is not None
    assert storage.claim() is None
    run_job(row,threading.Event())
    finished = storage.lookup(row["id"],jobs[2].key_id)
    assert finished["state"]=="succeeded",finished
    assert finished["expires"]-finished["completed"]==3600
    assert not (storage.job_dir(row["id"])/"inputs").exists()
    assert sorted(p.name for p in storage.job_dir(row["id"]).iterdir())==["result"]
    result = jobs[0].get(f'/api/v1/jobs/{row["id"]}/result',headers=headers(jobs))
    assert result.status_code==200,result.text
    if operation=="pdf-to-text":
        assert "Hello, PrivaTools" in result.json()["text"]
    else:
        assert result.content.startswith(b"%PDF")


def test_expiry_checked_before_sweep_and_delete_is_idempotent(jobs,sample_pdf):
    identifier = submit(jobs,sample_pdf).json()["id"]
    run_job(storage.claim(),threading.Event())
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET expires=? WHERE id=?",(time.time()-1,identifier))
    assert jobs[0].get(f"/api/v1/jobs/{identifier}",headers=headers(jobs)).json()["state"]=="expired"
    assert jobs[0].get(f"/api/v1/jobs/{identifier}/result",headers=headers(jobs)).status_code==410
    for _ in range(2):
        response = jobs[0].delete(f"/api/v1/jobs/{identifier}",headers=headers(jobs))
        assert response.status_code==200,response.text
    assert not storage.job_dir(identifier).exists()


def test_claim_recovery_is_bounded_and_fences_old_publisher(jobs,sample_pdf):
    identifier = submit(jobs,sample_pdf).json()["id"]
    first = storage.claim()
    leftover=storage.job_dir(identifier)/first["claim"]
    leftover.mkdir()
    (leftover/"unfinished-output").write_bytes(b"old result")
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET lease_until=0 WHERE id=?",(identifier,))
    storage.recover_and_sweep()
    assert not leftover.exists()
    assert (storage.job_dir(identifier)/"inputs"/"0.pdf").exists()
    second = storage.claim()
    assert second["attempts"]==2
    assert second["claim"]!=first["claim"]
    assert not storage.finish(identifier,first["claim"],error="stale_attempt")
    assert storage.lookup(identifier,jobs[2].key_id)["state"]=="running"
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET lease_until=0 WHERE id=?",(identifier,))
    storage.recover_and_sweep()
    assert storage.lookup(identifier,jobs[2].key_id)["state"]=="failed"
    assert storage.claim() is None
    assert not storage.job_dir(identifier).exists()
    assert quota.peek(jobs[2].key_id).units_used==1


def test_gracefully_requeued_attempts_cannot_exceed_retry_bound(jobs,sample_pdf):
    identifier=submit(jobs,sample_pdf).json()["id"]
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET attempts=? WHERE id=?",(config.LIMITS.attempts,identifier))
    assert storage.claim() is None
    storage.maintenance()
    assert storage.lookup(identifier,jobs[2].key_id)["state"]=="failed"


def test_active_shutdown_kills_child_preserves_inputs_and_clears_scratch(jobs,sample_pdf,monkeypatch):
    identifier=submit(jobs,sample_pdf).json()["id"]
    real_popen=subprocess.Popen
    children=[]
    def slow_child(_command,**kwargs):
        process=real_popen([sys.executable,"-c","import time; time.sleep(30)"],**kwargs)
        children.append(process)
        return process
    monkeypatch.setattr(worker.subprocess,"Popen",slow_child)
    stop=threading.Event()
    stop.set()
    row=storage.claim()
    run_job(row,stop)
    current=storage.lookup(identifier,jobs[2].key_id)
    assert current["state"]=="queued" and current["claim"] is None
    assert children[0].poll() is not None
    assert sorted(p.name for p in storage.job_dir(identifier).iterdir())==["inputs"]


def test_output_cap_prevents_publication(jobs,sample_pdf,monkeypatch):
    identifier = submit(jobs,sample_pdf).json()["id"]
    row = storage.claim()
    scratch = storage.job_dir(identifier)/row["claim"]
    scratch.mkdir()
    output = scratch/"large.pdf"
    output.write_bytes(b"x"*20)
    monkeypatch.setattr(config,"LIMITS",replace(config.LIMITS,result_bytes=10))
    storage.finish(identifier,row["claim"],output=output)
    current = storage.lookup(identifier,jobs[2].key_id)
    assert current["state"]=="failed"
    assert current["error_code"]=="job_output_too_large"
    assert not (storage.job_dir(identifier)/"result").exists()


def test_queue_storage_and_account_limits_are_atomic(jobs,monkeypatch):
    key = jobs[2]
    monkeypatch.setattr(config,"LIMITS",replace(config.LIMITS,per_key=1))
    identifier = storage.begin_ingest(key.key_id,key.user_id)
    with pytest.raises(storage.JobError,match="identity"):
        storage.begin_ingest(key.key_id,key.user_id)
    storage.abandon_ingest(identifier)
    monkeypatch.setattr(config,"LIMITS",replace(config.LIMITS,storage_bytes=1))
    with pytest.raises(storage.JobError,match="queue"):
        storage.begin_ingest(key.key_id,key.user_id)


def test_revoked_key_cannot_start_or_retrieve_job(jobs,sample_pdf):
    identifier = submit(jobs,sample_pdf).json()["id"]
    accounts.revoke_key(jobs[2].user_id,jobs[2].key_id)
    assert storage.claim() is None
    assert jobs[0].get(f"/api/v1/jobs/{identifier}",headers=headers(jobs)).status_code==401
    storage.recover_and_sweep()
    assert storage.lookup(identifier,jobs[2].key_id)["state"]=="canceled"
    assert not storage.job_dir(identifier).exists()


def test_cancel_running_prevents_publish_then_removes_artifacts(jobs,sample_pdf):
    identifier = submit(jobs,sample_pdf).json()["id"]
    row = storage.claim()
    response = jobs[0].delete(f"/api/v1/jobs/{identifier}",headers=headers(jobs))
    assert response.status_code==202
    assert storage.job_dir(identifier).exists() # still owned by executing child
    assert not storage.renew(identifier,row["claim"])
    assert not storage.finish(identifier,row["claim"],error="job_canceled")
    storage.recover_and_sweep()
    assert not storage.job_dir(identifier).exists()


def test_worker_child_does_not_receive_credentials(tmp_path,monkeypatch):
    monkeypatch.setenv("CLERK_WEBHOOK_SECRET","synthetic-sensitive-value")
    monkeypatch.setenv("GA4_API_SECRET","synthetic-sensitive-value")
    env = child_environment(tmp_path)
    assert "CLERK_WEBHOOK_SECRET" not in env and "GA4_API_SECRET" not in env
    assert env["TEMP_DIR"]==env["TMPDIR"]==str(tmp_path)


def test_process_group_timeout_terminates_and_reaps_ignoring_child():
    process = subprocess.Popen([sys.executable,"-c","import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)"],start_new_session=True)
    try:
        time.sleep(0.1)
        terminate_group(process,grace=0.1)
        assert process.poll() is not None
        with pytest.raises(ProcessLookupError):
            os.kill(process.pid,0)
    finally:
        if process.poll() is None:
            terminate_group(process)


def test_disabled_feature_still_expires_results_and_queued_inputs(jobs,sample_pdf,monkeypatch):
    finished = submit(jobs,sample_pdf).json()["id"]
    run_job(storage.claim(),threading.Event())
    queued = submit(jobs,sample_pdf,idempotency="queued").json()["id"]
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET expires=? WHERE id=?",(time.time()-1,finished))
        conn.execute("UPDATE api_async_jobs SET deadline=? WHERE id=?",(time.time()-1,queued))
    monkeypatch.setenv("API_V1_JOBS_ENABLED","false")
    storage.maintenance()
    assert not storage.job_dir(finished).exists()
    assert not storage.job_dir(queued).exists()
    assert storage.lookup(finished,jobs[2].key_id)["state"]=="expired"
    assert storage.lookup(queued,jobs[2].key_id)["state"]=="failed"


@pytest.mark.parametrize("reason",["deadline","delete","revoked"])
def test_disabled_maintenance_retires_abandoned_claims(jobs,sample_pdf,monkeypatch,reason):
    identifier=submit(jobs,sample_pdf).json()["id"]
    claimed=storage.claim()
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET lease_until=? WHERE id=?",(time.time()-1,identifier))
        if reason=="deadline":
            conn.execute("UPDATE api_async_jobs SET deadline=? WHERE id=?",(time.time()-1,identifier))
    monkeypatch.setenv("API_V1_JOBS_ENABLED","false")
    if reason=="delete":
        response=jobs[0].delete(f"/api/v1/jobs/{identifier}",headers=headers(jobs))
        assert response.status_code==202
        assert response.json()["deletion_pending"] is True
    elif reason=="revoked":
        accounts.revoke_key(jobs[2].user_id,jobs[2].key_id)
    assert storage.job_dir(identifier).exists()
    storage.maintenance()
    row=storage.lookup(identifier,jobs[2].key_id)
    assert row["state"]==("failed" if reason=="deadline" else "canceled")
    assert row["claim"] is None and row["lease_until"] is None
    assert row["reserved_bytes"]==0
    assert not storage.job_dir(identifier).exists()


def test_disabled_maintenance_never_retires_a_live_supervisor_claim(jobs,sample_pdf,monkeypatch):
    identifier=submit(jobs,sample_pdf).json()["id"]
    claimed=storage.claim()
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET lease_until=?,deadline=? WHERE id=?",(time.time()-1,time.time()-1,identifier))
    monkeypatch.setenv("API_V1_JOBS_ENABLED","false")
    # A stalled supervisor can have expired timestamps while it remains alive.
    # Maintenance must use the actual singleton lock, not those timestamps.
    with (config.root()/"worker.lock").open("a") as live_supervisor:
        fcntl.flock(live_supervisor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        storage.maintenance()
        row=storage.lookup(identifier,jobs[2].key_id)
        assert row["state"]=="running" and row["claim"]==claimed["claim"]
        assert (storage.job_dir(identifier)/"inputs"/"0.pdf").exists()
        response=jobs[0].delete(f"/api/v1/jobs/{identifier}",headers=headers(jobs))
        assert response.status_code==202
        storage.maintenance()
        assert storage.lookup(identifier,jobs[2].key_id)["claim"]==claimed["claim"]
        assert storage.job_dir(identifier).exists()
    # Simulate the owner dying/releasing its lock: cancellation can now finish.
    storage.maintenance()
    assert storage.lookup(identifier,jobs[2].key_id)["claim"] is None
    assert not storage.job_dir(identifier).exists()


def test_disabled_maintenance_leaves_unexpired_orphan_work_recoverable(jobs,sample_pdf,monkeypatch):
    identifier=submit(jobs,sample_pdf).json()["id"]
    claimed=storage.claim()
    with storage.connection(write=True) as conn:
        conn.execute("UPDATE api_async_jobs SET lease_until=? WHERE id=?",(time.time()-1,identifier))
    monkeypatch.setenv("API_V1_JOBS_ENABLED","false")
    storage.maintenance()
    row=storage.lookup(identifier,jobs[2].key_id)
    assert row["state"]=="running" and row["claim"]==claimed["claim"]
    assert (storage.job_dir(identifier)/"inputs"/"0.pdf").exists()


def test_accounts_and_keys_are_fairly_scheduled(jobs,sample_pdf):
    _,_,key = jobs
    other_user = accounts.create_user("second-job-tests@example.com","synthetic-long-password")
    other_raw,other_key = accounts.issue_api_key(other_user.id,"other tests")
    first = submit(jobs,sample_pdf,idempotency="a1").json()["id"]
    second = submit(jobs,sample_pdf,idempotency="a2").json()["id"]
    third = submit(jobs,sample_pdf,idempotency="b1",raw=other_raw).json()["id"]
    row = storage.claim()
    assert row["id"]==first
    storage.finish(row["id"],row["claim"],error="test_complete")
    assert storage.claim()["id"]==third # another account before A's next job


def test_cross_process_duplicate_acceptance_charges_once(jobs,sample_pdf):
    key = jobs[2]
    identifiers = [storage.begin_ingest(key.key_id,key.user_id) for _ in range(2)]
    inputs = [{"name":"0.pdf","sha256":hashlib.sha256(sample_pdf).hexdigest(),"bytes":len(sample_pdf)}]
    code = """import json,sys
from pathlib import Path
from backend.app import store
from backend.app.api_v1.jobs import storage
store.DATA_DIR=Path(sys.argv[1]); store.DB_PATH=store.DATA_DIR/'privatools.db'
row,state,replayed=storage.accept(sys.argv[2],sys.argv[3],sys.argv[4],'process-race','grayscale',{},json.loads(sys.argv[5]),321)
print(json.dumps({'id':row['id'],'replayed':replayed}))
"""
    processes = [subprocess.Popen([sys.executable,"-c",code,str(store.DATA_DIR),identifier,key.key_id,key.user_id,json.dumps(inputs)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for identifier in identifiers]
    results=[]
    try:
        for process in processes:
            out,err=process.communicate(timeout=15)
            assert process.returncode==0,err
            results.append(json.loads(out))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
    assert len({result["id"] for result in results})==1
    assert sorted(result["replayed"] for result in results)==[False,True]
    assert quota.peek(key.key_id).units_used==1
    assert quota.peek(key.key_id).bytes_used==321


def test_worker_cli_processes_durable_queue_and_drains_on_signal(jobs,sample_pdf):
    identifier=submit(jobs,sample_pdf).json()["id"]
    env=dict(os.environ,PRIVATOOLS_DATA_DIR=str(store.DATA_DIR))
    with (config.root()/"worker.lock").open("a") as maintenance_lock:
        fcntl.flock(maintenance_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        process=subprocess.Popen([sys.executable,"-m","backend.app.api_v1.jobs.worker"],env=env,
                                 stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,start_new_session=True)
        # A web maintenance sweep can own the lock during worker startup.
        # The supervisor waits for it rather than making the launcher fail.
        time.sleep(1)
        assert process.poll() is None
    try:
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            row=storage.lookup(identifier,jobs[2].key_id)
            if row["state"]=="succeeded":
                break
            assert process.poll() is None
            time.sleep(0.1)
        assert row["state"]=="succeeded",row
        process.send_signal(signal.SIGTERM)
        _,err=process.communicate(timeout=5)
        assert process.returncode==0,err
        assert not storage.capability()["available"]
    finally:
        if process.poll() is None:
            terminate_group(process)


def test_fsync_failure_never_accepts_or_charges(jobs,sample_pdf,monkeypatch):
    def fail(_):
        raise OSError("synthetic disk failure")
    monkeypatch.setattr(storage,"fsync_dir",fail)
    with pytest.raises(OSError,match="synthetic disk"):
        submit(jobs,sample_pdf)
    assert quota.peek(jobs[2].key_id).units_used==0
    with storage.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_async_jobs").fetchone()[0]==0
        assert conn.execute("SELECT COUNT(*) FROM api_async_ingest").fetchone()[0]==0


def test_download_delete_race_closes_without_reopening_a_deleted_path(jobs,sample_pdf):
    identifier=submit(jobs,sample_pdf).json()["id"]
    run_job(storage.claim(),threading.Event())
    def get():
        return jobs[0].get(f"/api/v1/jobs/{identifier}/result",headers=headers(jobs))
    def delete():
        return jobs[0].delete(f"/api/v1/jobs/{identifier}",headers=headers(jobs))
    with ThreadPoolExecutor(max_workers=2) as pool:
        download=pool.submit(get)
        deleted=pool.submit(delete)
        assert download.result().status_code in (200,409,410)
        assert deleted.result().status_code==200
    assert not storage.job_dir(identifier).exists()
