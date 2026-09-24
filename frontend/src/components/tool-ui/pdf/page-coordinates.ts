/**
 * Where a box drawn on a page preview lands on the page itself.
 *
 * PdfPageStage shows a page the way pdf.js draws it: turned by the page's
 * /Rotate setting and cut to its visible area (the CropBox), measured in
 * points from the top-left corner of that picture. The PyMuPDF routes
 * (Redact, White-Out, Annotate, Shapes, Form Creator, eSign) measure the page
 * as it is stored: from the top-left corner of the same visible area, before
 * /Rotate is applied. On a page without /Rotate the two agree. On a turned
 * page they do not, and a box sent as the preview showed it landed somewhere
 * else, or off the page, and hid nothing (fixed 2026-09-24).
 *
 * Every conversion goes through pdf.js's own viewports, the same ones the
 * preview draws with, so it cannot drift from what the visitor sees.
 * src/test/page-contract.test.tsx checks it against real pdf.js pages and
 * backend/tests/test_page_contract.py checks that the routes put the result
 * back where it was drawn.
 */
import type { PDFPageProxy } from "pdfjs-dist";

type Viewport = ReturnType<PDFPageProxy["getViewport"]>;

/** One page's two coordinate systems, from pdf.js. */
export interface PageFrame {
    /** The page as the preview shows it: after /Rotate, 1 unit per point. */
    shown: Viewport;
    /** The page as stored: the same visible area before /Rotate. */
    unrotated: Viewport;
}

export interface Box { x: number; y: number; width: number; height: number }

export function pageFrame(page: Pick<PDFPageProxy, "getViewport">): PageFrame {
    return { shown: page.getViewport({ scale: 1 }), unrotated: page.getViewport({ scale: 1, rotation: 0 }) };
}

/** How far the page is turned for showing, clockwise: 0, 90, 180 or 270. */
export function shownRotation(frame: PageFrame): number {
    return ((frame.shown.rotation % 360) + 360) % 360;
}

/** To a millionth of a point: drops floating-point noise such as 315.99999999999994. */
const tidy = (value: number) => Math.round(value * 1e6) / 1e6 + 0;

function move(from: Viewport, to: Viewport, x: number, y: number): [number, number] {
    const [px, py] = from.convertToPdfPoint(x, y);
    const [tx, ty] = to.convertToViewportPoint(px, py);
    return [tidy(tx), tidy(ty)];
}

/**
 * Convert a box between the two systems. Both corners move; a line keeps its
 * direction (its width and height may be negative), anything else comes back
 * with its top-left corner first.
 */
function convert(from: Viewport, to: Viewport, box: Box, line: boolean): Box {
    const [x0, y0] = move(from, to, box.x, box.y);
    const [x1, y1] = move(from, to, box.x + box.width, box.y + box.height);
    if (line) return { x: x0, y: y0, width: tidy(x1 - x0), height: tidy(y1 - y0) };
    return { x: Math.min(x0, x1), y: Math.min(y0, y1), width: tidy(Math.abs(x1 - x0)), height: tidy(Math.abs(y1 - y0)) };
}

/** A box drawn on the preview, in the page's stored (unrotated) coordinates. */
export function shownToUnrotated(frame: PageFrame, box: Box, { line = false } = {}): Box {
    return convert(frame.shown, frame.unrotated, box, line);
}

/** A box in the page's stored (unrotated) coordinates, where the preview shows it. */
export function unrotatedToShown(frame: PageFrame, box: Box, { line = false } = {}): Box {
    return convert(frame.unrotated, frame.shown, box, line);
}
