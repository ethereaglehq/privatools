import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Every tool surface that processes something must report a `tool_run`, or
 * the usage numbers silently undercount the catalogue. The shared engines
 * report centrally; everything else that talks to the backend, plus the
 * browser-only tools with an explicit run action, must call emitToolRun.
 * Tools whose output updates live as you type are counted by page view only.
 */
const root = process.cwd();
const ENGINES = [
    "src/components/tool-ui/GenericUI.tsx",
    "src/components/tool-ui/SimpleConvertUI.tsx",
    "src/components/tool-ui/media/useMediaJob.ts",
    "src/hooks/useMultiFileProcessor.ts",
];
const BROWSER_ONLY_RUNNERS = [
    "src/components/tool-ui/SummarizePdfUI.tsx",
    "src/components/tool-ui/ChatPdfUI.tsx",
    "src/components/tool-ui/TranscribeAudioUI.tsx",
    "src/components/tool-ui/SubtitleConverterUI.tsx",
    "src/components/tool-ui/JsonXmlFormatterUI.tsx",
    "src/components/tool-ui/TextDiffUI.tsx",
    "src/components/tool-ui/HashGeneratorUI.tsx",
    "src/components/tool-ui/CsvJsonUI.tsx",
];
/** Files whose only backend call is the per-file worker handed to useMultiFileProcessor, which reports for them. */
const ENGINE_WORKERS = ["src/components/tool-ui/RemoveExifUI.tsx"];
const BACKEND_CALL = /\b(uploadFile|uploadFiles|uploadFileWithProgress|uploadFilesWithProgress|uploadFileGetJson|postFormData|processAndDownload|processFilesAndDownload)\s*\(/;

function walk(dir: string): string[] {
    return readdirSync(dir).flatMap(name => {
        const full = join(dir, name);
        return statSync(full).isDirectory() ? walk(full) : [full];
    });
}

describe("tool_run coverage", () => {
    it("every tool surface that processes files reports its run", () => {
        const files = walk(join(root, "src/components/tool-ui"))
            .map(file => relative(root, file))
            .filter(rel => /\.tsx?$/.test(rel) && !/\.test\.tsx?$/.test(rel) && !ENGINES.includes(rel) && !ENGINE_WORKERS.includes(rel));
        const offenders = files.filter(rel => {
            const source = readFileSync(join(root, rel), "utf8");
            return (BACKEND_CALL.test(source) || BROWSER_ONLY_RUNNERS.includes(rel)) && !source.includes("emitToolRun(");
        });
        expect(offenders).toEqual([]);
    });
    it("the shared engines report their runs", () => {
        for (const rel of ENGINES) expect(readFileSync(join(root, rel), "utf8")).toContain("emitToolRun(");
    });
});
