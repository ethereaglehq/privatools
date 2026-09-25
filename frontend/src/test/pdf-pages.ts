/**
 * Real pdf.js pages for tests: PDFs with the boxes and /Rotate a test asks
 * for, opened by pdf.js the way the preview opens them. Only drawing is
 * replaced (jsdom has no canvas); every viewport is pdf.js's own, so a test of
 * where a box lands checks pdf.js's math rather than a copy of it.
 */
import type { MergePreviewDocument } from "@/components/tool-ui/merge-preview";

export interface PageSpec {
    mediabox: number[];
    cropbox?: number[];
    /** /Rotate as written, which pdf.js may read otherwise (-90 as 270, 80 as 0). */
    rotate?: number;
    /** Write /Rotate on the page tree instead of the page. */
    inherited?: boolean;
    /** Write /Rotate as a real number (-90.0) rather than an integer. */
    real?: boolean;
}

/** /Rotate as the file writes it. */
const rotateToken = ({ rotate, real }: PageSpec) => (real ? rotate!.toFixed(1) : String(rotate));

/** A PDF whose pages have these boxes and turns, and nothing on them. */
export function pdfBytes(pages: PageSpec[]): Uint8Array {
    const kids = pages.map((_, index) => `${index + 3} 0 R`).join(" ");
    // The page tree carries the first inherited /Rotate.
    const inherited = pages.find(page => page.inherited && page.rotate);
    const objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        `<< /Type /Pages /Kids [${kids}] /Count ${pages.length}${inherited ? ` /Rotate ${rotateToken(inherited)}` : ""} >>`,
        ...pages.map(page =>
            `<< /Type /Page /Parent 2 0 R /MediaBox [${page.mediabox.join(" ")}]` +
            `${page.cropbox ? ` /CropBox [${page.cropbox.join(" ")}]` : ""}${page.rotate && !page.inherited ? ` /Rotate ${rotateToken(page)}` : ""} >>`),
    ];
    let out = "%PDF-1.7\n";
    const offsets: number[] = [];
    objects.forEach((body, index) => { offsets.push(out.length); out += `${index + 1} 0 obj\n${body}\nendobj\n`; });
    const xref = out.length;
    out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
    out += offsets.map(offset => `${String(offset).padStart(10, "0")} 00000 n \n`).join("");
    out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
    return new TextEncoder().encode(out);
}

const noDrawing = () => ({ promise: Promise.resolve(), cancel: () => {} });

/** The PDF as the preview's pdf.js opens it, with drawing switched off. */
export async function openPdf(bytes: Uint8Array): Promise<MergePreviewDocument> {
    const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
    const doc = await pdfjs.getDocument({ data: bytes, isEvalSupported: false, verbosity: 0 }).promise;
    return {
        numPages: doc.numPages,
        getPage: async (number: number) => {
            const page = await doc.getPage(number);
            return { getViewport: page.getViewport.bind(page), render: noDrawing } as unknown as Awaited<ReturnType<MergePreviewDocument["getPage"]>>;
        },
        destroy: () => doc.destroy(),
    };
}
