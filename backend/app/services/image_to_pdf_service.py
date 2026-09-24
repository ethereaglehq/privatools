"""Images → single PDF, written to disk one page at a time.

Pages appear in the same order they were supplied (the route hands us
`input_paths` in upload order — FastAPI's `List[UploadFile]` preserves
multipart order, and we iterate that list directly without sorting).
Each image is checked against the per-image pixel cap (`MAX_IMAGE_PIXELS`,
or Pillow's lower decompression-bomb limit) before any decoding, so a "1 GB
pixel bomb" upload fails fast, and a batch is checked against
`MAX_DECODED_MEGAPIXELS` before any page is made.

Each image goes into the PDF file as soon as it is read, so memory follows
one page, not the whole document. ReportLab, which this service used before,
keeps every page in memory until it formats the whole file on save, at about
three times the finished PDF: 100 web-size WebPs took +1.6 GB. The images are
embedded exactly as ReportLab embedded them: a JPEG byte for byte
(DCTDecode); anything else decoded to 8-bit Gray, RGB or CMYK the way
ReportLab's ImageReader converted it (alpha dropped, other modes to RGB) and
deflated at zlib's default level (FlateDecode).
"""
from __future__ import annotations

import io
import logging
import math
import os
import time
import uuid
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import BinaryIO, Iterable, Iterator

from PIL import Image

from ..utils.cleanup import ensure_temp_dir, get_temp_path

logger = logging.getLogger(__name__)

_HEIC_EXTS = {".heic", ".heif"}
_SVG_EXTS = {".svg"}

# Page sizes in PDF points, as ReportLab defines them.
A4 = (595.2755905511812, 841.8897637795277)
LETTER = (612.0, 792.0)
PAGE_SIZES = {
    "A4": A4,
    "Letter": LETTER,
    "auto": "auto",  # sentinel — handled specially in images_to_pdf
}
MARGIN = 36  # 0.5 inch around the image on an A4 or Letter page

# Memory cap to prevent OOM on huge images — 200 MP per source image. A 16K
# (15360×8640) image is ~130 MP, so this still allows generous photo sizes
# while blocking malicious "1 GB pixel array" uploads. Pillow refuses to open
# anything over twice its `Image.MAX_IMAGE_PIXELS` as a possible decompression
# bomb, and `app/utils/__init__.py` leaves that at Pillow's default (89.5 MP),
# so the cap in force is 179 MP. Both answer "too large" (413): Pillow's
# DecompressionBombError used to reach the route as a 500.
MAX_IMAGE_PIXELS = 200_000_000

# Lower caps where decoding one image costs more memory. Peak bytes per pixel
# of one page, measured on the 2-core ARM VM: Pillow's WebP decoder 17-19, a
# HEIC photo 9, a compressed colour TIFF up to 8, PNG and BMP about 5. Each cap
# keeps a page under about 1 GB; PNG, BMP, GIF and rendered SVGs stay under
# that at Pillow's limit, and a JPEG is not decoded at all. Pillow holds
# 1-bit, grayscale and palette images at one byte per pixel, so such a TIFF
# (1.4-2.4 bytes per pixel) keeps Pillow's limit too.
FORMAT_PIXEL_CAPS = {
    "WEBP": ("WebP", 50_000_000),
    "HEIF": ("HEIC", 100_000_000),
    "TIFF": ("colour TIFF", 120_000_000),
}
_ONE_BYTE_MODES = {"1", "L", "P"}

# How many megapixels one PDF may decode. A JPEG is embedded as it is and
# costs almost nothing; every other image is decoded, which costs CPU in
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


class DecodeBudgetExceeded(ValueError):
    """A batch would decode more megapixels than one PDF may.

    A ValueError, so the route answers 413 with this message.
    """


@dataclass
class _Source:
    path: str  # what is read into the page: the rendered PNG for an SVG
    width: int
    height: int
    kind: str  # "jpeg" (embedded as it is), "heic" or "decoded"
    mode: str  # Pillow's mode for the file


def _svg_to_png(svg_path: str) -> str:
    """Rasterize an SVG to a high-res PNG temp file via cairosvg."""
    from cairosvg.surface import PNGSurface

    from .svg_safety import block_external_refs

    out_path = get_temp_path(f"svg_to_png_{uuid.uuid4().hex}.png")
    with open(svg_path, "rb") as f:
        svg_data = f.read()
    # Pass bytestring= (NOT url=) so relative refs can't resolve against the
    # server filesystem, and block_external_refs denies absolute file:// (LFI)
    # and http(s):// (SSRF) references — only inline data: URIs are allowed.
    # Render at 2x for crisp output even after PDF embed scaling.
    PNGSurface.convert(
        bytestring=svg_data,
        write_to=str(out_path),
        output_width=2400,
        url_fetcher=lambda url, resource_type: block_external_refs(url, resource_type)["string"],
    )
    return str(out_path)


def _pixel_cap() -> int:
    """The most pixels any image may have: MAX_IMAGE_PIXELS, or Pillow's limit if lower."""
    pillow = Image.MAX_IMAGE_PIXELS
    return MAX_IMAGE_PIXELS if pillow is None else min(MAX_IMAGE_PIXELS, 2 * pillow)


def _source(path: str, intermediates: list[str]) -> _Source:
    """Size and kind of one upload, read from its header without decoding it.

    Enforces the per-image pixel cap so callers can fail fast before any
    decoding work runs.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in _SVG_EXTS:
        path = _svg_to_png(path)
        intermediates.append(path)
    name, cap = os.path.basename(path), _pixel_cap()
    try:
        with Image.open(path) as img:
            (w, h), image_format, mode = img.size, img.format, img.mode
    except Image.DecompressionBombError:
        raise ValueError(f"Image {name} is too large. Max {cap // 1_000_000} MP per image.") from None
    label, format_cap = FORMAT_PIXEL_CAPS.get(image_format, ("", cap))
    if image_format == "TIFF" and mode in _ONE_BYTE_MODES:
        format_cap = cap
    if w * h > min(cap, format_cap):
        per = f"per {label} image" if format_cap < cap else "per image"
        raise ValueError(
            f"Image {name} is too large ({w}x{h} = {(w * h) // 1_000_000} MP). "
            f"Max {min(cap, format_cap) // 1_000_000} MP {per}."
        )
    if ext in _HEIC_EXTS:
        kind = "heic"
    elif image_format in ("JPEG", "MPO") and mode in _COLOUR_SPACES:
        kind = "jpeg"
    else:
        kind = "decoded"
    return _Source(path, w, h, kind, mode)


def _check_decode_budget(sources: list[_Source]) -> None:
    decoded = sum(s.width * s.height for s in sources if s.kind == "decoded") / 1e6
    heic = sum(s.width * s.height for s in sources if s.kind == "heic") / 1e6
    total = decoded + heic * HEIC_MEGAPIXEL_WEIGHT
    if total <= MAX_DECODED_MEGAPIXELS:
        return
    # Rounded up, so a batch just over the limit never reads as within it.
    if not heic:
        message = (f"One PDF can take up to {MAX_DECODED_MEGAPIXELS:,} megapixels of {_DECODED_FORMATS}; "
                   f"these add up to {math.ceil(decoded):,}.")
    elif not decoded:
        message = (f"One PDF can take up to {MAX_DECODED_MEGAPIXELS / HEIC_MEGAPIXEL_WEIGHT:,.0f} megapixels "
                   f"of HEIC photos; these add up to {math.ceil(heic):,}.")
    else:
        message = (f"One PDF can take up to {MAX_DECODED_MEGAPIXELS:,} megapixels of images other than JPEG, "
                   f"with HEIC photos counting half; these add up to {math.ceil(total):,}.")
    raise DecodeBudgetExceeded(message)


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


def _file_chunks(path: str) -> Iterator[bytes]:
    with open(path, "rb") as fh:
        while block := fh.read(1024 * 1024):
            yield block


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
            if band.mode != mode:
                band = band.convert(mode)
            if out := compressor.compress(band.tobytes()):
                yield out
        yield compressor.flush()
    finally:
        img.close()


def _image_stream(source: _Source) -> tuple[bytes, int | None, Iterable[bytes]]:
    """(image dictionary entries, length if known, data) for one page."""
    if source.kind == "jpeg":
        return (_image_dict(source.width, source.height, source.mode, b"/DCTDecode"),
                os.path.getsize(source.path), _file_chunks(source.path))
    img = Image.open(source.path)
    if source.kind == "heic":
        # PDF has no HEVC filter: decode and embed a JPEG, as before.
        buffer = io.BytesIO()
        with img:
            (img if img.mode == "RGB" else img.convert("RGB")).save(buffer, "JPEG", quality=92)
        data = buffer.getvalue()
        return _image_dict(source.width, source.height, "RGB", b"/DCTDecode"), len(data), [data]
    # ReportLab's ImageReader.getRGBData conversions: alpha dropped, every mode
    # other than L, RGB and CMYK converted to RGB.
    mode = img.mode[:-1] if img.mode in ("LA", "RGBA") else img.mode if img.mode in _COLOUR_SPACES else "RGB"
    return _image_dict(source.width, source.height, mode, b"/FlateDecode"), None, _deflated_rows(img, mode)


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
            raise OSError("an image changed while it was being read")
        self._fh.write(b"\nendstream\nendobj\n")
        if length_ref:
            self._object(length_ref, b"%d" % written)

    def add_page(self, page_size: tuple[float, float], stream, box: tuple[float, float, float, float] | None) -> None:
        page_ref = self._reserve()
        resources = b"<<>>"
        content = b""
        if stream is not None:
            image_ref, content_ref = self._reserve(), self._reserve()
            self._stream(image_ref, *stream)
            x, y, width, height = box
            content = b"q %s 0 0 %s %s %s cm /Im0 Do Q\n" % (_number(width), _number(height), _number(x), _number(y))
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


def images_to_pdf(input_paths: list, page_size: str = "A4") -> str:
    ensure_temp_dir()
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

    # Rendered SVGs, deleted even on error.
    intermediates: list[str] = []
    try:
        # Every size is known, and the batch checked, before any image is decoded.
        sources = [_source(path, intermediates) for path in input_paths]
        _check_decode_budget(sources)
        with open(output_path, "wb") as fh:
            writer = _PdfWriter(fh)
            for source in sources:
                if auto:
                    page = (source.width, source.height)
                    box = (0, 0, source.width, source.height)
                else:
                    page = fixed_size
                    page_width, page_height = fixed_size
                    ratio = min((page_width - 2 * MARGIN) / source.width, (page_height - 2 * MARGIN) / source.height)
                    width, height = source.width * ratio, source.height * ratio
                    box = ((page_width - width) / 2, (page_height - height) / 2, width, height)
                writer.add_page(page, _image_stream(source), box)
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
            try:
                os.unlink(p)
            except OSError:
                pass

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
