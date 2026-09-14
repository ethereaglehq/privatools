"""Authenticated submit/poll/download/delete. No existing sync route changes."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.datastructures import UploadFile

from ...auth.accounts import KeyRecord
from ...utils.cleanup import validate_pdf_content
from ...utils.logging import request_id_var
from ..deps import require_v1_key, acquire_http_slot
from .. import quota
from . import config, storage
from .adapters import ADAPTERS, validate_options
from .schema import JOB, DELETION, TEXT_RESULT, json_response

router = APIRouter(tags=["v1 · jobs"])


def error_response(exc: storage.JobError) -> JSONResponse:
    body = {"code":exc.code,"message":exc.message,"detail":exc.message}
    request_id = request_id_var.get()
    if request_id != "-":
        body["request_id"] = request_id
    return JSONResponse(body,status_code=exc.status,
                        headers={"Cache-Control":"no-store", **({"Retry-After":str(exc.retry)} if exc.retry else {})})


def require_feature() -> None:
    if not config.enabled():
        raise storage.JobError(503,"jobs_unavailable","Asynchronous processing is temporarily unavailable.",30)


@router.post("/jobs", status_code=202, operation_id="submit_async_job",
             responses={202:json_response(JOB,"Durably accepted job, or the existing job for an idempotent retry.")},openapi_extra={
    "parameters":[{"in":"header","name":"Idempotency-Key","required":True,"schema":{"type":"string","minLength":1,"maxLength":128}}],
    "requestBody":{"required":True,"content":{"multipart/form-data":{"schema":{
        "type":"object","required":["operation","files"],"properties":{
            "operation":{"type":"string","enum":list(ADAPTERS)},
            "options":{"type":"string","default":"{}","description":"JSON object. Only compress accepts level; other operations require empty options."},
            "files":{"type":"array","items":{"type":"string","format":"binary"},"minItems":1,"maxItems":10}}}}}}})
async def submit(request: Request, key: KeyRecord = Depends(require_v1_key)):
    identifier = None
    try:
        require_feature()
        idempotency = request.headers.get("idempotency-key", "")
        if not idempotency or len(idempotency)>128 or any(ord(c)<33 or ord(c)>126 for c in idempotency):
            raise storage.JobError(400,"invalid_idempotency_key","Send an Idempotency-Key of 1–128 visible ASCII characters.")
        # Shared request capacity and minute rate, with a zero-cost HTTP
        # receipt. Only storage.accept charges the durable job itself.
        await acquire_http_slot(request,key)
        identifier = await asyncio.to_thread(storage.begin_ingest,key.key_id,key.user_id,idempotency)
        # Bound chunked multipart bytes before the parser spools files. The
        # outer v1 middleware independently counts these same original bytes.
        receive = request._receive
        received = 0
        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body",b""))
                if received > config.LIMITS.input_bytes + 64*1024:
                    raise storage.JobError(413,"job_input_too_large","Job uploads exceed the 50 MiB total input limit.")
            return message
        request._receive = limited_receive
        async with request.form(max_files=10,max_fields=2,max_part_size=16*1024) as form:
            operation = form.get("operation")
            if not isinstance(operation,str) or operation not in ADAPTERS:
                raise storage.JobError(400,"unsupported_async_operation","Supported async operations: "+", ".join(ADAPTERS)+".")
            try:
                options = json.loads(form.get("options","{}"))
                if not isinstance(options,dict):
                    raise ValueError()
                options = validate_options(operation,options)
            except (ValueError,TypeError):
                raise storage.JobError(422,"invalid_job_options","Invalid options for this asynchronous operation.") from None
            files = form.getlist("files")
            adapter = ADAPTERS[operation]
            if not adapter.min_files <= len(files) <= adapter.max_files or any(not isinstance(f,UploadFile) for f in files):
                raise storage.JobError(422,"invalid_job_files",f"This operation requires {adapter.min_files}–{adapter.max_files} PDF files in the files field.")
            if any(name not in {"operation","options","files"} for name in form):
                raise storage.JobError(422,"invalid_job_fields","Unknown job submission field.")
            manifest = []
            total = 0
            for index,file in enumerate(files):
                if not (file.filename or "").lower().endswith(".pdf"):
                    raise storage.JobError(422,"invalid_job_files","Only PDF inputs are supported by these async operations.")
                name = f"{index}.pdf"
                path = storage.job_dir(identifier)/"inputs"/name
                digest = hashlib.sha256()
                count = 0
                with path.open("xb") as target:
                    while chunk := await file.read(256*1024):
                        if not count:
                            validate_pdf_content(chunk)
                        count += len(chunk)
                        total += len(chunk)
                        if total > config.LIMITS.input_bytes:
                            raise storage.JobError(413,"job_input_too_large","Job uploads exceed the 50 MiB total input limit.")
                        digest.update(chunk)
                        await asyncio.to_thread(target.write,chunk)
                    if not count:
                        raise storage.JobError(422,"invalid_job_files","An input PDF is empty.")
                    await asyncio.to_thread(target.flush)
                    await asyncio.to_thread(os.fsync,target.fileno())
                manifest.append({"name":name,"sha256":digest.hexdigest(),"bytes":count})
            await asyncio.to_thread(storage.fsync_dir,storage.job_dir(identifier)/"inputs")
            await asyncio.to_thread(storage.fsync_dir,storage.job_dir(identifier))
            await asyncio.to_thread(storage.fsync_dir,config.root())
        body_bytes = getattr(request.state,"v1_received_bytes",received)
        row,state,replayed = await asyncio.to_thread(storage.accept,identifier,key.key_id,key.user_id,idempotency,operation,options,manifest,body_bytes)
        # A completed/expired replay returns the existing state, never reruns it.
        row = await asyncio.to_thread(storage.lookup,row["id"],key.key_id)
        headers = {"Location":"/api/v1/jobs/"+row["id"],"Retry-After":"2","Cache-Control":"no-store",
                   "Idempotency-Replayed":str(replayed).lower()}
        if state is not None:
            headers.update(quota.headers(state))
        return JSONResponse(storage.public(row),status_code=202,headers=headers)
    except storage.JobError as exc:
        request.state.v1_error_code = exc.code
        return error_response(exc)
    finally:
        if identifier is not None:
            await asyncio.to_thread(storage.abandon_ingest,identifier)


@router.get("/jobs/{job_id}", operation_id="get_async_job",responses={200:json_response(JOB,"Current job state. No processing charge.")})
async def status(job_id: str, key: KeyRecord = Depends(require_v1_key)):
    try:
        # Retrieval remains available when new submissions are disabled.
        row = await asyncio.to_thread(storage.lookup,job_id,key.key_id)
        return JSONResponse(storage.public(row),headers={"Cache-Control":"no-store","Retry-After":"2"})
    except storage.JobError as exc:
        return error_response(exc)


@router.get("/jobs/{job_id}/result", operation_id="get_async_job_result",responses={200:{
    "description":"Completed PDF artifact or the pdf-to-text JSON artifact, available for one hour.",
    "content":{"application/pdf":{"schema":{"type":"string","format":"binary"}},"application/json":{"schema":TEXT_RESULT}}}})
async def result(job_id: str, key: KeyRecord = Depends(require_v1_key)):
    handle = None
    try:
        def open_result():
            # Open while holding the same database lock used to mark deletion;
            # no path is reopened later after its authorization check.
            with storage.connection(write=True) as conn:
                row = conn.execute("SELECT * FROM api_async_jobs WHERE id=? AND key_id=?",(job_id,key.key_id)).fetchone()
                if not row:
                    raise storage.JobError(404,"job_not_found","Job not found.")
                if row["state"] == "expired" or row["expires"] is not None and row["expires"]<=time.time():
                    raise storage.JobError(410,"job_result_expired","The job result has expired.")
                if row["state"] != "succeeded":
                    raise storage.JobError(409,"job_result_unavailable","The job has no available result.",2)
                return (storage.job_dir(job_id)/"result").open("rb"),ADAPTERS[row["operation"]]
        handle,adapter = await asyncio.to_thread(open_result)
        async def chunks():
            try:
                while True:
                    row = await asyncio.to_thread(storage.lookup,job_id,key.key_id)
                    if row["state"] != "succeeded":
                        break
                    data = await asyncio.to_thread(handle.read,256*1024)
                    if not data:
                        break
                    yield data
            finally:
                handle.close()
        return StreamingResponse(chunks(),media_type=adapter.media_type,
                                 headers={"Cache-Control":"no-store","Content-Disposition":f'attachment; filename="{adapter.filename}"',"X-Content-Type-Options":"nosniff"})
    except storage.JobError as exc:
        if handle:
            handle.close()
        return error_response(exc)
    except FileNotFoundError:
        return error_response(storage.JobError(410,"job_result_expired","The job result is no longer available."))


@router.delete("/jobs/{job_id}", operation_id="delete_async_job",responses={
    200:json_response(DELETION,"Artifacts deleted; repeated deletion is idempotent."),
    202:json_response(DELETION,"Cancellation accepted; worker will terminate the active process before deleting artifacts.")})
async def remove(job_id: str, key: KeyRecord = Depends(require_v1_key)):
    try:
        response = await asyncio.to_thread(storage.delete,job_id,key.key_id)
        return JSONResponse(response,status_code=202 if response["deletion_pending"] else 200,
                            headers={"Cache-Control":"no-store"})
    except storage.JobError as exc:
        return error_response(exc)
