"""Curated public v1 OpenAPI; never enables the whole-application schema."""
from __future__ import annotations

from copy import deepcopy
from threading import RLock

from fastapi.openapi.utils import get_openapi

from .catalog import CONSTRAINTS, PREFIX, cost, metadata, operation_id, public_routes

_CACHE_LOCK = RLock()
_ERROR_SCHEMA = {
    "type": "object", "required": ["code", "message"],
    "properties": {
        "code": {"type": "string", "description": "Stable machine-readable error identifier."},
        "message": {"type": "string", "description": "Safe human-readable explanation."},
        "detail": {"type": "string", "description": "Compatibility field for existing clients."},
        "request_id": {"type": "string"},
        "errors": {"type": "array", "items": {"type": "object", "properties": {
            "type": {"type": "string"}, "loc": {"type": "array", "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]}}, "msg": {"type": "string"},
        }}},
    },
}


def invalidate(app):
    """Clear static OpenAPI after intentional in-place route metadata changes."""
    with _CACHE_LOCK:
        app.state.api_v1_schema_cache = None


def _static_schema(app, routes):
    signature = tuple((id(r.original_route), r.path, tuple(sorted(r.methods))) for r in routes)
    with _CACHE_LOCK:
        cached = getattr(app.state, "api_v1_schema_cache", None)
        if cached is None or cached[0] != signature:
            document = get_openapi(
                title="PrivaTools API", version="1.0.0", routes=routes,
                description="Free authenticated file tools. Send X-API-Key or Authorization: Bearer. Paths are synchronous unless explicitly documented as jobs. Browser-only utilities are not HTTP operations.",
                servers=[{"url": "/", "description": "The API host serving this document"}],
            )
            app.state.api_v1_schema_cache = (signature, document)
        else:
            document = cached[1]
    # The cached document contains no costs, current policy, or worker state.
    return deepcopy(document)


def async_capability():
    # Lazy import avoids a dependency cycle during service/router registration.
    from .jobs import config
    from .jobs.storage import capability
    limits = config.LIMITS
    return {
        **capability(),
        "limits": {
            "max_input_bytes": limits.input_bytes,
            "max_result_bytes": limits.result_bytes,
            "max_outstanding_per_key": limits.per_key,
            "max_outstanding_per_account": limits.per_account,
            "max_outstanding_total": limits.max_pending,
            "outstanding_definition": "New jobs being uploaded, queued, or running count toward the applicable outstanding limits. Idempotent replays have separate bounded upload admission.",
            # The supervisor holds an exclusive lock and runs one child at a time.
            "worker_concurrency": 1,
            "queue_deadline_seconds": limits.queue_seconds,
            "runtime_per_attempt_seconds": limits.runtime_seconds,
            "max_attempts": limits.attempts,
            "upload_deadline_seconds": limits.upload_seconds,
            "max_submissions_per_minute": limits.submissions_per_minute,
            "storage_reservation_bytes": limits.storage_bytes,
            "storage_reservation_per_job_bytes": limits.reservation_bytes,
            "minimum_free_disk_bytes": limits.disk_headroom,
            "idempotency_retention_seconds": limits.tombstone_seconds,
        },
    }


def _body_schema(document, operation):
    content = operation.get("requestBody", {}).get("content", {})
    body = content.get("multipart/form-data", {}).get("schema", {})
    if "$ref" in body:
        return document["components"]["schemas"][body["$ref"].rsplit("/", 1)[1]]
    return body


def _request_overrides(document, path, operation):
    """Constraints checked inside handlers are absent from Form annotations."""
    fields = _body_schema(document, operation).get("properties", {})
    if path in {PREFIX + "/merge", PREFIX + "/compress", PREFIX + "/image-to-pdf"}:
        fields["files"].update(minItems=2 if path.endswith("/merge") else 1, maxItems=100)
    if path == PREFIX + "/compress":
        fields["level"]["enum"] = ["light", "recommended", "extreme", "email", "print", "archive", "web", "custom"]
        # Nullable Form fields use anyOf in OpenAPI 3.1.
        target = fields["target_size_mb"]
        for candidate in target.get("anyOf", [target]):
            if candidate.get("type") == "number":
                candidate["maximum"] = 500
    if path == PREFIX + "/rotate":
        fields["angle"].update(minimum=-360, maximum=360, multipleOf=90)


def build_schema(app) -> dict:
    routes = public_routes(app)
    document = _static_schema(app, routes)
    explicit_ids = {(r.path, method.lower()): r.operation_id for r in routes for method in r.methods if r.operation_id}
    capability = async_capability()
    document["x-privatools-async"] = capability
    document.setdefault("components", {}).setdefault("schemas", {})["ApiError"] = deepcopy(_ERROR_SCHEMA)
    # Pydantic describes UploadFile with contentMediaType. Retain that exact
    # declaration and add the familiar binary hint for OpenAPI client tooling.
    def binary_hints(value):
        if isinstance(value, dict):
            if value.get("contentMediaType") == "application/octet-stream":
                value.setdefault("format", "binary")
            for child in value.values():
                binary_hints(child)
        elif isinstance(value, list):
            for child in value:
                binary_hints(child)

    binary_hints(document.get("components", {}))
    for path, methods in document.get("paths", {}).items():
        for method, operation in methods.items():
            info = metadata(path)
            operation["operationId"] = explicit_ids.get((path, method), operation_id(method, path))
            operation["tags"] = [info["category"]]
            notes = CONSTRAINTS.get(path.removeprefix(PREFIX), [])
            if notes:
                operation["description"] = "\n\n".join(filter(None, [operation.get("description", ""), *notes]))
            media = info["response_media"]
            response = operation.get("responses", {}).get("200")
            if media and response:
                response["content"] = {
                    mime: {"schema": {} if mime == "application/json" else {"type": "string", "format": "binary"}}
                    for mime in media
                }
                response["description"] = "Successful response. The selected options and number of files determine the response media type."
            elif response and response.get("content") == {"application/json": {"schema": {}}}:
                # FastAPI's untyped default is not proof that a handler returns JSON.
                response.pop("content")
                response["description"] = "Successful response; the handler has not declared a detailed response schema."
            error_content = {"application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}}
            if "422" in operation["responses"]:
                operation["responses"]["422"] = {"description": "Request validation failed.", "content": deepcopy(error_content)}
            for status, description in {"401": "Missing, invalid, or revoked API key.", "429": "Rate, quota, or admission limit reached; inspect Retry-After.", "default": "Request or processing failed; inspect the stable error code and request ID."}.items():
                operation["responses"].setdefault(status, {"description": description, "content": deepcopy(error_content)})
            extension = operation.setdefault("x-privatools", {})
            extension["cost"] = cost(path)
            adapter = path.removeprefix(PREFIX + "/")
            enabled = method == "post" and capability.get("available", False) and adapter in capability.get("operations", [])
            extension["async"] = {"supported": True, "operation": adapter} if enabled else {"supported": False}
            extension["retrySafe"] = method in {"get", "head"}
            _request_overrides(document, path, operation)
    return document
