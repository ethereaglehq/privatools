/**
 * The page's own check that every item sits on a page the PDF has, before
 * anything is sent. Routes that skipped such an item returned the file
 * unchanged, so the visitor took the download for done (fixed 2026-09-24;
 * they now answer 400 too).
 *
 * Returns a message in the page's own numbers (pages counted from 1) for the
 * first item that is not on a page of the PDF, or null. `pageCount` is null
 * until the preview has opened the PDF.
 */
export function itemOffThePdf(items: { page: number }[], pageCount: number | null, noun: string): string | null {
    for (const [index, item] of items.entries()) {
        const message = pageOffThePdf(item.page, pageCount, `${noun} ${index + 1}`);
        if (message) return message;
    }
    return null;
}

/** The same for one thing on one page, named by `subject` ("The signature"). */
export function pageOffThePdf(page: number, pageCount: number | null, subject: string): string | null {
    if (Number.isInteger(page) && page >= 1 && (pageCount === null || page <= pageCount)) return null;
    const pages = pageCount === null ? "a page number from 1" : pageCount === 1 ? "page 1" : `a page from 1 to ${pageCount}`;
    return `${subject} is on page ${page}, which this PDF does not have. Choose ${pages}.`;
}
