"""Image to PDF writes each page as it is made, and embeds what ReportLab did.

Until this change the service drew every image on one ReportLab canvas, which
keeps each page in memory until `save()` formats the whole file: about three
times the finished PDF, so 100 web-size WebPs took +1.6 GB. The service now
writes each image to the PDF file as soon as it is read. These tests hold it
to ReportLab's output, image kind by image kind, and to memory that peaks at
one page however many pages there are. Two kinds differ from ReportLab on
purpose: 16-bit grayscale, which it clipped nearly white, and JPEGs that are
not DCT-coded, for which it drew a placeholder.
"""
from __future__ import annotations

import base64
import json
import os
import struct
import subprocess
import sys
import time
import tracemalloc
import zlib
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


# A 16 x 12 lossless JPEG (SOF3), written by libjpeg-turbo 3 through imagecodecs.
LOSSLESS_JPEG = base64.b64decode(
    "/9j/7gAOQWRvYmUAZAAAAAAA/8MAEQgADAAQA1IRAEcRAEIRAP/EABgAAQEBAQEAAAAAAAAAAAAAAAAFBAgH/9oADANSAEcAQgAB"
    "AADn/n/3+gz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0"
    "Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Ge"
    "gzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0"
    "Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqig"
    "z0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegzqigz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz0Gegz/AP/Z"
)


def _png_16_bit_rgb(width: int, height: int) -> bytes:
    """A 16-bit-per-channel RGB PNG (Pillow writes none), with full-range gradients."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    x = np.linspace(0, 65535, width)[None, :].repeat(height, 0)
    y = np.linspace(65535, 0, height)[:, None].repeat(width, 1)
    samples = np.stack([x, y, np.full_like(x, 30000)], axis=2).astype(">u2")
    rows = b"".join(b"\x00" + row.tobytes() for row in samples)
    header = struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


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
    # 16-bit colour: Pillow keeps each sample's high byte, for ReportLab too.
    "png-16-bit-rgb": (".png", lambda p: p.write_bytes(_png_16_bit_rgb(240, 160))),
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


def test_a_jpeg_dctdecode_cannot_read_is_embedded_as_its_pixels(temp_dir):
    # A lossless JPEG (SOF3) is not DCT-coded at all. Passed through as
    # DCTDecode, MuPDF rendered it black ("Unsupported JPEG process: SOF type
    # 0xc3"); ReportLab gave up on it and drew its 24 x 23 placeholder.
    source = temp_dir / "scan.jpg"
    source.write_bytes(LOSSLESS_JPEG)

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    (page,) = _embedded(output)
    assert (page["size"], page["colour space"], page["filters"]) == ((16, 12), "/DeviceRGB", ["/FlateDecode"])
    with Image.open(source) as original:
        assert page["pixels"] == original.convert("RGB").tobytes()


@pytest.mark.parametrize("fmt, ext", [("PNG", ".png"), ("TIFF", ".tiff")])
def test_a_16_bit_grayscale_image_keeps_its_whole_range(temp_dir, fmt, ext):
    # ReportLab, and this writer until now, converted Pillow's I;16 to RGB,
    # which clips every sample over 255: all but the darkest 0.4% came out white.
    gradient = np.linspace(0, 65535, 256 * 64).reshape(64, 256).astype(np.uint16)
    source = temp_dir / f"scan{ext}"
    Image.fromarray(gradient).save(source, fmt)
    with Image.open(source) as opened:
        assert opened.mode == "I;16"

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    (page,) = _embedded(output)
    assert (page["colour space"], page["bits"], page["filters"]) == ("/DeviceGray", 8, ["/FlateDecode"])
    # Each sample's high byte, as Pillow reduces 16-bit colour PNGs.
    assert page["pixels"] == (gradient >> 8).astype(np.uint8).tobytes()


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


def test_the_python_heap_follows_one_page_not_the_document(temp_dir):
    # tracemalloc sees only Python's own allocations: the bytes objects that
    # hold deflated pages, which is where ReportLab kept the document. Pillow's
    # decoded pixels are allocated outside it; the next test measures the
    # whole process.
    images = _noisy_pngs(temp_dir, 8)
    two, eight = _heap_peak(images[:2]), _heap_peak(images)

    # ReportLab held every deflated image (3 MB each here) until save and then
    # copied the whole file twice: 22 MB for two pages, 72 MB for eight. Now
    # the heap peaks at one page's band and its deflated bytes, about 12 MB
    # either way.
    assert eight < 24 * 1024 * 1024, eight
    assert eight < two * 1.25 + 512 * 1024, (two, eight)


# Run in a fresh interpreter: its peak RSS is reset just before the conversion
# (Linux's clear_refs), so the imports' own peak cannot hide the conversion's.
_PEAK_RSS = """
import json, os, sys
from pathlib import Path
from backend.app.services import image_to_pdf_service as service
def status(key):
    for line in open("/proc/self/status"):
        if line.startswith(key):
            return int(line.split()[1]) * 1024
work = Path(sys.argv[1])
service.ensure_temp_dir = lambda: None
service.get_temp_path = lambda name: work / name
before = status("VmRSS:")
with open("/proc/self/clear_refs", "w") as fh:
    fh.write("5")
os.unlink(service.images_to_pdf(sys.argv[2:], "auto"))
print(json.dumps({"growth": status("VmHWM:") - before}))
"""


def _peak_rss_growth(paths: list[str], work: Path) -> int:
    """How far converting `paths` raises a process's resident memory at its peak."""
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, "-c", _PEAK_RSS, str(work), *paths], cwd=repo,
                            capture_output=True, text=True, check=True, timeout=120)
    return json.loads(result.stdout.strip().splitlines()[-1])["growth"]


@pytest.mark.skipif(not Path("/proc/self/clear_refs").exists(), reason="needs Linux's peak-RSS reset")
def test_the_whole_process_follows_one_page_not_the_document(temp_dir):
    # Peak RSS, so Pillow's decoded pixels count too: 18 MB for each of these
    # 3,000 × 2,000 pictures, 9 MB deflated. Measured on the 2-core ARM VM, one
    # page or eight each peak at +48 MB; ReportLab's canvas peaked 100 MB
    # higher for eight pages than for two.
    pictures = []
    for index in range(8):
        path = temp_dir / f"photo-{index}.png"
        noise = rng.integers(0, 256, (1000, 3000, 3), dtype=np.uint8)
        Image.fromarray(np.concatenate([noise, np.zeros_like(noise)])).save(path, compress_level=1)
        pictures.append(str(path))

    two = _peak_rss_growth(pictures[:2], temp_dir)
    eight = _peak_rss_growth(pictures, temp_dir)

    assert eight - two < 16 * 1024 * 1024, (two, eight)


def test_each_page_is_in_the_file_before_the_next_image_is_read(temp_dir, monkeypatch):
    images = _noisy_pngs(temp_dir, 3, size=(300, 200))
    seen: list[int] = []
    stream = image_to_pdf_service._image_stream

    def spy(source, *args):
        output = next(temp_dir.glob("images_to_pdf_*.pdf"))
        seen.append(output.stat().st_size)
        return stream(source, *args)

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

    with pytest.raises(image_to_pdf_service.UnreadableImage, match="^scan 2.png could not be read as an image.$"):
        image_to_pdf_service.images_to_pdf([str(good), str(broken)], "auto", names=["scan 1.png", "scan 2.png"])
    assert not list(temp_dir.glob("images_to_pdf_*.pdf"))


def test_a_file_that_changes_after_planning_is_the_servers_error_not_the_senders(temp_dir, monkeypatch):
    source = temp_dir / "shot.png"
    _picture().save(source)
    monkeypatch.setattr(image_to_pdf_service, "_check_decode_budget",
                        lambda sources: _picture((100, 80)).save(source))

    with pytest.raises(OSError, match="changed") as refused:
        image_to_pdf_service.images_to_pdf([str(source)], "auto")
    assert not isinstance(refused.value, image_to_pdf_service.ImageRefused)
    assert not list(temp_dir.glob("images_to_pdf_*.pdf"))


def test_no_images_make_one_blank_a4_page(temp_dir):
    output = image_to_pdf_service.images_to_pdf([], "A4")
    with pikepdf.open(output) as pdf:
        assert pdf.check_pdf_syntax() == []
        assert [[round(float(v), 3) for v in page.mediabox] for page in pdf.pages] == [[0, 0, 595.276, 841.89]]
