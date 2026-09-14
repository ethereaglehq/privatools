"""Verified-key authentication and shared admission for the versioned API."""
from __future__ import annotations

import asyncio
import sqlite3
import anyio

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from ..auth import accounts
from . import admission, quota
from .body_accounting import database_call, renew_lease

api_key_header = APIKeyHeader(name="X-API-Key", scheme_name="XAPIKey", auto_error=False)
bearer_header = APIKeyHeader(name="Authorization", scheme_name="BearerAuth", auto_error=False)


def _from_bearer(value: str | None) -> str | None:
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    return (token.strip() or None) if scheme.lower() == "bearer" else None


def _error(status: int, code: str, detail: str, headers: dict | None = None) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": detail}, headers=headers)


async def require_v1_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
    authorization: str | None = Security(bearer_header),
) -> accounts.KeyRecord:
    api_key = api_key or _from_bearer(authorization)
    if not api_key:
        raise _error(401, "missing_api_key", "Send X-API-Key or Authorization: Bearer <key>. Create a key at /account.", {"WWW-Authenticate": "Bearer"})
    try:
        record = await database_call(accounts.resolve_key, api_key)
        if record is None:
            raise _error(401, "invalid_api_key", "That key is not recognised, or it has been revoked.", {"WWW-Authenticate": "Bearer"})
        await database_call(accounts.touch_key, record.key_id)
    except sqlite3.Error:
        raise _error(503, "admission_unavailable", "API admission is temporarily unavailable. Try again shortly.", {"Retry-After": "5"}) from None
    request.state.v1_key_id = record.key_id
    return record


async def enforce_quota(request: Request, key: accounts.KeyRecord = Depends(require_v1_key)) -> accounts.KeyRecord:
    units = quota.cost_for(request.url.path)
    if units == 0:
        return key
    if not getattr(request.state, "v1_body_meter_installed", False):
        raise _error(503, "admission_unavailable", "Request accounting is unavailable.", {"Retry-After": "5"})
    # Endpoints with no declared body may not have consumed it during parsing.
    # Drain their stream once; no buffer or second copy is retained.
    if not request.state.v1_body_complete:
        async for _ in request.stream():
            pass
    if request.url.path.rstrip("/") == "/api/v1/pipeline":
        from ..routes.developer import _steps_from_form
        form = await request.form()
        steps = _steps_from_form(form.get("steps", ""))
        units = sum(quota.PIPELINE_STEP_COSTS[slug] for slug in steps)
    return await acquire_http_slot(request, key, units, request.state.v1_received_bytes)


async def acquire_http_slot(request: Request, key: accounts.KeyRecord,
                            units: int = 0, size_bytes: int = 0) -> accounts.KeyRecord:
    """Share HTTP capacity/rate admission with async job submission.

    Jobs use a zero-cost HTTP receipt; their actual durable charge is committed
    with queue acceptance. Polling/download/deletion do not call this helper.
    """
    if not getattr(request.state, "v1_body_meter_installed", False):
        raise _error(503, "admission_unavailable", "Request accounting is unavailable.", {"Retry-After": "5"})
    try:
        pending = asyncio.create_task(database_call(admission.admit, key.key_id, units, size_bytes))
        try:
            result = await asyncio.shield(pending)
        except asyncio.CancelledError:
            # A database thread may commit after its HTTP waiter is cancelled.
            # Retrieve that result so the unused reservation cannot be lost.
            with anyio.CancelScope(shield=True):
                result = await pending
                if result.allowed:
                    await database_call(quota.refund_reservation, result.token)
                    await database_call(admission.release, result.token)
            raise
    except sqlite3.Error:
        raise _error(503, "admission_unavailable", "API admission is temporarily unavailable. Try again shortly.", {"Retry-After": "5"}) from None
    if not result.allowed:
        messages = {
            "quota_exceeded": "Daily free API quota reached. It resets at 00:00 UTC.",
            "concurrency_limit_exceeded": f"This key already has {quota.MAX_JOBS_PER_KEY} admitted processing requests. Retry after one completes.",
            "rate_limit_exceeded": f"This key's request burst is exhausted. Requests refill at {admission.REQUESTS_PER_MINUTE} per minute.",
            "server_busy": "The server's processing request capacity is occupied. Retry shortly.",
        }
        raise _error(503 if result.code == "server_busy" else 429, result.code, messages[result.code], {**quota.headers(result.state), "Retry-After": str(result.retry_after)})
    request.state.v1_reservation = result.token
    request.state.v1_quota = result.state
    request.state.v1_admitted = True
    request.state.v1_lease_heartbeat = asyncio.create_task(renew_lease(result.token))
    return key
