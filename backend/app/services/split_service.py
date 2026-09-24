"""Split a PDF into one or more output PDFs.

`parse_page_selection` is kept identical to its original signature and
behaviour — `tests/test_split_service.py` pins those semantics, including
the supported tokens (`end`, open ranges like `-3` / `8-`, dedup-preserving
order, rejection of `0`, `4-2`, `abc`).
"""
from __future__ import annotations

import logging
import os
import time
import uuid
import zipfile
from pathlib import Path
from typing import List

import pikepdf

from ..utils.cleanup import ensure_temp_dir, get_temp_path, safe_open_pdf
from ..utils.page_removal import PageCopier, prune_to_page_tree

logger = logging.getLogger(__name__)


def _parse_page_number(token: str, total_pages: int, context: str) -> int:
    if token == "end":
        return total_pages
    if not token.isdigit():
        raise ValueError(f"Invalid page value '{token}' in range '{context}'.")
    page = int(token)
    if page < 1 or page > total_pages:
        raise ValueError(f"Page {page} is out of bounds. Valid range is 1-{total_pages}.")
    return page


def parse_page_selection(pages: str, total_pages: int) -> List[int]:
    if total_pages <= 0:
        raise ValueError("Cannot split an empty PDF with no pages.")
    if not pages or not pages.strip():
        raise ValueError("No page range provided. Please specify pages to extract (e.g. '1-3,5,7-end').")

    selections: List[int] = []
    seen: set[int] = set()
    parts = [part.strip() for part in pages.split(",") if part.strip()]
    if not parts:
        raise ValueError("No valid page numbers found in the provided range.")

    for part in parts:
        token = part.lower()
        current: List[int] = []

        if "-" in token:
            start_raw, end_raw = [x.strip() for x in token.split("-", 1)]
            if not start_raw and not end_raw:
                raise ValueError(f"Invalid range '{part}'.")

            start_page = 1 if start_raw == "" else _parse_page_number(start_raw, total_pages, part)
            end_page = total_pages if end_raw in {"", "end"} else _parse_page_number(end_raw, total_pages, part)
            if start_page > end_page:
                raise ValueError(f"Invalid range '{part}': start page must be <= end page.")

            current = list(range(start_page - 1, end_page))
        else:
            page = _parse_page_number(token, total_pages, part)
            current = [page - 1]

        for index in current:
            if index not in seen:
                seen.add(index)
                selections.append(index)

    if not selections:
        raise ValueError("No valid page numbers found in the provided range.")
    return selections


def _write_part(copier: PageCopier, indices, out_path) -> None:
    with pikepdf.Pdf.new() as out:
        copier.copy(out, indices)
        # The other parts' pages must not ride along with this part's links,
        # form fields and threads.
        prune_to_page_tree(out).save(str(out_path), tool="split")


def split_pdf(input_path: str, mode: str = "pages", pages: str = "", n: int = 2) -> str:
    ensure_temp_dir()
    started = time.monotonic()
    try:
        input_size = os.path.getsize(input_path)
    except OSError:
        input_size = 0
    logger.info(
        "split: start mode=%s n=%d input_bytes=%d", mode, n, input_size,
    )

    output_files: List[str] = []
    try:
        with safe_open_pdf(input_path) as pdf:
            total_pages = len(pdf.pages)
            if total_pages <= 0:
                raise ValueError("Cannot split an empty PDF with no pages.")

            copier = PageCopier(pdf)
            if mode == "individual":
                for i in range(total_pages):
                    out_path = get_temp_path(f"page_{i+1}_{uuid.uuid4().hex}.pdf")
                    _write_part(copier, [i], out_path)
                    output_files.append(str(out_path))

            elif mode == "every_n":
                if n <= 0:
                    raise ValueError("Chunk size 'n' must be greater than 0.")
                for start in range(0, total_pages, n):
                    end = min(start + n, total_pages)
                    out_path = get_temp_path(f"pages_{start+1}_{end}_{uuid.uuid4().hex}.pdf")
                    _write_part(copier, range(start, end), out_path)
                    output_files.append(str(out_path))

            else:  # specific pages
                page_nums = parse_page_selection(pages, total_pages)
                out_path = get_temp_path(f"extracted_{uuid.uuid4().hex}.pdf")
                _write_part(copier, page_nums, out_path)
                output_files = [str(out_path)]

        if len(output_files) == 1:
            duration_ms = int((time.monotonic() - started) * 1000)
            try:
                out_size = os.path.getsize(output_files[0])
            except OSError:
                out_size = 0
            logger.info(
                "split: done mode=%s parts=1 duration_ms=%d output_bytes=%d",
                mode, duration_ms, out_size,
            )
            return output_files[0]

        zip_path = get_temp_path(f"split_{uuid.uuid4().hex}.zip")
        with zipfile.ZipFile(str(zip_path), "w") as zf:
            for f in output_files:
                zf.write(f, Path(f).name)
        # Clean up individual page files after zipping
        for f in output_files:
            try:
                Path(f).unlink(missing_ok=True)
            except OSError:
                pass

        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            zip_size = os.path.getsize(zip_path)
        except OSError:
            zip_size = 0
        logger.info(
            "split: done mode=%s parts=%d duration_ms=%d output_bytes=%d",
            mode, len(output_files), duration_ms, zip_size,
        )
        return str(zip_path)
    except Exception:
        # On failure, sweep any partial output files we created so they
        # don't linger in TEMP_DIR until the janitor sweeps them.
        for f in output_files:
            try:
                Path(f).unlink(missing_ok=True)
            except OSError:
                pass
        raise
