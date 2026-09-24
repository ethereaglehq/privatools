import zipfile
from pathlib import Path

import pikepdf

from ..utils.cleanup import safe_open_pdf
from ..utils.exceptions import ValidationError
from ..utils.filenames import temp_output
from ..utils.page_removal import PageCopier, prune_to_page_tree


def _resolve_page_index(pdf: pikepdf.Pdf, destination) -> int:
    """Resolve a bookmark destination to a 0-based page index."""
    try:
        if destination is None:
            return 0
        if isinstance(destination, pikepdf.Array):
            page_ref = destination[0]
            for i, page in enumerate(pdf.pages):
                if page.objgen == page_ref.objgen:
                    return i
        if isinstance(destination, pikepdf.Page):
            return pdf.pages.index(destination)
    except (AttributeError, IndexError, TypeError):
        pass
    return 0


def split_by_bookmarks(input_path: str) -> str:
    zip_path = temp_output("split_bookmarks", "zip")
    chunk_paths: list[Path] = []
    try:
        with safe_open_pdf(input_path) as pdf:
            total_pages = len(pdf.pages)
            bookmarks = []

            try:
                with pdf.open_outline() as outline:
                    for item in outline.root:
                        try:
                            dest = item.destination
                            page_idx = _resolve_page_index(pdf, dest)
                            title = item.title or f"Section_{len(bookmarks)+1}"
                            bookmarks.append((title, page_idx))
                        except (AttributeError, KeyError):
                            continue
            except (AttributeError, pikepdf.PdfError):
                pass

            if not bookmarks:
                raise ValidationError(
                    "PDF has no bookmarks to split on. Use the regular Split tool instead."
                )

            # Sort by page index
            bookmarks.sort(key=lambda x: x[1])

            # Build page ranges
            ranges = []
            for i, (title, start) in enumerate(bookmarks):
                end = bookmarks[i + 1][1] if i + 1 < len(bookmarks) else total_pages
                ranges.append((title, start, end))

            copier = PageCopier(pdf, tool="split-by-bookmarks")
            with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, (title, start, end) in enumerate(ranges, start=1):
                    if start >= end:
                        continue
                    chunk_path = temp_output("chunk", "pdf")
                    chunk_paths.append(chunk_path)
                    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:50]
                    with pikepdf.Pdf.new() as out:
                        copier.copy(out, range(start, end))
                        # The other sections' pages must not ride along with
                        # this section's links, form fields and threads.
                        prune_to_page_tree(out, tool="split-by-bookmarks").save(str(chunk_path))
                    zf.write(str(chunk_path), f"{idx:02d}_{safe_title}.pdf")

            return str(zip_path)
    finally:
        for path in chunk_paths:
            path.unlink(missing_ok=True)
