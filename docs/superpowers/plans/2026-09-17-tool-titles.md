# Tool titles, H1 and descriptions Implementation Plan

> **Status, 18 September 2026:** implemented in v2.6.0 by #171; the checkboxes were never ticked. Task 2's `scripts/seo/merge-tool-copy.py` remains as a one-shot script. In v2.6.1 #179 replaced the hand-kept `_PDF_TOOLS`/`_NONPDF_TOOLS` copy behind Task 4's server fallback with tables read from the committed tool manifest.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every tool page gets one hand-written search title and meta description, stored in the registries and used by the server head, the server H1, the visible H1 and the browser tab.

**Architecture:** Two new required fields on `Tool` and `NonPdfTool` flow through the existing `gen-llms.mjs` manifest into `backend/app/seo_meta.py`, which prefers them over the old formula. A small TypeScript helper feeds the workspace H1 and `document.title`; a backend parity test proves server and manifest agree.

**Tech Stack:** TypeScript registries, Vitest, FastAPI/pytest, `frontend/scripts/gen-llms.mjs` (static TS parsing via `content-data.mjs`).

**Spec:** `docs/superpowers/specs/2026-09-17-tool-page-seo-design.md` (sections 1 and 3)

## Global Constraints

- `seoTitle`: 40–60 characters, no "PrivaTools", unique across all 221 tools, query-first (`Merge PDF Files Online Free – Combine PDFs Privately`), en dash `–` as separator, Title Case.
- `metaDescription`: 120–160 characters, at most two sentences, ends with `.`, no `…`, unique.
- No three-digit tool counts in either field. Forbidden claims: `no file size limits`, `never written to disk`, `everything stays in your browser` unless `clientOnly: true`, `password|encrypt|AES` on `create-zip`, `unlimited`, `100% safe`.
- Type-check with `npx tsc --noEmit -p tsconfig.app.json` from `frontend/`. Run the whole backend suite with `.venv/bin/python -m pytest backend/tests -q --deselect backend/tests/test_api.py` from the repo root.
- Branch: `feat/tool-page-seo` (rebased on `main`). Commit after every task.

---

### Task 1: Registry rules as tests

**Files:**
- Modify: `frontend/src/data/tools.ts:18-40` (interface `Tool`)
- Modify: `frontend/src/data/non-pdf-tools.ts:21-42` (interface `NonPdfTool`)
- Test: `frontend/src/test/tool-registry.test.ts`

**Interfaces:**
- Produces: `Tool.seoTitle: string`, `Tool.metaDescription: string`, same on `NonPdfTool`. Tasks 3–5 read them.

- [ ] **Step 1: Write the failing tests** (append inside the existing `describe` in `tool-registry.test.ts`; `allTools` already exists there)

```ts
    const FORBIDDEN = [/no file size limits/i, /never written to disk/i, /unlimited/i, /100% safe/i];

    it("gives every tool a query-first search title within budget", () => {
        const bad = allTools.filter(tool => {
            const title = tool.seoTitle ?? "";
            return title.length < 40 || title.length > 60 || /PrivaTools/.test(title) || title.trim() !== title;
        }).map(tool => `${tool.slug}: ${tool.seoTitle}`);
        expect(bad).toEqual([]);
        const titles = allTools.map(tool => tool.seoTitle.toLowerCase());
        expect(new Set(titles).size).toBe(titles.length);
    });

    it("gives every tool a meta description written to budget", () => {
        const bad = allTools.filter(tool => {
            const text = tool.metaDescription ?? "";
            const sentences = text.split(/(?<=\.)\s+/).filter(Boolean).length;
            return text.length < 120 || text.length > 160 || !text.endsWith(".") || text.includes("…") || sentences > 2;
        }).map(tool => `${tool.slug}: ${tool.metaDescription}`);
        expect(bad).toEqual([]);
        const descriptions = allTools.map(tool => tool.metaDescription.toLowerCase());
        expect(new Set(descriptions).size).toBe(descriptions.length);
    });

    it("keeps search copy free of counts and forbidden claims", () => {
        const bad = allTools.filter(tool => {
            const copy = `${tool.seoTitle}\n${tool.metaDescription}`;
            const browserClaim = /stays in your browser|in your browser/i.test(copy) && !tool.clientOnly;
            return /\b\d{3,}\b/.test(copy) || FORBIDDEN.some(re => re.test(copy)) || browserClaim;
        }).map(tool => tool.slug);
        expect(bad).toEqual([]);
        const createZip = nonPdfTools.find(tool => tool.slug === "create-zip");
        expect(`${createZip?.seoTitle}\n${createZip?.metaDescription}`).not.toMatch(/password|encrypt|AES/i);
    });
```

- [ ] **Step 2: Add the fields to both interfaces** (so the test compiles and fails on content, not types)

In `tools.ts` after `longDescription: string;`:
```ts
  /** Whole <title>, 40–60 chars, query-first, no brand. See docs/superpowers/specs/2026-09-17-tool-page-seo-design.md. */
  seoTitle: string;
  /** Meta description, 120–160 chars, ends with a period. */
  metaDescription: string;
```
Same two lines in `non-pdf-tools.ts` after its `longDescription: string;`.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd frontend && npx vitest run src/test/tool-registry.test.ts`
Expected: the three new tests FAIL listing every slug (fields missing). `npx tsc --noEmit -p tsconfig.app.json` also fails on the 221 objects missing the fields; that is expected until Task 2.

- [ ] **Step 4: Commit the tests and types**

```bash
git add frontend/src/data/tools.ts frontend/src/data/non-pdf-tools.ts frontend/src/test/tool-registry.test.ts
git commit -m "Specify search title and meta description rules for every tool"
```

---

### Task 2: Write the 221 titles and descriptions

**Files:**
- Create (scratch, not committed): `/tmp/claude-1001/.../scratchpad/seo-copy/<group>.json` per author group
- Create: `scripts/seo/merge-tool-copy.py`
- Modify: `frontend/src/data/tools.ts`, `frontend/src/data/non-pdf-tools.ts` (one `seoTitle` and one `metaDescription` line per tool, inserted after `longDescription`)

**Interfaces:**
- Consumes: registry `slug`, `name`, `description`, `longDescription`, `synonyms`, `clientOnly`.
- Produces: JSON `{ "<slug>": { "seoTitle": "...", "metaDescription": "..." } }` merged into the registries.

- [ ] **Step 1: Export the authoring input**

```bash
cd frontend && node -e '
const { readContentArray } = await import("./scripts/content-data.mjs");
const pick = t => ({ slug: t.slug, name: t.name, description: t.description, longDescription: t.longDescription, synonyms: t.synonyms, clientOnly: !!t.clientOnly });
const pdf = readContentArray("src/data/tools.ts", "_toolsRaw", ["icon"]).map(pick);
const rest = readContentArray("src/data/non-pdf-tools.ts", "_nonPdfToolsRaw", ["icon"]).map(pick);
process.stdout.write(JSON.stringify({ pdf, rest }, null, 1));
' > "$SCRATCH/seo-copy/input.json"
```
(`readContentArray` is the same static parser `gen-llms.mjs` uses; run with `--input-type=module` if `await import` is rejected.)

- [ ] **Step 2: Author copy in four parallel groups**

Dispatch four agents, each with ~55 tools from `input.json` and exactly these rules, returning a JSON object keyed by slug:
- `seoTitle` 40–60 chars; opens with the natural search phrase for the task (`Merge PDF Files Online Free`, `Convert HEIC to JPG Online`, `Decode a JWT Token Online`), then ` – ` and one synonym or differentiator drawn from `synonyms`/`longDescription` (`Combine PDFs Privately`, `No Sign-Up`, `Batch Up to 25 Files`); Title Case; no brand; no numbers ≥ 100.
- `metaDescription` 120–160 chars, ≤ 2 sentences, ends with `.`: what it does, then one differentiator. Server tools: "temporary server processing" wording is fine; only `clientOnly` tools may say "in your browser". Forbidden phrases as in Global Constraints.
- Unique within the group; the merge step checks globally.

- [ ] **Step 3: Write the merge script**

```python
#!/usr/bin/env python3
"""Insert seoTitle/metaDescription into the tool registries from JSON copy files."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRIES = [ROOT / "frontend/src/data/tools.ts", ROOT / "frontend/src/data/non-pdf-tools.ts"]

def main(paths: list[str]) -> int:
    copy: dict[str, dict[str, str]] = {}
    for path in paths:
        copy.update(json.loads(Path(path).read_text(encoding="utf-8")))
    missing = []
    for registry in REGISTRIES:
        text = registry.read_text(encoding="utf-8")
        def insert(match: re.Match) -> str:
            slug = match.group(1)
            entry = copy.get(slug)
            if entry is None:
                missing.append(slug)
                return match.group(0)
            indent = match.group(2)
            title = json.dumps(entry["seoTitle"], ensure_ascii=False)
            desc = json.dumps(entry["metaDescription"], ensure_ascii=False)
            return f"{match.group(0)}\n{indent}seoTitle: {title},\n{indent}metaDescription: {desc},"
        # slug line ... longDescription line, capturing the indent of longDescription.
        pattern = re.compile(r'slug: "([a-z0-9-]+)",[\s\S]*?\n(\s*)longDescription: "(?:[^"\\]|\\.)*",')
        text = pattern.sub(insert, text)
        registry.write_text(text, encoding="utf-8")
    if missing:
        print("no copy for:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Merge and validate**

Run: `python3 scripts/seo/merge-tool-copy.py "$SCRATCH"/seo-copy/group-*.json && cd frontend && npx vitest run src/test/tool-registry.test.ts && npx tsc --noEmit -p tsconfig.app.json`
Expected: PASS. If a slug fails a rule, fix that entry in its JSON and re-run the merge on a clean checkout of the two registry files (`git checkout -- frontend/src/data/tools.ts frontend/src/data/non-pdf-tools.ts`).

- [ ] **Step 5: Read a sample by hand**

Print 15 random entries and check they read naturally and describe the right tool:
`node -e 'const {readContentArray}=await import("./scripts/content-data.mjs");const t=[...readContentArray("src/data/tools.ts","_toolsRaw",["icon"]),...readContentArray("src/data/non-pdf-tools.ts","_nonPdfToolsRaw",["icon"])];t.sort(()=>Math.random()-0.5).slice(0,15).forEach(x=>console.log(x.slug,"|",x.seoTitle,"|",x.metaDescription))'`

- [ ] **Step 6: Commit**

```bash
git add scripts/seo/merge-tool-copy.py frontend/src/data/tools.ts frontend/src/data/non-pdf-tools.ts
git commit -m "Write query-first search titles and meta descriptions for every tool"
```

---

### Task 3: One client source for title and H1

**Files:**
- Create: `frontend/src/lib/tool-seo.ts`
- Test: `frontend/src/lib/tool-seo.test.ts`
- Modify: `frontend/src/skins/experience/ToolWorkspace.tsx:7,27`
- Modify: `frontend/src/skins/daylight/SkinApp.tsx:849-853`
- Modify: `frontend/src/pages/NonPdfToolPage.tsx:379`
- Test: `frontend/src/skins/experience/ToolWorkspace.test.tsx`

**Interfaces:**
- Produces: `toolSeo(tool: { name: string; seoTitle?: string; metaDescription?: string; longDescription?: string }): { title: string; h1: string; description: string }`.

- [ ] **Step 1: Write the failing helper test**

```ts
import { describe, expect, it } from "vitest";
import { toolSeo } from "./tool-seo";

describe("toolSeo", () => {
  it("uses the registry search title for both the tab and the heading", () => {
    const seo = toolSeo({ name: "Merge PDF", seoTitle: "Merge PDF Files Online Free – Combine PDFs Privately", metaDescription: "Combine PDFs in order. Free, no sign-up." });
    expect(seo.title).toBe("Merge PDF Files Online Free – Combine PDFs Privately");
    expect(seo.h1).toBe("Merge PDF Files Online Free – Combine PDFs Privately");
    expect(seo.description).toBe("Combine PDFs in order. Free, no sign-up.");
  });
  it("falls back to the tool name for registries without search copy", () => {
    const seo = toolSeo({ name: "Merge PDF", longDescription: "Long text." });
    expect(seo).toEqual({ title: "Merge PDF — Free Online", h1: "Merge PDF", description: "Long text." });
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd frontend && npx vitest run src/lib/tool-seo.test.ts` — Expected: FAIL, module not found.

- [ ] **Step 3: Implement the helper**

```ts
/** One source for a tool page's title, H1 and description. The server reads the same registry fields through the build manifest. */
export interface ToolSeoInput { name: string; seoTitle?: string; metaDescription?: string; longDescription?: string; description?: string }
export interface ToolSeo { title: string; h1: string; description: string }

export function toolSeo(tool: ToolSeoInput): ToolSeo {
  const title = tool.seoTitle?.trim();
  return {
    title: title || `${tool.name} — Free Online`,
    h1: title || tool.name,
    description: tool.metaDescription?.trim() || tool.longDescription || tool.description || "",
  };
}
```

- [ ] **Step 4: Run the helper test** — Expected: PASS.

- [ ] **Step 5: Write the failing workspace test** (add to `ToolWorkspace.test.tsx`; keep the existing mocks)

```ts
  it("uses the search title as the page heading", async () => {
    await act(async () => { render(<ToolWorkspace tool={{ slug: "compress-pdf", name: "Compress PDF", seoTitle: "Compress PDF Online Free – Shrink Files, Keep Quality", description: "A smaller file", category: "pdf" }} categoryLabel="PDF" related={[]} onFindTool={() => undefined}><div>File picker</div></ToolWorkspace>); });
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Compress PDF Online Free – Shrink Files, Keep Quality");
  });
```

- [ ] **Step 6: Run it** — Expected: FAIL (heading is "Compress PDF").

- [ ] **Step 7: Wire the helper**

`ToolWorkspace.tsx`: extend `CatalogTool` with `seoTitle?: string; metaDescription?: string; longDescription?: string;`, import `toolSeo` from `@/lib/tool-seo`, and change the header to `<h1>{toolSeo(tool).h1}</h1>`.

`SkinApp.tsx:851`: replace `` if (t) return `${t.name} Online Free — No Sign Up | PrivaTools`; `` with `if (t) return toolSeo(t).title;` and add `import { toolSeo } from "@/lib/tool-seo";` next to the other `@/lib` imports (the file is `@ts-nocheck`; keep the edit minimal).

`NonPdfToolPage.tsx:379`: replace the `document.title = \`${tool.name} — PrivaTools\`` assignment with `document.title = toolSeo(tool).title;` and import the helper.

- [ ] **Step 8: Run tests and type-check**

Run: `cd frontend && npx vitest run src/skins/experience src/lib/tool-seo.test.ts && npx tsc --noEmit -p tsconfig.app.json` — Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/lib/tool-seo.ts frontend/src/lib/tool-seo.test.ts frontend/src/skins/experience/ToolWorkspace.tsx frontend/src/skins/experience/ToolWorkspace.test.tsx frontend/src/skins/daylight/SkinApp.tsx frontend/src/pages/NonPdfToolPage.tsx
git commit -m "Drive the tool H1 and tab title from the search title"
```

---

### Task 4: Server title, H1 and description from the manifest

**Files:**
- Modify: `backend/app/seo_meta.py:463-477` (`_tool_registries`), `:1713-1728` (`get_meta_for_path` tool branches), `:2426` and `:2486` (SSR `<h1>`)
- Test: `backend/tests/test_seo_meta.py`

**Interfaces:**
- Produces: `_tool_seo_fields(slug: str) -> dict[str, str]` returning `seoTitle`, `metaDescription`, `lastReviewed`, `category` and `popularity` (as strings) from the manifest row, `{}` when no manifest.
- Consumes: manifest rows written by `gen-llms.mjs` (fields flow automatically from the registries).

- [ ] **Step 1: Write the failing parity test**

```python
def test_tool_pages_use_registry_search_copy(tmp_path, monkeypatch):
    manifest = {
        "merge-pdf": {"slug": "merge-pdf", "name": "Merge PDF", "path": "/tool/merge-pdf", "category": "organize",
                      "description": "Combine PDFs", "longDescription": "Long intro text for the page.",
                      "seoTitle": "Merge PDF Files Online Free – Combine PDFs Privately",
                      "metaDescription": "Combine PDF files in the order you choose. Free, no sign-up, temporary server processing."},
        "image-compressor": {"slug": "image-compressor", "name": "Image Compressor", "path": "/tools/image-compressor", "category": "image",
                             "description": "Shrink images", "longDescription": "Long intro for images.",
                             "seoTitle": "Compress Images Online Free – Smaller JPG, PNG and WebP",
                             "metaDescription": "Reduce JPG, PNG and WebP file size with a quality preset you control. Free, no sign-up, temporary server processing."},
    }
    path = tmp_path / "tool-content.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(seo_meta, "_TOOL_JSON", path)
    seo_meta._load_manifest.cache_clear()

    title, description = seo_meta.get_meta_for_path("/tool/merge-pdf")
    assert title == "Merge PDF Files Online Free – Combine PDFs Privately"
    assert description == manifest["merge-pdf"]["metaDescription"]
    html = seo_meta.inject_seo("<html><head><title>x</title></head><body><div id=\"root\"></div></body></html>", "/tools/image-compressor")
    assert "<h1>Compress Images Online Free – Smaller JPG, PNG and WebP</h1>" in html
    assert 'content="Compress Images Online Free – Smaller JPG, PNG and WebP"' in html  # og:title
    assert "| PrivaTools" not in title
```
(`json` is already imported in that test module; `_load_manifest` is the `lru_cache`d loader at `seo_meta.py:405` — check the exact name and cache-clear call when writing the test. If `_TOOL_JSON` is a module constant `Path`, `monkeypatch.setattr` works as written.)

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest backend/tests/test_seo_meta.py -k registry_search_copy -q` — Expected: FAIL, title is `Merge PDF — Free Online | PrivaTools`.

- [ ] **Step 3: Implement**

Add after `_tool_registries`:
```python
_SEO_FIELDS = ("seoTitle", "metaDescription", "lastReviewed", "category", "popularity")


def _tool_seo_fields(slug: str) -> dict[str, str]:
    """Search copy and review data the registries carry through the build manifest."""
    data = _load_manifest(str(_TOOL_JSON), blog_content_mtime_ns())
    row = (data or {}).get(slug) or {}
    return {key: str(row[key]).strip() for key in _SEO_FIELDS if row.get(key) not in (None, "")}
```
In `get_meta_for_path`, both tool branches become:
```python
            name, desc = _PDF_TOOLS[slug]
            fields = _tool_seo_fields(slug)
            return fields.get("seoTitle") or _tool_title(name), fields.get("metaDescription") or _tool_desc(desc)
```
In `_build_ssr_content` (both branches) replace the `<h1>` line with:
```python
            parts.append(f"<h1>{_tool_seo_fields(slug).get('seoTitle') or name}</h1>")
```

- [ ] **Step 4: Run the parity test and the whole backend suite**

Run: `.venv/bin/python -m pytest backend/tests -q --deselect backend/tests/test_api.py` — Expected: PASS apart from the known font-dependent subtitle test on this VM. `test_top50_seo.py` and `test_seo_meta.py:335` only require `<h1` presence.

- [ ] **Step 5: Commit**

```bash
git add backend/app/seo_meta.py backend/tests/test_seo_meta.py
git commit -m "Serve the registry search title and description on tool pages"
```

---

### Task 5: Build, verify in the browser, open the PR

**Files:** none new.

- [ ] **Step 1: Regenerate content and build**

Run: `cd frontend && npm run build` (prebuild regenerates `public/tool-content.json`; confirm with `node -e 'const m=require("./public/tool-content.json");console.log(Object.values(m)[0].seoTitle)'`). Then `npm run check:bundle`.

- [ ] **Step 2: Serve the built app and check one tool page**

Run from repo root: `PORT=8010 .venv/bin/python scripts/dev/local-backend.py --port 8010` (check `--help`; port 8000 belongs to another service on this VM). Then `curl -s http://127.0.0.1:8010/tool/merge-pdf | grep -o '<title>[^<]*</title>\|<h1>[^<]*</h1>\|<meta name="description" content="[^"]*"'`. Expected: title and H1 equal the registry `seoTitle`, description equals `metaDescription`. Open the page in a browser (or Playwright script) and confirm `document.title` after hydration equals the same string and the visible H1 matches.

- [ ] **Step 3: Full verification**

Run: `cd frontend && npx tsc --noEmit -p tsconfig.app.json && npm run lint && npx vitest run` and the backend suite. All green.

- [ ] **Step 4: Open the PR**

```bash
git push -u origin feat/tool-page-seo
gh pr create --base main --title "Give every tool page a hand-written search title and description" --body-file <body>
```
Body: what changed, the copy rules, verification results, and that the H1 and tab title now share one source. End with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
