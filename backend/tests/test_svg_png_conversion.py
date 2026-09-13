"""Real SVG rendering exercises the guarded CairoSVG integration contract."""
import base64
import io
from pathlib import Path

import pytest
from PIL import Image

from backend.app.services.svg_to_png_service import svg_to_png


def test_inline_svg_renders_at_requested_scale(tmp_path):
    source = tmp_path / "icon.svg"
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="30"><rect width="40" height="30" fill="#c94363"/></svg>')
    output = Path(svg_to_png(str(source), scale=2))
    try:
        with Image.open(output) as image:
            assert image.format == "PNG"
            assert image.size == (80, 60)
            assert image.convert("RGB").getpixel((20, 20)) == (201, 67, 99)
    finally:
        output.unlink(missing_ok=True)


def test_inline_data_image_is_decoded_without_external_fetch(tmp_path):
    png = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(png, format="PNG")
    encoded = base64.b64encode(png.getvalue()).decode()
    source = tmp_path / "embedded.svg"
    source.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="4" height="4"><image width="4" height="4" xlink:href="data:image/png;base64,{encoded}"/></svg>')
    output = Path(svg_to_png(str(source), scale=1))
    try:
        with Image.open(output) as image:
            assert image.size == (4, 4)
            assert image.convert("RGB").getpixel((2, 2)) == (255, 0, 0)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.parametrize("url", ["https://example.invalid/private.png", "http://169.254.169.254/latest/meta-data/", "file:///etc/passwd"])
def test_external_svg_images_are_rejected_before_resource_access(tmp_path, monkeypatch, url):
    import cairosvg.url

    def forbidden_fetch(*args, **kwargs):
        pytest.fail("The default external URL fetcher must never run")

    monkeypatch.setattr(cairosvg.url, "urlopen", forbidden_fetch)
    source = tmp_path / "external.svg"
    source.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="40" height="30"><image width="40" height="30" xlink:href="{url}"/></svg>')
    with pytest.raises(ValueError, match="external SVG reference blocked"):
        svg_to_png(str(source), scale=1)
