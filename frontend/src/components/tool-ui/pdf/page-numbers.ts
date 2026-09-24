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
    const stray = items.findIndex(item => !Number.isInteger(item.page) || item.page < 1 || (pageCount !== null && item.page > pageCount));
    if (stray < 0) return null;
    const pages = pageCount === null ? "a page number from 1" : pageCount === 1 ? "page 1" : `a page from 1 to ${pageCount}`;
    return `${noun} ${stray + 1} is on page ${items[stray].page}, which this PDF does not have. Choose ${pages}.`;
}
