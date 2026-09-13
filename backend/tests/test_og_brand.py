"""The dynamic social card reuses the canonical brand asset when available."""
import io
from PIL import Image
from app.routes import og_image


def test_social_card_uses_new_logo_without_changing_output_contract(tmp_path, monkeypatch):
    brand = tmp_path / 'brand'
    brand.mkdir()
    Image.new('RGB', (512, 512), (120, 20, 180)).save(brand / 'privatools-icon-512.png')
    monkeypatch.setattr(og_image, '_CONTENT_DIR', tmp_path)
    output = og_image._make_og_image('A public tool', 'A concise description.', '', (24, 22, 18))
    with Image.open(io.BytesIO(output)) as image:
        assert image.format == 'PNG'
        assert image.size == (1200, 630)
        assert image.getpixel((82, 66)) == (120, 20, 180)
