"""Every tool's page and its route count pages the same way.

Redact PDF's page called the first page 1 and sent that number; its route read
the number as an index counted from 0. Redacting page 1 of a three-page PDF
blacked out page 2 and left page 1 readable, and every one-page PDF was
refused. Each side had tests, but only against itself.

frontend/src/test/page-contract.json records, for every tool whose page sends
a page number, the value the page sends to mean the first and the second page.
src/test/page-contract.test.tsx holds the pages to it. These tests send the
same values through the real routes with a two-page PDF and check that the
change lands on that page and leaves the other page as it was.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF
import pytest
from fastapi.routing import APIRoute
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CONTRACT = json.loads((ROOT / "frontend" / "src" / "test" / "page-contract.json").read_text(encoding="utf-8"))["tools"]

# Form fields that carry page numbers. A route with one of these must have a
# contract, or be listed below as one no page of the site calls with it.
PAGE_FIELDS = {"page", "pages", "page_order", "page_ranges"}
API_ONLY = {
    "/bates-numbering": "Bates Numbering's page numbers every page; only API callers choose pages.",
    "/extract-tables": "Extract Tables' page reads every page; only API callers choose pages.",
    "/qr-code": "QR Code Generator's page makes an image; only API callers place a code on a PDF page.",
}

MARKERS = ("FIRST PAGE 1111", "SECOND PAGE 2222")
# A region around the marker line, in points from the page's top-left corner.
REGION = {"x": 60, "y": 80, "width": 320, "height": 34}


def _pdf(pages: int) -> bytes:
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 100), MARKERS[index], fontsize=14)
        page.insert_text((72, 400), f"Public text on page {index + 1}", fontsize=12)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


TWO_PAGES = _pdf(2)
ONE_PAGE = _pdf(1)


def _png_data_url() -> str:
    image = Image.new("RGB", (60, 20), (20, 40, 160))
    out = io.BytesIO()
    image.save(out, "PNG")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


SIGNATURE = _png_data_url()

# What each page puts in a request besides its page number: one item per tool
# for the routes that take a JSON list, the other form fields for the rest.
ITEMS = {
    "redact-pdf": dict(REGION),
    "whiteout-pdf": dict(REGION),
    "annotate-pdf": {"type": "highlight", **REGION, "color": "#ffe24a", "text": ""},
    "add-shapes": {"type": "rectangle", **REGION, "x2": 380, "y2": 114, "color": "#0E8A56", "fill": "#0E8A56", "stroke_width": 2},
    "edit-pdf": {"type": "text", "x": 72, "y": 600, "text": "EDITED", "font_size": 14, "color": "#000000", "font_family": "Helvetica"},
    "form-creator": {"name": "contract_field", "type": "text", **REGION, "required": False, "value": "", "multiline": False},
    "bookmarks": {"title": "Contract"},
}
FIELDS = {
    "redact-pdf": {"color": "#000000"},
    "esign-pdf": {"signature": SIGNATURE, "x": "72", "y": "80", "width": "120", "height": "40"},
    # Sign PDF measures from the bottom-left corner.
    "sign-pdf": {"signature_data": SIGNATURE, "x": "72", "y": "600", "width": "120", "height": "40"},
    "split-pdf": {"mode": "pages"},
    "rotate-pdf": {"angle": "90"},
    "stamp-pdf": {"stamp_type": "confidential", "opacity": "0.5", "position": "center"},
}
IN_PLACE = {
    "redact-pdf", "whiteout-pdf", "annotate-pdf", "add-shapes", "edit-pdf", "form-creator",
    "esign-pdf", "sign-pdf", "rotate-pdf", "stamp-pdf",
}


def _post(client, slug: str, value, pdf: bytes):
    spec = CONTRACT[slug]
    data = dict(FIELDS.get(slug, {}))
    if "key" in spec:
        data[spec["field"]] = json.dumps([{**ITEMS[slug], spec["key"]: value}])
    elif isinstance(value, list):
        data[spec["field"]] = json.dumps(value)
    else:
        data[spec["field"]] = str(value)
    if slug == "merge-pdf":
        # One range per file: the same page of two copies.
        data[spec["field"]] = json.dumps([value, value])
        files = [("files", ("a.pdf", pdf, "application/pdf")), ("files", ("b.pdf", pdf, "application/pdf"))]
    else:
        files = {"file": ("contract.pdf", pdf, "application/pdf")}
    res = client.post("/api" + spec["endpoint"], files=files, data=data)
    assert res.status_code == 200, f"{slug} {spec['field']}={value!r}: {res.status_code} {res.text[:300]}"
    return res.content


def _fingerprints(pdf: bytes) -> list[tuple]:
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return [
            (
                page.rotation,
                page.get_text(),
                len(list(page.annots())),
                len(list(page.widgets())),
                len(page.get_images()),
                hashlib.sha256(page.get_pixmap(dpi=36).samples).hexdigest(),
            )
            for page in doc
        ]


def _changed_pages(before: bytes, after: bytes) -> set[int]:
    old, new = _fingerprints(before), _fingerprints(after)
    assert len(new) == len(old), f"the page count changed from {len(old)} to {len(new)}"
    return {number for number, (a, b) in enumerate(zip(old, new), start=1) if a != b}


def _source_pages(pdf: bytes) -> list[int]:
    """Which page of the two-page PDF each page of the result is."""
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        texts = [page.get_text() for page in doc]
    return [next(n for n, marker in enumerate(MARKERS, start=1) if marker in text) for text in texts]


def _bookmark_targets(pdf: bytes) -> list[int]:
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return [entry[2] for entry in doc.get_toc()]


def _landed_on(slug: str, result: bytes, pdf: bytes):
    """Where the change landed, in the terms the page's user thinks in."""
    if slug in IN_PLACE:
        return _changed_pages(pdf, result)
    if slug == "bookmarks":
        return _bookmark_targets(result)
    return _source_pages(result)


def _expected(slug: str, page: int):
    other = 3 - page
    return {
        "bookmarks": [page],
        "delete-pages": [other],
        "merge-pdf": [page, page],
    }.get(slug, {page} if slug in IN_PLACE else [page])


@pytest.mark.parametrize("which,page", [("first", 1), ("second", 2)])
@pytest.mark.parametrize("slug", sorted(CONTRACT))
def test_the_page_the_user_chose_is_the_page_that_changes(client, slug, which, page):
    result = _post(client, slug, CONTRACT[slug][which], TWO_PAGES)
    assert _landed_on(slug, result, TWO_PAGES) == _expected(slug, page), (
        f"{slug}: the page sends {CONTRACT[slug][which]!r} for page {page}, "
        f"and the route changed something else"
    )


@pytest.mark.parametrize("slug", sorted(IN_PLACE))
def test_the_first_page_of_a_one_page_pdf_works(client, slug):
    result = _post(client, slug, CONTRACT[slug]["first"], ONE_PAGE)
    assert _changed_pages(ONE_PAGE, result) == {1}


@pytest.mark.parametrize("page", [1, 2])
def test_redaction_removes_the_text_on_the_chosen_page_only(client, page):
    result = _post(client, "redact-pdf", CONTRACT["redact-pdf"]["first" if page == 1 else "second"], TWO_PAGES)
    with fitz.open(stream=result, filetype="pdf") as doc:
        texts = [p.get_text() for p in doc]
    assert MARKERS[page - 1] not in texts[page - 1], "the text under the box is still in the file"
    assert MARKERS[2 - page] in texts[2 - page], "the other page lost its text"
    assert f"Public text on page {page}" in texts[page - 1], "text outside the box was removed"


def _page_field_routes() -> dict[str, set[str]]:
    """Every /api route whose form has a page-number field, without /api."""
    from backend.app.main import app

    found: dict[str, set[str]] = {}

    def visit(route, prefix: str = "") -> None:
        if isinstance(route, APIRoute):
            path = f"{prefix}{route.path}"
            names = {param.alias for param in route.dependant.body_params} & PAGE_FIELDS
            if names and path.startswith("/api/") and not path.startswith("/api/v1/"):
                found[path[len("/api"):]] = names
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            child_prefix = f"{prefix}{getattr(getattr(route, 'include_context', None), 'prefix', '')}"
            for child in original_router.routes:
                visit(child, child_prefix)

    for route in app.routes:
        visit(route)
    return found


def test_every_route_that_takes_page_numbers_has_a_contract():
    routes = _page_field_routes()
    assert len(routes) >= 10, f"found only {sorted(routes)}; the route walk is broken"
    covered = {spec["endpoint"] for spec in CONTRACT.values()}
    missing = sorted(set(routes) - covered - set(API_ONLY))
    assert not missing, (
        "These routes take page numbers but frontend/src/test/page-contract.json has no entry "
        "for them, so nothing checks that their page and the route count pages alike: "
        + ", ".join(f"{path} ({', '.join(sorted(routes[path]))})" for path in missing)
    )
    stale = sorted(set(API_ONLY) - set(routes))
    assert not stale, f"API_ONLY names routes that no longer take page numbers: {stale}"
