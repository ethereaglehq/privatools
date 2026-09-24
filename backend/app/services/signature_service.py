"""Find a PDF's signature fields and check each signature with pyHanko.

For every signed field the check answers three questions: have the signed
bytes changed since signing, does the signature match the certificate it
carries, and what was saved to the file afterwards.

Certificates are not checked against any trust list, and revocation
information is never fetched. A valid result therefore means the file matches
its signature and certificate; it says nothing about who holds the
certificate.

Fields are found here with pikepdf, which opens damaged files the way readers
do and applies the same password handling as every other tool. pyHanko, which
is stricter, only reads files that contain a signature, and only in a separate
process (``_signature_check_worker.py``) with a time limit, a memory limit and
no network access, because some malformed files make its parser loop for ever.
"""

from __future__ import annotations

import io
import json
import logging
import subprocess
import sys
from pathlib import Path

import pikepdf
from pikepdf import Array, Dictionary, Name
from pyhanko.pdf_utils.generic import parse_pdf_date

from ..utils.cleanup import remove_files, safe_open_pdf
from ..utils.filenames import temp_output

logger = logging.getLogger(__name__)

NOTE = (
    "Certificates are not checked against a trust list, and revocation is not checked. "
    "A valid signature means the file is unchanged since it was signed with the certificate "
    "shown; it does not prove who holds that certificate."
)

_CHECK_WORKER = Path(__file__).with_name("_signature_check_worker.py")
# A small signed file takes about half a second, mostly starting Python and
# importing pyHanko, and a 150 MB file with two signatures and a thousand
# changes between them took under three. A file that makes the parser loop
# never finishes, so the check is stopped at this limit.
_CHECK_SECONDS_BASE = 10
_CHECK_SECONDS_PER_MB = 0.1
_CHECK_SECONDS_MAX = 60
_MAX_OUTPUT_BYTES = 8 * 1024 * 1024

# The signature formats pyHanko validates: the values of its SigSeedSubFilter,
# written out so the web process never imports pyHanko's validation code.
_SUPPORTED_SUBFILTERS = frozenset({"/adbe.pkcs7.detached", "/ETSI.CAdES.detached", "/ETSI.RFC3161"})
# pyHanko's ModificationLevel names, as the worker reports them.
_MODIFICATIONS = {
    "NONE": "none",
    # Only validation data for long-term checking was added: the content is as signed.
    "LTA_UPDATES": "none",
    "FORM_FILLING": "form_filling",
    "ANNOTATIONS": "annotations",
    "OTHER": "other",
}
# pyHanko's SignatureCoverageLevel names for a signature over all that it signed.
_WHOLE_REVISION = frozenset({"ENTIRE_FILE", "ENTIRE_REVISION"})
# Digests whose collisions can be made, as pyHanko names them, and as people
# know them. A signature made with one can be moved to a document built to
# collide with the signed one, so a match proves much less. pyHanko's own
# default policy calls these weak too.
_WEAK_DIGESTS = {"md2": "MD2", "md5": "MD5", "sha1": "SHA-1"}

_NOT_CHECKED = "This signature could not be checked."
_DAMAGED_FILE = "The file is damaged, so its signatures cannot be checked."
_DAMAGED_SIGNATURE = "The signature data is damaged or in a form that cannot be read."
_TIMED_OUT = "Checking this signature took too long, so it was stopped."


def inspect_signatures(data: bytes) -> dict:
    """Describe every signature field in the PDF in ``data``.

    Raises ValueError, with a message for the user, when the file needs a
    password to open or cannot be read at all.
    """
    with safe_open_pdf(io.BytesIO(data)) as pdf:
        found = _signature_fields(pdf)
    signed = [(entry, subfilter) for entry, subfilter in found if entry["signed"]]
    if signed:
        _check(data, signed)
    return {"has_signatures": bool(signed), "signatures": [entry for entry, _ in found], "note": NOTE}


def _entry(name: str, **values) -> dict:
    entry = {
        "field": name, "signed": False, "kind": "signature", "signer": "", "date": "",
        "status": "unsigned", "modification": None, "certificate": None, "digest_algorithm": None,
        "reason": "",
    }
    entry.update(values)
    return entry


def _text(value) -> str:
    return str(value).strip() if isinstance(value, pikepdf.String) else ""


def _date(value) -> str:
    try:
        return parse_pdf_date(_text(value), strict=False).isoformat() if _text(value) else ""
    except Exception:  # noqa: BLE001 - a malformed date is reported as unknown
        return ""


def _signature_fields(pdf: pikepdf.Pdf) -> list[tuple[dict, str]]:
    """Walk the form's field tree for signature fields, in document order.

    Returns each field's entry with the /SubFilter of its signature, if signed.
    """
    acroform = pdf.Root.get("/AcroForm")
    top = acroform.get("/Fields") if isinstance(acroform, Dictionary) else None
    if not isinstance(top, Array):
        return []
    found, seen = [], set()
    stack = [(field, "", None) for field in reversed(list(top))]
    while stack:
        field, parent_name, inherited_type = stack.pop()
        if not isinstance(field, Dictionary) or (field.is_indirect and field.objgen in seen):
            continue
        if field.is_indirect:
            seen.add(field.objgen)
        partial = _text(field.get("/T"))
        name = f"{parent_name}.{partial}" if parent_name and partial else partial or parent_name
        field_type = field.get("/FT", inherited_type)
        kids = field.get("/Kids")
        # A field's kids are child fields when they have names, widgets otherwise.
        children = [kid for kid in kids if isinstance(kid, Dictionary) and "/T" in kid] if isinstance(kids, Array) else []
        if children:
            stack += [(kid, name, field_type) for kid in reversed(children)]
            continue
        if field_type != Name.Sig:
            continue
        value = field.get("/V")
        if not isinstance(value, Dictionary):
            found.append((_entry(name), ""))
            continue
        found.append((_entry(
            name,
            signed=True,
            kind="timestamp" if value.get("/Type") == Name.DocTimeStamp else "signature",
            signer=_text(value.get("/Name")),
            date=_date(value.get("/M")),
            status="unchecked",
        ), str(value.get("/SubFilter", ""))))
    return found


def _check(data: bytes, signed: list[tuple[dict, str]]) -> None:
    """Fill in each signed entry's status from pyHanko's validation."""
    to_check = []
    for entry, subfilter in signed:
        if subfilter in _SUPPORTED_SUBFILTERS:
            to_check.append(entry)
        else:
            entry["reason"] = f"This signature uses the {subfilter.lstrip('/') or 'unnamed'} format, which cannot be checked here."
    if not to_check:
        return
    outcome = _run_worker(data, [{"name": entry["field"], "kind": entry["kind"]} for entry in to_check])
    if outcome in ("timeout", "failed"):
        for entry in to_check:
            entry["reason"] = _TIMED_OUT if outcome == "timeout" else _NOT_CHECKED
        return
    if outcome.get("readable") is not True:
        for entry in to_check:
            entry["reason"] = _DAMAGED_FILE
        return
    results = outcome.get("fields")
    for entry in to_check:
        facts = results.get(entry["field"]) if isinstance(results, dict) else None
        if not isinstance(facts, dict) or facts.get("error") == "missing":
            entry["reason"] = _NOT_CHECKED
        elif "error" in facts:
            entry["reason"] = _DAMAGED_SIGNATURE
        else:
            try:
                _apply(entry, facts)
            except (KeyError, TypeError, AttributeError):
                logger.warning("verify-signature: the signature check answered in an unexpected form")
                entry.update(status="unchecked", modification=None, certificate=None, reason=_NOT_CHECKED)


def _time_limit(size: int) -> float:
    return min(_CHECK_SECONDS_MAX, _CHECK_SECONDS_BASE + _CHECK_SECONDS_PER_MB * size / 1_000_000)


def _run_worker(data: bytes, fields: list[dict]) -> dict | str:
    """Run pyHanko on ``data`` in its own process. A string names a failure."""
    pdf_path = temp_output("signature-check", "pdf")
    limit = _time_limit(len(data))
    try:
        pdf_path.write_bytes(data)
        process = subprocess.run(
            [sys.executable, "-I", str(_CHECK_WORKER), str(pdf_path)],
            input=json.dumps({"fields": fields}).encode() + b"\n",
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=limit, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("verify-signature: the signature check was stopped after %.0f seconds", limit)
        return "timeout"
    except OSError:
        logger.exception("verify-signature: the signature check could not run")
        return "failed"
    finally:
        remove_files(pdf_path)
    # A crash, or the memory or CPU limit, stays inside the child.
    if process.returncode != 0 or len(process.stdout) > _MAX_OUTPUT_BYTES:
        logger.warning("verify-signature: the signature check failed with exit status %s", process.returncode)
        return "failed"
    try:
        payload = json.loads(process.stdout)
    except (ValueError, UnicodeDecodeError):
        return "failed"
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return "failed"
    return payload


def _weak_digest(facts: dict) -> str | None:
    """The broken digest a signature was made with, as people know it, or None.

    The mechanism counts too: "sha1_rsa" hashes with SHA-1 whatever digest
    the signature names for its content.
    """
    for name in (facts["digest"], facts["mechanism"].split("_")[0]):
        if name in _WEAK_DIGESTS:
            return _WEAK_DIGESTS[name]
    return None


def _apply(entry: dict, facts: dict) -> None:
    certificate = facts["certificate"]
    entry["signer"] = entry["signer"] or certificate["common_name"]
    entry["date"] = entry["date"] or facts["when"]
    entry["certificate"] = {
        key: certificate[key] for key in ("subject", "issuer", "valid_from", "valid_until", "self_signed")
    }
    entry["digest_algorithm"] = facts["digest"] or None
    if not facts["intact"]:
        entry.update(status="invalid", reason="The signed content has changed since it was signed.")
    elif not facts["valid"]:
        entry.update(status="invalid", reason="The signature does not match its certificate.")
    elif facts["coverage"] not in _WHOLE_REVISION:
        entry.update(status="invalid", reason="The signature does not cover the whole document as it was signed.")
    else:
        level = facts["modification_level"]
        if level is None:
            level = "NONE" if facts["coverage"] == "ENTIRE_FILE" else "OTHER"
        modification = _MODIFICATIONS.get(level, "other")
        weak = _weak_digest(facts)
        if weak:
            # Never plainly valid: what was saved afterwards is still reported.
            entry.update(status="weak", modification=modification, reason=(
                f"The signature matches, but it was made with {weak}, which can be forged, "
                "so it cannot show that the document is unchanged."
            ))
        else:
            entry.update(status="valid" if modification == "none" else "modified", modification=modification)
