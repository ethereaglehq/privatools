import { describe, expect, it } from "vitest";
import { mergePageSelection, toggleMergePage, moveMergeFile, mergeOutputFilename, mergeSourceMap, compactMergePages, saveMergeWorkflow } from "./merge-model";

describe("merge page selections", () => {
    it("snapshots ordered output sources and identifies every excluded source page", () => {
        expect(mergeSourceMap([{ filename: "check.pdf", total: 1, range: "" }, { filename: "notes.pdf", total: 5, range: "5,1" }])).toEqual({
            outputPages: [{ filename: "check.pdf", page: 1 }, { filename: "notes.pdf", page: 5 }, { filename: "notes.pdf", page: 1 }],
            excludedPages: [{ filename: "notes.pdf", pages: [2, 3, 4] }],
        });
        expect(compactMergePages([2, 3, 4, 6, 8, 9])).toBe("2–4, 6, 8–9");
    });
    it("never guesses output identities when a source count is unavailable", () => {
        expect(mergeSourceMap([{ filename: "unknown.pdf", total: null, range: "" }, { filename: "known.pdf", total: 3, range: "1" }])).toEqual({
            outputPages: null, excludedPages: [{ filename: "known.pdf", pages: [2, 3] }],
        });
    });
    it("preserves existing workflow names and reports blocked storage instead of claiming a save", () => {
        let value = JSON.stringify([{ name: "Merge PDFs", slugs: ["compress-pdf"], savedAt: 1 }]);
        const storage = { getItem: () => value, setItem: (_key: string, next: string) => { value = next; } };
        expect(saveMergeWorkflow(storage)).toBe("Merge PDFs 2");
        expect(saveMergeWorkflow(storage)).toBe("Merge PDFs 2");
        expect(JSON.parse(value)).toHaveLength(2);
        expect(JSON.parse(value)[1]).toEqual({ name: "Merge PDFs", slugs: ["compress-pdf"], savedAt: 1 });
        expect(() => saveMergeWorkflow({ getItem: () => "[]", setItem: () => { throw new Error("quota"); } })).toThrow("quota");
    });
    it("matches the server's ordered deduplication and open/end range semantics", () => {
        expect(mergePageSelection("3,1-2,3,end", 5)).toEqual({ pages: [3, 1, 2, 5], error: null });
        expect(mergePageSelection("-2,4-", 5)).toEqual({ pages: [1, 2, 4, 5], error: null });
        expect(mergePageSelection("2-end", 3).pages).toEqual([2, 3]);
        expect(mergePageSelection("", 3).pages).toEqual([1, 2, 3]);
        expect(mergePageSelection("ALL", 2).pages).toEqual([1, 2]);
    });
    it.each(["0", "00", "4", "3-2", "end-2", "-", ",,", "1-2-3", "hello", "9999999999"])("rejects invalid/out-of-bounds selection %s", value => {
        expect(mergePageSelection(value, 3).error).toBeTruthy();
    });
    it("validates unknown-page files without expanding huge ranges or inventing page counts", () => {
        expect(mergePageSelection("1-999999999", null)).toEqual({ pages: null, error: null });
        expect(mergePageSelection("end", null)).toEqual({ pages: null, error: null });
        expect(mergePageSelection("0", null).error).toBeTruthy();
    });
    it("keeps a thumbnail exclusion in the actual request range and forbids empty-means-all ambiguity", () => {
        expect(toggleMergePage("", 3, 2)).toBe("1,3");
        expect(toggleMergePage("1", 3, 1)).toBeNull();
        expect(toggleMergePage("", 1, 1)).toBeNull();
        expect(toggleMergePage("3,1", 3, 2)).toBe("3,1,2");
        expect(toggleMergePage("1,2", 3, 3)).toBe("");
    });
    it("moves the entire file plus its page selection, retaining identical filenames", () => {
        const files = [{ name: "same.pdf", pages: "1" }, { name: "same.pdf", pages: "2" }];
        expect(moveMergeFile(files, 1, 0)).toEqual([files[1], files[0]]);
        expect(moveMergeFile(files, 0, -1)).toBe(files);
        expect(files[0].pages).toBe("1");
    });
    it("produces a portable PDF filename without mutating its extension", () => {
        expect(mergeOutputFilename(" Combined ")).toBe("Combined.pdf");
        expect(mergeOutputFilename("report.PDF")).toBe("report.pdf");
        expect(mergeOutputFilename("/private/report?.pdf")).toBe("privatereport.pdf");
        expect(mergeOutputFilename("...  ")).toBe("Combined.pdf");
    });
});
