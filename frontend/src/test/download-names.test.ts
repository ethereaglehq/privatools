/**
 * How a download is named, now that the page can read Content-Disposition.
 *
 * Cross-origin, the page could not read the header, so every page named its
 * downloads itself. Pages that read it choose between the server's name and
 * their own with chooseDownloadFilename (lib/api.ts), which keeps the page's
 * name when the server's is a generic one such as "converted.docx".
 */
import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useMultiFileProcessor } from "@/hooks/useMultiFileProcessor";
import { installNetwork, sizedFile } from "./fake-network";

afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
});

async function convert(serverName: string, run: { endpoint: string; outputExt: string; outputSuffix: string | null }, file = "thesis.pdf") {
    installNetwork({ uploadMs: 0, answerAfterMs: 0, body: "result",
        headers: { "content-type": "application/octet-stream", "content-disposition": `attachment; filename="${serverName}"` } });
    const { result } = renderHook(() => useMultiFileProcessor());
    act(() => result.current.addFiles([sizedFile(file, 1024)]));
    await act(() => result.current.run(run));
    return result.current.entries[0];
}

describe("useMultiFileProcessor: PDF to Word, Protect, Compress and 41 other pages", () => {
    it("keeps its own name when the server's is generic", async () => {
        const entry = await convert("converted.docx", { endpoint: "/pdf-to-word", outputExt: "docx", outputSuffix: null });
        expect(entry.status).toBe("done");
        expect(entry.outName).toBe("thesis.docx");
    });

    it("takes the server's name when it names the file better", async () => {
        // Same stem, and the server knows the result is a ZIP of pages.
        const entry = await convert("report_images.zip", { endpoint: "/pdf-to-image", outputExt: "png", outputSuffix: "images" }, "report.pdf");
        expect(entry.outName).toBe("report_images.zip");
    });
});
