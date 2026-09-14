"""Request-ID middleware.

Tags every request with a short opaque ID, exposes it on
``request.state.request_id``, and echoes it in the ``X-Request-ID``
response header. The error handlers in
:mod:`app.middleware.error_handlers` include the same ID in their JSON
body, so a user can paste the ID into a bug report and we can grep logs
for that single request.

Versioned API requests always get a fresh server-generated ID so their
metadata history cannot retain private client text. Other routes respect a
safe inbound ``X-Request-ID`` (useful when a proxy already tagged a request)
or mint a fresh 12-character hex token. 12 hex chars = 48 bits of entropy,
plenty for collision avoidance within a server's log retention window
without being unwieldy in the UI.
"""

from __future__ import annotations

import logging
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..utils.logging import (
    configure_logging as _configure_json_logging,
    request_id_var,
)

logger = logging.getLogger("privatools.request")

_INBOUND_HEADER = "x-request-id"
_OUTBOUND_HEADER = "X-Request-ID"


def _generate_request_id() -> str:
    return secrets.token_hex(6)


def _safe_inbound(value: str | None) -> str | None:
    """Reject inbound IDs that aren't safe to echo into a header.

    Browsers / proxies occasionally send wild values here; we don't want
    to reflect anything that could break HTTP framing or smuggle log
    delimiters.
    """
    if not value:
        return None
    value = value.strip()
    if not value or len(value) > 64:
        return None
    # ASCII alphanumeric, dash, underscore only.
    if not all(c.isalnum() or c in "-_" for c in value):
        return None
    return value


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a request ID early so it's available to all later middleware.

    Also binds the ID to the ``request_id_var`` contextvar so any
    ``logger.info(...)`` called from inside the request handler picks up
    the right tag automatically — no need to thread ``extra={...}`` down
    every call.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.url.path.startswith("/api/v1/"):
            # Durable API history must never retain arbitrary client text in
            # this field. Accounting generates the same ID before this layer.
            rid = (getattr(request.state, "request_id", None)
                   if getattr(request.state, "v1_body_meter_installed", False) else None) or _generate_request_id()
        else:
            rid = _safe_inbound(request.headers.get(_INBOUND_HEADER)) or _generate_request_id()
        request.state.request_id = rid
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        except Exception:
            # Exception handlers run *after* this middleware unwinds, so
            # log a marker here with the ID so we can correlate them.
            logger.exception("request %s raised in handler", rid)
            raise
        finally:
            # Always reset — leaving the contextvar set would leak the
            # ID into the next request that reuses this asyncio task.
            request_id_var.reset(token)
        response.headers[_OUTBOUND_HEADER] = rid
        return response


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
# The actual implementation lives in :mod:`app.utils.logging` — re-exported
# here so legacy callers (``from .middleware import configure_logging``)
# keep working without churn.
def configure_logging(level: str | None = None) -> None:
    """Configure root logger with the structured JSON formatter.

    See :func:`app.utils.logging.configure_logging`.
    """
    _configure_json_logging(level)
