import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";
import { FILES_FIELD_ROUTES, uploadFieldFor } from "./upload-fields";

describe("the field an upload travels under", () => {
    it("is `files` for a route that reads `files: list[UploadFile]`", () => {
        expect(uploadFieldFor("/compress")).toBe("files");
        expect(uploadFieldFor("/strip-metadata")).toBe("files");
        expect(uploadFieldFor("/merge")).toBe("files");
    });

    it("is `file` for every other route", () => {
        expect(uploadFieldFor("/grayscale")).toBe("file");
        expect(uploadFieldFor("/watermark")).toBe("file");
        // A route whose name merely starts like a listed one is not listed.
        expect(uploadFieldFor("/compress-video")).toBe("file");
    });

    it("accepts the endpoint in every form the upload helpers accept", () => {
        for (const endpoint of ["/compress", "/api/compress", "compress", "/compress?level=light"]) {
            expect(uploadFieldFor(endpoint)).toBe("files");
        }
        for (const endpoint of ["/grayscale", "/api/grayscale", "grayscale"]) {
            expect(uploadFieldFor(endpoint)).toBe("file");
        }
    });

    it("keeps its route list in the form backend/tests/test_upload_fields.py compares", () => {
        expect([...FILES_FIELD_ROUTES]).toEqual([...new Set(FILES_FIELD_ROUTES)].sort());
        for (const route of FILES_FIELD_ROUTES) expect(route).toMatch(/^\/(?!api\/)[a-z0-9/-]+$/);
    });
});

/**
 * Appending one value under both `file` and `files` sends that file twice in
 * one request, which halves what fits under the 500 MB request cap. The
 * helpers name each upload after its route instead; this keeps hand-built
 * forms from bringing the double send back.
 */
describe("no request carries a file twice", () => {
    const root = process.cwd();
    function walk(dir: string): string[] {
        return readdirSync(dir).flatMap(name => {
            const full = join(dir, name);
            return statSync(full).isDirectory() ? walk(full) : [full];
        });
    }
    const sources = walk(join(root, "src")).filter(path => /\.tsx?$/.test(path) && !/\.test\.tsx?$/.test(path));

    function appended(text: string, field: string): Set<string> {
        const pattern = new RegExp(String.raw`\.append\(\s*(["'\`])${field}\1\s*,\s*([^,)]+)`, "g");
        return new Set([...text.matchAll(pattern)].map(match => match[2].trim()));
    }

    it("never appends the same value as both `file` and `files`", () => {
        expect(sources.length).toBeGreaterThan(100);
        const doubled = sources.flatMap(path => {
            const text = readFileSync(path, "utf8");
            const asFile = appended(text, "file");
            return [...appended(text, "files")].filter(value => asFile.has(value)).map(value => `${relative(root, path)}: ${value}`);
        });
        expect(doubled).toEqual([]);
    });
});
