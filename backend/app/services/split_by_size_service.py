"""Split a PDF into chunks bounded by file size.

Original implementation re-serialized the *entire* accumulated chunk on every
page just to measure size — O(n²) memory and time on a 500-page PDF that hit
the boundary near the end. This rewrite serializes incrementally by writing
each candidate chunk to a temp file and only re-checking total size every
SAMPLE_EVERY pages, then trims back if we overshot.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pikepdf

from ..utils.cleanup import safe_open_pdf
from ..utils.exceptions import ValidationError
from ..utils.filenames import temp_output
from ..utils.page_removal import PageCopier, prune_to_page_tree

# How many pages to add before re-checking the on-disk size. Lower = more
# accurate boundary, higher = less work per chunk. 5 is a good compromise for
# typical mixed-content PDFs (text + a few images per page).
SAMPLE_EVERY = 5
MIN_CHUNK_PAGES = 1


def split_by_size(input_path: str, max_size_mb: float = 10.0) -> str:
    if max_size_mb <= 0:
        raise ValidationError("max_size_mb must be > 0")

    max_bytes = int(max_size_mb * 1024 * 1024)
    zip_path = temp_output("split_size", "zip")
    chunk_paths: list[Path] = []

    copier: PageCopier | None = None
    src_pages: list = []

    def _save_chunk(pages_for_chunk: list[int], final: bool = False) -> Path:
        out_path = temp_output("chunk", "pdf")
        with pikepdf.Pdf.new() as out:
            if final:
                copier.copy(out, pages_for_chunk)
                # Without the other chunks' pages, which links, form fields
                # and threads would drag along.
                prune_to_page_tree(out).save(str(out_path))
            else:
                # A size probe. Pruning only ever removes objects, so the
                # unpruned copy bounds the final chunk's size from above.
                for i in pages_for_chunk:
                    out.pages.append(src_pages[i])
                out.save(str(out_path))
        return out_path

    try:
        with safe_open_pdf(input_path) as src:
            total_pages = len(src.pages)
            if total_pages == 0:
                raise ValidationError("Cannot split an empty PDF.")
            copier = PageCopier(src)
            src_pages = [page for page in src.pages]

            chunks: list[list] = []
            current: list = []

            for i in range(total_pages):
                current.append(i)
                # Only check disk size every SAMPLE_EVERY pages OR on the last
                # page — keeps the inner loop cheap.
                if (len(current) % SAMPLE_EVERY == 0) or i == total_pages - 1:
                    candidate = _save_chunk(current)
                    sz = os.path.getsize(candidate)

                    if sz > max_bytes and len(current) > MIN_CHUNK_PAGES:
                        # Overshot. Pop pages off the end one at a time and
                        # re-test until we're under the cap (or down to the
                        # minimum). EVERY popped page is carried forward to seed
                        # the next chunk — keeping only the last one (the old
                        # bug) silently dropped the rest. `carry` preserves the
                        # original page order (earliest-popped ends up first).
                        candidate.unlink(missing_ok=True)
                        carry: list = []
                        while len(current) > MIN_CHUNK_PAGES:
                            carry.insert(0, current.pop())
                            candidate = _save_chunk(current)
                            fits = os.path.getsize(candidate) <= max_bytes
                            candidate.unlink(missing_ok=True)
                            if fits:
                                break
                        # Either it fits now, or the loop ran out: `current` is
                        # a lone page that is still oversized. Write it as it
                        # ships.
                        chunks.append(current)
                        chunk_paths.append(_save_chunk(current, final=True))
                        # Seed the next chunk with ALL trimmed pages, in order.
                        current = carry
                    else:
                        # Either still under cap, or we're forced to keep this
                        # single oversized page in its own chunk. Keep going.
                        candidate.unlink(missing_ok=True)

            if current:
                chunks.append(current)
                chunk_paths.append(_save_chunk(current, final=True))

            with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, path in enumerate(chunk_paths, start=1):
                    zf.write(str(path), f"part_{idx:03d}.pdf")

        return str(zip_path)
    finally:
        for path in chunk_paths:
            path.unlink(missing_ok=True)
