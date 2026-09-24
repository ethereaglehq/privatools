"""Where the drawing tools put things on a page.

The PyMuPDF tools (Redact, White-Out, Annotate, Add Shapes, Form Creator and
eSign) take boxes in points from the top-left corner of the page's visible
area (its CropBox), before any /Rotate setting the page has is applied. The
website's page converts what the visitor draws on its preview into that
(frontend/src/components/tool-ui/pdf/page-coordinates.ts).

Two things went wrong on turned pages even with the right numbers:

* PyMuPDF's own drawing (Shape, insert_image, insert_text, and the fill that
  apply_redactions paints) forgets where the visible area starts once the page
  has a /Rotate: Page.transformation_matrix is (1, 0, 0, -1, 0, height) for any
  turned page. On a turned page whose CropBox or MediaBox does not start at
  0,0, a white-out or a redaction's black box landed that far away. With
  /Rotate 0, PyMuPDF uses MuPDF's own matrix, which is right, so the tools draw
  with the page unturned for the moment (PyMuPDF does the same itself when it
  adds text markup, in Page._add_text_marker).
* Things with a direction (a signature, a highlight) were laid along the page
  as stored, so on a page turned a quarter they showed sideways, or ran 57
  points past the box the visitor drew. They now follow the page as shown.

Sign PDF and Edit PDF draw with reportlab on a page of their own and lay it
over the PDF page with pikepdf, which keeps it upright as the page is shown.
They take boxes in points from the bottom-left corner of the page as shown.
Their overlay was the size of the MediaBox as stored and was fitted into the
TrimBox, so on a page turned a quarter, or cut by a CropBox, everything
shrank and moved. `shown_area` gives the overlay the size of the page as shown
and the place it is shown in.

backend/tests/test_page_contract.py checks every tool on turned and cropped
pages.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import fitz  # PyMuPDF
import pikepdf


@contextmanager
def drawing_unturned(page: fitz.Page) -> Iterator[int]:
    """Draw on `page` as stored, whatever its /Rotate; yields the rotation.

    Everything drawn inside uses the page's stored coordinates (the routes'
    convention). The page's /Rotate is restored afterwards, so the page shows
    exactly as before.
    """
    rotation = page.rotation
    if rotation:
        page.set_rotation(0)
    try:
        yield rotation
    finally:
        if rotation:
            page.set_rotation(rotation)


def upright_quad(page: fitz.Page, rect: fitz.Rect) -> fitz.Quad:
    """`rect` (stored coordinates) as a quad whose top edge is the top of the
    box as the page is shown, so text markup runs across the page as shown.
    Call it with the page at its own /Rotate."""
    shown = fitz.Rect(rect) * page.rotation_matrix
    return shown.quad * page.derotation_matrix


def shown_area(page: pikepdf.Page) -> tuple[pikepdf.Rectangle, float, float]:
    """Where and how big `page` is shown: its visible area (CropBox within
    MediaBox, in PDF units) and that area's width and height as shown, after
    /Rotate and /UserUnit, the way pdf.js measures it.

    An overlay page of that size laid on that area with `add_overlay(rect=)`
    maps 1:1 onto the page as shown, because pikepdf turns and scales it back
    by the page's /Rotate and /UserUnit.
    """
    media = pikepdf.Rectangle(page.mediabox)
    crop = pikepdf.Rectangle(page.cropbox)
    area = pikepdf.Rectangle(
        max(media.llx, crop.llx), max(media.lly, crop.lly),
        min(media.urx, crop.urx), min(media.ury, crop.ury),
    )
    if area.width <= 0 or area.height <= 0:
        area = media
    unit = float(page.obj.get(pikepdf.Name.UserUnit, 1) or 1)
    width, height = area.width * unit, area.height * unit
    if page.rotation in (90, 270):
        width, height = height, width
    return area, width, height
