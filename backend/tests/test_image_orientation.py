"""Rotate and Flip Image turn a phone photo the way the phone shows it.

Phones and cameras often store a photo sideways and record the turn that
shows it upright in the EXIF Orientation tag. The saved copy carries no EXIF,
so the tag has to be applied to the pixels before the user's rotation or
flip; otherwise the result comes out on its side or upside down. Found in
the copy review of #186.

The photos are four solid quadrants, so every expected result is written out
by hand. Upright, the picture is 120 wide and 160 tall: red top-left, green
top-right, blue bottom-left and yellow bottom-right ("RG/BY").
"""

from __future__ import annotations

import io
import struct

import pytest
from PIL import ExifTags, Image, ImageCms
from PIL.TiffImagePlugin import IFDRational

COLOURS = {"R": (220, 30, 30), "G": (30, 180, 30), "B": (30, 30, 220), "Y": (240, 220, 20)}

# The pixels a phone stores for the upright RG/BY picture: sideways, 160×120.
#   6: the stored top row is the picture's right edge, read downwards.
#   8: the stored top row is the picture's left edge, read upwards.
STORED = {6: "GY/RB", 8: "BR/YG"}

SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def _paint(layout: str, size: tuple[int, int], mode: str = "RGB") -> Image.Image:
    """Draw a picture from a layout such as "RG/BY" (top row / bottom row)."""
    width, height = size
    image = Image.new("RGB", size)
    for row, names in enumerate(layout.split("/")):
        for col, name in enumerate(names):
            box = (col * width // 2, row * height // 2, (col + 1) * width // 2, (row + 1) * height // 2)
            image.paste(COLOURS[name], box)
    return image.convert(mode)


def _layout(image: Image.Image) -> str:
    """Read the quadrant layout back from a result."""
    rgb = image.convert("RGB")
    width, height = rgb.size

    def colour(x: int, y: int) -> str:
        pixel = rgb.getpixel((x, y))
        return min(COLOURS, key=lambda name: sum((a - b) ** 2 for a, b in zip(COLOURS[name], pixel)))

    top = colour(width // 4, height // 4) + colour(3 * width // 4, height // 4)
    bottom = colour(width // 4, 3 * height // 4) + colour(3 * width // 4, 3 * height // 4)
    return f"{top}/{bottom}"


def _phone_photo(orientation: int, fmt: str = "JPEG", **save) -> bytes:
    """A sideways-stored photo with the metadata a phone writes."""
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = orientation
    exif[ExifTags.Base.Make] = "Apple"
    exif[ExifTags.Base.Model] = "iPhone 15"
    exif.get_ifd(ExifTags.IFD.Exif)[ExifTags.Base.DateTimeOriginal] = "2026:09:01 10:11:12"
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSLatitudeRef] = "N"
    gps[ExifTags.GPS.GPSLatitude] = (IFDRational(51, 1), IFDRational(30, 1), IFDRational(0, 1))
    buf = io.BytesIO()
    save.setdefault("quality", 95)
    _paint(STORED[orientation], (160, 120)).save(buf, fmt, exif=exif, **save)
    return buf.getvalue()


def _run(client, endpoint: str, filename: str, data: bytes, fields: dict[str, str]) -> Image.Image:
    resp = client.post(endpoint, files={"file": (filename, data, "application/octet-stream")}, data=fields)
    assert resp.status_code == 200, resp.text[:300]
    return Image.open(io.BytesIO(resp.content))


@pytest.mark.parametrize("orientation", [6, 8])
@pytest.mark.parametrize(
    ("endpoint", "fields", "size", "layout"),
    [
        ("/api/rotate-image", {"degrees": "0"}, (120, 160), "RG/BY"),  # "Original": upright
        ("/api/rotate-image", {"degrees": "90"}, (160, 120), "GY/RB"),  # 90° left
        ("/api/rotate-image", {"degrees": "270"}, (160, 120), "BR/YG"),  # 90° right
        ("/api/rotate-image", {"degrees": "180"}, (120, 160), "YB/GR"),
        ("/api/flip-image", {"direction": "horizontal"}, (120, 160), "GR/YB"),
        ("/api/flip-image", {"direction": "vertical"}, (120, 160), "BY/RG"),
    ],
)
def test_rotation_and_flip_start_from_the_upright_photo(client, orientation, endpoint, fields, size, layout):
    out = _run(client, endpoint, "IMG_0001.jpg", _phone_photo(orientation), fields)

    assert (out.size, _layout(out)) == (size, layout)
    # The turn is in the pixels, so no viewer may apply the tag a second time.
    assert out.getexif().get(ExifTags.Base.Orientation) is None


def test_free_angle_rotation_starts_from_the_upright_photo(client):
    out = _run(client, "/api/rotate-image", "IMG_0001.jpg", _phone_photo(6), {"degrees": "30"})

    # Turned 30°, the 120×160 portrait needs a canvas taller than it is wide;
    # the sideways 160×120 pixels would need a wider one.
    assert out.height > out.width


@pytest.mark.parametrize(("filename", "fmt"), [("IMG.jpg", "JPEG"), ("IMG.png", "PNG"), ("IMG.webp", "WEBP")])
@pytest.mark.parametrize(
    ("endpoint", "fields"),
    [("/api/rotate-image", {"degrees": "90"}), ("/api/flip-image", {"direction": "horizontal"})],
)
def test_saved_copy_keeps_the_colour_profile_and_drops_exif(client, filename, fmt, endpoint, fields):
    xmp = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF><exif:GPSLatitude>51,30N</exif:GPSLatitude></rdf:RDF></x:xmpmeta>'
    photo = _phone_photo(6, fmt, icc_profile=SRGB, xmp=xmp, comment=b"Taken at 12 Oak Street")

    out = _run(client, endpoint, filename, photo, fields)

    assert out.format == fmt
    assert out.info.get("icc_profile") == SRGB
    # No camera, capture time or location, and no orientation tag.
    assert "exif" not in out.info
    assert not out.getexif()
    # XMP and a JPEG comment describe the photo too.
    assert "xmp" not in out.info
    assert "comment" not in out.info


@pytest.mark.parametrize(
    ("orientation", "endpoint", "fields", "dpi"),
    [
        (1, "/api/rotate-image", {"degrees": "90"}, (150, 300)),
        (1, "/api/rotate-image", {"degrees": "180"}, (300, 150)),
        (6, "/api/rotate-image", {"degrees": "0"}, (150, 300)),
        (6, "/api/rotate-image", {"degrees": "90"}, (300, 150)),
        (6, "/api/flip-image", {"direction": "vertical"}, (150, 300)),
    ],
)
@pytest.mark.parametrize(("filename", "fmt"), [("scan.jpg", "JPEG"), ("scan.png", "PNG")])
def test_saved_copy_keeps_the_dpi_across_quarter_turns(client, orientation, endpoint, fields, dpi, filename, fmt):
    if orientation == 1:
        buf = io.BytesIO()
        _paint("RG/BY", (120, 160)).save(buf, fmt, dpi=(300, 150))
        data = buf.getvalue()
    else:
        data = _phone_photo(orientation, fmt, dpi=(300, 150))

    out = _run(client, endpoint, filename, data, fields)

    # PNG stores pixels per metre, so 300 dpi reads back as 299.9994.
    assert tuple(round(value) for value in out.info.get("dpi", ())) == dpi


def test_a_dpi_no_format_can_store_is_dropped(client):
    # A hand-built big-endian EXIF block whose XResolution is an infinite
    # DOUBLE; with no density in the JFIF header, Pillow takes the DPI from it.
    value = 8 + 2 + 2 * 12 + 4
    block = (
        b"MM\x00\x2a" + struct.pack(">IH", 8, 2)
        + struct.pack(">HHII", ExifTags.Base.XResolution, 12, 1, value)
        + struct.pack(">HHIHH", ExifTags.Base.ResolutionUnit, 3, 1, 2, 0)
        + struct.pack(">I", 0) + struct.pack(">d", float("inf"))
    )
    buf = io.BytesIO()
    _paint("RG/BY", (120, 160)).save(buf, "JPEG", exif=b"Exif\x00\x00" + block)
    assert Image.open(io.BytesIO(buf.getvalue())).info["dpi"] == (float("inf"), float("inf"))

    out = _run(client, "/api/rotate-image", "scan.jpg", buf.getvalue(), {"degrees": "90"})

    assert (out.size, _layout(out)) == ((160, 120), "GY/RB")
    assert "dpi" not in out.info


def test_a_profile_for_other_colours_is_not_attached_to_rgb_output(client):
    # A greyscale PNG with a greyscale profile comes back as RGB, which a
    # GRAY profile cannot describe. Only the 128-byte header matters here.
    gray_profile = bytearray(132)
    gray_profile[0:4] = len(gray_profile).to_bytes(4, "big")
    gray_profile[12:16] = b"mntr"
    gray_profile[16:20] = b"GRAY"
    gray_profile[20:24] = b"XYZ "
    gray_profile[36:40] = b"acsp"
    buf = io.BytesIO()
    _paint("RG/BY", (120, 160), mode="L").save(buf, "PNG", icc_profile=bytes(gray_profile))

    out = _run(client, "/api/rotate-image", "grey.png", buf.getvalue(), {"degrees": "90"})

    assert out.mode == "RGB"
    assert "icc_profile" not in out.info


@pytest.mark.parametrize(("filename", "fmt"), [("screenshot.png", "PNG"), ("sticker.webp", "WEBP")])
def test_unreadable_exif_leaves_the_pixels_as_stored(client, filename, fmt):
    # Pillow cannot parse this EXIF block and raises SyntaxError reading it.
    buf = io.BytesIO()
    _paint("RG/BY", (120, 160)).save(buf, fmt, exif=b"Exif\x00\x00not a TIFF header")

    out = _run(client, "/api/rotate-image", filename, buf.getvalue(), {"degrees": "0"})

    assert (out.size, _layout(out)) == ((120, 160), "RG/BY")
