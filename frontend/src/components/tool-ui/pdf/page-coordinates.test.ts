/**
 * The preview's boxes against pdf.js's own viewports, on the turned and
 * cropped pages of src/test/page-contract.json. The expected values there are
 * what backend/tests/test_page_contract.py sends through the real routes and
 * finds on the drawn box as the page is shown.
 */
import { describe, expect, it } from "vitest";
import contract from "@/test/page-contract.json";
import { openPdf, pdfBytes, type PageSpec } from "@/test/pdf-pages";
import { pageFrame, shownRotation, shownToUnrotated, unrotatedToShown } from "./page-coordinates";

const { drawn, pages } = contract.turned;

async function frameOf(spec: PageSpec) {
    const doc = await openPdf(pdfBytes([spec]));
    try {
        return pageFrame(await doc.getPage(1));
    } finally {
        await doc.destroy();
    }
}

describe("a box drawn on the preview, where the page stores it", () => {
    it.each(Object.entries(pages))("%s", async (_name, spec) => {
        const frame = await frameOf(spec);
        expect([frame.shown.width, frame.shown.height]).toEqual(spec.shown);
        // pdf.js reads /Rotate -90 as 270, 450 as 90 and 80 as 0; the routes read it the same way.
        expect(shownRotation(frame)).toBe("shown_rotate" in spec ? spec.shown_rotate : spec.rotate);
        expect(shownToUnrotated(frame, drawn)).toEqual(spec.unrotated);
        expect(unrotatedToShown(frame, spec.unrotated)).toEqual(drawn);
    });

    it("builds the page whose /Rotate is written as a real number with a real token", () => {
        const spec = pages["cropped-rotate-real-minus-90"];
        expect(spec.real).toBe(true);
        expect(new TextDecoder().decode(pdfBytes([spec]))).toContain("/Rotate -90.0 >>");
    });

    it("leaves a box on an unturned page that starts at 0,0 as drawn", async () => {
        const frame = await frameOf({ mediabox: [0, 0, 612, 792] });
        expect(shownToUnrotated(frame, drawn)).toEqual(drawn);
    });

    it("keeps the direction of a line", async () => {
        const frame = await frameOf(pages["rotate-90"]);
        // Drawn from the top-left corner of the box to its bottom-right, as shown.
        const line = shownToUnrotated(frame, drawn, { line: true });
        const { x, y, width, height } = pages["rotate-90"].unrotated;
        expect(line).toEqual({ x, y: y + height, width, height: -height });
        expect(unrotatedToShown(frame, line, { line: true })).toEqual(drawn);
    });
});
