"""A fresh worker decodes HEIC without another tool warming it up first.

Pillow cannot read HEIC by itself; pillow-heif adds the codec only in a
process where `register_heif_opener()` has run. Routes that `Image.open`
an upload with plain PIL (`/image-converter` behind heic-to-png,
remove-exif, image-compressor) therefore accept iPhone photos only if the
opener is registered while the app is imported — not lazily inside one
tool's function, where it helps only the requests that follow that tool
in the same worker.

The pytest process can't show this: conftest imports the whole app, and
any earlier test may have registered the opener. So the conversion runs in
a new interpreter that imports the app as a uvicorn worker does and serves
exactly one request.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pillow_heif
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]

_WORKER = """
import asyncio, json, sys
from pathlib import Path

import httpx

from backend.app.main import app
from backend.app.rate_limit import limiter

limiter.enabled = False
heic, out = Path(sys.argv[1]), Path(sys.argv[2])


async def convert():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        return await client.post(
            "/api/image-converter",
            files={"file": ("IMG_0001.HEIC", heic.read_bytes(), "image/heic")},
            data={"target_format": "png"},
        )


response = asyncio.run(convert())
(out / "body").write_bytes(response.content)
(out / "meta.json").write_text(json.dumps({
    "status": response.status_code,
    "content_type": response.headers.get("content-type"),
}))
"""


def test_fresh_worker_converts_heic_to_png(tmp_path):
    heic = tmp_path / "IMG_0001.HEIC"
    source = Image.new("RGB", (16, 12), (30, 120, 200))
    pillow_heif.from_pillow(source).save(heic, quality=95)

    child = subprocess.run(
        [sys.executable, "-c", _WORKER, str(heic), str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
    )
    assert child.returncode == 0, child.stderr[-3000:]

    meta = json.loads((tmp_path / "meta.json").read_text())
    body = (tmp_path / "body").read_bytes()
    assert meta["status"] == 200, body[:500]
    assert meta["content_type"] == "image/png"

    with Image.open(tmp_path / "body") as png:
        assert png.format == "PNG"
        assert png.size == (16, 12)
        # HEVC is lossy; a flat colour survives within a couple of levels.
        r, g, b = png.convert("RGB").getpixel((8, 6))
        assert abs(r - 30) <= 4 and abs(g - 120) <= 4 and abs(b - 200) <= 4
