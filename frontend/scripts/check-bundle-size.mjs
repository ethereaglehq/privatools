import { gzipSync } from "node:zlib";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const assetsDir = new URL("../dist/assets/", import.meta.url);
const maxRawKiB = Number(process.env.MAX_JS_CHUNK_RAW_KIB ?? 1200);
const maxGzipKiB = Number(process.env.MAX_JS_CHUNK_GZIP_KIB ?? 350);

function toKiB(bytes) {
  return bytes / 1024;
}

let entries;
try {
  entries = readdirSync(assetsDir).filter((name) => name.endsWith(".js"));
} catch {
  console.error("Bundle assets not found. Run `npm run build` before `npm run check:bundle`.");
  process.exit(1);
}

const chunks = entries
  .map((name) => {
    const file = join(assetsDir.pathname, name);
    const rawBytes = statSync(file).size;
    const gzipBytes = gzipSync(readFileSync(file)).length;
    return { name, rawKiB: toKiB(rawBytes), gzipKiB: toKiB(gzipBytes) };
  })
  .sort((a, b) => b.gzipKiB - a.gzipKiB);

const offenders = chunks.filter((chunk) => chunk.rawKiB > maxRawKiB || chunk.gzipKiB > maxGzipKiB);

console.log(`JS bundle budget: raw <= ${maxRawKiB} KiB, gzip <= ${maxGzipKiB} KiB per chunk`);
for (const chunk of chunks.slice(0, 20)) {
  console.log(`${chunk.gzipKiB.toFixed(1).padStart(7)} KiB gzip  ${chunk.rawKiB.toFixed(1).padStart(7)} KiB raw  ${chunk.name}`);
}

// The Vite entry chunk (assets/index-<hash>.js — the module the shell
// <script type="module"> tag loads eagerly on every single page) must never
// contain the per-tool guide glob map. `frontend/src/lib/tool-guide.ts`
// builds an `import.meta.glob` over all 221 `data/tool-guide/*.json` files
// (~24 KiB minified) so any one tool's guide can be lazy-loaded; it belongs
// behind the dynamic `import("@/lib/tool-guide")` its consumers (ToolGuide.tsx,
// ToolFaq.tsx) use, not statically imported where every visitor pays for it
// regardless of which page (or no tool page at all) they're on.
const entryChunk = chunks.find((chunk) => /^index-.*\.js$/.test(chunk.name));
let entryChunkLeaksToolGuide = false;
if (entryChunk) {
  const source = readFileSync(join(assetsDir.pathname, entryChunk.name), "utf8");
  entryChunkLeaksToolGuide = source.includes("tool-guide/");
} else {
  console.error("\nWarning: could not find the Vite entry chunk (assets/index-*.js) to check for the tool-guide glob leak.");
}

if (offenders.length > 0) {
  console.error("\nOversized JS chunks:");
  for (const chunk of offenders) {
    console.error(`- ${chunk.name}: ${chunk.gzipKiB.toFixed(1)} KiB gzip, ${chunk.rawKiB.toFixed(1)} KiB raw`);
  }
}

if (entryChunkLeaksToolGuide) {
  console.error(
    `\n${entryChunk.name} (the entry chunk) contains "tool-guide/" — the per-tool guide glob map from ` +
    "frontend/src/lib/tool-guide.ts leaked into it. Its consumers (ToolGuide.tsx, ToolFaq.tsx) must import " +
    'it dynamically inside their effect (e.g. `import("@/lib/tool-guide").then(({ loadToolGuide }) => ...)`) ' +
    "instead of as a static top-level import, or every visitor downloads the full 221-tool glob map."
  );
}

if (offenders.length > 0 || entryChunkLeaksToolGuide) {
  process.exit(1);
}
