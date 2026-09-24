"""Image to PDF puts phone photos upright and leaves their metadata out.

A phone stores a portrait photo sideways and records the turn that shows it
upright in the EXIF Orientation tag, which Rotate and Flip Image already apply
(`ImageOps.exif_transpose`). Image to PDF embedded JPEGs byte for byte, so such
a photo came out on its side, and its EXIF, GPS position included, went into
the PDF with it. HEIC to PDF already dropped both, by re-encoding.

The pictures are four solid quadrants, so every expected layout is written by
hand: upright, 120 wide and 160 tall, red top-left, green top-right, blue
bottom-left and yellow bottom-right ("RG/BY").
"""
from __future__ import annotations

import io
import struct
import zlib
from pathlib import Path

import pikepdf
import pillow_heif
import pymupdf
import pytest
from PIL import ExifTags, Image, ImageCms, ImageOps
from PIL.TiffImagePlugin import IFDRational

from backend.app.services import image_to_pdf_service

pillow_heif.register_heif_opener()

COLOURS = {"R": (220, 30, 30), "G": (30, 180, 30), "B": (30, 30, 220), "Y": (240, 220, 20)}
UPRIGHT = "RG/BY"
# The transpose that turns the upright picture into what the camera stores,
# for each EXIF Orientation: the inverse of what exif_transpose applies.
STORE = {
    1: None,
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_90,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_270,
}
SECRETS = (b"SecretCam", b"Model-X9", b"2026:09:01 10:11:12", b"SecretXMP", b"SecretIPTC", b"SecretComment", b"SecretArtist")
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    return tmp_path


def _upright(size=(120, 160)) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size)
    for row, names in enumerate(UPRIGHT.split("/")):
        for col, name in enumerate(names):
            image.paste(COLOURS[name], (col * width // 2, row * height // 2, (col + 1) * width // 2, (row + 1) * height // 2))
    return image


def _exif(orientation: int) -> Image.Exif:
    """The metadata a phone writes: orientation, make, model, time and GPS position."""
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = orientation
    exif[ExifTags.Base.Make] = "SecretCam"
    exif[ExifTags.Base.Model] = "Model-X9"
    exif.get_ifd(ExifTags.IFD.Exif)[ExifTags.Base.DateTimeOriginal] = "2026:09:01 10:11:12"
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSLatitudeRef] = "N"
    gps[ExifTags.GPS.GPSLatitude] = (IFDRational(51, 1), IFDRational(30, 1), IFDRational(7, 1))
    gps[ExifTags.GPS.GPSLongitudeRef] = "W"
    gps[ExifTags.GPS.GPSLongitude] = (IFDRational(0, 1), IFDRational(7, 1), IFDRational(39, 1))
    return exif


def _segment(marker: int, payload: bytes) -> bytes:
    return bytes((0xFF, marker)) + struct.pack(">H", len(payload) + 2) + payload


def _phone_jpeg(path: Path, orientation: int, progressive: bool = False) -> bytes:
    """A stored photo with EXIF, an sRGB profile, XMP, IPTC and a comment."""
    stored = _upright()
    if STORE[orientation] is not None:
        stored = stored.transpose(STORE[orientation])
    buffer = io.BytesIO()
    stored.save(buffer, "JPEG", quality=95, exif=_exif(orientation), icc_profile=SRGB, progressive=progressive)
    data = buffer.getvalue()
    xmp = b"http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta><rdf:Description exif:GPSLatitude='51,30N' dc:creator='SecretXMP'/></x:xmpmeta>"
    iptc = b"Photoshop 3.0\x008BIM\x04\x04\x00\x00" + struct.pack(">I", 16) + b"\x1c\x02\x50\x00\x0aSecretIPTC\x00"
    extra = _segment(0xE1, xmp) + _segment(0xED, iptc) + _segment(0xFE, b"SecretComment")
    data = data[:2] + extra + data[2:]
    path.write_bytes(data)
    return data


def _layout(image: Image.Image) -> str:
    rgb = image.convert("RGB")
    width, height = rgb.size

    def colour(x: int, y: int) -> str:
        pixel = rgb.getpixel((x, y))
        return min(COLOURS, key=lambda name: sum((a - b) ** 2 for a, b in zip(COLOURS[name], pixel)))

    return (colour(width // 4, height // 4) + colour(3 * width // 4, height // 4) + "/"
            + colour(width // 4, 3 * height // 4) + colour(3 * width // 4, 3 * height // 4))


def _rendered(pdf_path) -> tuple[tuple[float, float], Image.Image]:
    """The first page's size and its image as drawn (the page cropped to the picture)."""
    with pymupdf.open(pdf_path) as document:
        page = document[0]
        (rect,) = [page.get_image_rects(xref)[0] for xref, *_ in page.get_images()]
        pix = page.get_pixmap(dpi=144, clip=rect, alpha=False)
        return (page.rect.width, page.rect.height), Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _embedded_jpeg(pdf_path) -> bytes:
    with pikepdf.open(pdf_path) as pdf:
        (image,) = pdf.pages[0].get_images().values()
        return image.read_raw_bytes()


@pytest.mark.parametrize("page_size", ["auto", "A4"])
@pytest.mark.parametrize("orientation", [1, 2, 3, 4, 5, 6, 7, 8])
def test_a_phone_jpeg_is_placed_upright(temp_dir, orientation, page_size):
    source = temp_dir / f"IMG_000{orientation}.jpg"
    _phone_jpeg(source, orientation)
    # The layout Rotate Image and Flip Image produce from the same file.
    with Image.open(source) as original:
        assert _layout(ImageOps.exif_transpose(original)) == UPRIGHT

    output = image_to_pdf_service.images_to_pdf([str(source)], page_size)

    page, drawn = _rendered(output)
    assert _layout(drawn) == UPRIGHT
    assert drawn.width < drawn.height  # portrait, as shown on the phone
    if page_size == "auto":
        assert page == pytest.approx((120, 160))


@pytest.mark.parametrize("fmt, name", [("PNG", "shot.png"), ("WEBP", "photo.webp"), ("TIFF", "scan.tiff")])
def test_other_formats_follow_their_orientation_tag_too(temp_dir, fmt, name):
    source = temp_dir / name
    _upright().transpose(STORE[6]).save(source, fmt, exif=_exif(6))

    page, drawn = _rendered(image_to_pdf_service.images_to_pdf([str(source)], "auto"))

    assert _layout(drawn) == UPRIGHT
    assert page == pytest.approx((120, 160))


def test_reading_the_orientation_does_not_decode_a_png(temp_dir, monkeypatch):
    # PngImageFile.getexif decodes the whole image to look for EXIF after the
    # pixels; the budget is checked before anything is decoded.
    source = temp_dir / "shot.png"
    _upright().save(source, "PNG")
    loaded = []
    load = Image.Image.load
    monkeypatch.setattr(Image.Image, "load", lambda self: loaded.append(self.format) or load(self))
    monkeypatch.setattr(image_to_pdf_service, "_check_decode_budget", lambda sources: pytest.fail(str(loaded)) if loaded else None)

    image_to_pdf_service.images_to_pdf([str(source)], "auto")


@pytest.mark.parametrize("orientation", [3, 6, 8])
def test_the_jpeg_is_not_reencoded_to_turn_it(temp_dir, orientation):
    source = temp_dir / "IMG_0001.jpg"
    original = _phone_jpeg(source, orientation)

    embedded = _embedded_jpeg(image_to_pdf_service.images_to_pdf([str(source)], "auto"))

    # The same compressed picture: identical pixels, and only metadata removed.
    with Image.open(io.BytesIO(embedded)) as kept, Image.open(io.BytesIO(original)) as sent:
        assert kept.tobytes() == sent.tobytes()
    assert len(embedded) < len(original)
    assert embedded.endswith(original[original.index(b"\xff\xda"):])  # every scan, byte for byte


def test_a_jpeg_loses_its_location_camera_and_notes_but_keeps_its_icc_segment(temp_dir):
    source = temp_dir / "IMG_0006.jpg"
    _phone_jpeg(source, 6)

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    pdf_bytes = Path(output).read_bytes()
    for secret in SECRETS + (b"Exif\x00\x00", b"http://ns.adobe.com/xap/1.0/", b"Photoshop 3.0"):
        assert secret not in pdf_bytes, secret
    with Image.open(io.BytesIO(_embedded_jpeg(output))) as embedded:
        assert dict(embedded.getexif()) == {}
        assert embedded.info.get("icc_profile") == SRGB
        assert "jfif" in embedded.info  # the JFIF header stays


def test_nothing_after_the_first_picture_comes_along(temp_dir):
    # A multi-picture file's other pictures carry EXIF of their own, and a
    # motion photo appends a video: both follow the first picture's end.
    source = temp_dir / "MVIMG_0001.jpg"
    first = _phone_jpeg(temp_dir / "first.jpg", 1)
    source.write_bytes(first + b"\x00\x00ftypmp42 SecretTrailer" + first)

    pdf_bytes = Path(image_to_pdf_service.images_to_pdf([str(source)], "auto")).read_bytes()

    assert b"SecretTrailer" not in pdf_bytes
    assert all(secret not in pdf_bytes for secret in SECRETS)


def _stray_bytes_before_tables(data: bytes) -> bytes:
    at = data.index(b"\xff\xdb")
    return data[:at] + b"\x00junk" + data[at:]


def _stray_bytes_between_scans(data: bytes) -> bytes:
    # After the Huffman tables that follow the first scan: inside a scan they
    # would only lengthen it.
    tables = data.index(b"\xff\xc4", data.index(b"\xff\xda"))
    at = tables + 2 + int.from_bytes(data[tables + 2:tables + 4], "big")
    return data[:at] + b"\x00junk" + data[at:]


@pytest.mark.parametrize("progressive, damage", [
    (False, _stray_bytes_before_tables), (True, _stray_bytes_between_scans),
])
def test_a_jpeg_whose_segments_cannot_be_read_is_embedded_as_pixels(temp_dir, progressive, damage):
    # Pillow still decodes it (libjpeg skips stray bytes with a warning), but
    # its metadata can't be told apart from its picture, so the pixels go in
    # instead and count in the decode budget. The whole file is read when the
    # batch is planned, so a file that breaks after its first scan is no
    # different.
    source = temp_dir / "odd.jpg"
    source.write_bytes(damage(_phone_jpeg(temp_dir / "sent.jpg", 1, progressive)))
    with Image.open(source) as odd:
        odd.load()

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    with pikepdf.open(output) as pdf:
        (image,) = pdf.pages[0].get_images().values()
        assert str(image.Filter) == "/FlateDecode"
    assert all(secret not in _decoded_streams(output) for secret in SECRETS)


def _jpeg_segments(jpeg: bytes) -> list[bytes]:
    """Each marker segment up to the first scan, as its marker and payload."""
    segments, pos = [], 2
    while jpeg[pos + 1] != 0xDA:
        length = int.from_bytes(jpeg[pos + 2:pos + 4], "big")
        segments.append(jpeg[pos:pos + 2 + length])
        pos += 2 + length
    return segments


def _with_segments(jpeg: bytes, *segments: bytes) -> bytes:
    """The JPEG with these segments put straight after its JFIF header."""
    at = 4 + int.from_bytes(jpeg[4:6], "big") if jpeg[2:4] == b"\xff\xe0" else 2
    return jpeg[:at] + b"".join(segments) + jpeg[at:]


def test_a_jfif_thumbnail_and_a_jfxx_thumbnail_are_left_out(temp_dir):
    # JFIF's header may carry a thumbnail; the JFXX extension carries one too.
    buffer = io.BytesIO()
    _upright().save(buffer, "JPEG", quality=95, exif=_exif(1))
    photo = buffer.getvalue()
    assert photo[2:4] == b"\xff\xe0"  # Pillow's JFIF header, replaced below
    jfif = _segment(0xE0, b"JFIF\x00\x01\x02\x01\x00\x48\x00\x48" + bytes((8, 1)) + b"SecretThumbPixels1234567")
    jfxx = _segment(0xE0, b"JFXX\x00\x13" + bytes((8, 1)) + b"SecretJfxxPixels12345678")
    source = temp_dir / "IMG_0001.jpg"
    source.write_bytes(photo[:2] + jfif + jfxx + photo[4 + int.from_bytes(photo[4:6], "big"):])

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    pdf_bytes = Path(output).read_bytes()
    assert b"SecretThumb" not in pdf_bytes and b"SecretJfxx" not in pdf_bytes
    app0 = [segment for segment in _jpeg_segments(_embedded_jpeg(output)) if segment[1] == 0xE0]
    assert app0 == [b"\xff\xe0\x00\x10JFIF\x00\x01\x02\x01\x00\x48\x00\x48\x00\x00"]  # no thumbnail


def test_adobes_marker_keeps_its_colour_transform_and_nothing_else(temp_dir):
    buffer = io.BytesIO()
    _upright().convert("CMYK").save(buffer, "JPEG", quality=95)
    cmyk = buffer.getvalue()
    (adobe,) = [segment for segment in _jpeg_segments(cmyk) if segment[1] == 0xEE]
    payload = adobe[4:] + b"SecretTail"
    source = temp_dir / "print.jpg"
    source.write_bytes(cmyk.replace(adobe, _segment(0xEE, payload)))

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    embedded = _embedded_jpeg(output)
    assert b"SecretTail" not in Path(output).read_bytes()
    assert [segment for segment in _jpeg_segments(embedded) if segment[1] == 0xEE] == [adobe]
    with Image.open(io.BytesIO(embedded)) as kept, Image.open(io.BytesIO(cmyk)) as sent:
        assert kept.tobytes() == sent.tobytes()


@pytest.mark.parametrize("segment", [
    _segment(0xF0, b"SecretMarkerData"), _segment(0xC8, b"SecretMarkerData"),
    _segment(0xDE, b"SecretMarkerData"), _segment(0x02, b"SecretMarkerData"), b"\xff\x01",
], ids=["JPG0", "JPG", "DHP", "reserved", "TEM"])
def test_a_jpeg_with_a_marker_no_dct_decoder_takes_is_not_copied(temp_dir, segment):
    # Such a segment was copied into the PDF, data and all, and the picture
    # could not be drawn: libjpeg refuses these markers, and so does Pillow.
    # Only what a decoder needs is copied now; the file is decoded instead,
    # which fails, and the refusal names it.
    photo = _phone_jpeg(temp_dir / "sent.jpg", 1)
    source = temp_dir / "odd.jpg"
    source.write_bytes(_with_segments(photo, segment))

    with pytest.raises(image_to_pdf_service.UnreadableImage, match="^odd.jpg could not be read as an image.$"):
        image_to_pdf_service.images_to_pdf([str(source)], "auto")
    assert not list(temp_dir.glob("images_to_pdf_*.pdf"))


def test_tables_with_no_picture_before_the_picture_do_not_make_a_blank_page(temp_dir):
    # An end-of-image marker before any scan used to end the copy there: the
    # PDF held the tables and no picture, and showed a blank page.
    photo = _phone_jpeg(temp_dir / "sent.jpg", 1)
    tables_only = photo[:photo.index(b"\xff\xc0")] + b"\xff\xd9"
    source = temp_dir / "odd.jpg"
    source.write_bytes(tables_only + photo)

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    page, drawn = _rendered(output)
    assert _layout(drawn) == UPRIGHT


def _bad_tiff_header() -> bytes:
    """Where an EXIF block's TIFF header belongs, something else."""
    return b"ZZ\x00\x2a\x00\x00\x00\x08"


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def _png_with_chunk(chunk: bytes) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (30, 30, 200)).save(buffer, "PNG")
    data = buffer.getvalue()
    at = data.index(b"IDAT") - 4
    return data[:at] + chunk + data[at:]


def _jpeg_with_bad_exif() -> bytes:
    # With its resolution in the JFIF header, Pillow doesn't read the EXIF on
    # opening (where it would swallow the error), so getexif() raises.
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (200, 30, 30)).save(buffer, "JPEG", quality=90, dpi=(300, 300))
    return _with_segments(buffer.getvalue(), _segment(0xE1, b"Exif\x00\x00" + _bad_tiff_header()))


def _webp_with_bad_exif() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (30, 200, 30)).save(buffer, "WEBP", exif=b"Exif\x00\x00" + _bad_tiff_header())
    return buffer.getvalue()


@pytest.mark.parametrize("name, data", [
    ("photo.jpg", _jpeg_with_bad_exif()),
    ("shot.png", _png_with_chunk(_chunk(b"eXIf", _bad_tiff_header()))),
    ("photo.webp", _webp_with_bad_exif()),
    # ImageMagick's hex-encoded EXIF, with text that is not hex.
    ("shot.png", _png_with_chunk(_chunk(b"tEXt", b"Raw profile type exif\x00\nexif\n   20\nZZZZ-not-hex\n"))),
], ids=["JPEG APP1", "PNG eXIf", "WebP EXIF", "PNG raw profile"])
def test_an_image_whose_exif_cannot_be_read_is_placed_as_it_is_stored(temp_dir, name, data):
    # Reading its orientation used to fail the whole batch: a 500, or a 413
    # carrying Pillow's "non-hexadecimal number found in fromhex()".
    source = temp_dir / name
    source.write_bytes(data)
    with Image.open(source) as opened, pytest.raises(Exception):
        Image.Image.getexif(opened)  # the EXIF really can't be read

    page, drawn = _rendered(image_to_pdf_service.images_to_pdf([str(source)], "auto"))

    assert page == pytest.approx((64, 48))  # as stored, not turned


def test_a_jpeg_that_changes_after_planning_is_refused(temp_dir, monkeypatch):
    # What is copied was decided from the file as it was planned; a file that
    # is not the same size any more is not copied by those ranges.
    source = temp_dir / "IMG_0001.jpg"
    _phone_jpeg(source, 1)
    monkeypatch.setattr(image_to_pdf_service, "_check_decode_budget",
                        lambda sources: source.write_bytes(source.read_bytes() + b"more"))

    with pytest.raises(OSError, match="changed"):
        image_to_pdf_service.images_to_pdf([str(source)], "auto")
    assert not list(temp_dir.glob("images_to_pdf_*.pdf"))


def _decoded_streams(pdf_path) -> bytes:
    """Every stream in the PDF, decoded as far as qpdf can, joined."""
    parts = [Path(pdf_path).read_bytes()]
    with pikepdf.open(pdf_path) as pdf:
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Stream):
                try:
                    parts.append(obj.read_bytes())
                except pikepdf.PdfError:
                    parts.append(obj.read_raw_bytes())
    return b"".join(parts)


def _png_with_text(path: Path) -> None:
    from PIL.PngImagePlugin import PngInfo

    info = PngInfo()
    info.add_text("Comment", "SecretComment")
    info.add_itxt("XML:com.adobe.xmp", "<x:xmpmeta dc:creator='SecretXMP'/>")
    info.add_text("Author", "SecretArtist", zip=True)
    _upright().save(path, "PNG", pnginfo=info, exif=_exif(1))


def _webp_with_exif(path: Path) -> None:
    _upright().save(path, "WEBP", exif=_exif(1), xmp=b"<x:xmpmeta dc:creator='SecretXMP'/>", quality=90)


def _tiff_with_tags(path: Path) -> None:
    exif = _exif(1)
    exif[ExifTags.Base.Artist] = "SecretArtist"
    _upright().save(path, "TIFF", exif=exif)


def _heic_with_exif(path: Path) -> None:
    _upright().save(path, "HEIF", exif=_exif(1), xmp=b"<x:xmpmeta dc:creator='SecretXMP'/>", quality=80)


@pytest.mark.parametrize("name, write", [
    ("notes.png", _png_with_text), ("photo.webp", _webp_with_exif),
    ("scan.tiff", _tiff_with_tags), ("IMG_0001.heic", _heic_with_exif),
])
def test_no_other_format_carries_its_metadata_into_the_pdf(temp_dir, name, write):
    source = temp_dir / name
    write(source)
    with open(source, "rb") as fh:
        assert any(secret in fh.read() for secret in SECRETS), "the fixture must carry metadata"

    streams = _decoded_streams(image_to_pdf_service.images_to_pdf([str(source)], "auto"))

    for secret in SECRETS:
        assert secret not in streams, (name, secret)


IMAGE_TO_PDF_TOOLS = (
    "image-to-pdf", "jpg-to-pdf", "png-to-pdf", "heic-to-pdf", "webp-to-pdf",
    "tiff-to-pdf", "bmp-to-pdf", "gif-to-pdf", "svg-to-pdf",
)


def test_the_jpg_guide_promises_only_what_the_pdf_does():
    from backend.app.tool_content import TOOL_HOWTO

    guide = " ".join(step["text"] for step in TOOL_HOWTO["jpg-to-pdf"])
    # The ICC segment stays inside the JPEG, but the image is DeviceRGB, as it
    # was with ReportLab, so viewers don't apply the profile.
    assert "profile is kept" not in guide
    # A JPEG that can't be copied as it is goes in as pixels.
    assert "without re-encoding" in guide and "decoded pixels" in guide


def test_all_nine_tools_say_the_metadata_is_left_out():
    from backend.app.tool_content import TOOL_HOWTO

    registry = (Path(__file__).resolve().parents[2] / "frontend/src/data/tools.ts").read_text()
    for slug in IMAGE_TO_PDF_TOOLS:
        entry = registry.split(f'slug: "{slug}"', 1)[1].split("slug:", 1)[0]
        guide = " ".join(step["text"] for step in TOOL_HOWTO[slug])
        for text in (entry.lower(), guide.lower()):
            assert "location" in text or "metadata" in text, (slug, text[:200])
