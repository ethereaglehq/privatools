"""POST /api/image-to-pdf takes up to 100 images, within a combined size cap.

Nine tools share this route: Image, JPG, PNG, HEIC, WebP, TIFF, BMP, GIF and
SVG to PDF. The limits here are theirs, and their page copy states them.
"""
from __future__ import annotations

import io
import re
import struct
import threading
import zlib
from pathlib import Path

import fitz
import pytest
from PIL import Image

from backend.app.routes import image_to_pdf as route
from backend.app.services import image_to_pdf_service
from backend.app.tool_content import TOOL_FAQ, TOOL_HOWTO

REPO = Path(__file__).resolve().parents[2]
IMAGE_TO_PDF_TOOLS = (
    "image-to-pdf", "jpg-to-pdf", "png-to-pdf", "heic-to-pdf", "webp-to-pdf",
    "tiff-to-pdf", "bmp-to-pdf", "gif-to-pdf", "svg-to-pdf",
)
MB = 1024 * 1024


def _jpeg(index: int) -> bytes:
    # A distinct width per image lets a test read the page order back.
    buffer = io.BytesIO()
    Image.new("RGB", (10 + index, 8), (index % 256, 90, 160)).save(buffer, "JPEG", quality=80)
    return buffer.getvalue()


def _images(count: int) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (f"photo-{i:03d}.jpg", _jpeg(i), "image/jpeg")) for i in range(count)]


def test_one_hundred_images_become_a_one_hundred_page_pdf(client):
    response = client.post("/api/image-to-pdf", files=_images(100), data={"page_size": "auto"})

    assert response.status_code == 200, response.text
    with fitz.open(stream=response.content, filetype="pdf") as document:
        assert document.page_count == 100
        # Upload order is page order, past the old 50-image cut-off too.
        assert [page.get_images()[0][2] for page in document] == [10 + i for i in range(100)]


def test_a_101st_image_is_refused_with_a_clear_message_before_any_work(client, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "images_to_pdf", lambda *args, **kwargs: pytest.fail("must not convert"))

    response = client.post("/api/image-to-pdf", files=_images(101))

    assert response.status_code == 400
    assert response.json()["detail"] == "One PDF can take up to 100 images; this request has 101."


def test_the_conversion_runs_in_the_bounded_heavy_pool(client, monkeypatch):
    # A 100-image conversion is CPU and memory heavy. It shares the per-worker
    # heavy-work budget (MAX_CONCURRENT_HEAVY) with the other heavy tools
    # instead of running unbounded in asyncio's default executor.
    seen: dict[str, str] = {}
    convert = image_to_pdf_service.images_to_pdf

    def spy(paths, page_size="A4"):
        seen["thread"] = threading.current_thread().name
        return convert(paths, page_size=page_size)

    monkeypatch.setattr(image_to_pdf_service, "images_to_pdf", spy)

    response = client.post("/api/image-to-pdf", files=_images(2))

    assert response.status_code == 200, response.text
    assert seen["thread"].startswith("heavy"), seen


def test_the_combined_size_cap_stays_at_200_mb():
    # The owner's limit. When the image count went to 100 (PR #270) it also
    # bounded memory, because ReportLab held every page until it saved the
    # file; pages are now written as they are made.
    assert route.MAX_TOTAL_UPLOAD_BYTES == 200 * MB


def test_the_decode_budget_is_750_megapixels_with_heic_counting_half():
    # Measured on the 2-core ARM VM with pages written as they are made: about
    # 0.14 s of CPU per megapixel to decode and deflate a PNG, WebP, TIFF, BMP,
    # GIF or rendered SVG, about half that to turn a HEIC photo into a JPEG.
    # 100 phone-size WebPs (1,219 MP, 179 MB) passed every other limit and were
    # OOM-killed in a 4 GB container; written page by page they still took
    # 172 s. Within this budget a request stays under about 115 s of CPU, and
    # 100 iPhone photos (610 at half weight) still fit.
    assert image_to_pdf_service.MAX_DECODED_MEGAPIXELS == 750
    assert image_to_pdf_service.HEIC_MEGAPIXEL_WEIGHT == 0.5


def _png_header(width: int, height: int) -> bytes:
    """A PNG that claims width x height pixels; they are never read."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(64))) + chunk(b"IEND", b"")


def test_an_image_over_pillows_pixel_limit_is_too_large_not_a_server_error(client, monkeypatch):
    # Pillow refuses to open anything over twice its MAX_IMAGE_PIXELS (179 MP)
    # as a possible decompression bomb. That error used to reach the route as
    # a 500, "Processing failed", below the service's own 200 MP cap.
    _no_page_may_be_made(monkeypatch)

    response = client.post("/api/image-to-pdf", files=[("files", ("panorama.png", _png_header(14000, 13000), "image/png"))])

    assert response.status_code == 413
    assert re.fullmatch(r"Image \S+ is too large\. Max 178 MP per image\.", response.json()["detail"]), response.json()


def _image(fmt: str, size=(1000, 1000), colour=(30, 90, 160)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, fmt)
    return buffer.getvalue()


def _no_page_may_be_made(monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "_image_stream", lambda *args: pytest.fail("must not decode"))


def test_formats_that_take_more_memory_to_decode_have_lower_pixel_caps():
    # One page's peak, measured with pages written as they are made: a 178 MP
    # WebP (Pillow's limit) took +2.9 GB, because Pillow's WebP decoder keeps
    # 17-19 bytes per pixel; a HEIC photo takes 9 and a compressed colour TIFF
    # up to 8, PNG and BMP about 5. These caps keep one page under about 1 GB.
    assert image_to_pdf_service.FORMAT_PIXEL_CAPS == {
        "WEBP": ("WebP", 50_000_000),
        "HEIF": ("HEIC", 100_000_000),
        "TIFF": ("colour TIFF", 120_000_000),
    }


@pytest.mark.parametrize("fmt, name, label", [
    ("WEBP", "large.webp", "WebP"), ("HEIF", "IMG_1.heic", "HEIC"), ("TIFF", "scan.tiff", "colour TIFF"),
])
def test_an_image_over_its_formats_pixel_cap_is_too_large(client, monkeypatch, fmt, name, label):
    small = {key: (text, 1_000_000) for key, (text, _) in image_to_pdf_service.FORMAT_PIXEL_CAPS.items()}
    monkeypatch.setattr(image_to_pdf_service, "FORMAT_PIXEL_CAPS", small)
    _no_page_may_be_made(monkeypatch)

    response = client.post("/api/image-to-pdf", files=[("files", (name, _image(fmt, (1200, 1000)), "image/octet-stream"))])

    assert response.status_code == 413
    assert response.json()["detail"].endswith(f"is too large (1200x1000 = 1 MP). Max 1 MP per {label} image.")


def test_png_jpeg_and_grayscale_tiff_keep_the_general_pixel_cap(client, monkeypatch):
    small = {key: (text, 1_000_000) for key, (text, _) in image_to_pdf_service.FORMAT_PIXEL_CAPS.items()}
    monkeypatch.setattr(image_to_pdf_service, "FORMAT_PIXEL_CAPS", small)
    gray = io.BytesIO()
    Image.new("L", (1200, 1000), 200).save(gray, "TIFF", compression="tiff_lzw")
    files = [
        ("files", ("shot.png", _image("PNG", (1200, 1000)), "image/png")),
        ("files", ("photo.jpg", _image("JPEG", (1200, 1000)), "image/jpeg")),
        ("files", ("fax.tiff", gray.getvalue(), "image/tiff")),
    ]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 200, response.text


def test_images_past_the_decode_budget_are_refused_with_a_413_before_any_page(client, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 2)
    _no_page_may_be_made(monkeypatch)
    files = [("files", (f"shot-{i}.png", _image("PNG"), "image/png")) for i in range(3)]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "One PDF can take up to 2 megapixels of PNG, WebP, TIFF, BMP, GIF and SVG images; these add up to 3."
    )


def test_jpegs_do_not_count_toward_the_decode_budget(client, monkeypatch):
    # A JPEG is embedded as it is, without decoding.
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 1)
    files = [("files", (f"photo-{i}.jpg", _image("JPEG"), "image/jpeg")) for i in range(3)]

    response = client.post("/api/image-to-pdf", files=files, data={"page_size": "auto"})

    assert response.status_code == 200, response.text
    with fitz.open(stream=response.content, filetype="pdf") as document:
        assert document.page_count == 3


def test_a_heic_megapixel_counts_half(client, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 1)
    heic = _image("HEIF")

    two = client.post("/api/image-to-pdf", files=[("files", (f"IMG_{i}.heic", heic, "image/heic")) for i in range(2)])
    assert two.status_code == 200, two.text

    _no_page_may_be_made(monkeypatch)
    three = client.post("/api/image-to-pdf", files=[("files", (f"IMG_{i}.heic", heic, "image/heic")) for i in range(3)])
    assert three.status_code == 413
    assert three.json()["detail"] == "One PDF can take up to 2 megapixels of HEIC photos; these add up to 3."


def test_a_mixed_batch_is_told_how_heic_counts(client, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 2)
    _no_page_may_be_made(monkeypatch)
    files = [
        ("files", ("photo.jpg", _image("JPEG", (3000, 3000)), "image/jpeg")),
        ("files", ("shot.png", _image("PNG"), "image/png")),
        ("files", ("IMG_1.heic", _image("HEIF", (1500, 2000)), "image/heic")),
    ]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 413
    # 1 MP of PNG and 3 MP of HEIC counted at half: 2.5, shown rounded up.
    assert response.json()["detail"] == (
        "One PDF can take up to 2 megapixels of images other than JPEG, with HEIC photos counting half; "
        "these add up to 3."
    )


def test_images_past_the_combined_cap_are_refused_with_a_413_naming_the_cap(client, monkeypatch):
    monkeypatch.setattr(route, "MAX_TOTAL_UPLOAD_BYTES", 1 * MB)
    monkeypatch.setattr(image_to_pdf_service, "images_to_pdf", lambda *args, **kwargs: pytest.fail("must not convert"))
    half = b"\xff\xd8" + bytes(700 * 1024)
    files = [("files", (f"scan-{i}.jpg", half, "image/jpeg")) for i in range(2)]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 413
    assert response.json()["detail"] == "One PDF can take up to 1 MB of images in total; these add up to more."


def test_the_api_documents_the_image_limits():
    from backend.app.api_v1.catalog import build_catalog
    from backend.app.api_v1.schema import build_schema
    from backend.app.main import app

    schema = build_schema(app)
    operation = schema["paths"]["/api/v1/image-to-pdf"]["post"]
    ref = operation["requestBody"]["content"]["multipart/form-data"]["schema"]["$ref"]
    files = schema["components"]["schemas"][ref.rsplit("/", 1)[1]]["properties"]["files"]
    assert (files["minItems"], files["maxItems"]) == (1, route.MAX_FILES)
    constraints = next(op for op in build_catalog(app)["operations"] if op["path"] == "/api/v1/image-to-pdf")["constraints"]
    count, size = f"1–{route.MAX_FILES} images", f"{route.MAX_TOTAL_UPLOAD_BYTES // MB} MB combined"
    assert any(count in note and size in note for note in constraints), constraints
    pixels = f"{image_to_pdf_service.MAX_DECODED_MEGAPIXELS:,} megapixels, a HEIC megapixel counting half"
    assert any(pixels in note and "413" in note for note in constraints), constraints


def test_the_page_enforces_the_same_limits_as_the_route():
    source = (REPO / "frontend/src/components/tool-ui/image-to-pdf-limits.ts").read_text()
    assert re.search(r"IMAGE_TO_PDF_MAX_FILES = (\d+);", source).group(1) == str(route.MAX_FILES)
    assert re.search(r"IMAGE_TO_PDF_MAX_TOTAL_MB = (\d+);", source).group(1) == str(route.MAX_TOTAL_UPLOAD_BYTES // MB)
    # The page states the decode budget; the server enforces it.
    megapixels = image_to_pdf_service.MAX_DECODED_MEGAPIXELS
    assert re.search(r"IMAGE_TO_PDF_MAX_MEGAPIXELS = ([\d_]+);", source).group(1).replace("_", "") == str(megapixels)
    heic = megapixels / image_to_pdf_service.HEIC_MEGAPIXEL_WEIGHT
    assert re.search(r"IMAGE_TO_PDF_MAX_HEIC_MEGAPIXELS = ([\d_]+);", source).group(1).replace("_", "") == f"{heic:.0f}"


def _tool_copy(slug: str) -> list[str]:
    registry = (REPO / "frontend/src/data/tools.ts").read_text()
    entry = registry.split(f'slug: "{slug}"', 1)[1].split("slug:", 1)[0]
    guide = [step["text"] for step in TOOL_HOWTO.get(slug, [])]
    guide += [part for item in TOOL_FAQ.get(slug, []) for part in (item["q"], item["a"])]
    return [entry, *guide]


def test_every_limit_the_nine_tools_state_matches_the_route():
    counts, sizes, pixels = [], [], []
    for slug in IMAGE_TO_PDF_TOOLS:
        for text in _tool_copy(slug):
            counts += [(slug, int(n)) for n in re.findall(r"(?i)\bup to (\d+) (?:images|files|photos)\b", text)]
            sizes += [(slug, int(n)) for n in re.findall(r"\b(\d+) MB\b", text)]
            pixels += [(slug, int(n.replace(",", ""))) for n in re.findall(r"\b(\d[\d,]*) megapixels\b", text)]
    assert len(counts) >= 10 and len(sizes) >= 10, (counts, sizes)
    assert {n for _, n in counts} == {route.MAX_FILES}, counts
    assert {n for _, n in sizes} == {route.MAX_TOTAL_UPLOAD_BYTES // MB}, sizes
    # The decode budget, on every tool whose images are decoded. JPEGs are not;
    # GIF to PDF states no limits at all.
    budget = image_to_pdf_service.MAX_DECODED_MEGAPIXELS
    heic = round(budget / image_to_pdf_service.HEIC_MEGAPIXEL_WEIGHT)
    assert {slug for slug, _ in pixels} == set(IMAGE_TO_PDF_TOOLS) - {"jpg-to-pdf", "gif-to-pdf"}, pixels
    assert {n for slug, n in pixels if slug == "heic-to-pdf"} == {heic}, pixels
    assert {n for slug, n in pixels if slug != "heic-to-pdf"} == {budget}, pixels
