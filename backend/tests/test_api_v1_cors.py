"""External apps can use explicit API-key headers without opening account CORS."""


def test_external_api_preflight_accepts_key_and_idempotency_headers(client):
    response = client.options("/api/v1/jobs", headers={
        "Origin": "https://developer.example",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-api-key,content-type,idempotency-key",
    })
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert "Access-Control-Allow-Credentials" not in response.headers


def test_external_api_errors_expose_retry_and_usage_headers(client):
    response = client.get("/api/v1/whoami", headers={"Origin": "https://developer.example"})
    assert response.status_code == 401
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    exposed = response.headers["Access-Control-Expose-Headers"].lower()
    assert "retry-after" in exposed and "x-ratelimit-remaining" in exposed
    assert "x-request-id" in exposed


def test_public_api_cors_does_not_open_accounts_or_legacy_tools(client):
    for path in ("/api/auth/me", "/api/merge"):
        response = client.options(path, headers={
            "Origin": "https://developer.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert response.status_code == 400
        assert "Access-Control-Allow-Origin" not in response.headers
