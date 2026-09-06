from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Response
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_DEFAULT_MEASUREMENT_ID = "G-B3VWQ44MX1"
_PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://privatools.me").rstrip("/")
_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,96}$")


class AnalyticsPageview(BaseModel):
    path: str = Field(default="/", max_length=512)
    title: str | None = Field(default=None, max_length=160)
    referrer: str | None = Field(default=None, max_length=512)
    client_id: str | None = Field(default=None, max_length=96)
    # GA4 fills Realtime from events alone, but leaves every standard report
    # empty unless the event carries a session and some engagement time. We
    # sent neither, so page views arrived, showed up in Realtime, and never
    # reached Traffic acquisition or Pages and screens.
    session_id: str | None = Field(default=None, max_length=32)
    engagement_time_msec: int | None = Field(default=None, ge=0, le=3_600_000)
    # A page view and a report of time-on-page are different events. Sending
    # both as page_view would double the page-view count; sending neither is
    # how every single-page visit scored as a bounce.
    event: str | None = Field(default=None, max_length=32)
    # Engagement TIME alone does not make a session engaged. GA4 builds the
    # engaged-session count — and so bounce rate, its inverse — from this flag,
    # which is why the property once reported a real 40s average engagement
    # next to a 100% bounce rate.
    # Wide enough to accept a wrong value and normalise it to "0" rather than
    # 422 the whole event: a malformed flag should cost the engagement reading,
    # not the page view that carried it.
    session_engaged: str | None = Field(default=None, max_length=8)


def _clean_path(path: str | None) -> str:
    value = (path or "/").strip()
    if not value.startswith("/") or value.startswith("//"):
        return "/"
    # Keep aggregate page metrics from accidentally carrying share/query data.
    return value.split("?", 1)[0].split("#", 1)[0][:512] or "/"


_SESSION_ID_RE = re.compile(r"^[0-9]{6,20}$")


def _clean_session_id(value: str | None) -> str:
    """A GA4 session id is a numeric timestamp; anything else gets replaced.

    Falling back to a fresh id is deliberate: a missing or malformed session
    would otherwise drop the event out of every standard report, which is the
    exact failure this whole field exists to prevent.
    """
    v = (value or "").strip()
    if _SESSION_ID_RE.fullmatch(v):
        return v
    return str(int(time.time()))


# Only the two events this site actually sends. An allowlist rather than a
# passthrough: the endpoint is unauthenticated, and an open event name would
# let anyone write arbitrary events into the property.
_ALLOWED_EVENTS = frozenset({"page_view", "user_engagement"})


def _clean_event(value: str | None) -> str:
    v = (value or "").strip()
    return v if v in _ALLOWED_EVENTS else "page_view"


def _clean_engaged(value: str | None) -> str:
    """GA4 wants the literal string "1" or "0"; anything else is not engaged.

    Defaulting to "0" rather than omitting the parameter keeps the reading
    conservative: a session we cannot vouch for counts as a bounce, which
    understates engagement instead of inventing it.
    """
    return "1" if (value or "").strip() == "1" else "0"


def _clean_text(value: str | None, limit: int) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", value).strip()
    return cleaned[:limit] or None


def _clean_referrer(value: str | None) -> str | None:
    cleaned = _clean_text(value, 512)
    if not cleaned:
        return None
    parsed = urllib.parse.urlsplit(cleaned)
    if parsed.scheme != "https" or parsed.hostname not in {"privatools.me", "www.privatools.me"}:
        return None
    path = parsed.path or "/"
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _analytics_config() -> tuple[str, str] | None:
    secret = os.environ.get("GA4_API_SECRET")
    if not secret:
        return None
    measurement_id = os.environ.get("GA4_MEASUREMENT_ID", _DEFAULT_MEASUREMENT_ID)
    return measurement_id, secret


def _build_ga4_payload(pageview: AnalyticsPageview) -> dict[str, Any] | None:
    client_id = (pageview.client_id or "").strip()
    if not _CLIENT_ID_RE.fullmatch(client_id):
        return None

    path = _clean_path(pageview.path)
    params: dict[str, Any] = {
        "page_location": f"{_PUBLIC_BASE_URL}{path}",
        "page_path": path,
        # Both are required for a Measurement Protocol event to count towards
        # users, sessions and engagement rather than only appearing in Realtime.
        "session_id": _clean_session_id(pageview.session_id),
        # Present and non-zero, or GA4 keeps the event out of every standard
        # report. 1ms is the smallest honest floor: the real number arrives in
        # the user_engagement event sent when the page is hidden.
        "engagement_time_msec": max(pageview.engagement_time_msec or 0, 1),
        "session_engaged": _clean_engaged(pageview.session_engaged),
    }
    title = _clean_text(pageview.title, 160)
    referrer = _clean_referrer(pageview.referrer)
    if title:
        params["page_title"] = title
    if referrer:
        params["page_referrer"] = referrer

    return {
        "client_id": client_id,
        "non_personalized_ads": True,
        "events": [{"name": _clean_event(pageview.event), "params": params}],
    }


def _send_ga4_pageview(endpoint: str, body: dict[str, Any]) -> None:
    data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={
            "content-type": "application/json",
            "user-agent": "PrivaTools analytics proxy",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=1.5) as response:
            response.read(128)
    except (OSError, urllib.error.URLError) as exc:
        logger.debug("ga4 analytics proxy send failed: %s", exc.__class__.__name__)


@router.post("/analytics/pageview", status_code=204)
async def analytics_pageview(
    pageview: AnalyticsPageview,
    background_tasks: BackgroundTasks,
) -> Response:
    config = _analytics_config()
    body = _build_ga4_payload(pageview)
    if config and body:
        measurement_id, secret = config
        query = urllib.parse.urlencode({"measurement_id": measurement_id, "api_secret": secret})
        endpoint = f"https://www.google-analytics.com/mp/collect?{query}"
        background_tasks.add_task(_send_ga4_pageview, endpoint, body)
    return Response(status_code=204)
