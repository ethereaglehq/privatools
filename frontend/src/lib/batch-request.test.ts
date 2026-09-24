import { describe, expect, it } from "vitest";
import { batchConfigError, buildBatchForm } from "./batch-request";
import { toolErrorKind } from "./toolRun";

describe("batch settings that cannot run", () => {
    it("reports Highlight PDF without a query as bad input", () => {
        const problem = batchConfigError("highlight-pdf", "   ");
        expect(problem?.message).toBe("Enter the text to highlight before processing these PDFs.");
        expect(toolErrorKind(problem)).toBe("bad_input");
    });
    it("accepts a query, and tools that need none", () => {
        expect(batchConfigError("highlight-pdf", "invoice")).toBeNull();
        expect(batchConfigError("compress-pdf", "")).toBeNull();
    });
});

describe("batch endpoint contracts", () => {
    it.each([
        ["pdf-to-png", "format", "png"], ["pdf-to-jpg", "format", "jpeg"],
        ["pdf-to-tiff", "format", "tiff"], ["pdf-to-gif", "format", "gif"],
        ["png-to-webp", "target_format", "webp"], ["webp-to-jpg", "target_format", "jpeg"],
        ["heic-to-png", "target_format", "png"], ["tiff-to-png", "target_format", "png"],
        ["mp4-to-webm", "target_format", "webm"], ["mov-to-mp4", "target_format", "mp4"],
        ["m4a-to-mp3", "format", "mp3"], ["mp4-to-mp3", "format", "mp3"],
    ])("%s requests its promised output format", (slug, field, value) => {
        const input = new File(["synthetic"], "example.file");
        const body = buildBatchForm(slug, input);
        expect(body.get(field)).toBe(value);
        expect(body.get("file")).toBe(input);
        expect(body.get("files")).toBe(input);
    });
    it.each(["pdf-to-image", "image-converter", "rotate-pdf", "compress-pdf"])("%s keeps the endpoint's native defaults", slug => {
        expect([...buildBatchForm(slug, new File(["x"], "input.pdf")).keys()]).toEqual(["file", "files"]);
    });
    it("supplies the explicitly entered highlight query", () => {
        expect(buildBatchForm("highlight-pdf", new File(["x"], "input.pdf"), "  weekend  ").get("query")).toBe("weekend");
    });
});
