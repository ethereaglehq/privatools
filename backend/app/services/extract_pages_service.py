import logging

import pikepdf

from ..utils.pdf_accessibility import (
    preserve_document_properties,
    preserve_structure_tree,
)

from ..utils.cleanup import safe_open_pdf
from ..utils.exceptions import ValidationError
from ..utils.filenames import temp_output
from ..utils.page_range import parse_page_range
from ..utils.page_removal import copy_pages, prune_structure_tree_to_pages, prune_to_page_tree

logger = logging.getLogger(__name__)


# Kept as a module-level export so existing route tests that import
# `parse_page_ranges` from this module keep working.
def parse_page_ranges(pages_str: str, total_pages: int) -> list[int]:
    """Compatibility shim — delegates to utils.page_range.parse_page_range."""
    return parse_page_range(pages_str, total_pages, allow_empty=True)


def extract_pages(input_path: str, pages_str: str) -> str:
    output_path = temp_output("extracted", "pdf")

    with safe_open_pdf(input_path) as pdf:
        total = len(pdf.pages)
        indices = parse_page_range(pages_str, total, allow_empty=True)
        if not indices:
            raise ValidationError("No valid pages specified")

        with pikepdf.Pdf.new() as new_pdf:
            # The tags are pruned before any page is copied. A page that
            # reaches the structure tree, as a crafted file's can, copies the
            # whole tree with it, and preserve_structure_tree finds that copy.
            try:
                prune_structure_tree_to_pages(pdf, indices)
            except Exception:  # preserve_structure_tree tries again, or drops the tags
                logger.debug("extract: structure tree not pruned before the copy", exc_info=True)
            copy_pages(new_pdf, pdf, indices)
            # Pdf.new() starts from an empty catalog, so /Lang, the title and
            # /ViewerPreferences are dropped unless carried over explicitly.
            preserve_document_properties(pdf, new_pdf)
            # Must run after the pages are appended: that is what populates the
            # object map letting each struct element's /Pg resolve to the page
            # already in new_pdf instead of a duplicate.
            preserve_structure_tree(pdf, new_pdf, pages=indices)
            # The pages left out must not ride along with the links, form
            # fields and threads of the pages extracted.
            prune_to_page_tree(new_pdf).save(str(output_path), tool="extract-pages")

    return str(output_path)
