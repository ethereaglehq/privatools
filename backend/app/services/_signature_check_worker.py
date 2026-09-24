"""Private pyHanko subprocess protocol; the web process never parses signatures.

signature_service runs ``python -I this_file <pdf path>`` and writes one JSON
line to stdin naming the signed fields to check. Only JSON is written to
stdout: the facts pyHanko found for each field, which the service turns into
a status.

pyHanko is a pure-Python PDF parser, and some malformed files make it loop
for ever: a trailer whose /Prev points back at its own cross-reference
section is read again and again, growing memory as it goes, and an object
that ends in a comment at the end of its data spins the tokenizer. A thread
cannot be stopped, so the check runs here instead. The caller kills this
process after a time limit, and the limits set in ``_isolate`` stop it from
taking more memory or CPU than a check needs, or from using the network.

Validation uses an empty trust list and never fetches anything: certificates
are not checked against any trust list and revocation is never looked up.
pyHanko therefore never loads oscrypto, which it only uses to read the
operating system's trust store.
"""

from __future__ import annotations

import io
import json
import logging
import resource
import socket
import sys

# pyHanko reads the whole file, and parsing adds Python objects on top.
MEMORY_BASE_BYTES = 384 * 1024 * 1024
MEMORY_PER_FILE_BYTE = 3
# Backstop for a process whose caller died before killing it.
CPU_SECONDS = 60
MAX_OUTPUT_BYTES = 8 * 1024 * 1024

# With no trusted roots every certificate path fails to validate, and pyHanko
# logs each failure as a warning with a traceback. That is expected here.
for _library in ("pyhanko", "pyhanko_certvalidator"):
    logging.getLogger(_library).setLevel(logging.ERROR)


def _refuse_network(*args, **kwargs):
    raise OSError("The signature checker has no network access.")


def _limit(kind: int, soft: int, hard: int) -> None:
    """Lower a resource limit, keeping any hard limit that is already lower."""
    _, current = resource.getrlimit(kind)
    if current != resource.RLIM_INFINITY:
        soft, hard = min(soft, current), min(hard, current)
    resource.setrlimit(kind, (soft, hard))


def _isolate(file_size: int) -> None:
    """Cap memory and CPU time, and make every network call fail."""
    if sys.platform.startswith("linux"):
        # Where the image runs. macOS does not enforce an address-space limit
        # the same way, and the time limit still applies there.
        memory = MEMORY_BASE_BYTES + MEMORY_PER_FILE_BYTE * file_size
        _limit(resource.RLIMIT_AS, memory, memory)
    _limit(resource.RLIMIT_CPU, CPU_SECONDS, CPU_SECONDS + 5)
    _limit(resource.RLIMIT_CORE, 0, 0)
    # Validation is configured never to fetch; this makes sure of it.
    socket.socket.connect = _refuse_network
    socket.socket.connect_ex = _refuse_network
    socket.getaddrinfo = _refuse_network
    socket.create_connection = _refuse_network


def _certificate(certificate) -> dict:
    common_name = certificate.subject.native.get("common_name", "")
    if isinstance(common_name, list):
        common_name = ", ".join(common_name)
    return {
        "common_name": common_name if isinstance(common_name, str) else "",
        "subject": certificate.subject.human_friendly,
        "issuer": certificate.issuer.human_friendly,
        "valid_from": certificate.not_valid_before.isoformat(),
        "valid_until": certificate.not_valid_after.isoformat(),
        "self_signed": certificate.self_signed in ("yes", "maybe"),
    }


def _facts(status, kind: str) -> dict:
    when = status.timestamp if kind == "timestamp" else status.signer_reported_dt
    level = status.modification_level
    return {
        "intact": bool(status.intact),
        "valid": bool(status.valid),
        "coverage": status.coverage.name if status.coverage is not None else None,
        "modification_level": level.name if level is not None else None,
        "when": when.isoformat() if when else "",
        "certificate": _certificate(status.signing_cert),
    }


def check(data: bytes, fields: list[dict]) -> dict:
    """Validate each requested field of the PDF in ``data`` with pyHanko.

    ``fields`` lists ``{"name": ..., "kind": "signature" | "timestamp"}``.
    Returns ``{"readable": bool, "fields": {name: facts or {"error": ...}}}``.
    """
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.fields import enumerate_sig_fields
    from pyhanko.sign.validation import validate_pdf_signature, validate_pdf_timestamp
    from pyhanko.sign.validation.pdf_embedded import EmbeddedPdfSignature
    from pyhanko_certvalidator import ValidationContext

    try:
        reader = PdfFileReader(io.BytesIO(data), strict=False)
        if reader.encrypted:
            # The service has already opened it without a password, so any
            # encryption here only sets an owner password.
            reader.decrypt("")
        in_reader = {name: field for name, _, field in enumerate_sig_fields(reader, filled_status=True)}
    except Exception:  # noqa: BLE001 - pyHanko cannot read files that readers repair
        return {"readable": False, "fields": {}}
    context = ValidationContext(trust_roots=[], allow_fetching=False)
    results: dict[str, dict] = {}
    for field in fields:
        name, kind = field["name"], field["kind"]
        if name not in in_reader:
            results[name] = {"error": "missing"}
            continue
        try:
            signature = EmbeddedPdfSignature(reader, in_reader[name], name)
            if kind == "timestamp":
                status = validate_pdf_timestamp(signature, validation_context=context)
            else:
                status = validate_pdf_signature(signature, signer_validation_context=context)
            results[name] = _facts(status, kind)
        except Exception:  # noqa: BLE001 - unreadable signature data is reported, not raised
            results[name] = {"error": "unreadable"}
    return {"readable": True, "fields": results}


def _emit(payload: dict, status: int = 0) -> None:
    output = json.dumps(payload, ensure_ascii=True)
    if len(output) > MAX_OUTPUT_BYTES:
        output, status = '{"ok": false}', 3
    sys.stdout.write(output)
    sys.stdout.flush()
    raise SystemExit(status)


def main() -> None:
    try:
        request = json.loads(sys.stdin.buffer.readline())
        with open(sys.argv[1], "rb") as handle:
            data = handle.read()
        fields = [
            {"name": str(field["name"]), "kind": "timestamp" if field.get("kind") == "timestamp" else "signature"}
            for field in request["fields"]
        ]
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        _emit({"ok": False}, 2)
    _isolate(len(data))
    try:
        result = check(data, fields)
    except Exception:  # noqa: BLE001 - MemoryError from the limit, among others
        _emit({"ok": False}, 1)
    _emit({"ok": True, **result})


if __name__ == "__main__":
    main()
