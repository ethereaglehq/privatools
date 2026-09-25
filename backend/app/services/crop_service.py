from decimal import Decimal

import pikepdf

from ..utils.cleanup import safe_open_pdf
from ..utils.filenames import temp_output
from ..utils.page_space import settle_rotation, shown_area


def _stored_margins(rotation: int, top: float, right: float, bottom: float, left: float) -> tuple[float, float, float, float]:
    """Margins given for the page as shown, as (top, right, bottom, left) of
    the page as stored. /Rotate turns the stored page clockwise for showing:
    at 90 its left edge is shown at the top."""
    if rotation == 90:
        return right, bottom, left, top
    if rotation == 180:
        return bottom, left, top, right
    if rotation == 270:
        return left, top, right, bottom
    return top, right, bottom, left


def crop_pdf(
    input_path: str,
    top: float = 0.0,
    bottom: float = 0.0,
    left: float = 0.0,
    right: float = 0.0,
    margins_from: str = "mediabox",
) -> str:
    """Set every page's CropBox inside the given margins, in points.

    margins_from="mediabox" (the default, and the API's behaviour from the
    start) trims each margin from that edge of the MediaBox as stored, before
    any /Rotate, and replaces whatever CropBox the page had.

    margins_from="shown" trims each margin from the edge a reader sees on that
    side: from the page's visible area (its CropBox within the MediaBox), after
    /Rotate (read as pdf.js reads it) and /UserUnit, as pdf.js shows it. The
    website's Crop page sends this, because its visitor draws the area to keep
    on that picture.
    """
    output_path = temp_output("cropped", "pdf")

    with safe_open_pdf(input_path) as pdf:
        for page in pdf.pages:
            if margins_from == "shown":
                page = pikepdf.Page(page)
                rotation = settle_rotation(page)
                area, _, _ = shown_area(page)
                unit = float(page.obj.get(pikepdf.Name.UserUnit, 1) or 1)
                s_top, s_right, s_bottom, s_left = (
                    value / unit for value in _stored_margins(rotation, top, right, bottom, left)
                )
                box = (area.llx + s_left, area.lly + s_bottom, area.urx - s_right, area.ury - s_top)
                page.obj["/CropBox"] = pikepdf.Array([Decimal(str(round(value, 6))) for value in box])
                continue

            mediabox = page.mediabox
            x0 = float(mediabox[0])
            y0 = float(mediabox[1])
            x1 = float(mediabox[2])
            y1 = float(mediabox[3])

            new_x0 = x0 + left
            new_y0 = y0 + bottom
            new_x1 = x1 - right
            new_y1 = y1 - top

            page["/CropBox"] = pikepdf.Array([
                Decimal(str(new_x0)),
                Decimal(str(new_y0)),
                Decimal(str(new_x1)),
                Decimal(str(new_y1)),
            ])

        pdf.save(str(output_path))

    return str(output_path)
