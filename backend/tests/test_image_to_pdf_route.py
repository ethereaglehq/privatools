"""POST /api/image-to-pdf takes up to 100 images, within a combined size cap.

Nine tools share this route: Image, JPG, PNG, HEIC, WebP, TIFF, BMP, GIF and
SVG to PDF. The limits here are theirs, and their page copy states them.
"""
from __future__ import annotations

import io
import re
import threading
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
    # Measured before raising the image count (PR "Let Image to PDF take 100
    # images"): ReportLab holds every page and formats the whole file in memory,
    # so 358 MB of phone photos peaked at +1.4 GB RSS and took 124 s of CPU on
    # the 2-core ARM VM. Raising this cap needs a cheaper writer first.
    assert route.MAX_TOTAL_UPLOAD_BYTES == 200 * MB


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


def test_the_page_enforces_the_same_limits_as_the_route():
    source = (REPO / "frontend/src/components/tool-ui/image-to-pdf-limits.ts").read_text()
    assert re.search(r"IMAGE_TO_PDF_MAX_FILES = (\d+);", source).group(1) == str(route.MAX_FILES)
    assert re.search(r"IMAGE_TO_PDF_MAX_TOTAL_MB = (\d+);", source).group(1) == str(route.MAX_TOTAL_UPLOAD_BYTES // MB)


def _tool_copy(slug: str) -> list[str]:
    registry = (REPO / "frontend/src/data/tools.ts").read_text()
    entry = registry.split(f'slug: "{slug}"', 1)[1].split("slug:", 1)[0]
    guide = [step["text"] for step in TOOL_HOWTO.get(slug, [])]
    guide += [part for item in TOOL_FAQ.get(slug, []) for part in (item["q"], item["a"])]
    return [entry, *guide]


def test_every_limit_the_nine_tools_state_matches_the_route():
    counts, sizes = [], []
    for slug in IMAGE_TO_PDF_TOOLS:
        for text in _tool_copy(slug):
            counts += [(slug, int(n)) for n in re.findall(r"(?i)\bup to (\d+) (?:images|files|photos)\b", text)]
            sizes += [(slug, int(n)) for n in re.findall(r"\b(\d+) MB\b", text)]
    assert len(counts) >= 10 and len(sizes) >= 10, (counts, sizes)
    assert {n for _, n in counts} == {route.MAX_FILES}, counts
    assert {n for _, n in sizes} == {route.MAX_TOTAL_UPLOAD_BYTES // MB}, sizes
