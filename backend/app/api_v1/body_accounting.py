"""ASGI body metering and HTTP admission lifecycle, without copying uploads."""
from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from contextlib import suppress

import anyio
from fastapi import HTTPException
from starlette.datastructures import MutableHeaders

from . import admission, quota

logger = logging.getLogger(__name__)


async def database_call(fn, *args):
    # Shield completion so cancellation cannot lose a committed reservation's token.
    return await anyio.to_thread.run_sync(fn, *args, abandon_on_cancel=False)


async def renew_lease(token: str):
    while True:
        await asyncio.sleep(30)
        try:
            await database_call(admission.renew, token)
        except sqlite3.Error:
            # Expiry alone never reclaims a living owner's slot.
            logger.exception("API lease renewal failed")


class V1AccountingMiddleware:
    """Install outermost, replacing the old attach_quota_headers middleware.

    Body parsing runs before FastAPI dependencies; they use the completed count
    for atomic admission. Slots remain held through the response, including
    streaming, and are returned even after timeout/disconnection/exception.
    """
    def __init__(self, app, max_body_bytes: int | None = None):
        self.app = app
        self.max_body_bytes = max_body_bytes or int(os.environ.get("MAX_UPLOAD_MB", "500"))*1024*1024

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/api/v1/"):
            await self.app(scope, receive, send)
            return
        state = scope.setdefault("state", {})
        state["v1_received_bytes"] = 0
        state["v1_body_complete"] = False
        state["v1_body_meter_installed"] = True

        async def counted_receive():
            message = await receive()
            if message["type"] == "http.request":
                state["v1_received_bytes"] += len(message.get("body", b""))
                if state["v1_received_bytes"] > self.max_body_bytes:
                    state["v1_prework_rejected"] = True
                    raise HTTPException(413, detail={"code": "request_too_large", "message": "Request body exceeds the upload limit."})
                if not message.get("more_body", False):
                    state["v1_body_complete"] = True
            return message

        async def report_send(message):
            if message["type"] == "http.response.start":
                token = state.get("v1_reservation")
                if token and (state.get("v1_validation_rejected") or state.get("v1_prework_rejected")):
                    await database_call(quota.refund_reservation, token)
                key_id = state.get("v1_key_id")
                if key_id:
                    headers = MutableHeaders(scope=message)
                    try:
                        standing = await database_call(quota.peek, key_id)
                        for name, value in quota.headers(standing).items():
                            headers[name] = value
                    except sqlite3.Error:
                        # Preserve the intended 503 response if admission's store
                        # is unavailable; don't turn it into a header-time crash.
                        logger.exception("API quota header lookup failed")
                    headers["X-RateLimit-Requests-Per-Minute"] = str(admission.REQUESTS_PER_MINUTE)
                    headers["X-RateLimit-Request-Burst"] = str(admission.BURST)
            await send(message)

        try:
            await self.app(scope, counted_receive, report_send)
        finally:
            # An HTTP slot is separate from surviving native work. Do not claim
            # this release stops an arbitrary C extension or subprocess.
            heartbeat = state.get("v1_lease_heartbeat")
            if heartbeat:
                heartbeat.cancel()
            with anyio.CancelScope(shield=True):
                if heartbeat:
                    with suppress(asyncio.CancelledError):
                        await heartbeat
                token = state.get("v1_reservation")
                if token:
                    await database_call(admission.release, token)
