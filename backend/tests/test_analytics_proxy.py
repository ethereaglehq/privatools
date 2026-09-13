"""First-party analytics proxy tests.

The browser should never load Google Analytics scripts directly. It sends a
small first-party pageview beacon, and the backend forwards a sanitized GA4
Measurement Protocol event only when the deployment has configured a secret.
"""

from __future__ import annotations

from backend.app.routes import analytics


def test_pageview_noops_without_ga4_secret(client, monkeypatch):
    calls: list[tuple[str, dict]] = []
    monkeypatch.delenv("GA4_API_SECRET", raising=False)
    monkeypatch.setattr(
        analytics,
        "_send_ga4_pageview",
        lambda endpoint, body: calls.append((endpoint, body)),
    )

    resp = client.post(
        "/api/analytics/pageview",
        json={
            "path": "/tool/compress-pdf",
            "title": "Compress PDF",
            "client_id": "client.12345678",
        },
    )

    assert resp.status_code == 204
    assert resp.content == b""
    assert calls == []


def test_pageview_forwards_sanitized_ga4_payload(client, monkeypatch):
    calls: list[tuple[str, dict]] = []
    monkeypatch.setenv("GA4_API_SECRET", "test-secret")
    monkeypatch.setenv("GA4_MEASUREMENT_ID", "G-TEST123")
    monkeypatch.setattr(
        analytics,
        "_send_ga4_pageview",
        lambda endpoint, body: calls.append((endpoint, body)),
    )

    resp = client.post(
        "/api/analytics/pageview",
        json={
            "path": "/tool/compress-pdf?filename=private.pdf#fragment",
            "title": "Compress\nPDF",
            "referrer": "https://evil.example/private",
            "client_id": "client.12345678",
        },
    )

    assert resp.status_code == 204
    assert len(calls) == 1
    endpoint, body = calls[0]
    assert "measurement_id=G-TEST123" in endpoint
    assert "api_secret=test-secret" in endpoint
    assert body["client_id"] == "client.12345678"
    assert body["non_personalized_ads"] is True

    params = body["events"][0]["params"]
    assert body["events"][0]["name"] == "page_view"
    assert params["page_path"] == "/tool/compress-pdf"
    assert params["page_location"] == "https://privatools.me/tool/compress-pdf"
    assert params["page_title"] == "Compress PDF"
    assert "page_referrer" not in params


def test_pageview_keeps_same_origin_referrer(client, monkeypatch):
    calls: list[tuple[str, dict]] = []
    monkeypatch.setenv("GA4_API_SECRET", "test-secret")
    monkeypatch.setenv("GA4_MEASUREMENT_ID", "G-TEST123")
    monkeypatch.setattr(
        analytics,
        "_send_ga4_pageview",
        lambda endpoint, body: calls.append((endpoint, body)),
    )

    resp = client.post(
        "/api/analytics/pageview",
        json={
            "path": "/privacy",
            "title": "Privacy Policy",
            "referrer": "https://privatools.me/tool/merge-pdf?source=email#top",
            "client_id": "client.87654321",
        },
    )

    assert resp.status_code == 204
    params = calls[0][1]["events"][0]["params"]
    assert params["page_referrer"] == "https://privatools.me/tool/merge-pdf"


def test_pageview_invalid_client_id_noops(client, monkeypatch):
    calls: list[tuple[str, dict]] = []
    monkeypatch.setenv("GA4_API_SECRET", "test-secret")
    monkeypatch.setattr(
        analytics,
        "_send_ga4_pageview",
        lambda endpoint, body: calls.append((endpoint, body)),
    )

    resp = client.post(
        "/api/analytics/pageview",
        json={"path": "/tool/compress-pdf", "client_id": "short"},
    )

    assert resp.status_code == 204
    assert calls == []


def _forwarded(client, monkeypatch, payload: dict) -> dict:
    calls: list[tuple[str, dict]] = []
    monkeypatch.setenv("GA4_API_SECRET", "test-secret")
    monkeypatch.setattr(
        analytics,
        "_send_ga4_pageview",
        lambda endpoint, body: calls.append((endpoint, body)),
    )
    resp = client.post("/api/analytics/pageview", json=payload)
    assert resp.status_code == 204
    assert len(calls) == 1
    return calls[0][1]["events"][0]


def test_legacy_engagement_is_remapped_to_allowed_custom_event(client, monkeypatch):
    event = _forwarded(client, monkeypatch, {
        "event": "user_engagement", "path": "/tool/compress-pdf", "client_id": "client.12345678",
        "engagement_time_msec": 42_000, "session_id": "1800000000",
    })
    assert event["name"] == "foreground_time"
    assert event["params"]["engagement_time_msec"] == 42_000
    assert event["params"]["session_id"] == "1800000000"


def test_reserved_or_unknown_events_are_dropped_without_inventing_pageviews():
    for name in ("purchase", "first_visit", "session_start", "random_event"):
        assert analytics._build_ga4_payload(analytics.AnalyticsPageview(
            event=name, client_id="client.12345678")) is None


def test_zero_time_and_invalid_session_do_not_invent_measurements(client, monkeypatch):
    event = _forwarded(client, monkeypatch, {
        "path": "/", "client_id": "client.12345678", "engagement_time_msec": 0,
        "session_id": "not-a-measured-session",
    })
    assert "engagement_time_msec" not in event["params"]
    assert "session_id" not in event["params"]
    assert "session_engaged" not in event["params"]


def test_real_tool_success_is_allowed_only_on_tool_routes(client, monkeypatch):
    event = _forwarded(client, monkeypatch, {
        "event": "tool_success", "path": "/tools/json-formatter", "client_id": "client.12345678",
    })
    assert event["name"] == "tool_success"
    assert analytics._build_ga4_payload(analytics.AnalyticsPageview(
        event="tool_success", path="/account", client_id="client.12345678")) is None


def test_blank_measurement_id_uses_existing_public_default(monkeypatch):
    monkeypatch.setenv("GA4_API_SECRET", "test-secret")
    monkeypatch.setenv("GA4_MEASUREMENT_ID", "")
    assert analytics._analytics_config() == (analytics._DEFAULT_MEASUREMENT_ID, "test-secret")


def test_regional_policy_requires_explicit_flags_and_preserves_no_store(client, monkeypatch):
    monkeypatch.delenv("GA_BROWSER_TAG_ENABLED", raising=False)
    monkeypatch.delenv("GA_TRUSTED_COUNTRY_HEADER", raising=False)
    monkeypatch.setenv("GA_DEFAULT_ON_COUNTRIES", "US,IN")
    for headers in ({}, {"CF-IPCountry": "US"}, {"X-PrivaTools-Country": "US"}, {"X-Forwarded-For": "1.1.1.1"}):
        response = client.get("/api/analytics/policy", headers=headers)
        assert response.json() == {"mode": "opt_in"}
        assert "no-store" in response.headers["cache-control"]
    monkeypatch.setenv("GA_BROWSER_TAG_ENABLED", "true")
    assert client.get("/api/analytics/policy", headers={"X-PrivaTools-Country": "US"}).json() == {"mode": "opt_in"}
    monkeypatch.setenv("GA_TRUSTED_COUNTRY_HEADER", "true")
    assert client.get("/api/analytics/policy", headers={"CF-IPCountry": "US"}).json() == {"mode": "opt_in"}
    assert client.get("/api/analytics/policy", headers={"X-PrivaTools-Country": "US"}).json() == {"mode": "default_on"}
    for country in ("GB", "DE", "XX", "T1", "us", "USA", "US,IN", ""):
        assert client.get("/api/analytics/policy", headers={"X-PrivaTools-Country": country}).json() == {"mode": "opt_in"}
    monkeypatch.setenv("GA_DEFAULT_ON_COUNTRIES", "")
    assert client.get("/api/analytics/policy", headers={"X-PrivaTools-Country": "US"}).json() == {"mode": "opt_in"}
