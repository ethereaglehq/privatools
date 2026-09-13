"""Private QR/barcode subprocess protocol; never import native decoders in ASGI.

Invoked by qr_reader_service with ``python -I this_file engine image_path``.
Only JSON is written to stdout. Native stderr and uploaded paths are not exposed.
"""
from __future__ import annotations

import json
import sys

MAX_CODES = 1000
MAX_OUTPUT_BYTES = 8 * 1024 * 1024


def emit(payload: dict, status: int = 0) -> None:
    output = json.dumps(payload, ensure_ascii=True)
    if len(output) > MAX_OUTPUT_BYTES:
        output = '{"ok":false,"error":"invalid"}'
        status = 3
    sys.stdout.write(output)
    sys.stdout.flush()
    raise SystemExit(status)


def decode_zbar(image) -> list[dict]:
    try:
        from pyzbar.pyzbar import decode
    except OSError as exc:
        raise ImportError("zbar could not load") from exc

    decoded = decode(image)
    if len(decoded) > MAX_CODES:
        raise ValueError("Too many codes")
    return [{
        "data": item.data.decode("utf-8", errors="replace"),
        "type": item.type,
        "rect": {"left": item.rect.left, "top": item.rect.top,
                 "width": item.rect.width, "height": item.rect.height},
    } for item in decoded]


def decode_opencv(image) -> list[dict]:
    # OpenCV is already a runtime dependency. This fallback keeps QR and the
    # EAN/UPC formats it supports usable when a host's zbar binary is broken.
    try:
        import cv2
        import numpy as np
    except OSError as exc:
        raise ImportError("OpenCV could not load") from exc

    cv2.setNumThreads(1)
    pixels = np.asarray(image.convert("RGB"))[:, :, ::-1].copy()
    codes: list[dict] = []

    def append(data: str, kind: str, points) -> None:
        if not data or points is None:
            return
        x, y, width, height = cv2.boundingRect(np.asarray(points, dtype=np.float32))
        codes.append({"data": data, "type": kind, "rect": {
            "left": int(x), "top": int(y), "width": int(width), "height": int(height),
        }})

    detector = cv2.QRCodeDetector()
    found, values, points, _ = detector.detectAndDecodeMulti(pixels)
    if found:
        for value, polygon in zip(values, points):
            append(value, "QRCODE", polygon)
    else:
        value, polygon, _ = detector.detectAndDecode(pixels)
        append(value, "QRCODE", polygon)

    barcode_factory = getattr(cv2, "barcode_BarcodeDetector", None)
    if barcode_factory:
        barcode_detector = barcode_factory()
        found, values, kinds, points = barcode_detector.detectAndDecodeWithType(pixels)
        if not found:
            # Clean, tightly cropped barcode exports sometimes defeat OpenCV's
            # region detector even though its decoder can read them. Try the
            # whole image as one candidate; this rectangle accurately denotes
            # the region used for that decode, rather than invented bar bounds.
            height, width = pixels.shape[:2]
            points = np.array([[[0, height - 1], [0, 0],
                                [width - 1, 0], [width - 1, height - 1]]], dtype=np.float32)
            found, values, kinds = barcode_detector.decodeWithType(pixels, points)
        if found:
            for value, kind, polygon in zip(values, kinds, points):
                append(value, kind.replace("_", "").replace("-", ""), polygon)
    if len(codes) > MAX_CODES:
        raise ValueError("Too many codes")
    return codes


def main() -> None:
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ImportError, OSError, ValueError):
        pass
    if len(sys.argv) != 3 or sys.argv[1] not in {"zbar", "opencv"}:
        emit({"ok": False, "error": "failed"}, 4)
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        emit({"ok": False, "error": "dependency"}, 2)
    Image.MAX_IMAGE_PIXELS = 150_000_000
    try:
        with Image.open(sys.argv[2]) as image:
            image.load()
            codes = decode_zbar(image) if sys.argv[1] == "zbar" else decode_opencv(image)
    except (ImportError, OSError) as exc:
        # Missing shared libraries can surface as either ImportError or OSError.
        emit({"ok": False, "error": "dependency" if isinstance(exc, ImportError) else "invalid"}, 2 if isinstance(exc, ImportError) else 3)
    except (UnidentifiedImageError, Image.DecompressionBombError, ValueError):
        emit({"ok": False, "error": "invalid"}, 3)
    except Exception:
        emit({"ok": False, "error": "failed"}, 4)
    emit({"ok": True, "codes": codes})


if __name__ == "__main__":
    main()
