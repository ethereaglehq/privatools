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
 * helpers name each upload after its route instead; these checks keep
 * hand-built forms from bringing the double send back, or from sending one
 * name to a route that reads the other, which the route answers with a 422.
 */
describe("hand-built upload forms", () => {
    const root = process.cwd();
    function walk(dir: string): string[] {
        return readdirSync(dir).flatMap(name => {
            const full = join(dir, name);
            return statSync(full).isDirectory() ? walk(full) : [full];
        });
    }
    const sources = walk(join(root, "src"))
        .filter(path => /\.tsx?$/.test(path) && !/\.test\.tsx?$/.test(path))
        .map(path => ({ path: relative(root, path), text: readFileSync(path, "utf8") }));

    function appended(text: string, field: string): Set<string> {
        const pattern = new RegExp(String.raw`\.append\(\s*(["'\`])${field}\1\s*,\s*([^,)]+)`, "g");
        return new Set([...text.matchAll(pattern)].map(match => match[2].trim()));
    }

    /** Each `postFormData("<literal>", …)` call: its endpoint and the text of
     *  the whole call, found by matching parentheses outside strings and
     *  comments. Calls whose endpoint is not a plain literal are skipped. */
    function postFormDataCalls(text: string): { endpoint: string; call: string }[] {
        const calls: { endpoint: string; call: string }[] = [];
        for (const match of text.matchAll(/\bpostFormData\(\s*(["'`])(\/[^"'`$]*)\1/g)) {
            const open = match.index! + match[0].indexOf("(");
            let depth = 0;
            for (let i = open; i < text.length; i++) {
                const ch = text[i];
                if (ch === '"' || ch === "'" || ch === "`") {
                    for (i++; i < text.length && text[i] !== ch; i++) if (text[i] === "\\") i++;
                } else if (text.startsWith("//", i)) {
                    i = text.indexOf("\n", i) < 0 ? text.length : text.indexOf("\n", i);
                } else if (text.startsWith("/*", i)) {
                    i = text.indexOf("*/", i) < 0 ? text.length : text.indexOf("*/", i) + 1;
                } else if (ch === "(") {
                    depth++;
                } else if (ch === ")" && --depth === 0) {
                    calls.push({ endpoint: match[2], call: text.slice(open, i + 1) });
                    break;
                }
            }
        }
        return calls;
    }

    it("never appends the same value as both `file` and `files`", () => {
        expect(sources.length).toBeGreaterThan(100);
        const doubled = sources.flatMap(({ path, text }) => {
            const asFile = appended(text, "file");
            return [...appended(text, "files")].filter(value => asFile.has(value)).map(value => `${path}: ${value}`);
        });
        expect(doubled).toEqual([]);
    });

    it("never lists `file` and `files` together, as a loop over both names would", () => {
        const both = sources.flatMap(({ path, text }) => [...text.matchAll(/\[([^[\]]*)\]/g)]
            .filter(([, items]) => {
                const names = new Set([...items.matchAll(/(["'`])([^"'`]*)\1/g)].map(match => match[2]));
                return names.has("file") && names.has("files");
            })
            .map(([array]) => `${path}: ${array}`));
        expect(both).toEqual([]);
    });

    it("sends each hand-built postFormData upload under the field its route reads", () => {
        const checked: string[] = [];
        const wrong = sources.flatMap(({ path, text }) => postFormDataCalls(text).flatMap(({ endpoint, call }) =>
            [...call.matchAll(/\.append\(\s*(["'`])(files?)\1\s*,/g)].flatMap(([, , field]) => {
                checked.push(`${endpoint} ${field}`);
                const reads = uploadFieldFor(endpoint);
                return field === reads ? [] : [`${path}: posts \`${field}\` to ${endpoint}, which reads \`${reads}\``];
            })));
        expect(wrong).toEqual([]);
        // The scan found real forms for both kinds of route, so a pass means something.
        expect(checked.some(entry => entry.endsWith(" files"))).toBe(true);
        expect(checked.filter(entry => entry.endsWith(" file")).length).toBeGreaterThan(5);
    });
});
