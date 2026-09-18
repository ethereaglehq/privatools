"""Extract and return EXIF / IPTC / XMP / image metadata as a JSON-able dict.

Counterpart to /api/remove-exif — this one *shows* you what's in there.
Pure-read, never writes to disk.
"""

from __future__ import annotations

import json
import re
import struct
from typing import Any

from PIL import ExifTags, Image

# What Pillow raises for an EXIF block it cannot parse. A damaged block lists
# as empty instead of failing the whole request.
_UNREADABLE = (AttributeError, KeyError, OSError, SyntaxError, TypeError, ValueError, struct.error)

# Byte offsets to the sub-IFDs, which are listed in full instead.
_POINTERS = {ExifTags.IFD.Exif, ExifTags.IFD.GPSInfo, ExifTags.IFD.Interop}

# Control characters other than tabs and line breaks: bytes holding them are
# not text, and a browser draws them as boxes.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _text(v: bytes, encoding: str = "utf-8") -> str:
    """Bytes that hold text as that text; binary as hex when short, else its size."""
    try:
        text = v.decode(encoding).rstrip("\x00")
    except UnicodeDecodeError:
        text = None
    if text is not None and not _CONTROL.search(text):
        return text[:500]
    return v.hex(" ") if len(v) <= 16 else f"<{len(v)} bytes>"


def _jsonable(v: Any) -> Any:
    if isinstance(v, str):
        return v.rstrip("\x00")  # text fields are often NUL-padded
    try:
        # allow_nan=False: JSON has no NaN or Infinity, and the response
        # encoder rejects them, so a crafted DOUBLE would otherwise be a 500.
        json.dumps(v, allow_nan=False)
        return v
    except (TypeError, ValueError):
        # bytes, IFDRational, NaN, infinity, etc.
        if isinstance(v, bytes):
            return _text(v)
        return str(v)[:500]


def _coded_text(v: Any) -> Any:
    """UserComment and the GPS text fields: an 8-byte character code, then text."""
    if not isinstance(v, bytes) or len(v) < 8:
        return _jsonable(v)
    code, body = v[:8].rstrip(b"\x00 "), v[8:]
    if code == b"UNICODE":
        # UCS-2 in the writer's byte order; a Latin first letter shows which.
        return _text(body, "utf-16-be" if body[:1] == b"\x00" else "utf-16-le").strip()
    return _text(body).strip()


def _utf16le(v: Any) -> Any:
    # Windows writes its XP* fields (author, title, comment...) as UTF-16LE.
    return _text(v, "utf-16-le") if isinstance(v, bytes) else _jsonable(v)


def _exposure_time(v: Any) -> Any:
    """Shutter speed as photographers write it: 1/160, 0.5, 30."""
    try:
        seconds = float(v)
        if 0 < seconds <= 0.25:
            return f"1/{round(1 / seconds)}"
    except (TypeError, ValueError, OverflowError):  # OverflowError: too small to invert
        return _jsonable(v)
    return f"{seconds:.1f}".removesuffix(".0")


_EXIF_FORMAT = {
    ExifTags.Base.ExposureTime: _exposure_time,
    ExifTags.Base.UserComment: _coded_text,
    ExifTags.Base.XPTitle: _utf16le,
    ExifTags.Base.XPComment: _utf16le,
    ExifTags.Base.XPAuthor: _utf16le,
    ExifTags.Base.XPKeywords: _utf16le,
    ExifTags.Base.XPSubject: _utf16le,
}
_GPS_FORMAT = {
    ExifTags.GPS.GPSProcessingMethod: _coded_text,
    ExifTags.GPS.GPSAreaInformation: _coded_text,
}


def _listed(exif: Image.Exif, ifd: int | None, names: dict[int, str], prefix: str, formats: dict) -> dict[str, Any]:
    """Name and format the tags of IFD0 (``ifd=None``) or one sub-IFD."""
    try:
        tags = exif if ifd is None else exif.get_ifd(ifd)
        return {
            names.get(tag_id, f"{prefix}{tag_id}"): formats.get(tag_id, _jsonable)(value)
            for tag_id, value in tags.items()
            if tag_id not in _POINTERS
        }
    except _UNREADABLE:
        return {}


def view_exif(input_path: str) -> dict[str, Any]:
    # `with` makes sure we close the underlying file handle even if EXIF
    # parsing raises mid-iteration. Previously a bad GPS IFD on certain
    # images would skip the explicit img.close() and leak a descriptor.
    with Image.open(input_path) as img:
        info: dict[str, Any] = {
            "format": img.format,
            "mode": img.mode,
            "size": [img.width, img.height],
            "exif": {},
            "info": {},
            "gps": {},
        }
        try:
            exif = img.getexif()
        except _UNREADABLE:
            exif = Image.Exif()

        # Exposure time, aperture, ISO, the lens and the original capture
        # time live in the Exif sub-IFD, which getexif() leaves out.
        info["exif"] = _listed(exif, None, ExifTags.TAGS, "Tag", _EXIF_FORMAT) | _listed(
            exif, ExifTags.IFD.Exif, ExifTags.TAGS, "Tag", _EXIF_FORMAT
        )
        info["gps"] = _listed(exif, ExifTags.IFD.GPSInfo, ExifTags.GPSTAGS, "GPSTag", _GPS_FORMAT)

        for k, v in (img.info or {}).items():
            if k == "exif":  # the raw block the groups above decode
                continue
            info["info"][str(k)] = _jsonable(v)

    return info
