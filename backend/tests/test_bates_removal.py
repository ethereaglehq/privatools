"""Remove Bates Numbers on pages as the visitor sees them, and a true count.

The tool looks for stamps in the top and bottom inch of each page. It measured
the words where the file stores them against the height of the page as shown.
On a page stored with /Rotate 90 the top and bottom of the page as shown are
the stored left and right edges, so a stamp there was never found: a
four-page production turned 0, 90, 0 and 270 was reported as "3 stamps
removed" while PROD000002 stayed in the file. On /Rotate 90 and 270 the same
mix-up turned one "margin" into a band 252 points wide down a side of the
page, so Bates-shaped numbers well inside the page were removed.

Two more faults showed on every page. MuPDF removes every character whose box
touches a redaction, and a word's box runs from the font's ascender to its
descender, so a redaction the size of the stamp also took the characters of
the lines just above and below it at ordinary line spacing. And the count was
the number of stamps the tool tried to redact, not the number that left the
file: a stamp redaction cannot touch, such as one drawn by a stamp annotation,
was reported as removed.

These tests build pages turned and cut the way a visitor sees them, stamp
them as other tools and our own do, and check what leaves the file: in the
text layer as PyMuPDF and pypdf read it, in the page as rendered, and in the
counts the page shows (X-Bates-Removed, X-Bates-Remaining).
"""
from __future__ import annotations

import io
import math
from typing import NamedTuple

import fitz  # PyMuPDF
import numpy as np
import pikepdf
import pypdf
import pytest

LETTER = (0, 0, 612, 792)
CROP = (43, 61, 571, 737)  # a visible area inset by a different amount on each side
STAMP = "ABC000123"
BODY = "Body text of the page stays"


class Line(NamedTuple):
    """A line of text on a test page. (x, y) is where its baseline starts, in
    points from the top-left corner of the page as shown. `turn` turns it
    clockwise from reading upright as shown, in degrees; `hidden` writes it
    invisible (text render mode 3), as OCR writes a scan's text layer."""

    text: str
    x: float
    y: float
    size: float = 10
    turn: int = 0
    hidden: bool = False


# Pages turned and cut the ways a PDF can say it. `rotate` is /Rotate as the
# file writes it; `shown` is how pdf.js, which draws the site's preview, reads
# it where that differs (-90 as 270, 450 as 90, 80 as 0).
SPECS = {
    "rotate-0": {},
    "rotate-90": {"rotate": 90},
    "rotate-180": {"rotate": 180},
    "rotate-270": {"rotate": 270},
    "cropped": {"cropbox": CROP},
    "cropped-rotate-90": {"rotate": 90, "cropbox": CROP},
    "cropped-rotate-180": {"rotate": 180, "cropbox": CROP},
    "cropped-rotate-270": {"rotate": 270, "cropbox": CROP},
    "offset-rotate-90": {"rotate": 90, "mediabox": (100, 50, 712, 842)},
    "landscape-rotate-270": {"rotate": 270, "mediabox": (0, 0, 792, 612)},
    "rotate-minus-90": {"rotate": -90, "shown": 270},
    "cropped-rotate-450": {"rotate": 450, "shown": 90, "cropbox": CROP},
    "rotate-80": {"rotate": 80, "shown": 0},
    "inherited-rotate-90": {"rotate": 90, "inherited": True},
}


def _turn(spec: dict) -> int:
    return spec.get("shown", spec.get("rotate", 0))


def _visible(spec: dict) -> tuple[float, float, float, float]:
    media = spec.get("mediabox", LETTER)
    crop = spec.get("cropbox", media)
    return max(media[0], crop[0]), max(media[1], crop[1]), min(media[2], crop[2]), min(media[3], crop[3])


def _shown_size(spec: dict) -> tuple[float, float]:
    x0, y0, x1, y1 = _visible(spec)
    return (y1 - y0, x1 - x0) if _turn(spec) in (90, 270) else (x1 - x0, y1 - y0)


def _to_stored(spec: dict, x: float, y: float) -> tuple[float, float]:
    """A point on the page as shown, on the visible area as stored (points from
    its top-left corner, y down). Derived from the PDF specification: /Rotate
    turns the page clockwise for display."""
    x0, y0, x1, y1 = _visible(spec)
    w, h = x1 - x0, y1 - y0
    return {0: (x, y), 90: (y, h - x), 180: (w - x, h - y), 270: (w - y, x)}[_turn(spec)]


def _text_ops(spec: dict, line: Line) -> str:
    x0, _, _, top = _visible(spec)
    u, v = _to_stored(spec, line.x, line.y)
    # Turned against the page's /Rotate, text reads upright once the page is turned.
    angle = math.radians(_turn(spec) - line.turn)
    a, b = round(math.cos(angle), 6) + 0.0, round(math.sin(angle), 6) + 0.0
    mode = 3 if line.hidden else 0
    return f"BT /F1 {line.size:g} Tf {mode} Tr {a:g} {b:g} {-b:g} {a:g} {x0 + u:.3f} {top - v:.3f} Tm ({line.text}) Tj ET"


def _picture(spec: dict, dark: list[fitz.Rect]) -> dict:
    """A grey picture filling the visible area, like a scanned page, with the
    `dark` areas (on the page as shown) printed into it."""
    x0, y0, x1, y1 = _visible(spec)
    w, h = round(x1 - x0), round(y1 - y0)
    pixels = np.full((h, w), 200, dtype=np.uint8)
    for rect in dark:
        corners = [_to_stored(spec, x, y) for x, y in (rect.tl, rect.br)]
        us, vs = sorted(c[0] for c in corners), sorted(c[1] for c in corners)
        pixels[int(vs[0]):int(math.ceil(vs[1])), int(us[0]):int(math.ceil(us[1]))] = 40
    return {"Width": w, "Height": h, "data": pixels.tobytes()}


def _pdf(pages: list[tuple[dict, list[Line]]], *, dark: dict[int, list[fitz.Rect]] | None = None) -> bytes:
    pdf = pikepdf.new()
    font = pdf.make_indirect(pikepdf.Dictionary(
        Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica,
        Encoding=pikepdf.Name.WinAnsiEncoding,
    ))
    for index, (spec, lines) in enumerate(pages):
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page, MediaBox=pikepdf.Array(spec.get("mediabox", LETTER)),
            Resources=pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font)),
        )
        if "cropbox" in spec:
            page.CropBox = pikepdf.Array(spec["cropbox"])
        ops = []
        if dark is not None and index in dark:
            picture = _picture(spec, dark[index])
            image = pikepdf.Stream(pdf, picture["data"])
            image.Type, image.Subtype = pikepdf.Name.XObject, pikepdf.Name.Image
            image.Width, image.Height = picture["Width"], picture["Height"]
            image.ColorSpace, image.BitsPerComponent = pikepdf.Name.DeviceGray, 8
            page.Resources.XObject = pikepdf.Dictionary(Im0=image)
            x0, y0, x1, y1 = _visible(spec)
            ops.append(f"q {x1 - x0:g} 0 0 {y1 - y0:g} {x0:g} {y0:g} cm /Im0 Do Q")
        ops += [_text_ops(spec, line) for line in lines]
        pdf.pages.append(pikepdf.Page(page))
        pdf.pages[-1].Contents = pdf.make_stream("\n".join(ops).encode())
        if spec.get("rotate") and not spec.get("inherited"):
            pdf.pages[-1].obj.Rotate = spec["rotate"]
    for spec, _ in pages:
        if spec.get("inherited"):
            pdf.Root.Pages.Rotate = spec["rotate"]
    out = io.BytesIO()
    pdf.save(out)
    return out.getvalue()


def _width(text: str, size: float = 10) -> float:
    return fitz.get_text_length(text, "helv", size)


def _stamp(spec: dict, where: str, text: str = STAMP) -> Line:
    """A stamp 20 points in from two edges of the page as shown."""
    w, h = _shown_size(spec)
    if where == "bottom-right":
        return Line(text, w - 20 - _width(text), h - 20)
    assert where == "top-left"
    return Line(text, 20, 30)


def _ink_box(line: Line) -> fitz.Rect:
    """Where `line` shows, from its cap height to just below its baseline, with
    a point to spare (it must be upright as shown)."""
    assert line.turn == 0
    return fitz.Rect(line.x - 2, line.y - 0.8 * line.size - 2, line.x + _width(line.text, line.size) + 2, line.y + 0.3 * line.size + 2)


def _shown(pdf: bytes, index: int, turn: int) -> np.ndarray:
    """Page `index` as pdf.js shows it, in grey, a pixel per point. The page's
    /Rotate is written as `turn` first, since MuPDF reads 80 as 90."""
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        doc.pages[index].obj.Rotate = turn
        buf = io.BytesIO()
        doc.save(buf)
    with fitz.open(stream=buf.getvalue(), filetype="pdf") as doc:
        pix = doc[index].get_pixmap(dpi=72, colorspace=fitz.csGRAY, annots=True)
        return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()


def _region(pixels: np.ndarray, rect: fitz.Rect) -> np.ndarray:
    y0, y1 = max(0, int(rect.y0)), min(pixels.shape[0], int(math.ceil(rect.y1)))
    x0, x1 = max(0, int(rect.x0)), min(pixels.shape[1], int(math.ceil(rect.x1)))
    return pixels[y0:y1, x0:x1]


def _ink(pixels: np.ndarray, rect: fitz.Rect) -> int:
    return int((_region(pixels, rect) < 128).sum())


def _outside(pixels: np.ndarray, rect: fitz.Rect) -> np.ndarray:
    """The page with `rect` blanked, to compare everything else."""
    copy = pixels.copy()
    _region(copy, rect)[...] = 0
    return copy


def _edge_frame_ink(pixels: np.ndarray, width: float = 60) -> int:
    """Dark pixels within `width` points of any edge of the page as shown."""
    frame = np.zeros(pixels.shape, dtype=bool)
    n = int(width)
    frame[:n, :] = frame[-n:, :] = frame[:, :n] = frame[:, -n:] = True
    return int(((pixels < 128) & frame).sum())


def _texts(pdf: bytes) -> list[tuple[str, str]]:
    """Each page's text layer as PyMuPDF and as pypdf read it."""
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        mupdf = [page.get_text() for page in doc]
    return list(zip(mupdf, [page.extract_text() or "" for page in pypdf.PdfReader(io.BytesIO(pdf)).pages]))


def _post(client, endpoint: str, pdf: bytes, **fields):
    res = client.post(f"/api/{endpoint}", files={"file": ("p.pdf", pdf, "application/pdf")}, data=fields)
    assert res.status_code == 200, f"{endpoint}: {res.status_code} {res.text[:300]}"
    return res


def _remove(client, pdf: bytes, **fields):
    return _post(client, "bates-remove", pdf, **({"prefix": "ABC", "digits": "6"} | fields))


def _counts(res) -> tuple[str | None, str | None]:
    """What the page is told: stamps removed, and stamps found but still in the file."""
    return res.headers.get("X-Bates-Removed"), res.headers.get("X-Bates-Remaining")


def _mupdf_rotation(pdf: bytes, index: int = 0) -> int:
    """/Rotate as MuPDF reads it (80 as 90, where pdf.js reads 0)."""
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return doc[index].rotation


# ─── Stamps in the margins as shown ─────────────────────────────────────────

@pytest.mark.parametrize("where", ["bottom-right", "top-left"])
@pytest.mark.parametrize("name", sorted(SPECS))
def test_a_stamp_in_the_margin_as_shown_leaves_the_file(client, name, where):
    """A stamp written upright at the page's edge as shown, as a stamping tool
    that follows /Rotate (Acrobat's, say) writes it."""
    spec = SPECS[name]
    stamp = _stamp(spec, where)
    pdf = _pdf([(spec, [Line(BODY, 72, 120), stamp])])
    before = _shown(pdf, 0, _turn(spec))
    assert _ink(before, _ink_box(stamp)) > 50, f"{name}: the stamp does not show where it was written"

    res = _remove(client, pdf)
    ((mupdf, pypdf_text),) = _texts(res.content)
    assert STAMP not in mupdf and STAMP not in pypdf_text, f"{name} {where}: the stamp is still in the text layer"
    assert BODY in mupdf and BODY in pypdf_text, f"{name} {where}: the body text went too"
    after = _shown(res.content, 0, _turn(spec))
    assert _ink(after, _ink_box(stamp)) == 0, f"{name} {where}: the stamp still shows"
    assert np.array_equal(_outside(before, _ink_box(stamp)), _outside(after, _ink_box(stamp))), (
        f"{name} {where}: something outside the stamp changed"
    )
    assert _mupdf_rotation(res.content) == _turn(spec), f"{name}: /Rotate still reads differently in different viewers"
    assert _counts(res) == ("1", "0")


# Bates Numbering sizes its stamp for the page as stored, so on a landscape page
# turned a quarter the stamp is shrunk to fit the page as shown and lands 173
# points above the bottom edge, outside the margin, where removal rightly does
# not look. That is Bates Numbering's own fault.
STAMPED_HERE = sorted(set(SPECS) - {"landscape-rotate-270"})


@pytest.mark.parametrize("name", STAMPED_HERE)
def test_numbers_from_our_own_bates_tool_leave_turned_and_cut_pages(client, name):
    spec = SPECS[name]
    stamped = _post(client, "bates-numbering", _pdf([(spec, [Line(BODY, 72, 120)])]),
                    prefix="ABC", start_number="123", digits="6").content
    assert STAMP in _texts(stamped)[0][0], "the Bates tool did not stamp the page"
    before = _shown(stamped, 0, _turn(spec))
    assert _edge_frame_ink(before) > 50, f"{name}: the stamp does not show near an edge"

    res = _remove(client, stamped)
    ((mupdf, pypdf_text),) = _texts(res.content)
    assert STAMP not in mupdf and STAMP not in pypdf_text, f"{name}: the stamp is still in the text layer"
    assert BODY in mupdf and BODY in pypdf_text
    assert _edge_frame_ink(_shown(res.content, 0, _turn(spec))) == 0, f"{name}: the stamp still shows"
    assert _counts(res) == ("1", "0")


def test_a_production_turned_0_90_0_270_loses_every_number(client):
    """The review's file: four pages turned 0, 90, 0 and 270, stamped by our
    own Bates Numbering. PROD000002 stayed and the page said 3 were removed."""
    turns = (0, 90, 0, 270)
    pdf = _pdf([({"rotate": turn}, [Line(f"Page {n} body", 72, 300)]) for n, turn in enumerate(turns, start=1)])
    stamped = _post(client, "bates-numbering", pdf, prefix="PROD", digits="6").content
    res = _remove(client, stamped, prefix="PROD")
    for n, ((mupdf, pypdf_text), turn) in enumerate(zip(_texts(res.content), turns), start=1):
        assert f"PROD00000{n}" not in mupdf and f"PROD00000{n}" not in pypdf_text, f"page {n} (/Rotate {turn}) kept its number"
        assert f"Page {n} body" in mupdf
        assert _edge_frame_ink(_shown(res.content, n - 1, turn)) == 0, f"page {n} still shows its number"
    assert _counts(res) == ("4", "0")


@pytest.mark.parametrize("angle", [90, 180, 270])
def test_a_production_stamped_and_then_turned_here_loses_every_number(client, angle):
    """Numbers our Bates tool put on an upright portrait and an upright
    landscape page, which our Rotate tool then turned. The stamp stays upright
    on the page as stored, so a page turned a quarter shows it running up a
    side, where it sat in the bottom margin before the turn."""
    pdf = _pdf([({}, [Line(BODY, 100, 300)]), ({"mediabox": (0, 0, 792, 612)}, [Line(BODY, 100, 300)])])
    stamped = _post(client, "bates-numbering", pdf, prefix="PROD", digits="6").content
    turned = _post(client, "rotate", stamped, angle=str(angle)).content
    assert [_mupdf_rotation(turned, i) for i in (0, 1)] == [angle, angle]
    before = [_shown(turned, i, angle) for i in (0, 1)]
    assert all(_edge_frame_ink(pixels) > 50 for pixels in before)

    res = _remove(client, turned, prefix="PROD")
    for n, (mupdf, pypdf_text) in enumerate(_texts(res.content), start=1):
        assert f"PROD00000{n}" not in mupdf and f"PROD00000{n}" not in pypdf_text, f"page {n} turned {angle} kept its number"
        assert BODY in mupdf and BODY in pypdf_text
        assert _edge_frame_ink(_shown(res.content, n - 1, angle)) == 0, f"page {n} turned {angle} still shows its number"
    assert _counts(res) == ("2", "0")


# ─── Nothing else leaves the file ───────────────────────────────────────────

@pytest.mark.parametrize("name", ["rotate-0", "rotate-90", "rotate-180", "rotate-270", "cropped-rotate-90", "cropped-rotate-270"])
def test_only_the_stamp_goes_when_other_text_looks_like_one(client, name):
    """With no prefix or suffix, anything Bates-shaped in the top or bottom
    inch goes. A turned page must not widen that: before the fix the
    "bottom inch" of a page turned a quarter was a band 252 points wide down
    one side of the page as shown."""
    spec = SPECS[name]
    w, h = _shown_size(spec)
    keep = [
        Line("004512", 20, h / 2),  # the left margin as shown, halfway down
        Line("INV-778899", w - 20 - _width("INV-778899"), h / 2),  # the right margin
        Line("Claim 20240115 is filed", 72, h - 76),  # just above the bottom inch
        Line("Reference 998877 in the body", 72, h / 2 + 60),
    ]
    stamp = _stamp(spec, "bottom-right")
    pdf = _pdf([(spec, [*keep, stamp])])
    res = _remove(client, pdf, prefix="", digits="6")
    ((mupdf, pypdf_text),) = _texts(res.content)
    for line in keep:
        for word in line.text.split():
            assert word in mupdf and word in pypdf_text, f"{name}: {word!r} ({line.text!r}) was removed"
    assert STAMP not in mupdf and STAMP not in pypdf_text
    assert _counts(res) == ("1", "0")


@pytest.mark.parametrize("name", ["rotate-0", "rotate-90", "cropped-rotate-270"])
def test_the_lines_around_a_stamp_stay(client, name):
    """A footer set tight against the stamp: a line above and a line below at
    ordinary spacing (12 points for 10-point text), and a page number on the
    stamp's own line. MuPDF removes any character whose box touches a
    redaction, and these lines' boxes reach 1.7 points into the stamp's."""
    spec = SPECS[name]
    w, h = _shown_size(spec)
    stamp = _stamp(spec, "bottom-right")
    around = [
        Line("CONFIDENTIAL SUBJECT TO PROTECTIVE ORDER", w - 20 - _width("CONFIDENTIAL SUBJECT TO PROTECTIVE ORDER"), h - 32),
        Line("Produced by Example LLP", w - 20 - _width("Produced by Example LLP"), h - 8),
        Line("Page 1 of 4", stamp.x - 70, h - 20),
    ]
    pdf = _pdf([(spec, [*around, stamp])])
    before = _shown(pdf, 0, _turn(spec))
    res = _remove(client, pdf)
    ((mupdf, pypdf_text),) = _texts(res.content)
    for line in around:
        assert line.text in " ".join(mupdf.split()) and line.text in " ".join(pypdf_text.split()), (
            f"{name}: {line.text!r} lost characters: {mupdf!r}"
        )
    assert STAMP not in mupdf and STAMP not in pypdf_text
    after = _shown(res.content, 0, _turn(spec))
    assert _ink(after, _ink_box(stamp)) == 0
    assert np.array_equal(_outside(before, _ink_box(stamp)), _outside(after, _ink_box(stamp))), (
        f"{name}: the lines around the stamp look different"
    )
    assert _counts(res) == ("1", "0")


def test_a_stamp_on_a_slant_or_in_two_sizes_leaves_whole(client):
    """The redaction runs along the middle of a stamp, which every character
    of a line in one size crosses. A stamp set on a slant, or whose prefix is
    set much larger than its number, is taken out a character at a time."""
    w, h = _shown_size({})
    slanted = Line(STAMP, w - 110, h - 12, turn=-30)
    pdf = _pdf([({}, [Line(BODY, 72, 120), slanted]), ({}, [Line(BODY, 72, 120)])])
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        page = pikepdf.Page(doc.pages[1])
        page.contents_add(doc.make_stream(b"BT /F1 20 Tf 1 0 0 1 440 20 Tm (ABC) Tj /F1 5 Tf (000124) Tj ET"))
        out = io.BytesIO()
        doc.save(out)
        pdf = out.getvalue()
    assert [text.count(number) for (text, _), number in zip(_texts(pdf), (STAMP, "ABC000124"))] == [1, 1]

    res = _remove(client, pdf)
    for (mupdf, pypdf_text), number in zip(_texts(res.content), (STAMP, "ABC000124")):
        assert number not in mupdf and number not in pypdf_text, f"{number} is still in the text layer"
        assert BODY in mupdf
    for index in (0, 1):
        assert _edge_frame_ink(_shown(res.content, index, 0)) == 0, f"page {index + 1} still shows its number"
    assert _counts(res) == ("2", "0")


@pytest.mark.parametrize("name", ["rotate-0", "cropped-rotate-90"])
def test_a_picture_under_a_stamp_is_left_alone_unless_the_stamp_is_in_it(client, name):
    """A scanned page, grey here, with two numbers at its foot. One is a stamp
    drawn over the scan: only its text goes, and the scan under it stays. The
    other is printed into the scan, with the scan's invisible OCR text over it:
    the number that shows is part of the picture, so the picture under the
    OCR word is whitened as well as the word removed."""
    spec = SPECS[name]
    w, h = _shown_size(spec)
    drawn = Line(STAMP, w - 20 - _width(STAMP), h - 20)
    scanned = Line("ABC000124", 20, h - 20, hidden=True)
    burned = fitz.Rect(scanned.x, scanned.y - 7.2, scanned.x + _width(scanned.text), scanned.y)
    pdf = _pdf([(spec, [drawn, scanned])], dark={0: [burned]})
    before = _shown(pdf, 0, _turn(spec))
    assert _ink(before, burned) > 0.8 * burned.width * burned.height, f"{name}: the printed number is not in the scan"

    res = _remove(client, pdf)
    ((mupdf, pypdf_text),) = _texts(res.content)
    for text in (drawn.text, scanned.text):
        assert text not in mupdf and text not in pypdf_text, f"{name}: {text} is still in the text layer"
    after = _shown(res.content, 0, _turn(spec))
    under = _region(after, _ink_box(drawn))
    assert under.min() > 150 and under.max() < 250, f"{name}: the scan under the drawn stamp changed ({under.min()}-{under.max()})"
    assert _ink(after, burned) == 0, f"{name}: the number printed into the scan still shows"
    assert np.array_equal(
        _outside(_outside(before, _ink_box(drawn)), burned + (-2, -4, 2, 4)),
        _outside(_outside(after, _ink_box(drawn)), burned + (-2, -4, 2, 4)),
    ), f"{name}: the scan changed away from the two numbers"
    assert _counts(res) == ("2", "0")


# ─── The count is what left the file ────────────────────────────────────────

def _stamp_annotation(pdf: bytes, index: int, text: str) -> bytes:
    """`text` drawn at the foot of page `index` by a /Stamp annotation, as
    some editors put a label on a page, instead of in the page's content."""
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        page = doc.pages[index]
        font = doc.make_indirect(pikepdf.Dictionary(
            Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica,
        ))
        appearance = doc.make_stream(f"BT /F1 10 Tf 2 5 Td ({text}) Tj ET".encode())
        appearance.Type, appearance.Subtype = pikepdf.Name.XObject, pikepdf.Name.Form
        appearance.BBox = pikepdf.Array([0, 0, 110, 20])
        appearance.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
        page.obj.Annots = doc.make_indirect(pikepdf.Array([doc.make_indirect(pikepdf.Dictionary(
            Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.Stamp, F=4,
            Rect=pikepdf.Array([480, 17, 590, 37]), AP=pikepdf.Dictionary(N=appearance),
        ))]))
        out = io.BytesIO()
        doc.save(out)
        return out.getvalue()


def test_a_stamp_that_cannot_be_removed_is_reported_not_counted(client):
    """Page 1's stamp is page text and goes. Page 2's is drawn by an
    annotation, which redaction leaves in place: the page must be told one
    was removed and one is still in the file, not that two were removed."""
    pdf = _pdf([({}, [Line(BODY, 72, 120), _stamp({}, "bottom-right")]), ({}, [Line(BODY, 72, 120)])])
    pdf = _stamp_annotation(pdf, 1, "ABC000124")
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        assert "ABC000124" in doc[1].get_text(), "the annotation's number is not where text extraction sees it"

    res = _remove(client, pdf)
    with fitz.open(stream=res.content, filetype="pdf") as doc:
        assert STAMP not in doc[0].get_text()
        assert "ABC000124" in doc[1].get_text(), "the annotation's number went after all; this test needs another stamp"
    assert _counts(res) == ("1", "1")


def test_nothing_found_is_reported_as_nothing(client):
    res = _remove(client, _pdf([({"rotate": 90}, [Line(BODY, 72, 120)])]))
    assert _counts(res) == ("0", "0")
