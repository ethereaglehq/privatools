"""Uploads travel under the form field their route reads.

The site's single-file uploads (the helpers in frontend/src/lib/api.ts, and
the Batch and Pipeline pages) name each file with ``uploadFieldFor`` from
frontend/src/lib/upload-fields.ts: ``files`` for the routes that file lists,
``file`` for every other route. They once sent every file under both names so
one request suited either kind of route, which doubled each upload and left
one file only half of the 500 MB request cap.

These tests hold that list to the FastAPI app. A route that starts or stops
reading ``files: list[UploadFile]`` fails here until the list agrees, instead
of answering the site with a 422 in production. They see only uploads a route
declares as parameters: one that parses them itself with ``await
request.form()`` is invisible here (today only ``/api/v1/jobs``, which the site
never calls).
"""
from __future__ import annotations

import re
import sys
import types
import typing
from pathlib import Path

from fastapi import params
from fastapi.routing import APIRoute
from starlette.datastructures import UploadFile

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_FIELDS_TS = ROOT / "frontend" / "src" / "lib" / "upload-fields.ts"
sys.path.insert(0, str(ROOT))

# Routes whose uploads are neither one `file` nor one `files` list. Their pages
# build the form themselves with these names; the single-file helpers never
# post to them.
OTHER_UPLOAD_FIELDS = {
    "/alternate-mix": {"file1", "file2"},
    "/compare": {"file1", "file2"},
    "/overlay": {"base_file", "overlay_file"},
    "/qr-code": {"logo", "embed_in_pdf"},
}


def _listed_files_routes() -> list[str]:
    # Drop comments first, so a route commented out of the list does not count.
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", UPLOAD_FIELDS_TS.read_text(encoding="utf-8"), flags=re.S)
    block = re.search(r"export const FILES_FIELD_ROUTES\b[^=]*=\s*\[(.*?)\]", text, re.S)
    assert block, f"FILES_FIELD_ROUTES not found in {UPLOAD_FIELDS_TS.relative_to(ROOT)}"
    # Only quoted strings may remain; anything else is a form this parser cannot read.
    assert re.fullmatch(r"""\s*(?:(["'])[^"']*\1\s*,?\s*)*""", block.group(1)), (
        f"FILES_FIELD_ROUTES must be a plain list of quoted routes: [{block.group(1)}]"
    )
    return re.findall(r"""["']([^"']+)["']""", block.group(1))


def _upload_kind(annotation) -> str | None:
    """"one" for UploadFile, "list" for a list of them, None for anything else."""
    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        return _upload_kind(typing.get_args(annotation)[0])
    if origin in (typing.Union, types.UnionType):
        kinds = {_upload_kind(arg) for arg in typing.get_args(annotation) if arg is not type(None)}
        return kinds.pop() if len(kinds) == 1 else None
    if origin in (list, typing.List):
        args = typing.get_args(annotation)
        return "list" if args and _upload_kind(args[0]) == "one" else None
    if isinstance(annotation, type) and issubclass(annotation, UploadFile):
        return "one"
    return None


def _uploads(dependant) -> dict[str, str]:
    """The upload fields a route (and its dependencies) reads, by field name."""
    found: dict[str, str] = {}
    for param in dependant.body_params:
        kind = _upload_kind(param.field_info.annotation)
        if kind is None and isinstance(param.field_info, params.File):
            kind = "list" if typing.get_origin(param.field_info.annotation) in (list, typing.List) else "one"
        if kind:
            found[param.alias] = kind
    for sub in dependant.dependencies:
        found.update(_uploads(sub))
    return found


def _upload_routes() -> dict[str, dict[str, str]]:
    """Every POST route the site calls under /api that reads an upload, keyed
    by the path the frontend passes (without /api)."""
    from backend.app.main import app

    routes: dict[str, dict[str, str]] = {}

    def visit(route, prefix: str = "") -> None:
        if isinstance(route, APIRoute) and "POST" in route.methods:
            path = f"{prefix}{route.path}"
            if path.startswith("/api/") and not path.startswith("/api/v1/"):
                fields = _uploads(route.dependant)
                if fields:
                    routes[path[len("/api"):]] = fields
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            child_prefix = f"{prefix}{getattr(getattr(route, 'include_context', None), 'prefix', '')}"
            for child in original_router.routes:
                visit(child, child_prefix)

    for route in app.routes:
        visit(route)
    assert len(routes) > 100, f"found only {len(routes)} upload routes; the route walk is broken"
    return routes


def test_the_files_list_names_exactly_the_routes_that_read_a_files_list():
    listed = _listed_files_routes()
    assert len(listed) == len(set(listed)), f"duplicate entries in FILES_FIELD_ROUTES: {listed}"
    reading = {path for path, fields in _upload_routes().items() if fields.get("files") == "list"}

    missing = sorted(reading - set(listed))
    assert not missing, (
        "These routes read `files: list[UploadFile]` but frontend/src/lib/upload-fields.ts "
        "does not list them, so the upload helpers would send `file` and get a 422: "
        + ", ".join(missing)
    )
    stale = sorted(set(listed) - reading)
    assert not stale, (
        "frontend/src/lib/upload-fields.ts lists routes that do not read `files: list[UploadFile]`, "
        "so the upload helpers would send them the wrong field: " + ", ".join(stale)
    )


def test_every_other_upload_route_reads_one_file_field():
    listed = set(_listed_files_routes())
    wrong = [
        f"{path} reads {fields}"
        for path, fields in sorted(_upload_routes().items())
        if path not in listed and path not in OTHER_UPLOAD_FIELDS and fields.get("file") != "one"
    ]
    assert not wrong, (
        "Upload routes must read `file: UploadFile` or `files: list[UploadFile]` (listed in "
        "frontend/src/lib/upload-fields.ts), or be named in OTHER_UPLOAD_FIELDS with a page that "
        "builds its own form: " + "; ".join(wrong)
    )


def test_routes_with_other_upload_fields_still_read_them():
    routes = _upload_routes()
    drifted = {path: routes.get(path) for path, names in OTHER_UPLOAD_FIELDS.items() if set(routes.get(path, {})) != names}
    assert not drifted, f"OTHER_UPLOAD_FIELDS no longer matches these routes' upload fields: {drifted}"
