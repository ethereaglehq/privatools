"""Native decoder failures stay outside ASGI, with working local fallbacks."""
from __future__ import annotations

import json
import subprocess
import sys

import pytest
from PIL import Image

from backend.app.services import qr_reader_service as reader
from backend.app.utils.exceptions import (
    DependencyError,
    ExternalToolError,
    ToolTimeoutError,
    UnsupportedFileError,
    ValidationError,
)


CODE = {"data": "invoice-123", "type": "CODE128", "rect": {
    "left": 5, "top": 8, "width": 120, "height": 40,
}}


@pytest.fixture
def blank_image(tmp_path):
    path = tmp_path / "blank.png"
    Image.new("RGB", (100, 80), (200, 60, 90)).save(path)
    return str(path)


def test_primary_decoder_preserves_barcode_contract_and_uses_isolated_python(monkeypatch, blank_image):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, json.dumps({"ok": True, "codes": [CODE]}).encode())

    monkeypatch.setattr(reader.subprocess, "run", run)
    assert reader.read_qr(blank_image) == [CODE]
    assert len(calls) == 1
    command, options = calls[0]
    assert command == [sys.executable, "-I", str(reader._DECODE_WORKER), "zbar", blank_image]
    assert options == {
        "stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE,
        "stderr": subprocess.DEVNULL, "timeout": 10, "check": False,
    }


def test_native_crash_uses_fallback_without_losing_rect(monkeypatch, blank_image):
    engines = []

    def run(command, **kwargs):
        engines.append(command[3])
        if command[3] == "zbar":
            return subprocess.CompletedProcess(command, -11, b"")
        return subprocess.CompletedProcess(command, 0, json.dumps({"ok": True, "codes": [CODE]}).encode())

    monkeypatch.setattr(reader.subprocess, "run", run)
    assert reader.read_qr(blank_image) == [CODE]
    assert engines == ["zbar", "opencv"]


@pytest.mark.parametrize("payload", [
    b"native diagnostic, not JSON", b"[]", b'{"ok":false,"error":[]}',
    b'{"ok":true,"codes":[{"data":"x","type":"QRCODE","rect":{"left":0,"top":0,"width":true,"height":1}}]}',
    b'{"ok":true,"codes":[{"data":"x","type":"QRCODE","rect":{"left":0,"top":0,"width":-1,"height":1}}]}',
    b'{"ok":true,"codes":null}',
])
def test_malformed_worker_output_is_not_trusted(monkeypatch, blank_image, payload):
    monkeypatch.setattr(reader.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, payload))
    assert reader._run_decoder("zbar", blank_image) == ("failed", [])


def test_worker_timeout_is_enforced_in_a_real_child(monkeypatch, tmp_path, blank_image):
    worker = tmp_path / "slow_worker.py"
    worker.write_text("import time\ntime.sleep(5)\n")
    monkeypatch.setattr(reader, "_DECODE_WORKER", worker)
    monkeypatch.setattr(reader, "_DECODE_TIMEOUT_SECONDS", 0.1)
    assert reader._run_decoder("zbar", blank_image) == ("timeout", [])


@pytest.mark.parametrize("primary,fallback,expected", [
    ("dependency", "dependency", DependencyError),
    ("failed", "failed", ExternalToolError),
    ("timeout", "failed", ToolTimeoutError),
    ("failed", "timeout", ToolTimeoutError),
    ("failed", "invalid", ValidationError),
    ("invalid", "ok", ValidationError),
])
def test_failed_engines_have_typed_errors(monkeypatch, blank_image, primary, fallback, expected):
    monkeypatch.setattr(reader, "_run_decoder", lambda engine, path: (primary if engine == "zbar" else fallback, []))
    with pytest.raises(expected):
        reader.read_qr(blank_image)


def test_invalid_image_does_not_start_a_decoder(monkeypatch, tmp_path):
    invalid = tmp_path / "invalid.png"
    invalid.write_text("not image data")
    monkeypatch.setattr(reader, "_run_decoder", lambda *args: pytest.fail("Invalid image reached native code"))
    with pytest.raises(UnsupportedFileError):
        reader.read_qr(str(invalid))


def test_existing_opencv_dependency_reads_blank_and_generated_qr_in_subprocess(blank_image, tmp_path):
    import qrcode

    assert reader._run_decoder("opencv", blank_image) == ("ok", [])
    path = tmp_path / "qr.png"
    expected = "https://privatools.me/verified-local-qr"
    qrcode.make(expected).save(path)
    status, codes = reader._run_decoder("opencv", str(path))
    assert status == "ok"
    assert len(codes) == 1
    assert codes[0]["data"] == expected
    assert codes[0]["type"] == "QRCODE"
    assert codes[0]["rect"]["width"] > 0
    assert codes[0]["rect"]["height"] > 0


def test_existing_opencv_dependency_reads_generated_ean13_in_subprocess(tmp_path):
    from barcode import EAN13
    from barcode.writer import ImageWriter

    path = EAN13("590123412345", writer=ImageWriter()).save(str(tmp_path / "ean13"))
    status, codes = reader._run_decoder("opencv", path)
    assert status == "ok"
    assert len(codes) == 1
    assert codes[0]["data"] == "5901234123457"
    assert codes[0]["type"] == "EAN13"
    assert codes[0]["rect"]["width"] > 0
    assert codes[0]["rect"]["height"] > 0


def test_real_qr_route_reads_generated_code_and_stays_healthy(client, tmp_path):
    import qrcode

    path = tmp_path / "route-qr.png"
    expected = "PrivaTools QR subprocess integration"
    qrcode.make(expected).save(path)
    response = client.post("/api/read-qr", files={"file": ("qr.png", path.read_bytes(), "image/png")})
    assert response.status_code == 200
    codes = response.json()["codes"]
    assert codes[0]["data"] == expected
    assert codes[0]["type"] == "QRCODE"
    assert reader._valid_codes(codes)
    assert "no-store" in response.headers["cache-control"]
    assert client.get("/api/health").status_code == 200
