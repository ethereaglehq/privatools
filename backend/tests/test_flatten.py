"""Flatten turns annotations and form fields into page content, by `scope`.

Before this, the service set a flag constant PyMuPDF does not have
(`fitz.ANNOT_IS_PRINT`), so every PDF with an annotation returned 500. The
`apply_redactions()` that followed only applies redaction marks, so it could
not have baked anything in; form fields were only set read-only and stayed
interactive, and the route accepted `scope` and ignored it.
"""

from __future__ import annotations

import os

import fitz  # PyMuPDF
import pytest

RED = (255, 0, 0)
WHITE = (255, 255, 255)
SQUARE = fitz.Rect(72, 220, 200, 300)
CHECKBOX = fitz.Rect(72, 110, 90, 128)


def _annotated_pdf() -> bytes:
    """A highlight, a sticky note, a typed comment, a red square and a link."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Highlighted words", fontsize=12)
    page.add_highlight_annot(page.search_for("Highlighted words")[0])
    page.add_text_annot((400, 90), "A sticky note")
    page.add_freetext_annot(fitz.Rect(72, 150, 300, 190), "Typed comment", fontsize=12)
    square = page.add_rect_annot(SQUARE)
    square.set_colors(stroke=(1, 0, 0))
    square.set_border(width=4)
    square.update()
    page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 320, 200, 340), "uri": "https://example.com/"})
    return doc.tobytes()


def _filled_form_pdf(comment: bool = False) -> bytes:
    """A text field, a ticked checkbox and a dropdown, all filled in."""
    doc = fitz.open()
    page = doc.new_page()
    for name, kind, rect, value, extra in (
        ("fullname", fitz.PDF_WIDGET_TYPE_TEXT, fitz.Rect(72, 72, 300, 96), "Ada Lovelace", {}),
        ("agree", fitz.PDF_WIDGET_TYPE_CHECKBOX, CHECKBOX, True, {}),
        ("country", fitz.PDF_WIDGET_TYPE_COMBOBOX, fitz.Rect(72, 140, 250, 162), "Japan",
         {"choice_values": ["France", "Japan"]}),
    ):
        widget = fitz.Widget()
        widget.field_name, widget.field_type, widget.rect, widget.field_value = name, kind, rect, value
        widget.text_fontsize = 12
        for key, val in extra.items():
            setattr(widget, key, val)
        page.add_widget(widget)
    if comment:
        page.add_highlight_annot(fitz.Rect(320, 72, 500, 96))
    return doc.tobytes()


def _flatten(client, pdf: bytes, **data) -> fitz.Document:
    resp = client.post("/api/flatten", files={"file": ("in.pdf", pdf, "application/pdf")}, data=data)
    assert resp.status_code == 200, resp.text
    return fitz.open(stream=resp.content, filetype="pdf")


def _annotations(page) -> list[str]:
    return [annot.type[1] for annot in page.annots()]


def _ink(page, rect: fitz.Rect) -> int:
    pix = page.get_pixmap(dpi=144, clip=rect)
    return sum(1 for i in range(0, len(pix.samples), pix.n) if pix.samples[i] < 110)


def test_annotations_are_drawn_into_the_page(client):
    page = _flatten(client, _annotated_pdf())[0]

    assert _annotations(page) == []
    pix = page.get_pixmap(dpi=72)
    assert pix.pixel(int(SQUARE.x0), 260) == RED, "the square is no longer drawn"
    # With no annotation left, the comment's words can only be page content.
    assert "Typed comment" in page.get_text()


def test_links_stay_clickable(client):
    page = _flatten(client, _annotated_pdf())[0]
    assert [link["uri"] for link in page.get_links()] == ["https://example.com/"]


def test_filled_fields_become_page_content(client):
    doc = _flatten(client, _filled_form_pdf())
    page = doc[0]

    assert list(page.widgets()) == []
    assert not doc.is_form_pdf
    assert doc.xref_get_key(doc.pdf_catalog(), "AcroForm") == ("null", "null")
    text = page.get_text()
    assert "Ada Lovelace" in text
    assert "Japan" in text
    assert _ink(page, CHECKBOX) > 20, "the tick is no longer drawn"


def test_annotations_scope_leaves_form_fields_interactive(client):
    doc = _flatten(client, _filled_form_pdf(comment=True), scope="annotations")
    page = doc[0]

    assert _annotations(page) == []
    widgets = list(page.widgets())
    assert [w.field_name for w in widgets] == ["fullname", "agree", "country"]
    assert not any(w.field_flags & 1 for w in widgets), "fields were made read-only"


def test_forms_scope_leaves_annotations_editable(client):
    doc = _flatten(client, _filled_form_pdf(comment=True), scope="forms")
    page = doc[0]

    assert _annotations(page) == ["Highlight"]
    assert list(page.widgets()) == []
    assert not doc.is_form_pdf
    assert "Ada Lovelace" in page.get_text()


def test_annotation_on_a_hidden_layer_stays_hidden(client):
    doc = fitz.open()
    page = doc.new_page()
    layer = doc.add_ocg("Reviewer notes", on=False)
    square = page.add_rect_annot(SQUARE)
    square.set_colors(stroke=(1, 0, 0))
    square.set_border(width=4)
    square.set_oc(layer)
    square.update()

    out = _flatten(client, doc.tobytes())
    assert _annotations(out[0]) == []
    assert out[0].get_pixmap(dpi=72).pixel(int(SQUARE.x0), 260) == WHITE, "a hidden layer's markup became visible"

    # It was baked into that layer rather than dropped: switch the layer on.
    out.xref_set_key(out.pdf_catalog(), "OCProperties/D/OFF", "[]")
    shown = fitz.open(stream=out.tobytes(), filetype="pdf")
    assert shown[0].get_pixmap(dpi=72).pixel(int(SQUARE.x0), 260) == RED


def test_pipeline_step_flattens_both(tmp_path):
    from backend.app.routes.developer import _run_step

    source = tmp_path / "in.pdf"
    source.write_bytes(_filled_form_pdf(comment=True))
    output = _run_step("flatten-pdf", str(source))
    try:
        doc = fitz.open(output)
        assert _annotations(doc[0]) == []
        assert list(doc[0].widgets()) == []
        doc.close()
    finally:
        os.remove(output)


def test_unknown_scope_is_rejected(client):
    resp = client.post(
        "/api/flatten",
        files={"file": ("in.pdf", _annotated_pdf(), "application/pdf")},
        data={"scope": "layers"},
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("scope", ["all", "annotations", "forms"])
def test_every_scope_accepts_a_pdf_with_annotations(client, scope):
    """Any annotation used to make every scope fail with 500."""
    _flatten(client, _annotated_pdf(), scope=scope)
