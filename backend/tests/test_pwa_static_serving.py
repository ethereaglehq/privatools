"""The real ASGI server must serve an installable, nonce-consistent PWA build."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

import pytest


@pytest.fixture()
def frontend_build(tmp_path, monkeypatch):
    import backend.app.main as main

    root = tmp_path / "build"
    for directory in ("assets", "fonts", "icons", "pwa"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    script = b"document.documentElement.dataset.ready = 'yes';"
    integrity = "sha384-" + base64.b64encode(hashlib.sha384(script).digest()).decode()
    (root / "assets/main-abcd.js").write_bytes(script)
    (root / "index.html").write_text(
        '<!doctype html><html><head><title>PrivaTools</title>'
        '<script>window.prepaint = true;</script>'
        f'<script type="module" src="/assets/main-abcd.js" integrity="{integrity}" crossorigin="anonymous"></script>'
        '</head><body><div id="root">Public app shell</div></body></html>'
    )
    (root / "manifest.json").write_text(json.dumps({"name": "PrivaTools", "start_url": "/", "display": "standalone"}))
    (root / "sw.js").write_text("self.addEventListener('fetch', () => {});")
    (root / "local-runtime.wasm").write_bytes(b"\x00asm\x01\x00\x00\x00")
    (root / "fonts/test.woff2").write_bytes(b"font fixture")
    (root / "pwa/air-desktop.png").write_bytes(b"screenshot fixture")
    monkeypatch.setattr(main, "_frontend_path", root)
    monkeypatch.setattr(main, "_INDEX_HTML", root / "index.html")
    main._get_seo_html.cache_clear()
    yield root, integrity
    main._get_seo_html.cache_clear()


def test_precache_index_is_200_and_keeps_sri_and_nonce_policy(client, frontend_build):
    _, integrity = frontend_build
    response = client.get("/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-cache"
    assert f'integrity="{integrity}"' in response.text
    nonce = re.search(r"'nonce-([^']+)'", response.headers["content-security-policy"]).group(1)
    scripts = re.findall(r"<script\b[^>]*>", response.text)
    assert len(scripts) == 2
    assert all(f'nonce="{nonce}"' in tag for tag in scripts)
    assert client.get("/index.html").headers["content-security-policy"] != response.headers["content-security-policy"]


def test_worker_is_revalidated_and_manifest_has_install_media_type(client, frontend_build):
    worker = client.get("/sw.js")
    assert worker.status_code == 200
    assert "javascript" in worker.headers["content-type"]
    assert worker.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"
    assert worker.headers["service-worker-allowed"] == "/"
    assert "worker-src 'self' blob:" in worker.headers["content-security-policy"]
    manifest = client.get("/manifest.json")
    assert manifest.status_code == 200
    assert "application/manifest+json" in manifest.headers["content-type"]
    assert manifest.headers["cache-control"] == "no-cache"
    assert manifest.json()["start_url"] == "/"


@pytest.mark.parametrize("path,expected", [
    ("/assets/main-abcd.js", b"document.documentElement"),
    ("/local-runtime.wasm", b"\x00asm"),
    ("/fonts/test.woff2", b"font fixture"),
    ("/pwa/air-desktop.png", b"screenshot fixture"),
])
def test_runtime_assets_bypass_spa_seo(client, frontend_build, path, expected):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content.startswith(expected)
    assert "text/html" not in response.headers["content-type"]
    if path.startswith("/assets/"):
        assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.parametrize("path", ["/assets/missing.js", "/missing.wasm", "/missing.webmanifest", "/pwa/missing.png", "/missing.html"])
def test_missing_build_asset_is_a_real_404(client, frontend_build, path):
    response = client.get(path)
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"


def test_public_html_revalidates_and_account_html_cannot_be_cached(client, frontend_build):
    assert client.get("/pipeline").headers["cache-control"] == "no-cache"
    assert client.get("/account/settings").headers["cache-control"] == "no-store"
    assert client.get("/api/health").headers["cache-control"] == "no-store, max-age=0"


def test_static_file_symlink_cannot_escape_to_a_similarly_prefixed_directory(client, frontend_build):
    root, _ = frontend_build
    sibling = root.parent / "build-private"
    sibling.mkdir()
    (sibling / "secret.txt").write_text("private value")
    (root / "leak.txt").symlink_to(sibling / "secret.txt")
    response = client.get("/leak.txt")
    assert response.status_code == 404
    assert "private value" not in response.text


def test_custom_frontend_root_is_respected(monkeypatch, tmp_path):
    import backend.app.main as main
    monkeypatch.setenv("FRONTEND_PATH", str(tmp_path))
    assert main._resolve_frontend_path() == tmp_path
