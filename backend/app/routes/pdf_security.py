"""Companion security tools: PDF/A validator, signature verifier, sanitizer.

NOTE — the `/set-permissions` endpoint (consumed by `PermissionsUI`) is
defined in `phase4_tools.py`, not here. The frontend posts to
`POST /api/set-permissions`; that handler already validates the upload,
applies an owner password and per-action permission flags, and cleans up
temp files via BackgroundTasks. This file intentionally stays narrow and
just covers the "verify / sanitize" surface.
"""

import asyncio
import logging

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from ..services import sanitize_service, signature_service
from ..utils.cleanup import remove_files, validate_pdf_content
from ..utils.concurrency import run_bounded

router = APIRouter()
logger = logging.getLogger(__name__)


async def _read_pdf(upload: UploadFile, label: str = "PDF") -> bytes:
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail=f"{label} is empty")
    validate_pdf_content(data)
    return data


@router.post("/pdfa-validator")
async def pdfa_validator(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")
    data = await _read_pdf(file)

    def _work():
        doc = None
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            meta = doc.metadata or {}
            errors = []
            standard = ""
            is_pdfa = False

            xml_meta = doc.get_xml_metadata() if hasattr(doc, "get_xml_metadata") else ""
            xml_meta_lower = str(xml_meta).lower()
            if "pdfaid" in xml_meta_lower or "pdfa" in xml_meta_lower:
                is_pdfa = True
                standard = "PDF/A (detected)"
            else:
                errors.append(
                    "PDF/A identifier not found in XMP metadata — this looks like a "
                    "regular PDF, not PDF/A. Convert it via the PDF→PDF/A tool first."
                )

            if not meta.get("title"):
                errors.append("Missing title metadata (required for PDF/A)")
            if not meta.get("author"):
                errors.append("Missing author metadata (required for PDF/A)")
            if doc.is_encrypted:
                errors.append("Encrypted PDFs cannot be PDF/A compliant")

            return {
                "valid": is_pdfa and len(errors) == 0,
                "standard": standard,
                "errors": errors,
            }
        finally:
            if doc is not None:
                doc.close()

    try:
        result = await asyncio.to_thread(_work)
        return JSONResponse(result)
    except fitz.FileDataError as exc:
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF") from exc
    except Exception as exc:
        logger.exception("PDF/A validator error")
        raise HTTPException(status_code=500, detail="Failed to validate PDF/A") from exc


@router.post("/verify-signature")
async def verify_signature(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")
    data = await _read_pdf(file)

    try:
        # pyHanko's pure-Python parsing and change analysis grow with the file.
        result = await run_bounded(signature_service.inspect_signatures, data)
    except ValueError as exc:
        # safe_open_pdf: password-protected or unreadable. pyHanko's own errors
        # are ValueErrors too, but the service reports those per signature.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Verify signature error")
        raise HTTPException(status_code=500, detail="Failed to verify signatures") from exc
    return JSONResponse(result)


@router.post("/sanitize")
async def sanitize_pdf(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF")
    data = await _read_pdf(file)

    try:
        # A full object walk, and content-stream rewriting for layered pages.
        output_path = await run_bounded(sanitize_service.sanitize_pdf, data)
    except ValueError as exc:
        # safe_open_pdf: password-protected or unreadable.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Sanitize PDF error")
        raise HTTPException(status_code=500, detail="Failed to sanitize PDF") from exc

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="sanitized.pdf",
        background=BackgroundTask(remove_files, output_path),
    )
