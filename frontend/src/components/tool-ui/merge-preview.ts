import type { PDFDocumentProxy } from "pdfjs-dist";

export type MergePreviewDocument = Pick<PDFDocumentProxy, "numPages" | "getPage" | "destroy">;

let pdfjsPromise: Promise<typeof import("pdfjs-dist")> | undefined;

/** PDF previewing is local; the actual merge keeps the existing server engine. */
export async function openMergePreview(file: Blob): Promise<MergePreviewDocument> {
    pdfjsPromise ??= Promise.all([
        import("pdfjs-dist"),
        import("pdfjs-dist/build/pdf.worker.mjs?url"),
    ]).then(([pdfjs, worker]) => {
        pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
        return pdfjs;
    });
    const pdfjs = await pdfjsPromise;
    const data = new Uint8Array(await file.arrayBuffer());
    return pdfjs.getDocument({ data, isEvalSupported: false }).promise;
}
