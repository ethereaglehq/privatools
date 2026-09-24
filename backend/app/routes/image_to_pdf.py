import uuid
from typing import List
import logging
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from ..utils.cleanup import get_temp_path, ensure_temp_dir, remove_files
from ..utils.concurrency import run_bounded
from ..services import image_to_pdf_service

ALLOWED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".heic", ".heif", ".svg"}
# Nine tools share this route (Image, JPG, PNG, HEIC, WebP, TIFF, BMP, GIF and
# SVG to PDF); the page copy and ImageToPdfUI state both limits.
MAX_FILES = 100
# The combined cap stayed at 200 MB when the count went from 50 to 100.
# ReportLab keeps every page in memory and formats the whole file on save, so
# a request peaks at about four times its JPEG bytes: 358 MB of phone photos
# took +1.4 GB RSS and 124 s of CPU on the 2-core ARM VM, against a 4 GB
# container and a 300 s timeout.
MAX_TOTAL_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB

router = APIRouter()
logger = logging.getLogger(__name__)



@router.post("/image-to-pdf")
async def image_to_pdf(
    files: List[UploadFile] = File(...),
    page_size: str = Form("A4"),
):
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one image")
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"One PDF can take up to {MAX_FILES} images; this request has {len(files)}.",
        )

    # Accept case-insensitive variants ("a4" / "A4"). "auto" now means "each
    # PDF page matches its source image's pixel dimensions" rather than being
    # silently aliased to A4 — matches the React UI's expectation.
    raw_page_size = (page_size or "").strip()
    _alias = {"a4": "A4", "letter": "Letter", "auto": "auto"}
    normalized_page_size = _alias.get(raw_page_size.lower(), raw_page_size)
    if normalized_page_size not in image_to_pdf_service.PAGE_SIZES:
        allowed = ", ".join(sorted(image_to_pdf_service.PAGE_SIZES.keys()))
        raise HTTPException(status_code=400, detail=f"page_size must be one of: {allowed}")

    ensure_temp_dir()
    input_paths: list[str] = []
    output_path: str | None = None
    total_bytes = 0

    try:
        for file in files:
            filename = file.filename or ""
            suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if suffix not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} is not a supported image"
                )
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail=f"File {file.filename or 'unknown'} is empty")
            total_bytes += len(content)
            if total_bytes > MAX_TOTAL_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"One PDF can take up to {MAX_TOTAL_UPLOAD_BYTES // (1024 * 1024)} MB "
                        "of images in total; these add up to more."
                    ),
                )
            temp_path = get_temp_path(f"upload_{uuid.uuid4().hex}{suffix}")
            temp_path.write_bytes(content)
            input_paths.append(str(temp_path))

        # Heavy pool: a full batch can hold a core for minutes and need
        # gigabytes (100 web-size WebPs: 216 s CPU, +2.2 GB RSS), so it shares
        # MAX_CONCURRENT_HEAVY with the other heavy tools.
        output_path = await run_bounded(image_to_pdf_service.images_to_pdf, input_paths, page_size=normalized_page_size)
        cleanup = BackgroundTask(remove_files, *input_paths, output_path)
        return FileResponse(
            path=output_path,
            filename="images.pdf",
            media_type="application/pdf",
            background=cleanup,
        )
    except HTTPException:
        to_remove = input_paths + ([output_path] if output_path else [])
        remove_files(*to_remove)
        raise
    except ValueError as e:
        # Image-too-large from the service. Friendly 400 with "too large"
        # substring for frontend friendlyError().
        to_remove = input_paths + ([output_path] if output_path else [])
        remove_files(*to_remove)
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        to_remove = input_paths + ([output_path] if output_path else [])
        remove_files(*to_remove)
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
