"""Decode QR and barcodes without allowing a native crash to kill the server."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from ..utils.exceptions import DependencyError, ExternalToolError, ToolTimeoutError, ValidationError
from ..utils.images import open_image_safe

logger = logging.getLogger(__name__)
_DECODE_WORKER = Path(__file__).with_name("_qr_decode_worker.py")
_DECODE_TIMEOUT_SECONDS = 10
_MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_MAX_CODES = 1000


def _valid_codes(value: object) -> bool:
    if not isinstance(value, list) or len(value) > _MAX_CODES:
        return False
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("data"), str) or not isinstance(item.get("type"), str):
            return False
        rect = item.get("rect")
        if not isinstance(rect, dict) or any(type(rect.get(key)) is not int for key in ("left", "top", "width", "height")):
            return False
        if rect["width"] < 0 or rect["height"] < 0:
            return False
    return True


def _run_decoder(engine: str, image_path: str) -> tuple[str, list[dict]]:
    """Bound native execution and return a small, validated JSON protocol."""
    try:
        process = subprocess.run(
            [sys.executable, "-I", str(_DECODE_WORKER), engine, str(Path(image_path).resolve())],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=_DECODE_TIMEOUT_SECONDS, check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout", []
    except OSError:
        return "dependency", []
    # SIGSEGV/SIGABRT stays inside the child, and subprocess.run reaps it.
    if process.returncode < 0 or len(process.stdout) > _MAX_OUTPUT_BYTES:
        return "failed", []
    try:
        payload = json.loads(process.stdout)
    except (ValueError, UnicodeDecodeError):
        return "failed", []
    if not isinstance(payload, dict):
        return "failed", []
    if process.returncode == 0 and payload.get("ok") is True and _valid_codes(payload.get("codes")):
        return "ok", payload["codes"]
    status = payload.get("error")
    return (status if isinstance(status, str) and status in {"dependency", "invalid", "failed"} else "failed"), []


def read_qr(image_path: str) -> list[dict]:
    """Return decoded ``data``, barcode ``type`` and pixel ``rect`` dictionaries.

    Zbar remains the primary decoder for its complete barcode support. On a
    host where its native library crashes or cannot load, the already-installed
    OpenCV decoder handles QR and EAN/UPC instead. Both engines run in separate
    fresh processes with independent 10-second limits, including on Linux.
    """
    # Retain the existing image/size validation before starting a subprocess.
    with open_image_safe(image_path):
        pass
    primary_status, codes = _run_decoder("zbar", image_path)
    if primary_status == "ok":
        logger.info("qr_reader: decoded %d code(s)", len(codes))
        return codes
    if primary_status == "invalid":
        raise ValidationError("Could not decode QR codes or barcodes from this image.")
    logger.warning("qr_reader: isolated zbar decoder unavailable; trying OpenCV", extra={"decoder_status": primary_status})
    fallback_status, codes = _run_decoder("opencv", image_path)
    if fallback_status == "ok":
        logger.info("qr_reader: decoded %d code(s) with OpenCV", len(codes))
        return codes
    if fallback_status == "invalid":
        raise ValidationError("Could not decode QR codes or barcodes from this image.")
    if "timeout" in {primary_status, fallback_status}:
        raise ToolTimeoutError("QR and barcode reading timed out. Try a smaller image.")
    if primary_status == fallback_status == "dependency":
        raise DependencyError("QR reader is unavailable because its image-decoding libraries are missing on the server.")
    raise ExternalToolError("The QR and barcode decoder could not process this image. Try another image or try again later.")
