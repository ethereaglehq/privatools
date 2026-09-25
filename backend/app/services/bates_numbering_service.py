"""Bates numbering — stamping, continuous multi-file sequences, and removal.

Bates numbers exist to give a document production a single unbroken index: in a
legal production, page 1 of the first file and the last page of the last file
are ends of *one* sequence, not per-file sequences that each restart. The
original implementation numbered each file from `start_number` independently,
which makes the output unusable for the audience the tool is for.

`add_bates_numbering_batch` maintains the running counter across files and
returns a manifest of which range landed on which file — the production log a
paralegal would otherwise reconstruct by hand.
"""

import io
import logging
import re
from itertools import groupby
from typing import NamedTuple

import fitz  # PyMuPDF
import pikepdf
from reportlab.lib.colors import black
from reportlab.pdfgen import canvas

from ..utils.cleanup import safe_open_pdf
from ..utils.filenames import temp_output
from ..utils.page_range import parse_page_range
from ..utils.page_space import settle_rotation

logger = logging.getLogger(__name__)

VALID_POSITIONS = {
    "bottom-right",
    "bottom-left",
    "bottom-center",
    "top-right",
    "top-left",
    "top-center",
}

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 72

# How far from the page edge a stamp is considered to live. Removal only
# touches text inside this band, so body text that happens to look like a
# Bates number is never redacted.
_MARGIN_BAND_PT = 72.0

# Half the thickness of what is redacted along the middle of a stamp (see
# _marks).
_MARK_PT = 0.5


def format_bates(prefix: str, number: int, digits: int, suffix: str = "") -> str:
    return f"{prefix}{str(number).zfill(digits)}{suffix}"


def _draw(width: float, height: float, text: str, position: str, font_size: int) -> bytes:
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))
    c.setFillColor(black)
    c.setFont("Helvetica", font_size)
    margin = 20

    if position == "bottom-right":
        c.drawRightString(width - margin, margin, text)
    elif position == "bottom-left":
        c.drawString(margin, margin, text)
    elif position == "bottom-center":
        c.drawCentredString(width / 2, margin, text)
    elif position == "top-right":
        c.drawRightString(width - margin, height - margin - font_size, text)
    elif position == "top-left":
        c.drawString(margin, height - margin - font_size, text)
    elif position == "top-center":
        c.drawCentredString(width / 2, height - margin - font_size, text)

    c.save()
    packet.seek(0)
    return packet.read()


def add_bates_numbering(
    input_path: str,
    prefix: str = "",
    start_number: int = 1,
    digits: int = 6,
    position: str = "bottom-right",
    suffix: str = "",
    font_size: int = 10,
    pages: str | None = None,
) -> tuple[str, int]:
    """Stamp one document.

    Returns `(output_path, next_number)`. The second value is what makes a
    continuous multi-file sequence possible — the caller feeds it into the next
    document instead of restarting.

    `pages` restricts which pages are *stamped*; the counter still advances
    only for stamped pages, so the sequence stays dense.
    """
    output_path = temp_output("bates", "pdf")
    font_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, int(font_size)))
    number = start_number

    with safe_open_pdf(input_path) as pdf:
        total = len(pdf.pages)
        if pages:
            targets = set(parse_page_range(pages, total, allow_empty=True))
        else:
            targets = set(range(total))

        for i, page in enumerate(pdf.pages):
            if i not in targets:
                continue
            text = format_bates(prefix, number, digits, suffix)
            mediabox = page.mediabox
            width = float(mediabox[2]) - float(mediabox[0])
            height = float(mediabox[3]) - float(mediabox[1])

            overlay_pdf = pikepdf.Pdf.open(
                io.BytesIO(_draw(width, height, text, position, font_size))
            )
            pikepdf.Page(page).add_overlay(overlay_pdf.pages[0])
            number += 1

        pdf.save(str(output_path))

    return str(output_path), number


def add_bates_numbering_batch(
    input_paths: list[str],
    prefix: str = "",
    start_number: int = 1,
    digits: int = 6,
    position: str = "bottom-right",
    suffix: str = "",
    font_size: int = 10,
) -> tuple[list[str], list[dict]]:
    """Stamp several documents as ONE continuous sequence.

    This is the difference between a usable production tool and a toy: the
    second file picks up where the first stopped rather than restarting at
    `start_number`.

    Returns the output paths and a manifest — index, page count, and the first
    and last Bates number on each file.
    """
    outputs: list[str] = []
    manifest: list[dict] = []
    number = start_number

    for index, path in enumerate(input_paths):
        first = number
        out, number = add_bates_numbering(
            path,
            prefix=prefix,
            start_number=number,
            digits=digits,
            position=position,
            suffix=suffix,
            font_size=font_size,
        )
        outputs.append(out)
        manifest.append({
            "index": index,
            "pages": number - first,
            "firstBates": format_bates(prefix, first, digits, suffix),
            "lastBates": format_bates(prefix, max(number - 1, first), digits, suffix),
        })

    return outputs, manifest


def _removal_pattern(prefix: str, suffix: str, digits: int) -> re.Pattern:
    """Build the pattern removal will match.

    With a prefix or suffix supplied we match exactly, which is safe. With
    neither, we fall back to "optional letters, then at least `digits` digits" —
    still anchored, and still confined to the margin band by the caller.
    """
    if prefix or suffix:
        return re.compile(
            rf"^{re.escape(prefix)}\d{{1,12}}{re.escape(suffix)}$"
        )
    return re.compile(rf"^[A-Za-z._-]{{0,12}}\d{{{max(digits, 3)},12}}$")


class _Word(NamedTuple):
    """A word as PyMuPDF reads it, with the page unturned: points from the
    top-left corner of the page's visible area as stored."""

    text: str
    box: fitz.Rect
    # Each character and its box.
    chars: tuple[tuple[str, fitz.Rect], ...]
    # It runs across the page as stored (left to right, or right to left).
    across: bool
    # It is painted. A scan's OCR text layer is not: it is there to be found.
    drawn: bool


def _words(page: fitz.Page, clip: fitz.Rect) -> list[_Word]:
    """The words within `clip`, split at white space as get_text("words")
    splits them, with what "words" leaves out: which way each runs, whether
    it is painted, and each character's box. On a page of text this takes
    about twenty times as long as "words", so only a small part is read."""
    words: list[_Word] = []
    for block in page.get_text("rawdict", clip=clip, flags=fitz.TEXTFLAGS_WORDS)["blocks"]:
        for line in block.get("lines", ()):
            dx, dy = line["dir"]
            chars = [(char["c"], char["bbox"], span["alpha"] > 0) for span in line["spans"] for char in span["chars"]]
            for space, run in groupby(chars, key=lambda char: char[0].isspace()):
                if space:
                    continue
                run = list(run)
                boxes = [fitz.Rect(bbox) for _, bbox, _ in run]
                words.append(_Word(
                    text="".join(c for c, _, _ in run),
                    box=_union(boxes),
                    chars=tuple((c, box) for (c, _, _), box in zip(run, boxes)),
                    across=abs(dx) >= abs(dy),
                    drawn=any(painted for _, _, painted in run),
                ))
    return words


def _union(rects: list[fitz.Rect]) -> fitz.Rect:
    union = fitz.Rect(rects[0])
    for rect in rects[1:]:
        union |= rect
    return union


def _middle(rect: fitz.Rect) -> fitz.Point:
    return fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)


def _in_band(box: fitz.Rect, height: float) -> bool:
    """Whether `box` lies within the margin band at the top or the bottom of a
    page `height` tall, measured down from its top."""
    return box.y1 <= _MARGIN_BAND_PT or box.y0 >= height - _MARGIN_BAND_PT


def _stamps(page: fitz.Page, pattern: re.Pattern) -> list[_Word]:
    """The Bates stamps on `page`: words that match `pattern` and lie within
    the margin band at the top or the bottom of the page as it was stamped.

    That is the page as the visitor sees it, with /Rotate read the way the
    site's preview (pdf.js) reads it: settle_rotation writes it that way, so
    PyMuPDF's rotation matrix is the preview's. Words are measured where the
    file stores them, so they are turned into the page as shown first; before
    that, a stamp on a page turned a quarter was measured against the wrong
    edges and never found.

    A word laid across the page as stored may also have been stamped on the
    page as stored: by a stamping tool that ignores /Rotate (our own Bates
    Numbering does on a page whose /Rotate is written -90 or 450), or before
    the page was turned (by our Rotate tool, say), which leaves a stamp
    where it was. On a page turned a quarter such a stamp runs up a side of
    the page as shown. On a page turned 0 or 180 degrees both frames have
    the same top and bottom bands, so nothing more is matched there.
    """
    rotation = settle_rotation(page)
    shown = page.rect
    to_shown = page.rotation_matrix
    stored_height = shown.width if rotation in (90, 270) else shown.height

    def as_shown(box: fitz.Rect) -> bool:
        return _in_band(box * to_shown, shown.height)

    def as_stored(box: fitz.Rect) -> bool:
        return _in_band(box, stored_height)

    stamps = []
    # "words" is quick, and most pages end here; which way a word runs is
    # read only for the few near an edge.
    for *coords, text, _, _, _ in page.get_text("words"):
        box = fitz.Rect(coords)
        if not (pattern.match(text) and (as_shown(box) or as_stored(box))):
            continue
        # Only the word "words" found counts: one the clip cuts short could
        # match where the whole word does not.
        word = next((
            read for read in _words(page, box + (-1, -1, 1, 1))
            if read.text == text and all(abs(a - b) < 0.5 for a, b in zip(read.box, box))
        ), None)
        if word is not None and (as_shown(word.box) or (word.across and as_stored(word.box))):
            stamps.append(word)
    return stamps


def _marks(word: _Word) -> list[fitz.Rect]:
    """Where to redact to take `word` and nothing else.

    MuPDF removes every character whose box touches a redaction, and a
    word's box runs from the font's ascender to its descender, so at ordinary
    line spacing the lines just above and below a stamp reach a point or two
    into its box: redacting the stamp's box took their characters too. A
    band a point thick along the middle of the word takes the word alone,
    since every character of a line in one size crosses it. Where one does
    not (a stamp set in two sizes, or on a slant), a point in the middle of
    each character does.
    """
    box = word.box
    if word.across:
        middle = (box.y0 + box.y1) / 2
        band = fitz.Rect(box.x0 + _MARK_PT, middle - _MARK_PT, box.x1 - _MARK_PT, middle + _MARK_PT)
        crosses = all(rect.y0 < band.y1 and rect.y1 > band.y0 for _, rect in word.chars)
    else:
        middle = (box.x0 + box.x1) / 2
        band = fitz.Rect(middle - _MARK_PT, box.y0 + _MARK_PT, middle + _MARK_PT, box.y1 - _MARK_PT)
        crosses = all(rect.x0 < band.x1 and rect.x1 > band.x0 for _, rect in word.chars)
    if crosses:
        return [band]
    return [fitz.Rect(_middle(rect), _middle(rect)) + (-_MARK_PT, -_MARK_PT, _MARK_PT, _MARK_PT) for _, rect in word.chars]


def _redact(page: fitz.Page, stamps: list[_Word]) -> int:
    """Take `stamps` out of `page`; return how many are no longer on it.

    Only the text goes (see _marks), and nothing is painted over the place.
    Pictures and drawings are left alone, except under a stamp that is not
    painted, like a scan's OCR text: the number that shows there is part of
    the picture, so the picture under the word is whitened.

    The count is taken from the page afterwards: a stamp redaction does not
    reach, such as one drawn by a stamp annotation or a form field, is still
    there and is not counted.
    """
    for word in stamps:
        for rect in _marks(word):
            page.add_redact_annot(rect, cross_out=False)
    page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_REMOVE,
    )
    hidden = [word for word in stamps if not word.drawn]
    for word in hidden:
        page.add_redact_annot(word.box, cross_out=False)
    if hidden:
        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_PIXELS, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_NONE,
        )

    # A stamp is still there if any of its characters is: the same character
    # in the same place.
    def still_there(stamp: _Word) -> bool:
        left = [
            (char, _middle(rect))
            for word in _words(page, stamp.box + (-1, -1, 1, 1)) for char, rect in word.chars
        ]
        return any(
            char == other and abs(_middle(rect).x - point.x) < 1 and abs(_middle(rect).y - point.y) < 1
            for char, rect in stamp.chars for other, point in left
        )

    return sum(1 for stamp in stamps if not still_there(stamp))


def remove_bates_numbering(
    input_path: str,
    prefix: str = "",
    suffix: str = "",
    digits: int = 6,
) -> tuple[str, int, int]:
    """Remove Bates stamps, returning `(output_path, removed, remaining)`:
    how many stamps are no longer in the file, and how many were found but
    are still in it.

    Two guards keep this from eating real content: the text must match the
    Bates pattern, and it must sit within `_MARGIN_BAND_PT` of the top or
    bottom edge of the page (see _stamps). A figure caption reading "000123"
    in the middle of the page is left alone.

    Redaction is used rather than an overlay so the text is genuinely gone
    rather than covered — the whole point of removing a production number is
    that it is no longer in the file.
    """
    output_path = temp_output("bates_removed", "pdf")
    pattern = _removal_pattern(prefix, suffix, digits)
    removed = remaining = 0

    doc = fitz.open(input_path)
    try:
        for page in doc:
            stamps = _stamps(page, pattern)
            if stamps:
                gone = _redact(page, stamps)
                removed += gone
                remaining += len(stamps) - gone

        doc.save(str(output_path), garbage=4, deflate=True)
    finally:
        doc.close()

    return str(output_path), removed, remaining
