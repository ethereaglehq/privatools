"""View EXIF Data lists the camera settings a photo carries.

Exposure time, aperture, ISO, the lens and the original capture time are
stored in the Exif sub-IFD, which Pillow's getexif() leaves out unless it is
read with get_ifd(0x8769). The viewer listed only IFD0 and GPS, so none of
them appeared (found in the copy review of #186).
"""

from __future__ import annotations

import io
import re

import pytest
from PIL import ExifTags, Image, ImageCms
from PIL.TiffImagePlugin import IFDRational

# Vendor data is binary; these bytes are not valid UTF-8.
MAKER_NOTE = b"Nikon\x00\x02\x10\x00\x00II*\x00\x08\x00\x00\x00\xff\xfe\x80\x81"
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
XMP = b'<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta xmlns:x="adobe:ns:meta/"/>'


def _camera_photo(exposure: IFDRational = IFDRational(1, 160), comment: bytes = b"\x00" * 16) -> bytes:
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = "Canon"
    exif[ExifTags.Base.Model] = "Canon EOS 40D"
    # Windows writes its XP fields as UTF-16LE.
    exif[ExifTags.Base.XPAuthor] = "José".encode("utf-16-le") + b"\x00\x00"
    camera = exif.get_ifd(ExifTags.IFD.Exif)
    camera[ExifTags.Base.ExposureTime] = exposure
    camera[ExifTags.Base.FNumber] = IFDRational(71, 10)
    camera[ExifTags.Base.ISOSpeedRatings] = 100
    camera[ExifTags.Base.LensModel] = "EF-S17-85mm f/4-5.6 IS USM"
    camera[ExifTags.Base.DateTimeOriginal] = "2008:05:30 15:56:01"
    camera[ExifTags.Base.MakerNote] = MAKER_NOTE
    camera[ExifTags.Base.ComponentsConfiguration] = b"\x01\x02\x03\x00"
    # An 8-byte character code, then the text.
    camera[ExifTags.Base.UserComment] = comment
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSVersionID] = b"\x02\x02\x00\x00"
    gps[ExifTags.GPS.GPSLatitudeRef] = "N"
    gps[ExifTags.GPS.GPSLatitude] = (IFDRational(51, 1), IFDRational(30, 1), IFDRational(0, 1))
    gps[ExifTags.GPS.GPSProcessingMethod] = b"ASCII\x00\x00\x00GPS"
    # An unused text field, NUL-padded as a Nikon COOLPIX writes it.
    gps[ExifTags.GPS.GPSImgDirectionRef] = "\x00"
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (90, 120, 150)).save(buf, "JPEG", exif=exif, icc_profile=SRGB, xmp=XMP)
    return buf.getvalue()


def _view(client, filename: str, data: bytes) -> dict:
    resp = client.post("/api/view-exif", files={"file": (filename, data, "application/octet-stream")})
    assert resp.status_code == 200, resp.text[:300]
    return resp.json()


def test_lists_exposure_aperture_iso_lens_and_capture_time(client):
    body = _view(client, "IMG_0001.jpg", _camera_photo())

    exif = body["exif"]
    assert exif["ExposureTime"] == "1/160"
    assert exif["FNumber"] == "7.1"
    assert exif["ISOSpeedRatings"] == 100
    assert exif["LensModel"] == "EF-S17-85mm f/4-5.6 IS USM"
    assert exif["DateTimeOriginal"] == "2008:05:30 15:56:01"
    # IFD0 and GPS are still listed alongside.
    assert (exif["Make"], exif["Model"]) == ("Canon", "Canon EOS 40D")
    assert body["gps"]["GPSLatitudeRef"] == "N"


def test_lists_no_offsets_or_undecoded_binary(client):
    body = _view(client, "IMG_0001.jpg", _camera_photo())

    # ExifOffset and GPSInfo are byte offsets to the blocks listed in full.
    assert "ExifOffset" not in body["exif"]
    assert "GPSInfo" not in body["exif"]
    # Binary reads as hex when short and as its size otherwise.
    assert body["exif"]["ComponentsConfiguration"] == "01 02 03 00"
    assert body["gps"]["GPSVersionID"] == "02 02 00 00"
    assert body["gps"]["GPSImgDirectionRef"] == ""
    assert body["exif"]["MakerNote"] == f"<{len(MAKER_NOTE)} bytes>"
    assert body["info"]["icc_profile"] == f"<{len(SRGB)} bytes>"
    # The raw EXIF block is what the exif and gps groups decode.
    assert "exif" not in body["info"]
    values = [v for group in ("exif", "gps", "info") for v in body[group].values() if isinstance(v, str)]
    assert not [v for v in values if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", v)]


@pytest.mark.parametrize(
    ("comment", "shown"),
    [
        (b"ASCII\x00\x00\x00Hello from the beach", "Hello from the beach"),
        (b"UNICODE\x00" + "Olá".encode("utf-16-be"), "Olá"),
        (b"ASCII\x00\x00\x00" + b" " * 24, ""),  # an unused comment, padded
        (b"\x00" * 264, ""),
    ],
)
def test_text_fields_read_as_text(client, comment, shown):
    body = _view(client, "IMG_0001.jpg", _camera_photo(comment=comment))

    assert body["exif"]["UserComment"] == shown
    assert body["exif"]["XPAuthor"] == "José"
    assert body["gps"]["GPSProcessingMethod"] == "GPS"
    assert body["info"]["xmp"] == XMP.decode("utf-8")


@pytest.mark.parametrize(
    ("exposure", "shown"),
    [
        (IFDRational(1, 160), "1/160"),
        (IFDRational(10, 1250), "1/125"),
        (IFDRational(1, 4), "1/4"),
        (IFDRational(1, 2), "0.5"),
        (IFDRational(13, 10), "1.3"),
        (IFDRational(30, 1), "30"),
    ],
)
def test_exposure_time_reads_as_photographers_write_it(client, exposure, shown):
    body = _view(client, "IMG_0001.jpg", _camera_photo(exposure))

    assert body["exif"]["ExposureTime"] == shown


def test_unreadable_exif_still_returns_the_rest(client):
    # Pillow cannot parse this EXIF block and raises SyntaxError reading it.
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (90, 120, 150)).save(buf, "PNG", exif=b"Exif\x00\x00not a TIFF header")

    body = _view(client, "screenshot.png", buf.getvalue())

    assert (body["format"], body["size"], body["exif"], body["gps"]) == ("PNG", [64, 48], {}, {})
