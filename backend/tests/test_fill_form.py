"""Fill Form: every value it fills shows on the page, radio groups included.

#204 found that /NeedAppearances was never set: `pikepdf.Boolean` did not exist
in pikepdf 8.12 and the AttributeError was swallowed, so a field whose old
appearance had been deleted could look empty in a viewer that does not redraw
it. pikepdf 10.12 (#182) has `Boolean`; the first test pins that.

What still failed is fields whose widgets are separate from the field, which is
how every radio group is built: the value went onto the field, never onto its
buttons, so no option showed as selected, and the options were read from the
field instead of its buttons, so the page offered a text box instead of a list.
A checkbox with a separate widget stayed unticked for the same reason.

The form is built with ReportLab, as a different producer from the PyMuPDF the
tools themselves use: a radio group there is a parent field with one kid per
button, the structure authoring tools generally write.
"""

from __future__ import annotations

import io
import json

import fitz  # PyMuPDF
import pikepdf
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PAGE_HEIGHT = A4[1]
# ReportLab places fields by their bottom-left corner; these are the same
# boxes in PyMuPDF's top-left coordinates.
FULLNAME = fitz.Rect(130, PAGE_HEIGHT - 790, 330, PAGE_HEIGHT - 770)
AGREE = fitz.Rect(130, PAGE_HEIGHT - 751, 146, PAGE_HEIGHT - 735)
COLOURS = {name: fitz.Rect(x, PAGE_HEIGHT - 711, x + 16, PAGE_HEIGHT - 695)
           for name, x in (("Red", 130), ("Green", 210), ("Blue", 290))}
VALUES = {"fullname": "Ada Lovelace", "agree": "Yes", "colour": "Green", "country": "Japan"}


def _form(split_widgets: tuple[str, ...] = ()) -> bytes:
    """Text, checkbox, a three-button radio group and a dropdown, all empty.

    Fields named in `split_widgets` are rewritten from one merged field/widget
    dictionary into a field with a separate kid widget, as pdf-lib writes every
    field and Acrobat writes a field that appears on several pages.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    form = c.acroForm
    form.textfield(name="fullname", x=130, y=770, width=200, height=20, borderStyle="inset", forceBorder=True)
    form.checkbox(name="agree", x=130, y=735, size=16, checked=False, buttonStyle="check")
    for name, rect in COLOURS.items():
        form.radio(name="colour", value=name, x=rect.x0, y=695, size=16, selected=False, buttonStyle="circle")
    form.choice(name="country", x=130, y=652, width=150, height=20, options=["France", "Japan", "Peru"], value="France")
    c.showPage()
    c.save()
    if not split_widgets:
        return buf.getvalue()

    pdf = pikepdf.open(io.BytesIO(buf.getvalue()))
    fields = pdf.Root.AcroForm.Fields
    for i, widget in enumerate(list(fields)):
        if str(widget.get("/T", "")) not in split_widgets:
            continue
        field = pdf.make_indirect(pikepdf.Dictionary())
        for key in ("/FT", "/T", "/V", "/Ff", "/TU"):
            if key in widget:
                field[key] = widget[key]
                del widget[key]
        field.Kids = pikepdf.Array([widget])
        widget.Parent = field
        fields[i] = field
    out = io.BytesIO()
    pdf.save(out)
    return out.getvalue()


def _post(client, route: str, pdf: bytes, data: dict | None = None):
    return client.post(
        f"/api/{route}",
        files={"file": ("form.pdf", pdf, "application/pdf")},
        data=data or {},
    )


def _fill(client, pdf: bytes, values: dict) -> bytes:
    resp = _post(client, "fill-form", pdf, {"field_values": json.dumps(values)})
    assert resp.status_code == 200, resp.text
    return resp.content


def _ink(page, rect: fitz.Rect) -> int:
    """Dark pixels drawn inside `rect`, rendered by PyMuPDF."""
    pix = page.get_pixmap(dpi=144, clip=rect)
    return sum(1 for i in range(0, len(pix.samples), pix.n) if pix.samples[i] < 110)


def _field(pdf: pikepdf.Pdf, name: str):
    (field,) = [f for f in pdf.Root.AcroForm.Fields if str(f.get("/T")) == name]
    return field


def test_filled_form_asks_viewers_to_redraw_its_fields(client):
    pdf = pikepdf.open(io.BytesIO(_fill(client, _form(), VALUES)))
    assert pdf.Root.AcroForm.get("/NeedAppearances") is True


def test_detect_fields_offers_a_radio_groups_options(client):
    resp = _post(client, "fill-form/fields", _form())
    assert resp.status_code == 200, resp.text
    fields = {f["name"]: f for f in resp.json()["fields"]}
    assert fields["colour"]["type"] == "radio"
    assert fields["colour"]["options"] == ["Red", "Green", "Blue"]


def test_radio_value_goes_on_the_chosen_button(client):
    pdf = pikepdf.open(io.BytesIO(_fill(client, _form(), VALUES)))
    colour = _field(pdf, "colour")
    assert str(colour.V) == "/Green"
    assert [str(kid.AS) for kid in colour.Kids] == ["/Off", "/Green", "/Off"]


def test_every_filled_value_shows_on_the_page(client):
    empty = fitz.open(stream=_form(), filetype="pdf")[0]
    page = fitz.open(stream=_fill(client, _form(), VALUES), filetype="pdf")[0]

    text = page.get_text()
    assert "Ada Lovelace" in text
    assert "Japan" in text
    assert _ink(page, AGREE) > _ink(empty, AGREE) + 40, "checkbox not drawn ticked"
    green = _ink(page, COLOURS["Green"])
    assert green > _ink(page, COLOURS["Red"]) + 40, "Green not drawn selected"
    assert green > _ink(page, COLOURS["Blue"]) + 40, "Green not drawn selected"


def test_checkbox_with_a_separate_widget_is_ticked(client):
    form = _form(split_widgets=("agree",))
    fields = {f["name"]: f for f in _post(client, "fill-form/fields", form).json()["fields"]}
    assert fields["agree"]["options"] == ["Yes"]

    pdf_bytes = _fill(client, form, {"agree": "Yes"})
    pdf = pikepdf.open(io.BytesIO(pdf_bytes))
    (widget,) = _field(pdf, "agree").Kids
    assert str(widget.AS) == "/Yes"
    empty = fitz.open(stream=form, filetype="pdf")[0]
    page = fitz.open(stream=pdf_bytes, filetype="pdf")[0]
    assert _ink(page, AGREE) > _ink(empty, AGREE) + 40


@pytest.mark.parametrize("value", ["Purple", "green"])
def test_value_that_is_not_one_of_the_radio_options_is_rejected(client, value):
    resp = _post(client, "fill-form", _form(), {"field_values": json.dumps({"colour": value})})
    assert resp.status_code == 400


def test_value_a_radio_group_already_had_is_left_alone(client):
    """The page sends every field back, touched or not. A group whose stored
    value matches none of its buttons must not make the whole form unfillable."""
    pdf = pikepdf.open(io.BytesIO(_form()))
    colour = _field(pdf, "colour")
    colour.V = pikepdf.Name("/Teal")
    colour.Kids[2].AS = pikepdf.Name("/Blue")
    out = io.BytesIO()
    pdf.save(out)

    filled = pikepdf.open(io.BytesIO(_fill(client, out.getvalue(), {"fullname": "Ada Lovelace", "colour": "Teal"})))
    colour = _field(filled, "colour")
    assert str(colour.V) == "/Teal"
    assert [str(kid.AS) for kid in colour.Kids] == ["/Off", "/Off", "/Blue"]


def test_clearing_a_radio_group_selects_nothing(client):
    chosen = _fill(client, _form(), {"colour": "Green"})
    pdf = pikepdf.open(io.BytesIO(_fill(client, chosen, {"colour": ""})))
    colour = _field(pdf, "colour")
    assert str(colour.V) == "/Off"
    assert [str(kid.AS) for kid in colour.Kids] == ["/Off", "/Off", "/Off"]


def test_filled_form_flattens_into_page_content(client):
    resp = _post(client, "flatten", _fill(client, _form(), VALUES))
    assert resp.status_code == 200, resp.text
    doc = fitz.open(stream=resp.content, filetype="pdf")
    page = doc[0]

    assert list(page.widgets()) == []
    assert not doc.is_form_pdf
    text = page.get_text()
    assert "Ada Lovelace" in text
    assert "Japan" in text
    assert _ink(page, COLOURS["Green"]) > _ink(page, COLOURS["Red"]) + 40
