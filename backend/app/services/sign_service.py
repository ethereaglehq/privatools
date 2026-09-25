import base64
import io

import pikepdf
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from ..utils.cleanup import safe_open_pdf
from ..utils.filenames import temp_output
from ..utils.page_space import settle_rotation, shown_area


def sign_pdf(
    input_path: str,
    signature_path: str,
    page: int = 1,
    x: float = 50,
    y: float = 50,
    width: float = 200,
    height: float = 80,
) -> str:
    """Place the signature image at x, y (its bottom-left corner), in points
    from the bottom-left corner of the page as it is shown: its visible area
    (CropBox), after /Rotate. The signature stays upright as shown."""
    output_path = temp_output("signed", "pdf")

    with safe_open_pdf(input_path) as pdf:
        page_count = len(pdf.pages)
        page_idx = max(0, min(page - 1, page_count - 1))
        target_page = pikepdf.Page(pdf.pages[page_idx])

        # An overlay the size of the page as shown, laid on the visible area:
        # pikepdf turns it with the page, so it maps 1:1 (utils/page_space.py).
        # pikepdf only turns it for /Rotate written 90, 180 or 270, so the
        # page's /Rotate is written that way first.
        settle_rotation(target_page)
        area, shown_width, shown_height = shown_area(target_page)

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(shown_width, shown_height))
        c.drawImage(ImageReader(signature_path), x, y, width=width, height=height, mask="auto")
        c.save()
        packet.seek(0)

        overlay_pdf = pikepdf.Pdf.open(packet)
        overlay_page = overlay_pdf.pages[0]
        target_page.add_overlay(overlay_page, rect=area)

        pdf.save(str(output_path))

    return str(output_path)


def decode_base64_signature(data_url: str) -> str:
    """Decode a base64 data URL and save as a temporary PNG file."""
    if data_url.startswith("data:"):
        _header, encoded = data_url.split(",", 1)
    else:
        encoded = data_url
    image_bytes = base64.b64decode(encoded)
    sig_path = temp_output("sig", "png")
    sig_path.write_bytes(image_bytes)
    return str(sig_path)
