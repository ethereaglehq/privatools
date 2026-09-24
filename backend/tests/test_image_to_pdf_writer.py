"""Image to PDF writes each page as it is made, and embeds what ReportLab did.

Until this change the service drew every image on one ReportLab canvas, which
keeps each page in memory until `save()` formats the whole file: about three
times the finished PDF, so 100 web-size WebPs took +1.6 GB. The service now
writes each image to the PDF file as soon as it is read. These tests hold it
to ReportLab's output, image kind by image kind, and to a Python heap that
peaks at one page however many pages there are.
"""
from __future__ import annotations

import os
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pikepdf
import pillow_heif
import pymupdf
import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.rl_accel import asciiBase85Encode
from reportlab.pdfgen.canvas import Canvas

from backend.app.services import image_to_pdf_service

pillow_heif.register_heif_opener()
rng = np.random.default_rng(271)


@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    return tmp_path


def _picture(size=(240, 160)) -> Image.Image:
    width, height = size
    image = Image.fromarray(rng.integers(0, 256, (height, width, 3), dtype=np.uint8), "RGB")
    ImageDraw.Draw(image).ellipse([width // 5, height // 5, width * 4 // 5, height * 4 // 5], fill=(200, 30, 60))
    return image


def _with_alpha(image: Image.Image) -> Image.Image:
    alpha = Image.new("L", image.size, 0)
    ImageDraw.Draw(alpha).rectangle([10, 10, image.width - 10, image.height - 10], fill=255)
    image = image.convert("RGBA")
    image.putalpha(alpha)
    return image


KINDS = {
    "jpeg-rgb": (".jpg", lambda p: _picture().save(p, "JPEG", quality=85)),
    "jpeg-gray": (".jpg", lambda p: _picture().convert("L").save(p, "JPEG", quality=85)),
    "jpeg-cmyk": (".jpg", lambda p: _picture().convert("CMYK").save(p, "JPEG", quality=85)),
    "jpeg-progressive": (".jpeg", lambda p: _picture().save(p, "JPEG", quality=85, progressive=True)),
    "png-rgba": (".png", lambda p: _with_alpha(_picture()).save(p)),
    "png-gray-alpha": (".png", lambda p: _with_alpha(_picture()).convert("LA").save(p)),
    "png-palette-transparent": (".png", lambda p: _picture().convert("P", palette=Image.ADAPTIVE).save(p, transparency=0)),
    "png-16-bit": (".png", lambda p: Image.fromarray(np.linspace(0, 65535, 240 * 160).reshape(160, 240).astype(np.uint16)).save(p)),
    "tiff-bilevel-g4": (".tiff", lambda p: _picture((1000, 700)).convert("1").save(p, compression="group4")),
    "tiff-cmyk": (".tif", lambda p: _picture().convert("CMYK").save(p, compression="tiff_lzw")),
    "tiff-two-pages": (".tiff", lambda p: _picture().save(p, save_all=True, append_images=[_picture((90, 60))])),
    "bmp": (".bmp", lambda p: _picture().save(p)),
    "gif-transparent": (".gif", lambda p: _picture().convert("P", palette=Image.ADAPTIVE).save(p, transparency=3)),
    "webp-lossy": (".webp", lambda p: _picture().save(p, "WEBP", quality=80)),
    "webp-lossless-alpha": (".webp", lambda p: _with_alpha(_picture()).save(p, "WEBP", lossless=True)),
    "heic": (".heic", lambda p: _picture().save(p, quality=70)),
}


def _reportlab_pdf(path: str, page_size: str, out: Path) -> Path:
    """The PDF the service made before, drawing the image on a ReportLab canvas."""
    if path.endswith(".heic"):
        with Image.open(path) as img:
            img.convert("RGB").save(out.with_suffix(".jpg"), "JPEG", quality=92)
        path = str(out.with_suffix(".jpg"))
    with Image.open(path) as img:
        width, height = img.size
    if page_size == "auto":
        canvas = Canvas(str(out), pagesize=(width, height))
        canvas.drawImage(path, 0, 0, width=width, height=height)
    else:
        page = A4 if page_size == "A4" else LETTER
        ratio = min((page[0] - 72) / width, (page[1] - 72) / height)
        canvas = Canvas(str(out), pagesize=page)
        canvas.drawImage(path, (page[0] - width * ratio) / 2, (page[1] - height * ratio) / 2,
                         width=width * ratio, height=height * ratio)
    canvas.showPage()
    canvas.save()
    return out


def _embedded(path) -> list[dict]:
    pages = []
    with pikepdf.open(path) as pdf:
        for page in pdf.pages:
            (image,) = page.get_images().values()
            picture = pikepdf.PdfImage(image)
            filters = image.Filter if isinstance(image.Filter, pikepdf.Array) else [image.Filter]
            pages.append({
                "page": [round(float(v), 3) for v in page.mediabox],
                "size": (picture.width, picture.height),
                "colour space": str(image.ColorSpace),
                "bits": picture.bits_per_component,
                "filters": [str(f) for f in filters],
                "decode": [float(v) for v in image.get("/Decode", [])],
                "pixels": picture.as_pil_image().tobytes(),
                "jpeg": image.read_raw_bytes() if "/DCTDecode" in map(str, filters) else None,
            })
    return pages


def _raster(path) -> list[bytes]:
    with pymupdf.open(path) as document:
        return [page.get_pixmap(dpi=72, alpha=False).samples for page in document]


@pytest.mark.parametrize("page_size", ["auto", "A4", "Letter"])
@pytest.mark.parametrize("kind", sorted(KINDS))
def test_each_kind_of_image_is_embedded_as_reportlab_embedded_it(temp_dir, kind, page_size):
    ext, write = KINDS[kind]
    source = temp_dir / f"{kind}{ext}"
    write(source)

    output = image_to_pdf_service.images_to_pdf([str(source)], page_size)
    reference = _reportlab_pdf(str(source), page_size, temp_dir / "reference.pdf")

    # Same page box, image dictionary, decoded pixels and JPEG bytes, and the
    # same raster: alpha dropped, only a TIFF's first page, CMYK JPEGs inverted.
    assert _embedded(output) == _embedded(reference)
    assert _raster(output) == _raster(reference)
    with pikepdf.open(output) as pdf:
        assert pdf.check_pdf_syntax() == []


def _noisy_pngs(folder: Path, count: int, size=(1000, 1000)) -> list[str]:
    """Barely compressible pixels: 3 MB each once decoded, about the same deflated."""
    paths = []
    for index in range(count):
        path = folder / f"noise-{index}.png"
        Image.fromarray(rng.integers(0, 256, (size[1], size[0], 3), dtype=np.uint8), "RGB").save(path, compress_level=1)
        paths.append(str(path))
    return paths


def _heap_peak(paths: list[str]) -> int:
    tracemalloc.start()
    try:
        image_to_pdf_service.images_to_pdf(paths, "auto")
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def test_memory_follows_one_page_not_the_document(temp_dir):
    images = _noisy_pngs(temp_dir, 8)
    two, eight = _heap_peak(images[:2]), _heap_peak(images)

    # ReportLab held every deflated image (3 MB each here) until save and then
    # copied the whole file twice: 22 MB for two pages, 72 MB for eight. Now
    # the heap peaks at one page's band and its deflated bytes, about 12 MB
    # either way.
    assert eight < 24 * 1024 * 1024, eight
    assert eight < two * 1.25 + 512 * 1024, (two, eight)


def test_each_page_is_in_the_file_before_the_next_image_is_read(temp_dir, monkeypatch):
    images = _noisy_pngs(temp_dir, 3, size=(300, 200))
    seen: list[int] = []
    stream = image_to_pdf_service._image_stream

    def spy(source):
        output = next(temp_dir.glob("images_to_pdf_*.pdf"))
        seen.append(output.stat().st_size)
        return stream(source)

    monkeypatch.setattr(image_to_pdf_service, "_image_stream", spy)
    image_to_pdf_service.images_to_pdf(images, "auto")

    # 300 x 200 x 3 bytes of noise deflate to about 180 KB per page.
    assert all(later - earlier > 150_000 for earlier, later in zip(seen, seen[1:])), seen


def test_jpegs_are_embedded_byte_for_byte_with_cpu_far_below_ascii85(temp_dir):
    photos = []
    for index in range(6):
        path = temp_dir / f"photo-{index}.jpg"
        base = np.linspace(0, 255, 900 * 1200 * 3).reshape(900, 1200, 3)
        Image.fromarray(np.clip(base + rng.normal(0, 18, base.shape), 0, 255).astype(np.uint8)).save(path, quality=90)
        photos.append(path)
    data = b"".join(p.read_bytes() for p in photos)
    # A yardstick taken on the same machine, so the bound holds on a slow CI
    # runner too: PR #270's ReportLab path cost at least this much.
    started = time.process_time()
    asciiBase85Encode(data)
    ascii85_cpu = time.process_time() - started

    started = time.process_time()
    output = image_to_pdf_service.images_to_pdf([str(p) for p in photos], "auto")
    conversion_cpu = time.process_time() - started

    assert conversion_cpu < ascii85_cpu / 4, (conversion_cpu, ascii85_cpu)
    with pikepdf.open(output) as pdf:
        assert [image.read_raw_bytes() for page in pdf.pages for image in page.get_images().values()] == [
            p.read_bytes() for p in photos
        ]
    assert os.path.getsize(output) <= len(data) * 1.01 + 16 * 1024


def test_a_failed_image_leaves_no_partial_pdf(temp_dir):
    good = temp_dir / "good.png"
    _picture().save(good)
    broken = temp_dir / "broken.png"
    broken.write_bytes(good.read_bytes()[:400])

    with pytest.raises(OSError):
        image_to_pdf_service.images_to_pdf([str(good), str(broken)], "auto")
    assert not list(temp_dir.glob("images_to_pdf_*.pdf"))


def test_no_images_make_one_blank_a4_page(temp_dir):
    output = image_to_pdf_service.images_to_pdf([], "A4")
    with pikepdf.open(output) as pdf:
        assert pdf.check_pdf_syntax() == []
        assert [[round(float(v), 3) for v in page.mediabox] for page in pdf.pages] == [[0, 0, 595.276, 841.89]]
