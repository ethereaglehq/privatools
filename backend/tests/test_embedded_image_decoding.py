"""Embedded images that pikepdf 10 decodes differently from pikepdf 8.

grayscale and compress both decode every embedded image with
``pikepdf.PdfImage.as_pil_image()`` and write new samples back into the same
image object. pikepdf 10 changed two things underneath them:

* An image it cannot decode raises one of pikepdf's own exception types, and
  those derive from Exception directly. 8.x mostly raised NotImplementedError
  or returned a partial image. grayscale's per-image except clause knew only
  the old types, so a single truncated image failed the whole request with a
  500 instead of being skipped.
* Since 10.10, ``as_pil_image()`` composites the image's /SMask by default.
  Both services replace only the image's own samples and leave the /SMask in
  the PDF, where it still applies, so they ask for the unmasked image. With
  the default, a mask pikepdf cannot decode costs the image it belongs to.
"""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

import pikepdf
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.services.compress_service import compress_pdf  # noqa: E402
from backend.app.services.grayscale_service import convert_to_grayscale  # noqa: E402

SIDE = 200


def _rgb_image(pdf: pikepdf.Pdf, **extra) -> pikepdf.Stream:
    """A Flate-encoded colour gradient: big enough for compress to touch, and
    compressible enough that a JPEG of it is smaller than the original."""
    samples = bytes(
        channel
        for y in range(SIDE)
        for x in range(SIDE)
        for channel in (x % 256, y % 256, (x * y) % 256)
    )
    return pdf.make_stream(
        zlib.compress(samples),
        Type=pikepdf.Name.XObject,
        Subtype=pikepdf.Name.Image,
        Width=SIDE,
        Height=SIDE,
        ColorSpace=pikepdf.Name.DeviceRGB,
        BitsPerComponent=8,
        Filter=pikepdf.Name.FlateDecode,
        **extra,
    )


def _truncated(pdf: pikepdf.Pdf, colorspace: pikepdf.Name, bits: int) -> pikepdf.Stream:
    """Declares SIDE x SIDE but carries ten bytes of samples."""
    return pdf.make_stream(
        b"\x12" * 10,
        Type=pikepdf.Name.XObject,
        Subtype=pikepdf.Name.Image,
        Width=SIDE,
        Height=SIDE,
        ColorSpace=colorspace,
        BitsPerComponent=bits,
    )


def _save_page(path: Path, pdf: pikepdf.Pdf, images: dict[str, pikepdf.Stream]) -> str:
    page = pdf.add_blank_page(page_size=(500, 500))
    page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(**images))
    draw = b"".join(
        b"q 200 0 0 200 %d %d cm /%s Do Q " % (20 + 240 * i, 20, name.encode())
        for i, name in enumerate(images)
    )
    page.Contents = pdf.make_stream(draw)
    pdf.save(path)
    return str(path)


def _images(path: str) -> dict[str, dict[str, str]]:
    with pikepdf.open(path) as pdf:
        xobjects = pdf.pages[0].Resources.XObject
        return {
            key.lstrip("/"): {
                "colorspace": str(xobjects[key].get("/ColorSpace")),
                "filter": str(xobjects[key].get("/Filter")),
                "smask": str("/SMask" in xobjects[key]),
            }
            for key in xobjects.keys()
        }


@pytest.mark.parametrize(
    "colorspace",
    [
        # pikepdf 10 raises ImageDecompressionError; 8.x decoded it with a
        # black tail, so this one worked before the upgrade.
        pikepdf.Name.DeviceGray,
        # pikepdf 10 raises UnsupportedImageTypeError.
        pikepdf.Name.DeviceRGB,
    ],
    ids=["gray", "rgb"],
)
def test_grayscale_skips_an_image_it_cannot_decode_and_converts_the_rest(tmp_path, colorspace):
    pdf = pikepdf.new()
    src = _save_page(
        tmp_path / "in.pdf",
        pdf,
        {"Good": _rgb_image(pdf), "Truncated": _truncated(pdf, colorspace, 4)},
    )

    images = _images(convert_to_grayscale(src))

    assert images["Good"]["colorspace"] == "/DeviceGray"
    assert images["Good"]["filter"] == "/DCTDecode"
    # Converted images are rewritten as JPEG; the skipped one keeps its data.
    assert images["Truncated"]["filter"] != "/DCTDecode", "the undecodable image was not skipped"


def test_grayscale_converts_an_image_whose_soft_mask_cannot_be_decoded(tmp_path):
    pdf = pikepdf.new()
    mask = _truncated(pdf, pikepdf.Name.DeviceGray, 8)
    src = _save_page(tmp_path / "in.pdf", pdf, {"Masked": _rgb_image(pdf, SMask=mask)})

    images = _images(convert_to_grayscale(src))

    assert images["Masked"]["colorspace"] == "/DeviceGray"
    assert images["Masked"]["smask"] == "True", "the soft mask should stay in the PDF"


def test_compress_recompresses_an_image_whose_soft_mask_cannot_be_decoded(tmp_path):
    pdf = pikepdf.new()
    mask = _truncated(pdf, pikepdf.Name.DeviceGray, 8)
    src = _save_page(tmp_path / "in.pdf", pdf, {"Masked": _rgb_image(pdf, SMask=mask)})

    images = _images(compress_pdf(src, level="extreme"))

    assert images["Masked"]["filter"] == "/DCTDecode", "the image was left uncompressed"
    assert images["Masked"]["smask"] == "True", "the soft mask should stay in the PDF"
