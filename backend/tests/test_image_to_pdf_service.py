"""The image workspace exports one correctly sized PDF page per source image."""

from pathlib import Path

import fitz
import pytest
from PIL import Image
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
    with pytest.raises(ValueError, match="external SVG reference blocked"):
        image_to_pdf_service.images_to_pdf([str(source)], "A4")
