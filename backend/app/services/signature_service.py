"""Find a PDF's signature fields and check each signature with pyHanko.

For every signed field the check answers three questions: have the signed
bytes changed since signing, does the signature match the certificate it
carries, and what was saved to the file afterwards.

Certificates are not checked against any trust list, and revocation
information is never fetched. A valid result therefore means the file matches
its signature and certificate; it says nothing about who holds the
certificate. Validation runs with an empty trust list and fetching disabled,
so it never touches the network, and pyHanko never loads oscrypto, which it
only uses to read the operating system's trust store.

Fields are found with pikepdf, which opens damaged files the way readers do
and applies the same password handling as every other tool; pyHanko, which is
stricter, is only asked to read files that contain a signature.
"""

from __future__ import annotations

import io
import logging

import pikepdf
from pikepdf import Array, Dictionary, Name
from pyhanko.pdf_utils.generic import parse_pdf_date
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.diff_analysis import ModificationLevel
from pyhanko.sign.fields import SigSeedSubFilter, enumerate_sig_fields
from pyhanko.sign.validation import validate_pdf_signature, validate_pdf_timestamp
from pyhanko.sign.validation.pdf_embedded import EmbeddedPdfSignature
from pyhanko.sign.validation.status import SignatureCoverageLevel
from pyhanko_certvalidator import ValidationContext

from ..utils.cleanup import safe_open_pdf

logger = logging.getLogger(__name__)

# With no trusted roots, every certificate path fails to validate, and pyHanko
# logs each failure as a warning with a full traceback. That is the expected
# outcome here, not an error.
for _library in ("pyhanko", "pyhanko_certvalidator"):
    logging.getLogger(_library).setLevel(logging.ERROR)

NOTE = (
    "Certificates are not checked against a trust list, and revocation is not checked. "
    "A valid signature means the file is unchanged since it was signed with the certificate "
    "shown; it does not prove who holds that certificate."
)

_SUPPORTED_SUBFILTERS = frozenset(subfilter.value for subfilter in SigSeedSubFilter)
_MODIFICATIONS = {
    ModificationLevel.NONE: "none",
    # Only validation data for long-term checking was added: the content is as signed.
    ModificationLevel.LTA_UPDATES: "none",
    ModificationLevel.FORM_FILLING: "form_filling",
    ModificationLevel.ANNOTATIONS: "annotations",
    ModificationLevel.OTHER: "other",
}
_WHOLE_REVISION = (SignatureCoverageLevel.ENTIRE_FILE, SignatureCoverageLevel.ENTIRE_REVISION)


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
        "status": "unsigned", "modification": None, "certificate": None, "reason": "",
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
    try:
        reader = PdfFileReader(io.BytesIO(data), strict=False)
        if reader.encrypted:
            reader.decrypt("")  # pikepdf has already opened it without a password
        in_reader = {name: field for name, _, field in enumerate_sig_fields(reader, filled_status=True)}
    except Exception:  # noqa: BLE001 - pyHanko cannot read files that readers repair
        logger.info("verify-signature: pyHanko could not read the file", exc_info=True)
        for entry, _ in signed:
            entry["reason"] = "The file is damaged, so its signatures cannot be checked."
        return
    context = ValidationContext(trust_roots=[], allow_fetching=False)
    for entry, subfilter in signed:
        if subfilter not in _SUPPORTED_SUBFILTERS:
            entry["reason"] = f"This signature uses the {subfilter.lstrip('/') or 'unnamed'} format, which cannot be checked here."
            continue
        if entry["field"] not in in_reader:
            entry["reason"] = "This signature could not be checked."
            continue
        try:
            signature = EmbeddedPdfSignature(reader, in_reader[entry["field"]], entry["field"])
            if entry["kind"] == "timestamp":
                status = validate_pdf_timestamp(signature, validation_context=context)
            else:
                status = validate_pdf_signature(signature, signer_validation_context=context)
        except Exception:  # noqa: BLE001 - unreadable signature data is reported, not raised
            logger.info("verify-signature: could not validate %s", entry["field"], exc_info=True)
            entry["reason"] = "The signature data is damaged or in a form that cannot be read."
            continue
        _apply(entry, status)


def _apply(entry: dict, status) -> None:
    certificate = status.signing_cert
    common_name = certificate.subject.native.get("common_name", "")
    if isinstance(common_name, list):
        common_name = ", ".join(common_name)
    entry["signer"] = entry["signer"] or common_name
    if not entry["date"]:
        when = status.timestamp if entry["kind"] == "timestamp" else status.signer_reported_dt
        entry["date"] = when.isoformat() if when else ""
    entry["certificate"] = {
        "subject": certificate.subject.human_friendly,
        "issuer": certificate.issuer.human_friendly,
        "valid_from": certificate.not_valid_before.isoformat(),
        "valid_until": certificate.not_valid_after.isoformat(),
        "self_signed": certificate.self_signed in ("yes", "maybe"),
    }
    if not status.intact:
        entry.update(status="invalid", reason="The signed content has changed since it was signed.")
    elif not status.valid:
        entry.update(status="invalid", reason="The signature does not match its certificate.")
    elif status.coverage not in _WHOLE_REVISION:
        entry.update(status="invalid", reason="The signature does not cover the whole document as it was signed.")
    else:
        level = status.modification_level
        if level is None:
            level = ModificationLevel.NONE if status.coverage == SignatureCoverageLevel.ENTIRE_FILE else ModificationLevel.OTHER
        modification = _MODIFICATIONS.get(level, "other")
        entry.update(status="valid" if modification == "none" else "modified", modification=modification)
