"""The image workspace exports one correctly sized PDF page per source image."""

import re
from pathlib import Path

import fitz
import pikepdf
import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, LETTER

from backend.app.services import image_to_pdf_service


@pytest.mark.parametrize("page_size,dimensions", [("A4", A4), ("Letter", LETTER), ("auto", None)])
def test_image_pages_preserve_order_and_fit_selected_paper(tmp_path, monkeypatch, page_size, dimensions):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    sources = [(1600, 1000), (240, 340)]
    paths = []
    for index, size in enumerate(sources):
        path = tmp_path / f"source-{index}.png"
        Image.new("RGB", size, (index * 200, 40, 80)).save(path)
        paths.append(str(path))

    output = image_to_pdf_service.images_to_pdf(paths, page_size)

    assert Path(output).is_file()
    with fitz.open(output) as document:
        assert document.page_count == len(sources)
        for page, source in zip(document, sources):
            assert (page.rect.width, page.rect.height) == pytest.approx(dimensions or source, abs=0.01)
            images = page.get_images()
            assert len(images) == 1
            # The embedded dimensions also prove the images kept their input order.
            assert images[0][2:4] == source
            image_rect = page.get_image_rects(images[0][0])[0]
            if dimensions:
                assert image_rect.x0 >= 36 - 0.01
                assert image_rect.y0 >= 36 - 0.01
                assert image_rect.x1 <= page.rect.width - 36 + 0.01
                assert image_rect.y1 <= page.rect.height - 36 + 0.01
                assert image_rect.x0 == pytest.approx(page.rect.width - image_rect.x1, abs=0.01)
                assert image_rect.y0 == pytest.approx(page.rect.height - image_rect.y1, abs=0.01)
            else:
                assert tuple(image_rect) == pytest.approx(tuple(page.rect), abs=0.01)
            assert image_rect.width / image_rect.height == pytest.approx(source[0] / source[1], rel=0.001)


def test_svg_is_rendered_into_pdf_with_guarded_cairo_fetcher(tmp_path, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    source = tmp_path / "drawing.svg"
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="320"><rect width="480" height="320" fill="#c94363"/></svg>')
    output = image_to_pdf_service.images_to_pdf([str(source)], "A4")
    with fitz.open(output) as document:
        assert document.page_count == 1
        assert tuple(document[0].rect)[2:] == pytest.approx(A4, abs=0.01)
        assert document[0].get_images()[0][2:4] == (2400, 1600)
    assert not list(tmp_path.glob("svg_to_png_*.png")), "Temporary SVG render should be removed"


def test_svg_pdf_blocks_external_image_fetches(tmp_path, monkeypatch):
    import cairosvg.url
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    monkeypatch.setattr(cairosvg.url, "urlopen", lambda *args, **kwargs: pytest.fail("External fetch must not run"))
    source = tmp_path / "external.svg"
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="40" height="30"><image width="40" height="30" xlink:href="https://example.invalid/private.png"/></svg>')
    with pytest.raises(image_to_pdf_service.UnreadableImage, match="^external.svg loads an image from another file"):
        image_to_pdf_service.images_to_pdf([str(source)], "A4")
    assert not list(tmp_path.glob("svg_to_png_*.png")), "The drawing that failed must not be left behind"


REPO = Path(__file__).resolve().parents[2]


def _formats_label(component: str) -> str:
    """The dropzone label of one of the named Image to PDF pages."""
    source = (REPO / "frontend/src/components/tool-ui/NamedImageToPdfVariants.tsx").read_text()
    return re.search(rf'function {component}\(\).*?formatsLabel="([^"]+)"', source, re.S).group(1)


def test_png_to_pdf_says_transparent_areas_are_not_kept(tmp_path, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    # A red disc on a transparent background whose hidden pixels are black, as
    # most editors store them.
    logo = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    ImageDraw.Draw(logo).ellipse([50, 0, 150, 100], fill=(220, 30, 40, 255))
    source = tmp_path / "logo.png"
    logo.save(source)

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    with pikepdf.open(output) as pdf:
        (image,) = pdf.pages[0].get_images().values()
        assert "/SMask" not in image and "/Mask" not in image
    with fitz.open(output) as document:
        assert document[0].get_pixmap(dpi=72, alpha=False).pixel(2, 2) == (0, 0, 0)
    # The page used to promise "transparency preserved".
    label = _formats_label("PngToPdfUI")
    assert "transparent areas are not kept" in label and "preserved" not in label


def test_tiff_to_pdf_says_only_the_first_page_of_a_multi_page_tiff_is_used(tmp_path, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    pages = [Image.new("RGB", (300, 200), colour) for colour in ((200, 0, 0), (0, 160, 0), (0, 0, 200))]
    source = tmp_path / "scan.tiff"
    pages[0].save(source, save_all=True, append_images=pages[1:])

    output = image_to_pdf_service.images_to_pdf([str(source)], "auto")

    with fitz.open(output) as document:
        assert document.page_count == 1
        assert document[0].get_pixmap(dpi=72).pixel(150, 100) == (200, 0, 0)
    # The page used to promise that multi-page TIFFs are unpacked.
    label = _formats_label("TiffToPdfUI")
    assert "only the first page of a multi-page TIFF is used" in label and "unpacked" not in label


def test_an_svg_drawn_at_the_height_cap_still_draws_a_full_canvas_gradient(tmp_path):
    # cairo draws nothing for a gradient filling the whole canvas when the
    # canvas is exactly 32,767 pixels tall, and the transparent page then
    # comes out black. A tall, narrow SVG is capped at _SVG_MAX_SIDE, so the
    # cap has to stay below that height. 1:1000 keeps it near one megapixel.
    svg = tmp_path / "tall.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1000" viewBox="0 0 1 1000">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ff0000"/><stop offset="1" stop-color="#0000ff"/>'
        "</linearGradient></defs>"
        '<rect width="1" height="1000" fill="url(#g)"/></svg>'
    )
    width, height = image_to_pdf_service._svg_size(str(svg), "tall.svg")
    assert height == image_to_pdf_service._SVG_MAX_SIDE
    out = tmp_path / "tall.png"
    image_to_pdf_service._svg_to_png(str(svg), str(out), width, height)
    with Image.open(out) as img:
        rgba = img.convert("RGBA")
        assert rgba.getchannel("A").getextrema()[1] == 255, "the gradient was not drawn"
        top = rgba.getpixel((width // 2, 10))
        bottom = rgba.getpixel((width // 2, height - 10))
    assert top[0] > 200 and top[2] < 60, top
    assert bottom[2] > 200 and bottom[0] < 60, bottom
