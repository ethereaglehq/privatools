"""Redaction with statutory exemption codes, and the withholding log.

A plain black box answers "hide this". A FOIA or Privacy Act production has to
answer "under what authority" — the released page carries the citation, and the
producing party keeps an accounting of what was withheld under which exemption.
Adobe is the only competitor that does this; everyone else stops at the box.

There were no redaction tests at all before this file, so the basics are
covered here too: content under a rect must actually be gone, not covered.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.services.redact_service import (
    _readable_text_color,
    redact_pdf,
)


def _pdf(path: Path, pages: int = 1, secret: str = "CLASSIFIED SECRET") -> str:
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((72, 100), secret, fontsize=12)
        page.insert_text((72, 300), "Public information", fontsize=12)
    doc.save(str(path))
    doc.close()
    return str(path)


def _text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


# The rect covering the secret line in _pdf().
_SECRET_RECT = {"page": 0, "x0": 60, "y0": 85, "x1": 300, "y1": 110}


# ── the basics, which nothing covered before ────────────────────────────────

def test_redaction_actually_removes_the_content(tmp_path):
    out, _ = redact_pdf(_pdf(tmp_path / "a.pdf"), [dict(_SECRET_RECT)])
    text = _text(out)
    assert "CLASSIFIED SECRET" not in text
    assert "Public information" in text


def test_redaction_leaves_other_pages_alone(tmp_path):
    out, _ = redact_pdf(_pdf(tmp_path / "a.pdf", pages=3), [dict(_SECRET_RECT)])
    doc = fitz.open(out)
    try:
        assert "CLASSIFIED SECRET" not in doc[0].get_text()
        assert "CLASSIFIED SECRET" in doc[1].get_text()
        assert "CLASSIFIED SECRET" in doc[2].get_text()
    finally:
        doc.close()


def test_out_of_range_pages_are_skipped_not_fatal(tmp_path):
    out, report = redact_pdf(
        _pdf(tmp_path / "a.pdf", pages=1),
        [dict(_SECRET_RECT), {"page": 99, "x0": 0, "y0": 0, "x1": 10, "y1": 10}],
    )
    assert report["totalRedactions"] == 1
    assert Path(out).exists()


# ── exemption codes ─────────────────────────────────────────────────────────

def test_the_exemption_code_is_stamped_onto_the_page(tmp_path):
    out, _ = redact_pdf(
        _pdf(tmp_path / "a.pdf"),
        [{**_SECRET_RECT, "code": "(b)(6)"}],
    )
    text = _text(out)
    assert "(b)(6)" in text, "exemption code was not written into the redacted area"
    assert "CLASSIFIED SECRET" not in text


def test_the_code_survives_as_flattened_content_not_an_annotation(tmp_path):
    """A citation someone can peel off is not a citation."""
    out, _ = redact_pdf(_pdf(tmp_path / "a.pdf"), [{**_SECRET_RECT, "code": "(b)(7)(C)"}])
    doc = fitz.open(out)
    try:
        page = doc[0]
        assert "(b)(7)(C)" in page.get_text()
        assert len(list(page.annots() or [])) == 0, "left a live annotation behind"
    finally:
        doc.close()


def test_over_long_codes_are_truncated_rather_than_overflowing(tmp_path):
    out, report = redact_pdf(
        _pdf(tmp_path / "a.pdf"),
        [{**_SECRET_RECT, "code": "X" * 100}],
    )
    assert Path(out).exists()
    code = next(iter(report["codes"]))
    assert len(code) <= 32


# ── the withholding log ─────────────────────────────────────────────────────

def test_report_counts_redactions_per_code(tmp_path):
    _, report = redact_pdf(
        _pdf(tmp_path / "a.pdf", pages=2),
        [
            {"page": 0, "x0": 60, "y0": 85, "x1": 200, "y1": 110, "code": "(b)(6)"},
            {"page": 0, "x0": 60, "y0": 290, "x1": 200, "y1": 310, "code": "(b)(6)"},
            {"page": 1, "x0": 60, "y0": 85, "x1": 200, "y1": 110, "code": "(b)(7)(C)"},
        ],
    )
    assert report["totalRedactions"] == 3
    assert report["codes"] == {"(b)(6)": 2, "(b)(7)(C)": 1}
    assert report["uncoded"] == 0


def test_report_breaks_down_by_page(tmp_path):
    _, report = redact_pdf(
        _pdf(tmp_path / "a.pdf", pages=2),
        [
            {"page": 0, "x0": 60, "y0": 85, "x1": 200, "y1": 110, "code": "(b)(6)"},
            {"page": 1, "x0": 60, "y0": 85, "x1": 200, "y1": 110, "code": "(b)(6)"},
            {"page": 1, "x0": 60, "y0": 290, "x1": 200, "y1": 310, "code": "(b)(5)"},
        ],
    )
    pages = {row["page"]: row for row in report["pages"]}
    # Reported 1-indexed, the way a person cites a page.
    assert pages[1]["count"] == 1
    assert pages[2]["count"] == 2
    assert pages[2]["codes"] == {"(b)(6)": 1, "(b)(5)": 1}


def test_uncoded_redactions_are_counted_separately(tmp_path):
    """Mixing coded and uncoded is a real state — the log has to show it."""
    _, report = redact_pdf(
        _pdf(tmp_path / "a.pdf"),
        [
            {**_SECRET_RECT, "code": "(b)(6)"},
            {"page": 0, "x0": 60, "y0": 290, "x1": 200, "y1": 310},
        ],
    )
    assert report["totalRedactions"] == 2
    assert report["uncoded"] == 1
    assert report["codes"] == {"(b)(6)": 1}


def test_report_is_json_serialisable(tmp_path):
    """It travels as a response header, so it has to survive json.dumps."""
    _, report = redact_pdf(_pdf(tmp_path / "a.pdf"), [{**_SECRET_RECT, "code": "(b)(6)"}])
    assert json.loads(json.dumps(report)) == report


# ── legibility ──────────────────────────────────────────────────────────────

def test_code_colour_contrasts_with_the_box():
    """An unreadable citation is the same as no citation."""
    assert _readable_text_color((0.0, 0.0, 0.0)) == (1.0, 1.0, 1.0)   # white on black
    assert _readable_text_color((1.0, 1.0, 1.0)) == (0.0, 0.0, 0.0)   # black on white
    # Green is perceptually bright, so it takes dark text despite being a colour.
    assert _readable_text_color((0.0, 1.0, 0.0)) == (0.0, 0.0, 0.0)
    assert _readable_text_color((0.0, 0.0, 1.0)) == (1.0, 1.0, 1.0)   # dark blue


def test_a_white_box_still_stamps_a_readable_code(tmp_path):
    out, _ = redact_pdf(
        _pdf(tmp_path / "a.pdf"), [{**_SECRET_RECT, "code": "(b)(5)"}], color="#FFFFFF"
    )
    assert "(b)(5)" in _text(out)


# ── HTTP ────────────────────────────────────────────────────────────────────

def test_endpoint_returns_the_withholding_log(client, tmp_path):
    data = Path(_pdf(tmp_path / "a.pdf")).read_bytes()
    res = client.post(
        "/api/redact",
        files={"file": ("a.pdf", data, "application/pdf")},
        data={"redactions": json.dumps([{**_SECRET_RECT, "code": "(b)(6)"}])},
    )
    assert res.status_code == 200
    report = json.loads(res.headers["X-Redaction-Report"])
    assert report["codes"] == {"(b)(6)": 1}
    assert report["totalRedactions"] == 1


def test_endpoint_rejects_a_non_string_code(client, tmp_path):
    data = Path(_pdf(tmp_path / "a.pdf")).read_bytes()
    res = client.post(
        "/api/redact",
        files={"file": ("a.pdf", data, "application/pdf")},
        data={"redactions": json.dumps([{**_SECRET_RECT, "code": 42}])},
    )
    assert res.status_code == 400


def test_endpoint_rejects_an_over_long_code(client, tmp_path):
    data = Path(_pdf(tmp_path / "a.pdf")).read_bytes()
    res = client.post(
        "/api/redact",
        files={"file": ("a.pdf", data, "application/pdf")},
        data={"redactions": json.dumps([{**_SECRET_RECT, "code": "X" * 100}])},
    )
    assert res.status_code == 400


# ── what the guide says redaction removes and keeps ─────────────────────────
# backend/app/tool_content.py's Redact PDF answers describe exactly this. If a
# PyMuPDF upgrade changes any of it, change the answers with the test.

def _guide_pdf(path: Path) -> str:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "ABCDEFGH", fontsize=20)
    page.insert_text((72, 400), "Outside the box", fontsize=12)
    page.draw_rect(fitz.Rect(90, 150, 110, 160), color=(1, 0, 0), fill=(1, 0, 0))  # wholly inside
    page.draw_line((80, 180), (500, 180), color=(0, 0, 1), width=1)  # reaches past
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40), False)
    pixmap.set_rect(pixmap.irect, (0, 128, 255))
    page.insert_image(fitz.Rect(80, 200, 240, 240), pixmap=pixmap)  # half inside
    page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 84, 200, 104), "uri": "https://example.com/"})
    page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 390, 200, 404), "uri": "https://example.org/"})
    page.add_text_annot((100, 120), "note under the box")
    page.add_highlight_annot(fitz.Rect(72, 84, 120, 104))
    widget = fitz.Widget()
    widget.field_name, widget.field_type, widget.field_value = "name", fitz.PDF_WIDGET_TYPE_TEXT, "FIELD VALUE"
    widget.rect = fitz.Rect(72, 130, 150, 145)
    page.add_widget(widget)
    doc.set_toc([[1, "Chapter", 1]])
    doc.save(str(path))
    doc.close()
    return str(path)


def test_what_the_guide_says_redaction_removes_and_keeps(tmp_path):
    src = _guide_pdf(tmp_path / "guide.pdf")
    with fitz.open(src) as doc:
        d_left = next(c["bbox"][0] for b in doc[0].get_text("rawdict")["blocks"] for l in b["lines"]
                      for s in l["spans"] for c in s["chars"] if c["c"] == "D")
        d_right = next(c["bbox"][2] for b in doc[0].get_text("rawdict")["blocks"] for l in b["lines"]
                       for s in l["spans"] for c in s["chars"] if c["c"] == "D")
    # The box ends a quarter of the way into "D", and covers half the image.
    right = d_left + (d_right - d_left) / 4
    out, _ = redact_pdf(src, [{"page": 0, "x0": 60, "y0": 80, "x1": right, "y1": 250}])
    with fitz.open(out) as doc:
        page = doc[0]
        words = [word[4] for word in page.get_text("words")]
        assert "EFGH" in words and "DEFGH" not in words, f"a part-covered character must go whole: {words}"
        assert not any("ABC" in word for word in words)
        assert "Outside" in words
        drawings = page.get_drawings()
        assert not any(d.get("fill") == (1.0, 0.0, 0.0) for d in drawings), "a shape wholly inside the box must be removed"
        assert any(d.get("color") == (0.0, 0.0, 1.0) and d["rect"].x1 == 500 for d in drawings), (
            "a line reaching past the box is kept (the guide says so)"
        )
        image = fitz.Pixmap(doc, page.get_images()[0][0])
        assert image.pixel(0, 0) != (0, 128, 255), "image pixels under the box must be blanked"
        assert image.pixel(image.width - 1, 0) == (0, 128, 255), "image pixels outside the box must stay"
        assert [link["uri"] for link in page.get_links()] == ["https://example.org/"], "a link over the box goes, one outside stays"
        assert sorted(a.type[1] for a in page.annots()) == ["Highlight", "Text"], "notes and highlights are kept (the guide says so)"
        assert [w.field_value for w in page.widgets()] == ["FIELD VALUE"], "form fields are kept (the guide says so)"
        assert doc.get_toc() == [[1, "Chapter", 1]]


# ── page numbers ────────────────────────────────────────────────────────────
# `page` counts from 0 (test_page_contract.py holds the website's page to it).
# It was once answered with "page 1 is out of range (PDF has 1 page)", which
# reads as a bug in the PDF rather than in the request.

def test_a_page_the_pdf_lacks_is_refused_with_how_pages_are_counted(client, tmp_path):
    data = Path(_pdf(tmp_path / "a.pdf", pages=3)).read_bytes()
    res = client.post(
        "/api/redact",
        files={"file": ("a.pdf", data, "application/pdf")},
        data={"redactions": json.dumps([{**_SECRET_RECT, "page": 3}])},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == (
        "Redaction #1 has page 3, which this PDF does not have: "
        "the page field counts from 0, so a PDF with 3 pages takes 0 to 2."
    )


def test_the_public_api_says_pages_count_from_zero():
    from backend.app.api_v1.schema import build_schema
    from backend.app.main import app

    schema = build_schema(app)
    body = schema["paths"]["/api/v1/redact"]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
    if "$ref" in body:
        body = schema["components"]["schemas"][body["$ref"].rsplit("/", 1)[1]]
    description = body["properties"]["redactions"]["description"]
    assert "counted from 0 (0 is the first page)" in description
