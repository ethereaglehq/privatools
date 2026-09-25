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


def _pdf(
    pages: list[tuple[dict, list[Line]]], *,
    dark: dict[int, list[fitz.Rect]] | None = None, picture_after: dict[int, int] | None = None, inline: bool = False,
) -> bytes:
    """Pages of text. `dark` gives a page a picture filling it, like a scan;
    it is drawn first, or after the first `picture_after[page]` lines, so that
    it covers them; with `inline`, written into the page's content (BI ... EI)
    instead of as an image the page lists."""
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
        ops = [_text_ops(spec, line).encode() for line in lines]
        if dark is not None and index in dark:
            picture = _picture(spec, dark[index])
            x0, y0, x1, y1 = _visible(spec)
            place = f"q {x1 - x0:g} 0 0 {y1 - y0:g} {x0:g} {y0:g} cm ".encode()
            if inline:
                draw = place + f"BI /W {picture['Width']} /H {picture['Height']} /CS /G /BPC 8 ID ".encode() + picture["data"] + b" EI Q"
            else:
                image = pikepdf.Stream(pdf, picture["data"])
                image.Type, image.Subtype = pikepdf.Name.XObject, pikepdf.Name.Image
                image.Width, image.Height = picture["Width"], picture["Height"]
                image.ColorSpace, image.BitsPerComponent = pikepdf.Name.DeviceGray, 8
                page.Resources.XObject = pikepdf.Dictionary(Im0=image)
                draw = place + b"/Im0 Do Q"
            ops.insert((picture_after or {}).get(index, 0), draw)
        pdf.pages.append(pikepdf.Page(page))
        pdf.pages[-1].Contents = pdf.make_stream(b"\n".join(ops))
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


def _counts(res) -> tuple[str | None, str | None, str | None]:
    """What the page is told: stamps removed, stamps found but still in the
    file, and text matching the prefix or suffix found elsewhere and left."""
    return (res.headers.get("X-Bates-Removed"), res.headers.get("X-Bates-Remaining"),
            res.headers.get("X-Bates-Elsewhere"))


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
    assert _counts(res) == ("1", "0", "0")


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
    assert _counts(res) == ("1", "0", "0")


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
    assert _counts(res) == ("4", "0", "0")


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
    assert _counts(res) == ("2", "0", "0")


# ─── Nothing else leaves the file ───────────────────────────────────────────

@pytest.mark.parametrize("name", ["rotate-0", "rotate-90", "rotate-180", "rotate-270", "cropped-rotate-90", "cropped-rotate-270"])
def test_only_the_stamp_goes_when_other_text_looks_like_one(client, name):
    """With no prefix or suffix, anything Bates-shaped in the top or bottom
    inch goes. A turned page must not widen that: before the fix the
    "bottom inch" of a page turned a quarter was a band 252 points wide down
    one side of the page as shown. On a page turned a quarter, the number in
    the inch at the left side stays but is reported as left in place, since
    a stamp can sit there that the net without a prefix does not take."""
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
    assert _counts(res) == ("1", "0", "1" if _turn(spec) in (90, 270) else "0")


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
    assert _counts(res) == ("1", "0", "0")


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
    assert _counts(res) == ("2", "0", "0")


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
    assert _counts(res) == ("2", "0", "0")


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
    assert _counts(res) == ("1", "1", "0")


def test_nothing_found_is_reported_as_nothing(client):
    res = _remove(client, _pdf([({"rotate": 90}, [Line(BODY, 72, 120)])]))
    assert _counts(res) == ("0", "0", "0")


# ─── Review, round 1 ────────────────────────────────────────────────────────
#
# A scan laid over its own OCR text; our own stamps on landscape pages stored
# turned, and on pages stamped while turned and then turned again; text that
# matches the prefix elsewhere in the file; links and comments that cross a
# stamp; a stamp drawn twice; a stamp in a form field; and pages crammed with
# Bates-shaped numbers.


def _to_user(spec: dict, rect: fitz.Rect) -> list[float]:
    """A rectangle on the page as shown, in PDF user space (an annotation's /Rect)."""
    x0, _, _, top = _visible(spec)
    corners = [_to_stored(spec, x, y) for x, y in (rect.tl, rect.br)]
    us, vs = sorted(c[0] for c in corners), sorted(c[1] for c in corners)
    return [x0 + us[0], top - vs[1], x0 + us[1], top - vs[0]]


def _shown_word(pdf: bytes, text: str, index: int = 0) -> fitz.Rect:
    """Where `text` is on the page as shown (the page's /Rotate is 0, 90, 180 or 270)."""
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        page = doc[index]
        return next(fitz.Rect(w[:4]) * page.rotation_matrix for w in page.get_text("words") if w[4] == text)


@pytest.mark.parametrize("inline", [False, True], ids=["listed", "inline"])
@pytest.mark.parametrize("name", ["rotate-0", "cropped-rotate-90"])
def test_a_number_printed_in_a_scan_laid_over_its_ocr_text_is_whitened(client, name, inline):
    """Some OCR software draws the text it recognised in the ordinary way and
    lays the scan over it, so the number that shows is the one in the picture.
    Taking out only the text left that number showing, while the page said it
    was gone. A stamp drawn over the scan still leaves the scan alone. The
    scan is an image the page lists, or one written into its content."""
    spec = SPECS[name]
    w, h = _shown_size(spec)
    ocr = Line("ABC000124", 20, h - 20)
    printed = fitz.Rect(ocr.x, ocr.y - 7.2, ocr.x + _width(ocr.text), ocr.y)
    drawn = Line(STAMP, w - 20 - _width(STAMP), h - 20)
    pdf = _pdf([(spec, [ocr, drawn])], dark={0: [printed]}, picture_after={0: 1}, inline=inline)
    before = _shown(pdf, 0, _turn(spec))
    assert _ink(before, printed) > 0.8 * printed.width * printed.height, f"{name}: the printed number is not in the scan"
    ocr_box = _shown_word(pdf, ocr.text)

    res = _remove(client, pdf)
    ((mupdf, pypdf_text),) = _texts(res.content)
    for text in (ocr.text, drawn.text):
        assert text not in mupdf and text not in pypdf_text, f"{name}: {text} is still in the text layer"
    after = _shown(res.content, 0, _turn(spec))
    assert _ink(after, printed) == 0, f"{name}: the number printed into the scan still shows"
    under = _region(after, _ink_box(drawn))
    assert under.min() > 150 and under.max() < 250, f"{name}: the scan under the drawn stamp changed ({under.min()}-{under.max()})"
    assert np.array_equal(
        _outside(_outside(before, _ink_box(drawn)), ocr_box + (-2, -2, 2, 2)),
        _outside(_outside(after, _ink_box(drawn)), ocr_box + (-2, -2, 2, 2)),
    ), f"{name}: the scan changed away from the two numbers"
    assert _counts(res) == ("2", "0", "0")


@pytest.mark.parametrize("position", ["bottom-left", "bottom-center", "bottom-right", "top-left", "top-center", "top-right"])
@pytest.mark.parametrize("rotate", [90, 270])
def test_our_stamp_on_a_landscape_page_stored_turned_is_removed_or_reported(client, rotate, position):
    """Bates Numbering sizes its stamp for the page as stored, so on a
    landscape page stored turned a quarter it lands 173 points from the top or
    bottom as shown, and 16 points from a side unless it is centred. v2.7.4
    removed four of these twelve placements by accident; the first version of
    this fix removed none and said "No Bates numbers found". With the prefix,
    a stamp within an inch of any edge goes, and the centred ones, which are
    not, are reported rather than left in silence."""
    spec = {"rotate": rotate, "mediabox": (0, 0, 792, 612)}
    stamped = _post(client, "bates-numbering", _pdf([(spec, [Line(BODY, 72, 120)])]),
                    prefix="PROD", start_number="123", digits="6", position=position).content
    where = _shown_word(stamped, "PROD000123")

    res = _remove(client, stamped, prefix="PROD")
    ((mupdf, pypdf_text),) = _texts(res.content)
    left = "PROD000123" in mupdf or "PROD000123" in pypdf_text
    if position.endswith("center"):
        assert left and _counts(res) == ("0", "0", "1"), f"{where}: the stamp left in place is not reported"
    else:
        assert not left, f"{position} on /Rotate {rotate}: the stamp at {where} is still in the file"
        assert _ink(_shown(res.content, 0, rotate), where + (-1, -1, 1, 1)) == 0, "the stamp still shows"
        assert _counts(res) == ("1", "0", "0")


@pytest.mark.parametrize("angle", [90, 180, 270])
def test_a_page_stamped_while_turned_and_turned_again_loses_its_number(client, angle):
    """Our Bates Numbering on a page stored turned 90, then our Rotate tool
    turning the page again: the stamp now runs along a side of the page as
    shown (turned by 90 or 270), or sits upside down at the top (180). The
    versions before missed the side ones."""
    stamped = _post(client, "bates-numbering", _pdf([({"rotate": 90}, [Line(BODY, 72, 120)])]),
                    prefix="PROD", digits="6").content
    turned = _post(client, "rotate", stamped, angle=str(angle)).content
    turn = (90 + angle) % 360
    assert _mupdf_rotation(turned) == turn
    assert _edge_frame_ink(_shown(turned, 0, turn)) > 50

    res = _remove(client, turned, prefix="PROD")
    ((mupdf, pypdf_text),) = _texts(res.content)
    assert "PROD000001" not in mupdf and "PROD000001" not in pypdf_text, f"turned {angle}: the number is still there"
    assert BODY in mupdf
    assert _edge_frame_ink(_shown(res.content, 0, turn)) == 0, f"turned {angle}: the number still shows"
    assert _counts(res) == ("1", "0", "0")


def test_text_matching_the_prefix_elsewhere_is_left_and_reported(client):
    """A reference to a Bates number in the body is not a stamp, and a number
    hidden outside the visible page is not in its margins: both stay, and the
    page is told how many, so it never says the file is clean while text
    matching the prefix is still in it. With no prefix there is nothing exact
    to count, and nothing is reported."""
    spec = {"cropbox": (0, 72, 612, 792)}  # hides the bottom inch of the page
    w, h = _shown_size(spec)
    lines = [Line("See ABC000555 for the invoice", 72, 300), Line("ABC000556", 72, h + 40), _stamp(spec, "bottom-right")]
    pdf = _pdf([(spec, lines)])
    ((mupdf, pypdf_text),) = _texts(pdf)
    assert "ABC000556" in pypdf_text and "ABC000556" not in mupdf, "the hidden number is not where only pypdf reads it"

    res = _remove(client, pdf)
    ((mupdf, pypdf_text),) = _texts(res.content)
    assert STAMP not in mupdf and STAMP not in pypdf_text
    assert "ABC000555" in mupdf and "ABC000556" in pypdf_text
    assert _counts(res) == ("1", "0", "2")

    res = _remove(client, pdf, prefix="")
    assert "ABC000555" in _texts(res.content)[0][0]
    assert _counts(res) == ("1", "0", "0")


def _appearance(doc: pikepdf.Pdf, rect: list[float], text: str) -> pikepdf.Stream:
    """An annotation's appearance showing `text` along its box: up the box
    when it is taller than wide (a box on a page turned a quarter), so that
    the text reads upright as the page is shown."""
    font = doc.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica))
    width, height = rect[2] - rect[0], rect[3] - rect[1]
    place = f"0 1 -1 0 {width - 4:g} 2 Tm" if height > width else "2 4 Td"
    form = doc.make_stream(f"BT /F1 8 Tf {place} ({text}) Tj ET".encode())
    form.Type, form.Subtype = pikepdf.Name.XObject, pikepdf.Name.Form
    form.BBox = pikepdf.Array([0, 0, rect[2] - rect[0], rect[3] - rect[1]])
    form.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
    return form


def _annotated(pdf: bytes, annots: list[dict]) -> bytes:
    """Page 1 of `pdf` with link and FreeText annotations: {"kind", "rect"
    (PDF user space), "uri" or "text"}."""
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        made = []
        for spec in annots:
            rect = spec["rect"]
            if spec["kind"] == "link":
                annot = pikepdf.Dictionary(Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.Link, Rect=pikepdf.Array(rect),
                                           Border=pikepdf.Array([0, 0, 0]),
                                           A=pikepdf.Dictionary(S=pikepdf.Name.URI, URI=pikepdf.String(spec["uri"])))
            else:
                annot = pikepdf.Dictionary(Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.FreeText, F=4, Rect=pikepdf.Array(rect),
                                           Contents=pikepdf.String(spec["text"]), DA=pikepdf.String("/Helv 8 Tf 0 g"),
                                           AP=pikepdf.Dictionary(N=_appearance(doc, rect, spec["text"])))
            made.append(doc.make_indirect(annot))
        doc.pages[0].obj.Annots = doc.make_indirect(pikepdf.Array(made))
        out = io.BytesIO()
        doc.save(out)
        return out.getvalue()


def _annotations(pdf: bytes) -> list[tuple[str, str]]:
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        return sorted((str(a.Subtype), str(a.A.URI) if "/A" in a else str(a.get("/Contents", "")))
                      for a in doc.pages[0].get("/Annots", []))


@pytest.mark.parametrize("name", ["rotate-0", "rotate-90"])
def test_links_and_comments_crossing_a_stamp_stay(client, name):
    """MuPDF deletes every link and FreeText annotation a redaction touches: a
    link over the whole page, one across the footer, a reviewer's comment
    across it. They stay now. A link on the stamp alone goes with the stamp,
    and so does a FreeText annotation that is itself a Bates number."""
    spec = SPECS[name]
    w, h = _shown_size(spec)
    stamp = _stamp(spec, "bottom-right")
    pdf = _pdf([(spec, [Line(BODY, 72, 120), stamp])])
    on_stamp = _shown_word(pdf, STAMP) + (0.5, 0.5, -0.5, -0.5)
    pdf = _annotated(pdf, [
        {"kind": "link", "uri": "https://example.com/page", "rect": _to_user(spec, fitz.Rect(0, 0, w, h))},
        {"kind": "link", "uri": "https://example.com/footer", "rect": _to_user(spec, fitz.Rect(10, h - 40, w - 10, h - 5))},
        {"kind": "link", "uri": "https://example.com/stamp", "rect": _to_user(spec, on_stamp)},
        {"kind": "freetext", "text": "See exhibit list", "rect": _to_user(spec, fitz.Rect(10, h - 45, w - 10, h - 2))},
        {"kind": "freetext", "text": "ABC000124", "rect": _to_user(spec, fitz.Rect(20, h - 34, 120, h - 14))},
    ])
    assert "ABC000124" in _texts(pdf)[0][0], "the FreeText stamp is not where text extraction sees it"

    res = _remove(client, pdf)
    assert _annotations(res.content) == [
        ("/FreeText", "See exhibit list"), ("/Link", "https://example.com/footer"), ("/Link", "https://example.com/page"),
    ]
    ((mupdf, _),) = _texts(res.content)
    assert STAMP not in mupdf and "ABC000124" not in mupdf
    assert _counts(res) == ("2", "0", "0")


@pytest.mark.parametrize("name", ["rotate-0", "rotate-90"])
def test_a_stamp_drawn_twice_in_one_place_counts_once(client, name):
    """A "fake bold" stamp is drawn twice, 0.3 points apart: one stamp to the
    visitor, and it was counted as two."""
    spec = SPECS[name]
    stamp = _stamp(spec, "bottom-right")
    pdf = _pdf([(spec, [Line(BODY, 72, 120), stamp, stamp._replace(x=stamp.x + 0.3)])])
    assert _texts(pdf)[0][0].count(STAMP) == 2

    res = _remove(client, pdf)
    ((mupdf, pypdf_text),) = _texts(res.content)
    assert STAMP not in mupdf and STAMP not in pypdf_text
    assert _ink(_shown(res.content, 0, _turn(spec)), _ink_box(stamp) + (0, 0, 1, 0)) == 0
    assert _counts(res) == ("1", "0", "0")


def test_a_stamp_in_a_form_field_is_reported_as_still_in_the_file(client):
    """A number held by a form field is drawn by the field, where redaction
    does not reach: the page is told it is still in the file."""
    pdf = _pdf([({}, [Line(BODY, 72, 120), _stamp({}, "bottom-right")])])
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        rect = [20, 12, 140, 34]
        field = doc.make_indirect(pikepdf.Dictionary(
            Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.Widget, F=4, FT=pikepdf.Name.Tx, T=pikepdf.String("bates"),
            V=pikepdf.String("ABC000124"), Rect=pikepdf.Array(rect), DA=pikepdf.String("/Helv 8 Tf 0 g"),
            AP=pikepdf.Dictionary(N=_appearance(doc, rect, "ABC000124")),
        ))
        doc.pages[0].obj.Annots = doc.make_indirect(pikepdf.Array([field]))
        doc.Root.AcroForm = pikepdf.Dictionary(Fields=pikepdf.Array([field]))
        out = io.BytesIO()
        doc.save(out)
        pdf = out.getvalue()
    assert "ABC000124" in _texts(pdf)[0][0]

    res = _remove(client, pdf)
    ((mupdf, _),) = _texts(res.content)
    assert STAMP not in mupdf
    assert "ABC000124" in mupdf, "the field's number went after all; this test needs another stamp"
    assert _counts(res) == ("1", "1", "0")


def _crammed(pages: int, numbers: int) -> bytes:
    """`pages` pages sharing one content stream: a body of text and `numbers`
    Bates-shaped numbers in 4-point type in the top and bottom inch."""
    ops = [f"BT /F1 10 Tf 54 {720 - 12.5 * i:.1f} Td (lorem ipsum dolor sit amet consectetur adipiscing elit sed do) Tj ET"
           for i in range(50)]
    rows = [" ".join(f"{n:06d}" for n in range(start, min(start + 40, numbers))) for start in range(0, numbers, 40)]
    for r, row in enumerate(rows):
        y = 786 - (r // 2) * 4.2 if r % 2 == 0 else 4 + (r // 2) * 4.2
        ops.append(f"BT /F1 4 Tf 8 {y:.1f} Td ({row}) Tj ET")
    pdf = pikepdf.new()
    font = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica))
    content = pdf.make_indirect(pdf.make_stream("\n".join(ops).encode()))
    for _ in range(pages):
        pdf.pages.append(pikepdf.Page(pikepdf.Dictionary(
            Type=pikepdf.Name.Page, MediaBox=pikepdf.Array(LETTER), Contents=content,
            Resources=pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font)),
        )))
    out = io.BytesIO()
    pdf.save(out, compress_streams=True)
    return out.getvalue()


@pytest.mark.parametrize("pages,numbers", [(1, 1280), (20, 1280), (60, 100)])
def test_pages_crammed_with_bates_shaped_numbers_are_refused_quickly(client, pages, numbers):
    """Each Bates-shaped number in a margin costs a pass over its page's
    words. 1,280 of them on one page took about 28 seconds, and twenty such
    pages sharing their content, an upload of 8.5 KB, minutes. The work is
    counted before it is done and refused past what a file of that size
    warrants: the busiest real page found had 13 such numbers."""
    import time

    pdf = _crammed(pages, numbers)
    start = time.process_time()
    res = client.post("/api/bates-remove", files={"file": ("p.pdf", pdf, "application/pdf")}, data={"prefix": "", "digits": "6"})
    spent = time.process_time() - start
    assert res.status_code == 422, res.text[:300]
    detail = res.json()["detail"]
    assert "no file was made" in detail and "prefix" in detail, detail
    assert spent < 5, f"refusing took {spent:.1f} s of CPU"


def test_the_busiest_real_page_is_not_refused(client):
    """The busiest real page in 616 statements and terms had 3,171 words and,
    with the fewest digits allowed, 13 Bates-shaped numbers in its margins."""
    pdf = _crammed(1, 13)
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        page = pikepdf.Page(doc.pages[0])
        page.contents_add(doc.make_stream("\n".join(
            f"BT /F1 3 Tf 80 {640 - 1.6 * i:.1f} Td ({' '.join(['word'] * 10)}) Tj ET" for i in range(300)
        ).encode()))
        out = io.BytesIO()
        doc.save(out)
        pdf = out.getvalue()
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        assert len(doc[0].get_text("words")) > 3171
    res = _remove(client, pdf, prefix="", digits="3")
    assert _counts(res) == ("13", "0", "0")


# ─── Review, round 2 ────────────────────────────────────────────────────────
#
# Our own stamps left without a prefix, and never in silence; pages that draw
# a lot; pictures you can see through.


@pytest.mark.parametrize("position", ["bottom-left", "bottom-center", "bottom-right", "top-left", "top-center", "top-right"])
@pytest.mark.parametrize("rotate", [90, 270])
def test_our_stamp_left_without_a_prefix_is_reported(client, rotate, position):
    """With no prefix, our own stamp on a landscape page stored turned a
    quarter is outside the net: about 173 points from the top or bottom as
    shown. It stays (removing Bates-shaped numbers from the middle of pages
    is what the net avoids), but the page is told it was left in place,
    where before it said "No Bates numbers found", or with other files,
    that the text was gone. v2.7.4 removed four of these by accident, among
    them Bates Numbering's default, bottom right on /Rotate 90."""
    spec = {"rotate": rotate, "mediabox": (0, 0, 792, 612)}
    stamped = _post(client, "bates-numbering", _pdf([(spec, [Line(BODY, 72, 120)])]),
                    prefix="PROD", start_number="123", digits="6", position=position).content

    res = _remove(client, stamped, prefix="", digits="6")
    ((mupdf, pypdf_text),) = _texts(res.content)
    assert "PROD000123" in mupdf and "PROD000123" in pypdf_text
    assert BODY in mupdf
    assert _counts(res) == ("0", "0", "1")


def test_numbers_in_the_body_of_a_turned_page_are_not_reported(client):
    """The report without a prefix covers the inch at either side of a page
    turned a quarter and the bands where our Bates Numbering puts its stamp
    there, nothing more: Bates-shaped numbers elsewhere in the body stay and
    are not mentioned."""
    for spec in ({"rotate": 90, "mediabox": (0, 0, 792, 612)}, {"rotate": 90}, {"rotate": 270, "cropbox": CROP}):
        w, h = _shown_size(spec)
        body = [Line("Account 00451234 opened", 100, h / 2), Line("Reference 998877 filed", 100, h / 2 + 60),
                Line("Invoice 20240115 paid", 100, 100)]
        pdf = _pdf([(spec, [*body, _stamp(spec, "bottom-right")])])
        res = _remove(client, pdf, prefix="", digits="6")
        ((mupdf, _),) = _texts(res.content)
        for number in ("00451234", "998877", "20240115"):
            assert number in mupdf, f"{spec}: {number} was removed"
        assert _counts(res) == ("1", "0", "0"), spec


def _drawing(segments: int, numbers: int) -> bytes:
    """One page drawing `segments` short line segments (a detailed drawing),
    with `numbers` Bates-shaped numbers in 4-point type in its bottom inch."""
    ops = [f"{100 + i % 400} {200 + (i // 400) % 400} m {101 + i % 400} {201 + (i // 400) % 400} l" for i in range(segments)]
    ops.append("S")
    for row in range(0, numbers, 40):
        codes = " ".join(f"{n:06d}" for n in range(row, min(row + 40, numbers)))
        ops.append(f"BT /F1 4 Tf 1 0 0 1 8 {4 + row / 40 * 4.2:.1f} Tm ({codes}) Tj ET")
    pdf = pikepdf.new()
    font = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica))
    pdf.pages.append(pikepdf.Page(pikepdf.Dictionary(
        Type=pikepdf.Name.Page, MediaBox=pikepdf.Array(LETTER), Resources=pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font)),
    )))
    pdf.pages[0].Contents = pdf.make_stream("\n".join(ops).encode())
    out = io.BytesIO()
    pdf.save(out, compress_streams=True)
    return out.getvalue()


def test_a_page_that_draws_a_lot_is_charged_for_it(client):
    """Each candidate costs two runs over the page's whole content, drawings
    included. The charge counted words, so a small page drawing 200,000 line
    segments with 100 numbers in its margin passed and took 2.5 times what
    v2.7.4 took (a 49 KB page of 1 million segments with 150 numbers: 88 s).
    The charge now follows the time the page took to read, so it is refused
    after that first read; with 12 numbers it is processed."""
    import time

    pdf = _drawing(200_000, 100)
    start = time.process_time()
    res = client.post("/api/bates-remove", files={"file": ("d.pdf", pdf, "application/pdf")}, data={"prefix": "", "digits": "6"})
    spent = time.process_time() - start
    assert res.status_code == 422, res.text[:300]
    assert "no file was made" in res.json()["detail"]
    assert spent < 3, f"refusing took {spent:.1f} s of CPU"

    res = _remove(client, _drawing(200_000, 12), prefix="", digits="6")
    assert _counts(res) == ("12", "0", "0")


def _overlay(pdf: bytes, alpha: str) -> bytes:
    """`pdf` with a grey picture laid over the whole of page 1 after its text,
    see-through: with a soft mask (`alpha` "smask") or drawn at a constant
    fill alpha ("ca")."""
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        page = doc.pages[0]
        grey = pikepdf.Stream(doc, bytes([150]) * 64)
        grey.Type, grey.Subtype, grey.Width, grey.Height = pikepdf.Name.XObject, pikepdf.Name.Image, 8, 8
        grey.ColorSpace, grey.BitsPerComponent = pikepdf.Name.DeviceGray, 8
        resources = page.obj.Resources
        draw = b"q 612 0 0 792 0 0 cm /Veil Do Q"
        if alpha == "smask":
            mask = pikepdf.Stream(doc, bytes([100]) * 64)
            mask.Type, mask.Subtype, mask.Width, mask.Height = pikepdf.Name.XObject, pikepdf.Name.Image, 8, 8
            mask.ColorSpace, mask.BitsPerComponent = pikepdf.Name.DeviceGray, 8
            grey.SMask = mask
        else:
            resources.ExtGState = pikepdf.Dictionary(Half=pikepdf.Dictionary(Type=pikepdf.Name.ExtGState, ca=0.4))
            draw = b"q /Half gs 612 0 0 792 0 0 cm /Veil Do Q"
        resources.XObject = pikepdf.Dictionary(Veil=grey)
        page.contents_add(doc.make_stream(draw))
        out = io.BytesIO()
        doc.save(out)
        return out.getvalue()


@pytest.mark.parametrize("alpha", ["smask", "ca"])
def test_a_see_through_picture_over_a_stamp_is_not_whitened(client, alpha):
    """A picture laid over a stamp after it hides it only if it is opaque.
    Through a see-through one (a watermark, a tint) the stamp's text shows,
    so only the text goes: the picture under it stays as it was, and the
    page looks as it would have without the stamp."""
    stamp = _stamp({}, "bottom-right")
    pdf = _overlay(_pdf([({}, [Line(BODY, 72, 120), stamp])]), alpha)
    without = _overlay(_pdf([({}, [Line(BODY, 72, 120)])]), alpha)

    res = _remove(client, pdf)
    ((mupdf, _),) = _texts(res.content)
    assert STAMP not in mupdf
    after, expected = _shown(res.content, 0, 0), _shown(without, 0, 0)
    region = _ink_box(stamp) + (-2, -2, 2, 2)
    assert np.abs(_region(after, region).astype(int) - _region(expected, region).astype(int)).max() <= 2, (
        f"{alpha}: the stamp's box does not look as it would without the stamp"
    )
    assert _counts(res) == ("1", "0", "0")
