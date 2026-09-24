"""ReportLab writes binary streams, not ASCII85, in every service.

By default ReportLab ASCII85-encodes every image and page stream
(``rl_config.useA85 = 1``), in pure Python because its optional C accelerator
is not installed. In Image to PDF that was about 95% of the CPU time: 100
phone photos took 124 s where 6.3 s would do, and the PDF came out a quarter
bigger than its JPEGs (PR #270). ASCII85 only keeps a file 7-bit clean; PDF
readers take binary streams.

``backend/app/utils/__init__.py`` turns it off once per process. Every module
that imports ReportLab also imports that package at module level, so no
conversion can run before the setting is in place.
"""
from __future__ import annotations

import ast
import base64
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pikepdf
import pytest
from PIL import Image
from reportlab.lib.rl_accel import asciiBase85Encode

from backend.app.services import edit_pdf_service, image_to_pdf_service, qr_code_service, txt_to_pdf_service

REPO = Path(__file__).resolve().parents[2]
APP = REPO / "backend" / "app"


def _imports(tree: ast.Module, module: str) -> list[tuple[str, bool]]:
    """(imported module, is top level) for every import in a module's AST."""
    package = module.rsplit(".", 1)[0]
    found = []
    top_level = set(map(id, tree.body))
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")
                base = base[: len(base) - node.level + 1]
                names = [".".join([*base, node.module] if node.module else base)]
            else:
                names = [node.module or ""]
        found += [(name, id(node) in top_level) for name in names]
    return found


def test_every_module_that_imports_reportlab_imports_the_utils_package_first():
    users = []
    for path in sorted(APP.rglob("*.py")):
        module = ".".join(path.relative_to(REPO).with_suffix("").parts)
        if module == "backend.app.utils.__init__":
            continue  # it sets the encoding
        imports = _imports(ast.parse(path.read_text()), module)
        if not any(name == "reportlab" or name.startswith("reportlab.") for name, _ in imports):
            continue
        users.append(module)
        assert any(
            top and (name == "backend.app.utils" or name.startswith("backend.app.utils."))
            for name, top in imports
        ), f"{module} imports ReportLab but not backend.app.utils, which sets its stream encoding"
    # The fifteen ReportLab services at the time of writing; a scan that finds
    # none would pass for the wrong reason.
    assert len(users) >= 15, users


def test_importing_one_service_turns_ascii85_off_in_a_fresh_worker():
    code = (
        "from reportlab import rl_config\n"
        "assert rl_config.useA85 == 1, 'ReportLab default changed; revisit this test'\n"
        "import backend.app.services.txt_to_pdf_service\n"
        "print(rl_config.useA85)\n"
    )
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=REPO, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0"


def _stream_filters(path: str) -> list[tuple[str, list[str]]]:
    filters = []
    with pikepdf.open(path) as pdf:
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Stream):
                value = obj.get("/Filter")
                names = [] if value is None else [str(value)] if isinstance(value, pikepdf.Name) else [str(v) for v in value]
                filters.append((str(obj.get("/Subtype", "")), names))
    return filters


def _photos(tmp_path: Path, count: int = 6) -> list[str]:
    """Noisy 1200x900 JPEGs: grain keeps them near a phone photo's bytes per pixel."""
    rng = np.random.default_rng(7)
    base = np.linspace(0, 255, 900 * 1200 * 3).reshape(900, 1200, 3)
    paths = []
    for index in range(count):
        pixels = np.clip(base + rng.normal(0, 18, base.shape), 0, 255).astype(np.uint8)
        path = tmp_path / f"photo-{index}.jpg"
        Image.fromarray(pixels).save(path, "JPEG", quality=90)
        paths.append(str(path))
    return paths


@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(image_to_pdf_service, "ensure_temp_dir", lambda: None)
    monkeypatch.setattr(image_to_pdf_service, "get_temp_path", lambda name: tmp_path / name)
    return tmp_path


@pytest.mark.parametrize("page_size", ["A4", "auto"])
def test_image_to_pdf_embeds_jpegs_byte_for_byte(temp_dir, page_size):
    photos = _photos(temp_dir)
    jpeg_bytes = sum(os.path.getsize(p) for p in photos)

    output = image_to_pdf_service.images_to_pdf(photos, page_size)

    with pikepdf.open(output) as pdf:
        embedded = [image.read_raw_bytes() for page in pdf.pages for image in page.get_images().values()]
    assert embedded == [Path(p).read_bytes() for p in photos]
    # ASCII85 made the file 25% bigger than its JPEGs; now only the page
    # structure is added.
    assert os.path.getsize(output) <= jpeg_bytes * 1.01 + 16 * 1024


def test_image_to_pdf_cpu_is_a_small_fraction_of_ascii85_encoding_the_same_bytes(temp_dir):
    photos = _photos(temp_dir)
    data = b"".join(Path(p).read_bytes() for p in photos)
    # A yardstick measured on the same machine, so the bound holds on a slow
    # CI runner too: with ASCII85 on, the conversion costs at least this much.
    started = time.process_time()
    asciiBase85Encode(data)
    ascii85_cpu = time.process_time() - started

    started = time.process_time()
    image_to_pdf_service.images_to_pdf(photos, "auto")
    conversion_cpu = time.process_time() - started

    assert conversion_cpu < ascii85_cpu / 4, (conversion_cpu, ascii85_cpu)


def test_no_stream_is_ascii85_encoded(temp_dir, monkeypatch, tmp_path):
    for service in (txt_to_pdf_service, qr_code_service, edit_pdf_service):
        monkeypatch.setattr(service, "temp_output", lambda prefix, ext: tmp_path / f"{prefix}.{ext}")
    text = tmp_path / "notes.txt"
    text.write_text("Binary streams are fine.\n" * 200)
    # Page streams.
    text_pdf = txt_to_pdf_service.txt_to_pdf(str(text))
    # A decoded image, deflated.
    qr_pdf = qr_code_service.generate_qr_pdf("https://example.org/a", size=300)
    # A JPEG placed on an existing page, which pikepdf then saves: qpdf strips
    # ASCII85 from deflated streams on save but kept it on JPEGs.
    photo = Path(_photos(tmp_path, 1)[0]).read_bytes()
    source = tmp_path / "source.pdf"
    with pikepdf.new() as blank:
        blank.add_blank_page(page_size=(595, 842))
        blank.save(source)
    edited_pdf = edit_pdf_service.edit_pdf(str(source), [{
        "page": 1, "type": "image", "x": 50, "y": 50, "width": 240, "height": 180,
        "image_data": "data:image/jpeg;base64," + base64.b64encode(photo).decode(),
    }])
    screenshot = temp_dir / "screenshot.png"
    Image.new("RGB", (300, 200), (20, 120, 200)).save(screenshot)
    image_pdf = image_to_pdf_service.images_to_pdf([_photos(temp_dir, 1)[0], str(screenshot)], "A4")

    for output in (text_pdf, qr_pdf, edited_pdf, image_pdf):
        filters = _stream_filters(output)
        assert filters, output
        assert all("/ASCII85Decode" not in names for _, names in filters), (output, filters)
    assert [names for kind, names in _stream_filters(qr_pdf) if kind == "/Image"] == [["/FlateDecode"]]
    with pikepdf.open(edited_pdf) as pdf:
        assert [image.read_raw_bytes() for image in pdf.pages[0].get_images().values()] == [photo]
    assert sorted(names for kind, names in _stream_filters(image_pdf) if kind == "/Image") == [
        ["/DCTDecode"], ["/FlateDecode"],
    ]
