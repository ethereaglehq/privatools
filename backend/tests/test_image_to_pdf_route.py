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
from PIL import Image, features

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

    def spy(paths, page_size="A4", **kwargs):
        seen["thread"] = threading.current_thread().name
        return convert(paths, page_size=page_size, **kwargs)

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


def test_an_image_over_pillows_pixel_limit_is_refused_by_the_name_it_was_uploaded_under(client, monkeypatch):
    # Pillow refuses to open anything over twice its MAX_IMAGE_PIXELS (178.96
    # million pixels) as a possible decompression bomb. That error used to reach
    # the route as a 500, and then as a 413 naming the server's temporary copy.
    _no_page_may_be_made(monkeypatch)

    response = client.post("/api/image-to-pdf", files=[("files", ("IMG_2041.png", _png_header(14000, 13000), "image/png"))])

    assert response.status_code == 413
    assert response.json()["detail"] == "IMG_2041.png has more than 178 megapixels, the most one image can have."


def test_an_image_over_the_general_pixel_cap_is_told_its_size_rounded_up(client, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "MAX_IMAGE_PIXELS", 2_000_000)
    _no_page_may_be_made(monkeypatch)

    response = client.post("/api/image-to-pdf", files=[("files", ("shot.png", _image("PNG", (2000, 1001)), "image/png"))])

    assert response.status_code == 413
    # 2,002,000 pixels: rounded down, "2 megapixels" would sit next to "at most 2".
    assert response.json()["detail"] == (
        "shot.png is 2,000 × 1,001 pixels, which is 2.1 megapixels; one image can have at most 2 megapixels."
    )


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
        "WEBP": ("a WebP image", 50_000_000),
        "HEIF": ("a HEIC photo", 100_000_000),
        "TIFF": ("a colour TIFF", 120_000_000),
    }


@pytest.mark.parametrize("fmt, name, noun", [
    ("WEBP", "holiday-panorama.webp", "a WebP image"),
    ("HEIF", "IMG_1.heic", "a HEIC photo"),
    ("TIFF", "scan.tiff", "a colour TIFF"),
])
def test_an_image_over_its_formats_pixel_cap_is_refused_by_name_and_true_size(client, monkeypatch, fmt, name, noun):
    small = {key: (text, 2_000_000) for key, (text, _) in image_to_pdf_service.FORMAT_PIXEL_CAPS.items()}
    monkeypatch.setattr(image_to_pdf_service, "FORMAT_PIXEL_CAPS", small)
    _no_page_may_be_made(monkeypatch)

    response = client.post("/api/image-to-pdf", files=[("files", (name, _image(fmt, (2000, 1001)), "image/octet-stream"))])

    assert response.status_code == 413
    assert response.json()["detail"] == (
        f"{name} is 2,000 × 1,001 pixels, which is 2.1 megapixels; {noun} can have at most 2 megapixels."
    )


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


ACCEPTED = "JPEG, PNG, WebP, HEIC, TIFF, BMP or GIF"


def _encoded(fmt: str, **options) -> bytes:
    if not features.check({"JPEG2000": "jpg_2000", "AVIF": "avif"}.get(fmt, fmt.lower())):
        pytest.skip(f"this Pillow cannot write {fmt}")
    buffer = io.BytesIO()
    Image.new("RGB", (120, 90), (40, 90, 160)).save(buffer, fmt, **options)
    return buffer.getvalue()


@pytest.mark.parametrize("name", ["picture.png", "picture.webp", "IMG_1.heic"])
@pytest.mark.parametrize("fmt, options", [("JPEG2000", {}), ("AVIF", {"quality": 50})])
def test_a_format_none_of_the_nine_tools_takes_is_refused_whatever_its_name(client, monkeypatch, fmt, options, name):
    # Pillow decodes JPEG 2000 and AVIF too, and did under these names, outside
    # every per-format cap: a 36-megapixel JPEG 2000 of 540 KB took +667 MB.
    _no_page_may_be_made(monkeypatch)

    response = client.post("/api/image-to-pdf", files=[("files", (name, _encoded(fmt, **options), "application/octet-stream"))])

    assert response.status_code == 400
    assert response.json()["detail"] == f"{name} is not a {ACCEPTED} image."


def test_a_file_that_is_no_image_at_all_is_a_400_naming_it(client):
    response = client.post("/api/image-to-pdf", files=[("files", ("notes.png", b"these are my notes", "image/png"))])

    assert response.status_code == 400
    assert response.json()["detail"] == f"notes.png is not a {ACCEPTED} image."


def test_an_image_cut_short_is_a_400_naming_it(client):
    whole = _image("PNG", (600, 400), colour=(10, 20, 30))
    cut = whole[: len(whole) // 2]

    response = client.post("/api/image-to-pdf", files=[("files", ("shot.png", cut, "image/png"))])

    assert response.status_code == 400
    assert response.json()["detail"] == "shot.png could not be read as an image."


def test_a_multi_picture_jpeg_is_still_embedded_as_it_is(client):
    buffer = io.BytesIO()
    first = Image.new("RGB", (64, 48), (200, 30, 30))
    first.save(buffer, "MPO", save_all=True, append_images=[Image.new("RGB", (64, 48), (30, 30, 200))])

    response = client.post("/api/image-to-pdf", files=[("files", ("DSC_0001.jpg", buffer.getvalue(), "image/jpeg"))])

    assert response.status_code == 200, response.text
    with fitz.open(stream=response.content, filetype="pdf") as document:
        (xref, *_), = document[0].get_images()
        assert document.xref_get_key(xref, "Filter") == ("name", "/DCTDecode")


def test_a_png_named_heic_counts_in_full(client, monkeypatch):
    # HEIC's half weight used to be decided by the file name.
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 2)
    _no_page_may_be_made(monkeypatch)
    files = [("files", (f"IMG_{i}.heic", _image("PNG"), "image/heic")) for i in range(3)]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "One PDF can take up to 2 megapixels of PNG, WebP, TIFF, BMP, GIF and SVG images; these add up to 3."
    )


def test_a_heic_photo_counts_half_and_becomes_a_jpeg_whatever_its_name(client, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 1)
    files = [("files", (f"IMG_{i}.png", _image("HEIF"), "image/png")) for i in range(2)]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 200, response.text
    with fitz.open(stream=response.content, filetype="pdf") as document:
        for page in document:
            (xref, *_), = page.get_images()
            assert document.xref_get_key(xref, "Filter") == ("name", "/DCTDecode")


def _svg(width: int, height: int, body: str = '<rect width="100%" height="100%" fill="#2a6"/>') -> bytes:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{body}</svg>'.encode()


def test_svgs_are_counted_in_the_budget_before_any_is_drawn(client, monkeypatch):
    # A 274-byte SVG draws at up to 78 megapixels (3.9 s of CPU, +307 MB), and
    # every SVG used to be drawn before the budget was checked.
    monkeypatch.setattr(image_to_pdf_service, "MAX_DECODED_MEGAPIXELS", 10)
    monkeypatch.setattr(image_to_pdf_service, "_svg_to_png", lambda *args, **kwargs: pytest.fail("must not draw"))
    _no_page_may_be_made(monkeypatch)
    # Each draws 2,400 pixels wide: 2,400 × 2,400 is 5.76 megapixels.
    files = [("files", (f"logo-{i}.svg", _svg(100, 100), "image/svg+xml")) for i in range(2)]

    response = client.post("/api/image-to-pdf", files=files)

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "One PDF can take up to 10 megapixels of PNG, WebP, TIFF, BMP, GIF and SVG images; these add up to 12."
    )


def test_an_svg_too_tall_to_draw_2400_pixels_wide_is_drawn_narrower(client, monkeypatch):
    # 32,767 pixels is the tallest image cairo draws; past it the SVG was a 500.
    monkeypatch.setattr(image_to_pdf_service, "_SVG_MAX_SIDE", 3000)

    response = client.post("/api/image-to-pdf", files=[("files", ("timeline.svg", _svg(100, 200), "image/svg+xml"))],
                           data={"page_size": "auto"})

    assert response.status_code == 200, response.text
    with fitz.open(stream=response.content, filetype="pdf") as document:
        assert (document[0].rect.width, document[0].rect.height) == (1500, 3000)


@pytest.mark.parametrize("svg, reason", [
    (b'<svg xmlns="http://www.w3.org/2000/svg" width="10"', "could not be drawn: it is not a valid SVG."),
    (_svg(10, 10, '<image href="http://169.254.169.254/latest" width="10" height="10"/>'),
     "loads an image from another file or a web address, which is not allowed."),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="5" height="5"/></svg>',
     "could not be drawn: it has no width or height."),
])
def test_an_svg_that_cannot_be_drawn_is_a_400_naming_it(client, svg, reason):
    response = client.post("/api/image-to-pdf", files=[("files", ("drawing.svg", svg, "image/svg+xml"))])

    assert response.status_code == 400
    assert response.json()["detail"] == f"drawing.svg {reason}"


def test_only_a_refusal_for_size_is_a_413(client, monkeypatch):
    # Any ValueError used to become a 413 carrying its text, such as Pillow's
    # "non-hexadecimal number found in fromhex() arg at position 0".
    def fail(*args, **kwargs):
        raise ValueError("non-hexadecimal number found in fromhex() arg at position 0")

    monkeypatch.setattr(image_to_pdf_service, "images_to_pdf", fail)

    response = client.post("/api/image-to-pdf", files=_images(1))

    assert response.status_code == 500
    assert "hexadecimal" not in response.text


def test_the_counts_the_guides_give_follow_from_the_limits():
    megabytes = route.MAX_TOTAL_UPLOAD_BYTES / MB
    budget = image_to_pdf_service.MAX_DECODED_MEGAPIXELS
    # A 12-megapixel phone photo is about 3.8 MB as a JPEG, 1.8 MB as a HEIC
    # or a lossy WebP, and 23 MB saved as a PNG.
    assert 45 <= megabytes / 3.8 <= 55  # JPEG photos: the megabytes run out
    assert 55 <= budget / 12.2 <= 65  # WebP photos: the megapixels run out
    assert megabytes / 23 < 10  # PNG photos: the megabytes run out
    assert 100 * 12.2 * image_to_pdf_service.HEIC_MEGAPIXEL_WEIGHT <= budget and 100 * 1.8 <= megabytes  # HEIC

    image = " ".join(step["text"] for step in TOOL_HOWTO["image-to-pdf"])
    for claim in ("roughly 50 phone photos", "fewer than 10", "about 60 phone-size WebP photos",
                  "100 photos from a 12-megapixel iPhone"):
        assert claim in image, claim
    # A phone photo saved as PNG is not one of the ~60 that fit the megapixels.
    assert "PNG or WebP photos" not in image


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
