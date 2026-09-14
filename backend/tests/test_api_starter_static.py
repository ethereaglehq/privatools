"""Full middleware must serve starter source downloads rather than SEO HTML."""
import pytest
from fastapi.testclient import TestClient

from backend.app import main


@pytest.fixture()
def starter_static(tmp_path, monkeypatch):
    root = tmp_path / "build"
    directory = root / "api-starters"
    directory.mkdir(parents=True)
    files = {
        "README.md": b"# Synthetic starter instructions\n",
        "privatools.py": b"print('synthetic starter source')\n",
        "privatools.mjs": b"console.log('synthetic starter source');\n",
        "manifest.json": b'{"version":1,"files":[]}',
    }
    for name, content in files.items():
        (directory / name).write_bytes(content)
    index = root / "index.html"
    index.write_text("<!doctype html><html><head><title>App</title></head><body>App shell</body></html>")
    # This file is deliberately outside the public build boundary.
    (tmp_path / "private.py").write_text("private synthetic marker")
    (directory / "outside.py").symlink_to(tmp_path / "private.py")
    monkeypatch.setattr(main, "_frontend_path", root)
    monkeypatch.setattr(main, "_INDEX_HTML", index)
    main._frontend_file_inventory.cache_clear()
    client = TestClient(main.app, base_url="http://localhost")
    yield client, files
    main._frontend_file_inventory.cache_clear()


@pytest.mark.parametrize("name,media", [
    ("README.md", "text/markdown"),
    ("privatools.py", "text/x-python"),
    ("privatools.mjs", "text/javascript"),
    ("manifest.json", "application/json"),
])
def test_starter_download_bytes_and_media_survive_full_middleware(starter_static, name, media):
    client, files = starter_static
    response = client.get("/api-starters/" + name)
    assert response.status_code == 200
    assert response.content == files[name]
    # Some OS MIME databases identify JS as application/javascript.
    actual = response.headers["content-type"].split(";")[0]
    assert actual == media or (media == "text/javascript" and actual == "application/javascript")
    assert response.headers["cache-control"] == "no-cache"
    head = client.head("/api-starters/" + name)
    assert head.status_code == 200 and head.content == b""
    assert head.headers["content-length"] == str(len(files[name]))


@pytest.mark.parametrize("path", [
    "/api-starters/missing.py", "/api-starters/missing.md",
    "/api-starters/missing", "/api-starters/outside.py",
    "/api-starters/%2e%2e/private.py", "/api-starters/%2e%2e%2fprivate.py",
])
def test_missing_and_traversal_starter_paths_return_json_404(starter_static, path):
    client, _ = starter_static
    response = client.get(path)
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Not found"}
    assert b"private synthetic marker" not in response.content


def test_starter_bypass_does_not_change_other_source_extension_routes(starter_static):
    client, _ = starter_static
    response = client.get("/api-starters-other/private.py")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert b"private synthetic marker" not in response.content
