from ..utils.cleanup import safe_open_pdf
from ..utils.exceptions import ValidationError
from ..utils.filenames import temp_output
from ..utils.page_range import parse_page_range
from ..utils.page_removal import remove_pages


def parse_page_ranges(pages_str: str, total_pages: int) -> list[int]:
    """Compatibility shim — delegates to utils.page_range.parse_page_range."""
    return parse_page_range(pages_str, total_pages, allow_empty=True)


def delete_pages(input_path: str, pages_str: str) -> str:
    output_path = temp_output("deleted", "pdf")

    with safe_open_pdf(input_path) as pdf:
        total = len(pdf.pages)
        to_delete = set(parse_page_range(pages_str, total, allow_empty=True))
        if not to_delete:
            raise ValidationError("No valid pages specified")
        if len(to_delete) >= total:
            raise ValidationError("Cannot delete all pages from a PDF")

        # Not just `del pdf.pages[idx]`: bookmarks, links, form fields and
        # the structure tree would keep the deleted pages in the file.
        remove_pages(pdf, to_delete, tool="delete-pages").save(str(output_path))

    return str(output_path)
