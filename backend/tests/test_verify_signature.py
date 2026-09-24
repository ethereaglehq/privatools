"""Verify Signature finds signature fields and checks each signature with pyHanko.

Fixtures are signed here with pyHanko and throwaway self-signed certificates,
then posted through the real /api/verify-signature route. No certificate is
ever trusted: the route checks integrity, not identity.

pyHanko runs in a separate process (_signature_check_worker.py). Tests that
watch what pyHanko does from inside, such as its network use, call the
worker's ``check`` in this process, or in a fresh interpreter.
"""

from __future__ import annotations

import datetime
import functools
import io
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pikepdf
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import AuthorityInformationAccessOID, NameOID
from pyhanko import keys as pyhanko_keys
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko.sign.timestamps.dummy_client import DummyTimeStamper

from backend.app.services import _signature_check_worker as check_worker
from backend.app.services import signature_service

REPO_ROOT = Path(__file__).resolve().parents[2]


@functools.lru_cache(maxsize=None)
def _signer(common_name: str = "Test Signer", *, key: str = "ec", revocation_url: str | None = None):
    """A self-signed signer, cached because RSA key generation is slow on small machines."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048) if key == "rsa" else ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=30))
    )
    if revocation_url:
        builder = builder.add_extension(x509.AuthorityInformationAccess([
            x509.AccessDescription(AuthorityInformationAccessOID.OCSP, x509.UniformResourceIdentifier(revocation_url + "/ocsp")),
            x509.AccessDescription(AuthorityInformationAccessOID.CA_ISSUERS, x509.UniformResourceIdentifier(revocation_url + "/ca.der")),
        ]), critical=False).add_extension(x509.CRLDistributionPoints([
            x509.DistributionPoint([x509.UniformResourceIdentifier(revocation_url + "/crl")], None, None, None),
        ]), critical=False)
    certificate = builder.sign(private_key, hashes.SHA256())
    return signers.SimpleSigner(
        signing_cert=next(iter(pyhanko_keys.load_certs_from_pemder_data(certificate.public_bytes(serialization.Encoding.PEM)))),
        signing_key=pyhanko_keys.load_private_key_from_pemder_data(
            private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
            passphrase=None,
        ),
        cert_registry=None,
    )


def _unsigned_pdf() -> bytes:
    pdf = pikepdf.new()
    pdf.add_blank_page()
    font = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica))
    pdf.pages[0].obj.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
    pdf.pages[0].obj.Contents = pdf.make_stream(b"BT /F1 12 Tf 72 700 Td (Pay Bob 100 dollars) Tj ET")
    buf = io.BytesIO()
    pdf.save(buf, compress_streams=False)
    return buf.getvalue()


def _sign(data: bytes, field: str = "Signature1", name: str | None = "Alice Example", signer=None) -> bytes:
    writer = IncrementalPdfFileWriter(io.BytesIO(data))
    meta = signers.PdfSignatureMetadata(field_name=field, name=name)
    return signers.sign_pdf(writer, meta, signer=signer or _signer()).getvalue()


def _sign_by_hand(cover_short_by: int = 0, break_signature: bool = False, smuggle: bytes = b"") -> bytes:
    """Sign a PDF without pyHanko: a detached CMS signature from cryptography.

    The signature dictionary's /M says 2026-01-01 while the CMS signing time
    says now. ``cover_short_by`` leaves the last bytes of the file outside the
    signed byte range. ``smuggle`` wraps the signature instead: the byte range
    still leaves out the whole space reserved for the signature value, but the
    value ends early and these unsigned bytes follow it, inside the signature
    dictionary, so they change what the file says while every signed byte
    still matches the digest. ``break_signature`` flips a bit of the signature
    value, the last thing in the CMS, so the signed bytes still match their
    digest but the signature no longer matches the certificate.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Hand Certificate")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    placeholder = 9_999_999_999
    pdf = pikepdf.new()
    pdf.add_blank_page()
    page = pdf.pages[0]
    value = pikepdf.Dictionary(
        Type=pikepdf.Name.Sig, Filter=pikepdf.Name("/Adobe.PPKLite"), SubFilter=pikepdf.Name("/adbe.pkcs7.detached"),
        Name=pikepdf.String("Hand Signer"), M=pikepdf.String("D:20260101120000Z"),
        ByteRange=pikepdf.Array([0, placeholder, placeholder, placeholder]), Contents=pikepdf.String(b"\x00" * 4096),
    )
    field = pdf.make_indirect(pikepdf.Dictionary(
        Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.Widget, FT=pikepdf.Name.Sig, T=pikepdf.String("HandSig"),
        F=132, Rect=pikepdf.Array([0, 0, 0, 0]), P=page.obj, V=pdf.make_indirect(value),
    ))
    page.obj.Annots = pikepdf.Array([field])
    pdf.Root.AcroForm = pikepdf.Dictionary(Fields=pikepdf.Array([field]), SigFlags=3)
    buf = io.BytesIO()
    pdf.save(buf, compress_streams=False, object_stream_mode=pikepdf.ObjectStreamMode.disable)
    data = buf.getvalue()

    contents = re.search(rb"/Contents <(0+)>", data)
    start, end = contents.start(1) - 1, contents.end(1) + 1
    byte_range = [0, start, end, len(data) - end - cover_short_by]
    slot = re.search(rb"/ByteRange \[ 0 9999999999 9999999999 9999999999 \]", data)
    filled = (b"/ByteRange [ %d %d %d %d ]" % tuple(byte_range)).ljust(slot.end() - slot.start())
    data = data[:slot.start()] + filled + data[slot.end():]
    cms = (
        pkcs7.PKCS7SignatureBuilder().set_data(data[:start] + data[end:end + byte_range[3]])
        .add_signer(certificate, key, hashes.SHA256())
        .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary])
    )
    if break_signature:
        cms = cms[:-1] + bytes([cms[-1] ^ 1])
    if smuggle:
        value = b"<" + cms.hex().encode() + b">" + smuggle
        return data[:start] + value.ljust(end - start) + data[end:]
    return data[:start + 1] + cms.hex().encode().ljust(end - start - 2, b"0") + data[end - 1:]


def _replace_page_content(data: bytes, content: bytes) -> bytes:
    """Save a new page content stream as an incremental update after signing."""
    writer = IncrementalPdfFileWriter(io.BytesIO(data))
    page = writer.root["/Pages"]["/Kids"][0].get_object()
    page[generic.NameObject("/Contents")] = writer.add_object(generic.StreamObject(stream_data=content))
    writer.update_container(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _verify(client, data: bytes) -> dict:
    resp = client.post("/api/verify-signature", files={"file": ("in.pdf", data, "application/pdf")})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _verify_within(client, data: bytes, seconds: float) -> tuple[dict, float]:
    """Verify from a daemon thread, so a request that never ends fails the test instead of hanging the run."""
    answer = {}

    def run():
        answer["response"] = client.post("/api/verify-signature", files={"file": ("in.pdf", data, "application/pdf")})

    started = time.monotonic()
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(seconds)
    assert not thread.is_alive(), f"verify-signature was still running after {seconds} seconds"
    assert answer["response"].status_code == 200, answer["response"].text
    return answer["response"].json(), time.monotonic() - started


def _with_xref_loop(data: bytes) -> bytes:
    """Point the last trailer's /Prev at that trailer's own cross-reference table."""
    startxref = int(re.findall(rb"startxref\s+(\d+)", data)[-1])
    trailer = data.rindex(b"trailer")
    head, tail = data[:trailer], data[trailer:]
    tail = re.sub(rb"/Prev \d+", b"/Prev %d" % startxref, tail, count=1) if b"/Prev" in tail else tail.replace(b"<<", b"<< /Prev %d" % startxref, 1)
    return head + tail


def _signing_time_in_file(data: bytes, field: str = "Signature1") -> str:
    """The /M entry of the field's signature dictionary, rewritten as ISO 8601 by hand."""
    with pikepdf.open(io.BytesIO(data)) as pdf:
        for f in pdf.Root.AcroForm.Fields:
            if str(f.T) == field:
                raw = str(f.V.M)
    m = re.fullmatch(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z", raw)
    assert m, raw
    y, mo, d, h, mi, s = m.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:{s}+00:00"


def test_pdf_without_signature_fields(client, sample_pdf):
    result = _verify(client, sample_pdf)
    assert result["has_signatures"] is False
    assert result["signatures"] == []


def test_signed_field_is_found_with_signer_and_signing_time(client):
    signed = _sign(_unsigned_pdf(), signer=_signer(key="rsa"))
    result = _verify(client, signed)
    assert result["has_signatures"] is True
    [sig] = result["signatures"]
    assert sig["field"] == "Signature1"
    assert sig["signed"] is True
    assert sig["kind"] == "signature"
    assert sig["signer"] == "Alice Example"
    assert sig["date"] == _signing_time_in_file(signed)


def test_signer_falls_back_to_the_certificate_name(client):
    [sig] = _verify(client, _sign(_unsigned_pdf(), name=None, signer=_signer("Certificate Holder")))["signatures"]
    assert sig["signer"] == "Certificate Holder"


def test_untouched_signature_is_valid_and_its_certificate_is_described(client):
    [sig] = _verify(client, _sign(_unsigned_pdf(), signer=_signer("Test Signer")))["signatures"]
    assert sig["status"] == "valid"
    assert sig["modification"] == "none"
    assert sig["certificate"]["subject"] == "Common Name: Test Signer"
    assert sig["certificate"]["issuer"] == "Common Name: Test Signer"
    assert sig["certificate"]["self_signed"] is True
    assert "trusted" not in sig


def test_signature_from_another_implementation_is_checked(client):
    [sig] = _verify(client, _sign_by_hand())["signatures"]
    assert (sig["status"], sig["signer"]) == ("valid", "Hand Signer")
    assert sig["date"] == "2026-01-01T12:00:00+00:00"  # /M, not the CMS signing time


def test_signature_that_does_not_match_its_certificate_is_invalid(client):
    [sig] = _verify(client, _sign_by_hand(break_signature=True))["signatures"]
    assert sig["status"] == "invalid"
    assert "certificate" in sig["reason"]


def test_signature_that_leaves_bytes_unsigned_is_invalid(client):
    [sig] = _verify(client, _sign_by_hand(cover_short_by=12))["signatures"]
    assert sig["status"] == "invalid"


def test_signature_wrapping_attack_is_invalid(client):
    """Unsigned bytes smuggled in beside the signature value, where the byte range skips.

    Every signed byte still matches the digest and the signature still matches
    its certificate, so a check of the digest alone passes. The smuggled
    /Reason is really in the file: readers show it.
    """
    wrapped = _sign_by_hand(smuggle=b" /Reason (Approved by the finance director)")
    with pikepdf.open(io.BytesIO(wrapped)) as pdf:
        assert str(pdf.Root.AcroForm.Fields[0].V.Reason) == "Approved by the finance director"
    [sig] = _verify(client, wrapped)["signatures"]
    assert sig["status"] == "invalid"
    assert "cover" in sig["reason"]
    assert sig["certificate"]["subject"] == "Common Name: Hand Certificate"


def test_changing_signed_bytes_makes_the_signature_invalid(client):
    signed = _sign(_unsigned_pdf())
    tampered = signed.replace(b"Pay Bob 100", b"Pay Bob 900")
    assert tampered != signed
    [sig] = _verify(client, tampered)["signatures"]
    assert sig["status"] == "invalid"


def test_content_changed_after_signing_is_reported(client):
    changed = _replace_page_content(_sign(_unsigned_pdf()), b"BT /F1 12 Tf 72 700 Td (Pay Bob 900 dollars) Tj ET")
    [sig] = _verify(client, changed)["signatures"]
    assert sig["status"] == "modified"
    assert sig["modification"] == "other"


def test_a_later_signature_counts_as_form_filling(client):
    twice = _sign(_sign(_unsigned_pdf(), field="First", name="Alice"), field="Second", name="Bob", signer=_signer("Bob"))
    sigs = {s["field"]: s for s in _verify(client, twice)["signatures"]}
    assert (sigs["First"]["status"], sigs["First"]["modification"]) == ("modified", "form_filling")
    assert (sigs["Second"]["status"], sigs["Second"]["modification"]) == ("valid", "none")


def test_empty_signature_field_is_listed_as_unsigned(client):
    writer = IncrementalPdfFileWriter(io.BytesIO(_unsigned_pdf()))
    fields.append_signature_field(writer, fields.SigFieldSpec(sig_field_name="Empty", on_page=0, box=(10, 10, 100, 40)))
    out = io.BytesIO()
    writer.write(out)
    result = _verify(client, out.getvalue())
    assert result["has_signatures"] is False
    assert result["signatures"] == [
        {"field": "Empty", "signed": False, "kind": "signature", "signer": "", "date": "", "status": "unsigned",
         "modification": None, "certificate": None, "reason": ""},
    ]


def _field_hierarchy_pdf() -> bytes:
    """An empty signature field "Approvals.Manager" whose /FT /Sig is set only on its parent."""
    with pikepdf.open(io.BytesIO(_unsigned_pdf())) as pdf:
        parent = pdf.make_indirect(pikepdf.Dictionary(FT=pikepdf.Name.Sig, T=pikepdf.String("Approvals")))
        child = pdf.make_indirect(pikepdf.Dictionary(
            Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.Widget, T=pikepdf.String("Manager"), Parent=parent,
            Rect=pikepdf.Array([0, 0, 100, 30]), P=pdf.pages[0].obj,
        ))
        parent.Kids = pikepdf.Array([child])
        pdf.pages[0].obj.Annots = pikepdf.Array([child])
        pdf.Root.AcroForm = pikepdf.Dictionary(Fields=pikepdf.Array([parent]))
        buf = io.BytesIO()
        pdf.save(buf)
    return buf.getvalue()


def test_field_type_inherited_from_a_parent_field_is_recognised(client):
    [sig] = _verify(client, _field_hierarchy_pdf())["signatures"]
    assert (sig["field"], sig["status"]) == ("Approvals.Manager", "unsigned")


def test_signed_field_inside_a_field_hierarchy_is_checked(client):
    """The field name found by walking the form must match pyHanko's, or nothing is checked."""
    [sig] = _verify(client, _sign(_field_hierarchy_pdf(), field="Approvals.Manager"))["signatures"]
    assert (sig["field"], sig["status"]) == ("Approvals.Manager", "valid")


def test_document_timestamp_is_reported_as_a_timestamp(client):
    tsa = _signer("Test TSA", key="rsa")  # pyHanko's offline timestamper is RSA-only
    stamper = signers.PdfTimeStamper(DummyTimeStamper(tsa_cert=tsa.signing_cert, tsa_key=tsa.signing_key))
    stamped = stamper.timestamp_pdf(IncrementalPdfFileWriter(io.BytesIO(_sign(_unsigned_pdf()))), md_algorithm="sha256").getvalue()
    sigs = _verify(client, stamped)["signatures"]
    assert [(s["kind"], s["status"], s["modification"]) for s in sigs] == [("signature", "valid", "none"), ("timestamp", "valid", "none")]
    assert sigs[1]["signer"] == "Test TSA"
    assert sigs[1]["date"]


def test_damaged_signature_data_is_reported_not_raised(client):
    signed = _sign(_unsigned_pdf())
    start = signed.index(b"/Contents <") + len(b"/Contents <")
    damaged = signed[:start] + b"00" * 20 + signed[start + 40:]
    [sig] = _verify(client, damaged)["signatures"]
    assert sig["signed"] is True
    assert sig["status"] == "unchecked"
    assert sig["reason"]


def test_unsupported_signature_format_is_reported_unchecked(client):
    signed = _sign(_unsigned_pdf())
    legacy = signed.replace(b"/adbe.pkcs7.detached", b"/adbe.x509.rsa_sha1 ")
    assert legacy != signed
    [sig] = _verify(client, legacy)["signatures"]
    assert sig["status"] == "unchecked"
    assert "adbe.x509.rsa_sha1" in sig["reason"]


def test_damaged_file_without_signatures_still_answers(client, sample_pdf):
    # Shifted xref offsets: readers repair this, and so must the check.
    broken = re.sub(rb"(\d{10}) 00000 n", lambda m: b"%010d 00000 n" % (int(m.group(1)) + 7), sample_pdf)
    assert broken != sample_pdf
    result = _verify(client, broken)
    assert result["signatures"] == []


def test_damaged_signed_file_lists_its_signatures_as_unchecked(client):
    signed = _sign(_unsigned_pdf())
    broken = re.sub(rb"(\d{10}) 00000 n", lambda m: b"%010d 00000 n" % (int(m.group(1)) + 7), signed)
    [sig] = _verify(client, broken)["signatures"]
    assert (sig["field"], sig["signed"], sig["signer"], sig["status"]) == ("Signature1", True, "Alice Example", "unchecked")


def test_password_protected_pdf_is_rejected(client, locked_pdf):
    resp = client.post("/api/verify-signature", files={"file": ("locked.pdf", locked_pdf, "application/pdf")})
    assert resp.status_code == 400
    assert "password" in resp.json()["detail"].lower()


def test_signed_pdf_with_only_an_owner_password_is_checked(client):
    with pikepdf.open(io.BytesIO(_unsigned_pdf())) as pdf:
        buf = io.BytesIO()
        pdf.save(buf, encryption=pikepdf.Encryption(owner="owner-secret", user="", R=4))
    writer = IncrementalPdfFileWriter(io.BytesIO(buf.getvalue()))
    writer.encrypt("")
    signed = signers.sign_pdf(writer, signers.PdfSignatureMetadata(field_name="Signature1"), signer=_signer()).getvalue()
    [sig] = _verify(client, signed)["signatures"]
    assert sig["status"] == "valid"


def test_checking_never_opens_a_network_connection(client, monkeypatch):
    """The certificate names issuer, OCSP and CRL addresses; with fetching on, pyHanko tries one.

    pyHanko runs in the checker process, so its code is run here too, where
    the sockets can be watched. The route's answer comes from the real process.
    """
    signed = _sign(_unsigned_pdf(), signer=_signer(revocation_url="http://revocation.invalid"))
    [sig] = _verify(client, signed)["signatures"]
    assert sig["status"] == "valid"
    attempts = []

    def refuse(*args, **kwargs):
        attempts.append(args)
        raise OSError("network disabled in this test")

    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    facts = check_worker.check(signed, [{"name": "Signature1", "kind": "signature"}])["fields"]["Signature1"]
    assert (facts["intact"], facts["valid"]) == (True, True)
    assert attempts == []


def test_the_checker_process_cannot_use_the_network():
    """Belt and braces: the process that runs pyHanko fails every connection it tries."""
    script = (
        "import socket, sys\n"
        "sys.path.insert(0, {root!r})\n"
        "from backend.app.services import _signature_check_worker as worker\n"
        "worker._isolate(0)\n"
        "attempts = (\n"
        "    lambda: socket.create_connection(('127.0.0.1', 9)),\n"
        "    lambda: socket.getaddrinfo('example.com', 443),\n"
        "    lambda: socket.socket().connect(('127.0.0.1', 9)),\n"
        ")\n"
        "for attempt in attempts:\n"
        "    try:\n"
        "        attempt()\n"
        "    except OSError as exc:\n"
        "        print(exc)\n"
    ).format(root=str(REPO_ROOT))
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=REPO_ROOT, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.splitlines() == ["The signature checker has no network access."] * 3


def test_checking_never_imports_oscrypto(tmp_path):
    """oscrypto 1.3.0 cannot parse OpenSSL 3.x.10+ version strings and fails at import.

    pyHanko only reaches it to load the operating system's trust roots, which
    the check never asks for. Each side runs in a fresh interpreter, so no
    other import can hide a regression: the checker, and the service in the
    web process, which does not load pyHanko's validation code at all.
    """
    signed = tmp_path / "signed.pdf"
    signed.write_bytes(_sign(_unsigned_pdf()))
    checker = (
        "import sys\n"
        "sys.path.insert(0, {root!r})\n"
        "from backend.app.services._signature_check_worker import check\n"
        "result = check(open({pdf!r}, 'rb').read(), [{{'name': 'Signature1', 'kind': 'signature'}}])\n"
        "assert result['fields']['Signature1']['valid'], result\n"
        "print(sorted(name for name in sys.modules if name.startswith('oscrypto')))\n"
    )
    service = (
        "import sys\n"
        "sys.path.insert(0, {root!r})\n"
        "from backend.app.services.signature_service import inspect_signatures\n"
        "result = inspect_signatures(open({pdf!r}, 'rb').read())\n"
        "assert result['signatures'][0]['status'] == 'valid', result\n"
        "print(sorted(name for name in sys.modules if name.startswith(('oscrypto', 'pyhanko.sign'))))\n"
    )
    for script in (checker, service):
        out = subprocess.run(
            [sys.executable, "-c", script.format(root=str(REPO_ROOT), pdf=str(signed))],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=120,
            env={**os.environ, "TEMP_DIR": str(tmp_path)},
        )
        assert out.returncode == 0, out.stderr
        assert out.stdout.strip().splitlines()[-1] == "[]"


def test_the_formats_checked_are_the_ones_pyhanko_validates():
    """The web process lists them itself, so a pyHanko upgrade that adds one must update the list."""
    assert signature_service._SUPPORTED_SUBFILTERS == {subfilter.value for subfilter in SigSeedSubFilter}


# ── Files that make pyHanko loop, and checks that fail ───────────────────────

def test_a_file_built_to_make_the_parser_loop_returns_quickly(client, monkeypatch):
    """A trailer whose /Prev points at its own section: pyHanko reads it for ever, growing memory.

    The limit for a small file is cut from 10 seconds to 3 to keep the test short.
    """
    monkeypatch.setattr(signature_service, "_CHECK_SECONDS_BASE", 3)
    result, elapsed = _verify_within(client, _with_xref_loop(_sign(_unsigned_pdf())), seconds=60)
    [sig] = result["signatures"]
    assert (sig["field"], sig["signed"], sig["signer"], sig["status"]) == ("Signature1", True, "Alice Example", "unchecked")
    assert sig["reason"] in (signature_service._TIMED_OUT, signature_service._DAMAGED_FILE)
    assert elapsed < 20


def _stub_checker(tmp_path, monkeypatch, body: str) -> None:
    stub = tmp_path / "stub_checker.py"
    stub.write_text(body)
    monkeypatch.setattr(signature_service, "_CHECK_WORKER", stub)


def test_a_check_that_never_finishes_is_stopped(client, monkeypatch, tmp_path):
    _stub_checker(tmp_path, monkeypatch, "import time\ntime.sleep(600)\n")
    monkeypatch.setattr(signature_service, "_CHECK_SECONDS_BASE", 1)
    result, elapsed = _verify_within(client, _sign(_unsigned_pdf()), seconds=60)
    [sig] = result["signatures"]
    assert (sig["status"], sig["reason"]) == ("unchecked", "Checking this signature took too long, so it was stopped.")
    assert elapsed < 15


@pytest.mark.parametrize("body", [
    "import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n",
    "print('not json')\n",
    "import json\nprint(json.dumps({'ok': True, 'readable': True, 'fields': {'Signature1': {'intact': True}}}))\n",
], ids=["killed", "garbage", "incomplete"])
def test_a_check_that_fails_leaves_the_signature_unchecked(client, monkeypatch, tmp_path, body):
    _stub_checker(tmp_path, monkeypatch, body)
    [sig] = _verify(client, _sign(_unsigned_pdf()))["signatures"]
    assert (sig["signed"], sig["signer"], sig["status"], sig["certificate"]) == (True, "Alice Example", "unchecked", None)
    assert sig["reason"] == "This signature could not be checked."
