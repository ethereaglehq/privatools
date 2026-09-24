"""Images → single PDF, written to disk one page at a time.

Pages appear in the same order they were supplied (the route hands us
`input_paths` in upload order — FastAPI's `List[UploadFile]` preserves
multipart order, and we iterate that list directly without sorting).
Pillow opens only the formats the nine tools take, whatever a file is called.
Each image is checked against its pixel cap before any decoding, so a "1 GB
pixel bomb" upload fails fast, and the batch against `MAX_DECODED_MEGAPIXELS`
before any page is made; an SVG is measured without being drawn.

Each image goes into the PDF file as soon as it is read, so memory follows
one page, not the whole document. ReportLab, which this service used before,
keeps every page in memory until it formats the whole file on save, at about
three times the finished PDF: 100 web-size WebPs took +1.6 GB. The images are
embedded as ReportLab embedded them: a JPEG's compressed picture unchanged
(DCTDecode); anything else decoded to 8-bit Gray, RGB or CMYK the way ReportLab's
ImageReader converted it (alpha dropped, other modes to RGB) and deflated at
zlib's default level (FlateDecode). Two differences: a 16-bit grayscale image
keeps each sample's high byte, where ReportLab clipped it nearly white; and
a JPEG whose coding DCTDecode does not read (lossless or arithmetic) is
decoded like the rest, where ReportLab drew a placeholder.

And two things ReportLab did not do. A photo is drawn upright, as its EXIF
Orientation says (the turn Rotate and Flip Image apply), by the page matrix
rather than by decoding it. And no metadata reaches the PDF: a JPEG keeps
only what a decoder needs, so its EXIF (GPS position, camera, serial
numbers, times), XMP, IPTC, comments and thumbnails are dropped, and every
other format contributes pixels only.

Refusals are `ImageRefused` errors naming the file as it was uploaded:
`ImageTooLarge` and `DecodeBudgetExceeded` (413), `UnreadableImage` (400).
"""
from __future__ import annotations

import io
import logging
import math
import os
import re
import time
import uuid
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator

from PIL import ExifTags, Image, UnidentifiedImageError

from ..utils.cleanup import ensure_temp_dir, get_temp_path
from .svg_safety import ExternalReferenceBlocked, block_external_refs

logger = logging.getLogger(__name__)

_SVG_EXTS = {".svg"}

# What the nine tools take, by content, whatever a file is called: Pillow can
# decode more (JPEG 2000, AVIF and others), outside every cap below, and did
# under these tools' extensions; a 36-megapixel JPEG 2000 of 540 KB took
# +667 MB. Pillow's JPEG opener returns MPO for a multi-picture JPEG, so MPO
# has no entry of its own. SVGs go by their extension to cairosvg instead.
_OPEN_FORMATS = ("JPEG", "PNG", "GIF", "BMP", "TIFF", "WEBP", "HEIF")
_ACCEPTED = "JPEG, PNG, WebP, HEIC, TIFF, BMP or GIF"
_HEIF_BRANDS = (b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"hevm", b"hevs", b"mif1", b"msf1")

# Page sizes in PDF points, as ReportLab defines them.
A4 = (595.2755905511812, 841.8897637795277)
LETTER = (612.0, 792.0)
PAGE_SIZES = {
    "A4": A4,
    "Letter": LETTER,
    "auto": "auto",  # sentinel — handled specially in images_to_pdf
}
MARGIN = 36  # 0.5 inch around the image on an A4 or Letter page

# The most pixels one image may have. Pillow refuses to open anything over
# twice its `Image.MAX_IMAGE_PIXELS` as a possible decompression bomb, and
# `app/utils/__init__.py` leaves that at Pillow's default, so Pillow's limit
# is 178,956,970 pixels. This cap sits just under it, so a refusal can state
# the limit exactly. A 16K frame (15360 x 8640) is 133 megapixels.
MAX_IMAGE_PIXELS = 178_000_000

# Lower caps where decoding one image costs more memory. Peak bytes per pixel
# of one page, measured on the 2-core ARM VM: Pillow's WebP decoder 17-19, a
# HEIC photo 9, a compressed colour TIFF up to 8, PNG and BMP about 5. Each cap
# keeps a page under about 1 GB; PNG, BMP, GIF and rendered SVGs stay under
# that at Pillow's limit, and a JPEG is not decoded at all. Pillow holds
# 1-bit, grayscale and palette images at one byte per pixel, so such a TIFF
# (1.4-2.4 bytes per pixel) keeps Pillow's limit too.
FORMAT_PIXEL_CAPS = {
    "WEBP": ("a WebP image", 50_000_000),
    "HEIF": ("a HEIC photo", 100_000_000),
    "TIFF": ("a colour TIFF", 120_000_000),
}
_ONE_BYTE_MODES = {"1", "L", "P"}

# How many megapixels one PDF may decode. A JPEG is embedded as it is and
# costs almost nothing; every other image is decoded (a rare JPEG too, see
# _DCT_FRAMES) or drawn (an SVG), which costs CPU in
# proportion to its pixels. Measured on the 2-core ARM VM: about 0.14 s per
# megapixel to decode and deflate a photo in PNG, WebP, TIFF, BMP, GIF or SVG,
# and about 0.075 s to decode a HEIC photo and re-encode it as JPEG, so a HEIC
# megapixel counts half. 750 keeps any request under about 115 s of CPU. It
# fits 100 iPhone photos (610 at half weight) or 100 phone screenshots (300);
# 100 phone-size WebPs (1,219) do not fit.
MAX_DECODED_MEGAPIXELS = 750
HEIC_MEGAPIXEL_WEIGHT = 0.5

_DECODED_FORMATS = "PNG, WebP, TIFF, BMP, GIF and SVG images"
_BAND_BYTES = 4 * 1024 * 1024  # decoded rows deflated per step
_COLOUR_SPACES = {"L": b"/DeviceGray", "RGB": b"/DeviceRGB", "CMYK": b"/DeviceCMYK"}
# The JPEG codings DCTDecode reads, embedded as they are: baseline, extended
# and progressive DCT with Huffman coding. Lossless (SOF3), arithmetic-coded
# and hierarchical JPEGs are decoded instead and count in the budget: MuPDF
# drew a lossless JPEG black ("Unsupported JPEG process"), and ReportLab put
# its placeholder in the image's place.
_DCT_FRAMES = {0xC0, 0xC1, 0xC2}
_OTHER_FRAMES = {0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}

# An SVG is drawn 2,400 pixels wide, its height following its aspect ratio,
# unless that is taller than cairo can draw: then it is drawn that tall and
# narrower.
_SVG_WIDTH = 2400
_SVG_MAX_SIDE = 32_767


class ImageRefused(ValueError):
    """An upload this service will not convert; the message names it for the person who sent it."""


class ImageTooLarge(ImageRefused):
    """One image has more pixels than it may (413)."""


class DecodeBudgetExceeded(ImageRefused):
    """A batch would decode more megapixels than one PDF may (413)."""


class UnreadableImage(ImageRefused):
    """A file that is not an image these tools take, or cannot be read or drawn (400)."""


class _ImageChanged(OSError):
    """A file changed on disk between planning its page and writing it: the server's fault."""


@dataclass
class _Source:
    path: str  # the upload; an SVG is drawn when its page is made
    name: str  # what it was called when it was uploaded
    width: int  # pixels as embedded: an SVG's as it will be drawn
    height: int
    kind: str  # "jpeg" (its picture copied as it is), "heic", "svg" or "decoded"
    mode: str  # Pillow's mode for the file
    format: str  # Pillow's format, or "SVG"
    orientation: int = 1  # EXIF Orientation: how the stored pixels turn to show upright
    # For a JPEG: what is copied into the PDF (ranges of the file, and headers
    # rewritten without their extras), found when the batch is planned, and
    # the file's size then.
    parts: tuple[tuple[int, int] | bytes, ...] = ()
    file_size: int = 0

    @property
    def upright_size(self) -> tuple[int, int]:
        """Width and height as shown: orientations 5 to 8 turn the picture a quarter."""
        return (self.height, self.width) if self.orientation >= 5 else (self.width, self.height)


def _fetch_for_svg(url: str, resource_type: str | None = None) -> bytes:
    # block_external_refs denies absolute file:// (LFI) and http(s):// (SSRF)
    # references; only inline data: URIs are drawn.
    return block_external_refs(url, resource_type)["string"]


class _SvgSize(Exception):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.width, self.height = width, height


@lru_cache(maxsize=1)
def _measuring_surface():
    from cairosvg.surface import PNGSurface

    class MeasuringSurface(PNGSurface):
        # cairosvg works out the drawing's size from its width, height and
        # viewBox, then asks for a surface that size: stop there, before any
        # pixel is allocated or drawn.
        def _create_surface(self, width, height):
            raise _SvgSize(int(round(width)), int(round(height)))

    return MeasuringSurface


def _svg_error(name: str, exc: BaseException) -> UnreadableImage:
    if isinstance(exc, ExternalReferenceBlocked):
        return UnreadableImage(f"{name} loads an image from another file or a web address, which is not allowed.")
    return UnreadableImage(f"{name} could not be drawn.")


def _svg_size(path: str, name: str) -> tuple[int, int]:
    """The size an SVG will be drawn at, in pixels, without drawing it."""
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        # bytestring= (not url=), so relative references can't resolve
        # against the server's files.
        _measuring_surface().convert(bytestring=data, output_width=_SVG_WIDTH, url_fetcher=_fetch_for_svg)
    except _SvgSize as size:
        width, height = size.width, size.height
    except ExternalReferenceBlocked as exc:
        raise _svg_error(name, exc) from None
    except MemoryError:
        raise
    except Exception:
        raise UnreadableImage(f"{name} could not be drawn: it is not a valid SVG.") from None
    else:  # cairosvg asks for its surface before it draws anything
        raise UnreadableImage(f"{name} could not be drawn.")
    if width <= 0 or height <= 0:
        raise UnreadableImage(f"{name} could not be drawn: it has no width or height.")
    if height > _SVG_MAX_SIDE:
        width, height = max(1, round(width * _SVG_MAX_SIDE / height)), _SVG_MAX_SIDE
    return width, height


def _svg_to_png(svg_path: str, out_path: str, width: int, height: int) -> None:
    """Draw an SVG at width x height pixels into a PNG file via cairosvg."""
    from cairosvg.surface import PNGSurface

    with open(svg_path, "rb") as f:
        svg_data = f.read()
    PNGSurface.convert(bytestring=svg_data, write_to=out_path, output_width=width, output_height=height,
                       url_fetcher=_fetch_for_svg)


def _pixel_cap() -> int:
    """The most pixels any image may have: MAX_IMAGE_PIXELS, or Pillow's limit if lower."""
    pillow = Image.MAX_IMAGE_PIXELS
    return MAX_IMAGE_PIXELS if pillow is None else min(MAX_IMAGE_PIXELS, 2 * pillow)


def _megapixels(pixels: int) -> str:
    """Pixels in megapixels, rounded up to a tenth, so a size just over a cap never reads as within it."""
    return f"{math.ceil(pixels / 100_000) / 10:,.1f}".removesuffix(".0")


def _is_server_fault(exc: BaseException) -> bool:
    # Pillow's decoding errors carry no errno; a real I/O error (a missing
    # file, a full disk) does, and is the server's to answer for.
    if isinstance(exc, (MemoryError, _ImageChanged)):
        return True
    return isinstance(exc, OSError) and exc.errno is not None


def _signed_as_ours(path: str) -> bool:
    """Whether a file starts the way one of the accepted formats does, so a
    file Pillow can't open is a damaged image rather than something else."""
    with open(path, "rb") as fh:
        head = fh.read(12)
    return (head.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"BM",
                             b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"))
            or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
            or (head[4:8] == b"ftyp" and head[8:12] in _HEIF_BRANDS))


def _orientation(img: Image.Image) -> int:
    """The EXIF Orientation: the turn Rotate and Flip Image apply with
    ImageOps.exif_transpose.

    Read as Image.getexif reads it (EXIF or XMP), but from the header only:
    PngImageFile.getexif decodes the pixels to look for EXIF after them.
    Pillow turns a TIFF itself as it decodes it (and reports the turned size),
    and pillow-heif has already applied a HEIC photo's turn, so those are
    drawn as they come. EXIF that can't be read means no turn: one odd file
    must not fail the batch.
    """
    if img.format == "TIFF":
        return 1
    try:
        value = Image.Image.getexif(img).get(ExifTags.Base.Orientation, 1)
        return int(value) if value in _PLACEMENT else 1
    except Exception:  # noqa: BLE001 - Pillow raises many kinds for broken EXIF
        return 1


def _source(path: str, name: str) -> _Source:
    """Size and kind of one upload, read without decoding it.

    Enforces the per-image pixel cap so callers can fail fast before any
    decoding work runs.
    """
    if os.path.splitext(path)[1].lower() in _SVG_EXTS:
        width, height = _svg_size(path, name)
        return _Source(path, name, width, height, "svg", "RGBA", "SVG")
    cap = _pixel_cap()
    try:
        with Image.open(path, formats=_OPEN_FORMATS) as img:
            (w, h), image_format, mode = img.size, img.format, img.mode
            orientation = _orientation(img)
    except Image.DecompressionBombError:
        raise ImageTooLarge(f"{name} has more than {cap // 1_000_000:,} megapixels, the most one image can have.") from None
    except UnidentifiedImageError:
        if _signed_as_ours(path):
            raise UnreadableImage(f"{name} could not be read as an image.") from None
        raise UnreadableImage(f"{name} is not a {_ACCEPTED} image.") from None
    except Exception as exc:
        if _is_server_fault(exc):
            raise
        raise UnreadableImage(f"{name} could not be read as an image.") from None
    noun, format_cap = FORMAT_PIXEL_CAPS.get(image_format, ("one image", cap))
    if image_format == "TIFF" and mode in _ONE_BYTE_MODES:
        noun, format_cap = "one image", cap
    if format_cap > cap:
        noun, format_cap = "one image", cap
    if w * h > format_cap:
        raise ImageTooLarge(
            f"{name} is {w:,} × {h:,} pixels, which is {_megapixels(w * h)} megapixels; "
            f"{noun} can have at most {format_cap // 1_000_000:,} megapixels."
        )
    if image_format == "HEIF":
        return _Source(path, name, w, h, "heic", mode, image_format, orientation)
    if image_format in ("JPEG", "MPO") and mode in _COLOUR_SPACES:
        data = Path(path).read_bytes()
        parts = _jpeg_parts(data)
        if parts is not None:
            return _Source(path, name, w, h, "jpeg", mode, image_format, orientation, parts, len(data))
    # Including a JPEG that can't be embedded as it is: its pixels are
    # embedded instead, so its metadata can't come along.
    return _Source(path, name, w, h, "decoded", mode, image_format, orientation)


def _check_decode_budget(sources: list[_Source]) -> None:
    decoded = [s for s in sources if s.kind in ("decoded", "svg")]
    heic = [s for s in sources if s.kind == "heic"]
    decoded_megapixels = sum(s.width * s.height for s in decoded) / 1e6
    heic_megapixels = sum(s.width * s.height for s in heic) / 1e6
    total = decoded_megapixels + heic_megapixels * HEIC_MEGAPIXEL_WEIGHT
    if total <= MAX_DECODED_MEGAPIXELS:
        return
    # Rounded up, so a batch just over the limit never reads as within it.
    if not decoded:
        raise DecodeBudgetExceeded(
            f"One PDF can take up to {MAX_DECODED_MEGAPIXELS / HEIC_MEGAPIXEL_WEIGHT:,.0f} megapixels "
            f"of HEIC photos; these add up to {math.ceil(heic_megapixels):,}.")
    jpegs = sum(s.format in ("JPEG", "MPO") for s in decoded)
    if jpegs:
        what = "images that have to be decoded"
    elif heic:
        what = "images other than JPEG"
    else:
        what = _DECODED_FORMATS
    counting = ", with HEIC photos counting half" if heic else ""
    message = (f"One PDF can take up to {MAX_DECODED_MEGAPIXELS:,} megapixels of {what}{counting}; "
               f"these add up to {math.ceil(total):,}.")
    if jpegs:
        message += (" That includes a JPEG that can't be copied into the PDF as it is." if jpegs == 1 else
                    f" That includes {jpegs} JPEGs that can't be copied into the PDF as they are.")
    raise DecodeBudgetExceeded(message)


# The page matrix that draws an image upright in the box (x, y, w, h), for
# each EXIF Orientation. PDF draws an image in the unit square with its first
# stored row at the top; these map that square onto the box and turn or
# mirror it as ImageOps.exif_transpose would turn the pixels, so the picture
# is shown upright without decoding it.
_PLACEMENT = {
    1: lambda x, y, w, h: (w, 0, 0, h, x, y),
    2: lambda x, y, w, h: (-w, 0, 0, h, x + w, y),
    3: lambda x, y, w, h: (-w, 0, 0, -h, x + w, y + h),
    4: lambda x, y, w, h: (w, 0, 0, -h, x, y + h),
    5: lambda x, y, w, h: (0, -h, -w, 0, x + w, y + h),
    6: lambda x, y, w, h: (0, -h, w, 0, x, y + h),
    7: lambda x, y, w, h: (0, h, w, 0, x, y),
    8: lambda x, y, w, h: (0, h, -w, 0, x + w, y),
}

# What of a JPEG is copied into the PDF: an allow-list of what a decoder
# needs. The frame (one DCT coding DCTDecode reads, see _DCT_FRAMES), the
# Huffman and quantization tables, the restart interval, a DNL and the scans
# are copied as they are, each table checked to hold exactly the tables it
# declares. JFIF's header is rewritten without its thumbnail, Adobe's
# colour-transform marker (which CMYK and some RGB JPEGs need) without any
# extra bytes, and the ICC profile's segments are copied. Every other APPn
# segment (EXIF, which holds GPS, camera, serial numbers and times; XMP; IPTC
# in APP13; JFXX thumbnails; vendor notes) and comments are dropped, and
# nothing after the first picture's end is kept (a multi-picture file's other
# pictures carry EXIF of their own, a motion photo a video). Any other marker,
# a table that doesn't add up, or no picture at all, and the JPEG is decoded
# instead.
_ENTROPY_END = re.compile(rb"\xff[^\x00\xd0-\xd7\xff]")
_TABLES = {0xC4, 0xDB}  # DHT, DQT


def _tables_fit(marker: int, payload: bytes) -> bool:
    """Whether a DHT or DQT segment holds exactly the tables it declares."""
    at = 0
    while at < len(payload):
        if marker == 0xDB:  # precision and id, then 64 values of one or two bytes
            if payload[at] >> 4 > 1:
                return False
            at += 1 + (128 if payload[at] >> 4 else 64)
        else:  # class and id, 16 code counts, then the symbols
            if at + 17 > len(payload):
                return False
            at += 17 + sum(payload[at + 1:at + 17])
    return 0 < at == len(payload)


def _jpeg_parts(data: bytes) -> tuple[tuple[int, int] | bytes, ...] | None:
    """What of a JPEG goes into the PDF (see above), or None if it can't be
    embedded as it is."""
    if not data.startswith(b"\xff\xd8"):
        return None
    parts: list[tuple[int, int] | bytes] = [(0, 2)]
    framed = scanned = False
    pos, end = 2, len(data)

    def keep(start: int, stop: int) -> None:
        last = parts[-1]
        if isinstance(last, tuple) and last[1] == start:
            parts[-1] = (last[0], stop)
        else:
            parts.append((start, stop))

    while pos < end:
        if data[pos] != 0xFF:
            return None
        while pos < end and data[pos] == 0xFF:  # fill bytes
            pos += 1
        if pos >= end:
            return None
        marker = data[pos]
        pos += 1
        # From here on, data[pos - 2:pos] is 0xFF and the marker.
        if marker == 0xD9:  # EOI: the first picture ends here
            if not scanned:
                return None  # tables and no picture
            keep(pos - 2, pos)
            return tuple(parts)
        if pos + 2 > end or not 0xC0 <= marker <= 0xFE:
            return None  # TEM or a reserved marker
        length = int.from_bytes(data[pos:pos + 2], "big")
        body = pos + 2  # the segment's payload runs from body to pos + length
        if length < 2 or pos + length > end:
            return None
        if marker in _DCT_FRAMES:
            if framed or length < 11 or length != 8 + 3 * data[body + 5]:
                return None
            framed = True
            keep(pos - 2, pos + length)
        elif marker in _TABLES:
            if not _tables_fit(marker, data[body:pos + length]):
                return None
            keep(pos - 2, pos + length)
        elif marker in (0xDD, 0xDC):  # DRI, DNL
            if length != 4:
                return None
            keep(pos - 2, pos + length)
        elif marker == 0xDA:  # SOS: the compressed scan runs to the next marker
            if not framed or length < 8 or length != 6 + 2 * data[body] or data[body] > 4:
                return None
            scanned = True
            found = _ENTROPY_END.search(data, pos + length)
            pos = found.start() if found else end
            keep(body - 4, pos)
            continue
        elif marker == 0xE0:  # APP0: JFIF's header only, without a thumbnail
            if data.startswith(b"JFIF\x00", body) and length >= 16:
                parts.append(b"\xff\xe0\x00\x10" + data[body:body + 12] + b"\x00\x00")
        elif marker == 0xE2:  # APP2: the ICC colour profile only
            if data.startswith(b"ICC_PROFILE\x00", body):
                keep(pos - 2, pos + length)
        elif marker == 0xEE:  # APP14: Adobe's colour transform, without extras
            if data.startswith(b"Adobe", body) and length >= 14:
                parts.append(b"\xff\xee\x00\x0e" + data[body:body + 12])
        elif not (0xE0 <= marker <= 0xEF or marker == 0xFE):
            # Not something a DCT decoder needs, nor metadata to drop: another
            # coding's frame or tables, a restart marker outside a scan...
            return None
        pos += length
    # A file cut short in its last scan: keep what there is.
    return tuple(parts) if scanned else None


def _number(value: float) -> bytes:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return (text if text not in ("", "-0") else "0").encode()


def _image_dict(width: int, height: int, mode: str, filter_name: bytes) -> bytes:
    entries = b"/Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s /BitsPerComponent 8 /Filter %s" % (
        width, height, _COLOUR_SPACES[mode], filter_name)
    if mode == "CMYK" and filter_name == b"/DCTDecode":
        # ReportLab treated every 4-channel JPEG as Adobe's inverted CMYK.
        entries += b" /Decode [1 0 1 0 1 0 1 0]"
    return entries


def _sixteen_bit(mode: str) -> bool:
    # Pillow holds 16-bit grayscale as I;16 (I;16B, I;16L...), and some 16-bit
    # data, signed TIFF samples among it, as 32-bit I.
    return mode.startswith("I;16") or mode == "I"


def _deflated_rows(img: Image.Image, mode: str) -> Iterator[bytes]:
    """The image's pixels in `mode`, deflated a band of rows at a time."""
    try:
        width, height = img.size
        rows = max(1, _BAND_BYTES // (width * len(mode)))
        # A palette with a transparent entry goes through RGBA, as ReportLab
        # did for PNGs: the same colours, without Pillow's warning.
        via = "RGBA" if img.mode in ("P", "PA") and "transparency" in img.info else None
        compressor = zlib.compressobj()  # zlib's default level, as ReportLab used
        for top in range(0, height, rows):
            band = img.crop((0, top, width, min(height, top + rows)))
            if via:
                band = band.convert(via)
            if _sixteen_bit(band.mode):
                # Each sample's high byte, as Pillow reduces a 16-bit colour
                # PNG. Converting I;16 straight to 8 bits clips every sample
                # over 255, which left all but the darkest 0.4% white.
                band = band.convert("I").point(lambda value: value * (1 / 256))
            if band.mode != mode:
                band = band.convert(mode)
            if out := compressor.compress(band.tobytes()):
                yield out
        yield compressor.flush()
    finally:
        img.close()


def _image_stream(source: _Source, temp_files: list[str]) -> tuple[bytes, int | None, Iterable[bytes]]:
    """(image dictionary entries, length if known, data) for one page."""
    if source.kind == "jpeg":
        data = memoryview(Path(source.path).read_bytes())
        if len(data) != source.file_size:
            raise _ImageChanged(f"{source.name} changed while it was being read")
        chunks = [data[part[0]:part[1]] if isinstance(part, tuple) else part for part in source.parts]
        return _image_dict(source.width, source.height, source.mode, b"/DCTDecode"), sum(map(len, chunks)), chunks
    if source.kind == "svg":
        path = str(get_temp_path(f"svg_to_png_{uuid.uuid4().hex}.png"))
        temp_files.append(path)
        _svg_to_png(source.path, path, source.width, source.height)
        img = Image.open(path, formats=("PNG",))
    else:
        img = Image.open(source.path, formats=_OPEN_FORMATS)
    if img.size != (source.width, source.height):
        img.close()
        raise _ImageChanged(f"{source.name} changed while it was being read")
    if source.kind == "heic":
        # PDF has no HEVC filter: decode and embed a JPEG, as before.
        buffer = io.BytesIO()
        with img:
            (img if img.mode == "RGB" else img.convert("RGB")).save(buffer, "JPEG", quality=92)
        data = buffer.getvalue()
        return _image_dict(source.width, source.height, "RGB", b"/DCTDecode"), len(data), [data]
    # ReportLab's ImageReader.getRGBData conversions: alpha dropped, every mode
    # other than L, RGB and CMYK converted to RGB; 16-bit grayscale is gray.
    if _sixteen_bit(img.mode):
        mode = "L"
    elif img.mode in ("LA", "RGBA"):
        mode = img.mode[:-1]
    else:
        mode = img.mode if img.mode in _COLOUR_SPACES else "RGB"
    return _image_dict(source.width, source.height, mode, b"/FlateDecode"), None, _deflated_rows(img, mode)


def _remove(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _unreadable(source: _Source, exc: BaseException) -> UnreadableImage:
    if source.kind == "svg":
        return _svg_error(source.name, exc)
    return UnreadableImage(f"{source.name} could not be read as an image.")


def _page_image(source: _Source, temp_files: list[str]) -> tuple[bytes, int | None, Iterable[bytes]]:
    """The page's image stream. A file that fails to read or draw, now or
    while its rows are deflated, is refused by its name."""
    try:
        entries, length, chunks = _image_stream(source, temp_files)
    except Exception as exc:
        if _is_server_fault(exc):
            raise
        raise _unreadable(source, exc) from exc

    def reading() -> Iterator[bytes]:
        try:
            yield from chunks
        except Exception as exc:
            if _is_server_fault(exc):
                raise
            raise _unreadable(source, exc) from exc

    return entries, length, reading()


class _PdfWriter:
    """A PDF of one image per page, written to a file as each page is added."""

    def __init__(self, fh: BinaryIO) -> None:
        self._fh = fh
        self._offsets: list[int] = []
        fh.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        self._pages = self._reserve()
        self._kids: list[int] = []

    def _reserve(self) -> int:
        self._offsets.append(0)
        return len(self._offsets)

    def _begin(self, number: int) -> None:
        self._offsets[number - 1] = self._fh.tell()
        self._fh.write(b"%d 0 obj\n" % number)

    def _object(self, number: int, body: bytes) -> None:
        self._begin(number)
        self._fh.write(body + b"\nendobj\n")

    def _stream(self, number: int, entries: bytes, length: int | None, chunks: Iterable[bytes]) -> None:
        # An unknown length (a stream deflated as it is written) is given as an
        # indirect object written after the stream.
        length_ref = self._reserve() if length is None else None
        self._begin(number)
        self._fh.write(b"<<%s /Length %s>>\nstream\n" % (entries, b"%d 0 R" % length_ref if length_ref else b"%d" % length))
        start = self._fh.tell()
        for chunk in chunks:
            self._fh.write(chunk)
        written = self._fh.tell() - start
        if length is not None and written != length:
            raise _ImageChanged("an image changed while it was being read")
        self._fh.write(b"\nendstream\nendobj\n")
        if length_ref:
            self._object(length_ref, b"%d" % written)

    def add_page(self, page_size: tuple[float, float], stream, box: tuple[float, float, float, float] | None,
                 orientation: int = 1) -> None:
        page_ref = self._reserve()
        resources = b"<<>>"
        content = b""
        if stream is not None:
            image_ref, content_ref = self._reserve(), self._reserve()
            self._stream(image_ref, *stream)
            matrix = b" ".join(_number(value) for value in _PLACEMENT[orientation](*box))
            content = b"q %s cm /Im0 Do Q\n" % matrix
            self._stream(content_ref, b"", len(content), [content])
            resources = b"<</XObject <</Im0 %d 0 R>> /ProcSet [/PDF /ImageB /ImageC /ImageI]>>" % image_ref
        self._object(page_ref, b"<</Type /Page /Parent %d 0 R /MediaBox [0 0 %s %s] /Resources %s%s>>" % (
            self._pages, _number(page_size[0]), _number(page_size[1]), resources,
            b" /Contents %d 0 R" % content_ref if content else b""))
        self._kids.append(page_ref)

    def close(self) -> None:
        kids = b" ".join(b"%d 0 R" % kid for kid in self._kids)
        self._object(self._pages, b"<</Type /Pages /Kids [%s] /Count %d>>" % (kids, len(self._kids)))
        catalog, info = self._reserve(), self._reserve()
        self._object(catalog, b"<</Type /Catalog /Pages %d 0 R>>" % self._pages)
        stamp = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%S+00'00'").encode()
        self._object(info, b"<</Producer (PrivaTools) /CreationDate (%s) /ModDate (%s)>>" % (stamp, stamp))
        xref = self._fh.tell()
        self._fh.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(self._offsets) + 1))
        self._fh.write(b"".join(b"%010d 00000 n \n" % offset for offset in self._offsets))
        file_id = uuid.uuid4().hex.encode()
        self._fh.write(b"trailer\n<</Size %d /Root %d 0 R /Info %d 0 R /ID [<%s> <%s>]>>\nstartxref\n%d\n%%%%EOF\n" % (
            len(self._offsets) + 1, catalog, info, file_id, file_id, xref))


def images_to_pdf(input_paths: list, page_size: str = "A4", names: list[str] | None = None) -> str:
    """One PDF page per image, in order. `names` are the files' names as
    uploaded, for refusals; they default to the paths' own."""
    ensure_temp_dir()
    names = [os.path.basename(p) for p in input_paths] if names is None else list(names)
    if len(names) != len(input_paths):
        raise TypeError("images_to_pdf needs one name per path")
    started = time.monotonic()
    total_input_bytes = 0
    for p in input_paths:
        try:
            total_input_bytes += os.path.getsize(p)
        except OSError:
            pass
    logger.info(
        "image_to_pdf: start images=%d page_size=%s total_input_bytes=%d",
        len(input_paths), page_size, total_input_bytes,
    )

    output_path = get_temp_path(f"images_to_pdf_{uuid.uuid4().hex}.pdf")
    # "auto": each page matches its source image's pixel dimensions (treating
    # 1 px = 1 PDF point, which gives a 72 DPI document at original scale).
    auto = page_size == "auto"
    fixed_size = None if auto else PAGE_SIZES.get(page_size, A4)
    if fixed_size == "auto":  # paranoia
        fixed_size = A4

    # Drawn SVGs, each deleted once its page is written, and even on error.
    intermediates: list[str] = []
    try:
        # Every size is known, and the batch checked, before any image is
        # decoded or drawn.
        sources = [_source(path, name) for path, name in zip(input_paths, names)]
        _check_decode_budget(sources)
        with open(output_path, "wb") as fh:
            writer = _PdfWriter(fh)
            for source in sources:
                shown_width, shown_height = source.upright_size
                if auto:
                    page = (shown_width, shown_height)
                    box = (0, 0, shown_width, shown_height)
                else:
                    page = fixed_size
                    page_width, page_height = fixed_size
                    ratio = min((page_width - 2 * MARGIN) / shown_width, (page_height - 2 * MARGIN) / shown_height)
                    width, height = shown_width * ratio, shown_height * ratio
                    box = ((page_width - width) / 2, (page_height - height) / 2, width, height)
                writer.add_page(page, _page_image(source, intermediates), box, source.orientation)
                while intermediates:
                    _remove(intermediates.pop())
            if not sources:
                # Empty input — write a minimal blank A4 PDF rather than crash.
                writer.add_page(A4, None, None)
            writer.close()
    except BaseException:
        try:
            os.unlink(output_path)
        except OSError:
            pass
        raise
    finally:
        for p in intermediates:
            _remove(p)

    duration_ms = int((time.monotonic() - started) * 1000)
    try:
        out_size = os.path.getsize(output_path)
    except OSError:
        out_size = 0
    logger.info(
        "image_to_pdf: done images=%d duration_ms=%d output_bytes=%d",
        len(input_paths), duration_ms, out_size,
    )
    return str(output_path)
