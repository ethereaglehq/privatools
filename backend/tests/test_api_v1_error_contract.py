"""Public v1 errors are machine-readable without changing legacy replies."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from backend.app.middleware.error_handlers import register_error_handlers
from backend.app.utils.exceptions import ToolError


def application():
    app = FastAPI()
    register_error_handlers(app)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = "test-request"
        response = await call_next(request)
        if getattr(request.state, "v1_validation_rejected", False):
            response.headers["X-Test-Validation-Rejected"] = "true"
        return response

    @app.get("/api/v1/validation")
    async def validation(number: int):
        return {"number": number}

    @app.get("/api/v1/tool")
    async def tool():
        raise HTTPException(400, "This file cannot be processed")

    @app.get("/api/tool")
    async def legacy():
        raise HTTPException(400, "This file cannot be processed")

    @app.get("/api/v1/refused")
    async def refused():
        raise HTTPException(429, {"code": "quota_exceeded", "message": "Quota exhausted"},
                            headers={"Retry-After": "30"})

    @app.get("/api/v1/failed")
    async def failed():
        raise ToolError("private path /srv/secrets must not leak")

    @app.get("/api/v1/busy")
    async def busy():
        raise HTTPException(503, {"code": "server_busy", "message": "private implementation detail"},
                            headers={"Retry-After": "2"})

    return app


def test_v1_error_fields_are_additive_and_legacy_is_unchanged():
    with TestClient(application(), raise_server_exceptions=False) as client:
        result = client.get("/api/v1/tool")
        assert result.status_code == 400
        assert result.json() == {
            "code": "invalid_request", "message": "This file cannot be processed",
            "detail": "This file cannot be processed", "request_id": "test-request",
        }
        assert result.headers["X-Request-ID"] == "test-request"
        legacy = client.get("/api/tool").json()
        assert "code" not in legacy and "message" not in legacy


def test_validation_marks_preprocessing_rejection_without_echoing_input():
    with TestClient(application()) as client:
        result = client.get("/api/v1/validation?number=private-input")
        assert result.status_code == 422
        assert result.json()["code"] == "validation_error"
        assert result.headers["X-Test-Validation-Rejected"] == "true"
        assert result.json()["errors"][0]["loc"] == ["query", "number"]
        assert "private-input" not in result.text


def test_existing_quota_code_and_retry_header_are_preserved():
    with TestClient(application()) as client:
        result = client.get("/api/v1/refused")
        assert result.json()["code"] == "quota_exceeded"
        assert result.json()["message"] == "Quota exhausted"
        assert result.headers["Retry-After"] == "30"


def test_v1_tool_server_failures_do_not_expose_internal_details():
    with TestClient(application(), raise_server_exceptions=False) as client:
        result = client.get("/api/v1/failed")
        assert result.status_code == 500
        assert result.json()["code"] == "processing_failed"
        assert "private path" not in result.text and "/srv/" not in result.text


def test_busy_response_keeps_retry_code_with_a_safe_message():
    with TestClient(application()) as client:
        result = client.get("/api/v1/busy")
        assert result.status_code == 503
        assert result.json()["code"] == "server_busy"
        assert result.headers["Retry-After"] == "2"
        assert "private implementation detail" not in result.text
