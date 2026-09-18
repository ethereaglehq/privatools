# Sitemap priority and review dates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The served sitemap carries `priority` and a real per-tool `lastmod`; the visible review line and JSON-LD `dateModified` use the same date; dead sitemap constants are gone.

**Architecture:** A required `lastReviewed` field on every tool flows through `gen-llms.mjs` into `tool-content.json`, which `seo_meta._last_reviewed_for` already reads. A JSON list of priority slugs feeds both the generator (served file) and the Python fallback through a `priority` value written into each manifest row.

**Tech Stack:** TypeScript registries, `frontend/scripts/gen-llms.mjs`, Vitest, FastAPI/pytest.

**Spec:** `docs/superpowers/specs/2026-09-17-tool-page-seo-design.md` (section 5)

## Global Constraints

- `lastReviewed` is an ISO `YYYY-MM-DD` date, never in the future. Initial value for every tool: the date the copy rewrite lands (use today's date when executing).
- Priorities: `/` 1.0, `/tools` 0.9, listed tools 0.8, other tools 0.6, `/blog` and posts 0.5, `/compare` and pages 0.5, remaining static pages 0.4.
- `_generated_body()` must keep accepting the generated file.
- Branch `feat/tool-page-seo`; commit after every task.

---

### Task 1: Per-tool review dates

**Files:**
- Modify: `frontend/src/data/tools.ts`, `frontend/src/data/non-pdf-tools.ts` (interfaces + one `lastReviewed` line per tool)
- Modify: `frontend/scripts/gen-llms.mjs:73`
- Test: `frontend/src/test/tool-registry.test.ts`, `backend/tests/test_seo_meta.py`, `backend/tests/test_phase2_tool_catalog.py:69-71`

**Interfaces:**
- Produces: `Tool.lastReviewed: string`, `NonPdfTool.lastReviewed: string`; manifest rows carry `lastReviewed`.

- [ ] **Step 1: Write the failing registry test**

```ts
    it("records a valid, non-future review date for every tool", () => {
        const today = new Date().toISOString().slice(0, 10);
        const bad = allTools.filter(tool => !/^\d{4}-\d{2}-\d{2}$/.test(tool.lastReviewed ?? "") || tool.lastReviewed > today).map(tool => tool.slug);
        expect(bad).toEqual([]);
    });
```
Add `/** ISO date of the last content review; drives the sitemap lastmod and the visible review line. */ lastReviewed: string;` to both interfaces.

- [ ] **Step 2: Run it** — `cd frontend && npx vitest run src/test/tool-registry.test.ts` — Expected: FAIL for all 221 tools.

- [ ] **Step 3: Insert the field in every tool**

```bash
DATE=$(date +%F)
python3 - <<PY
import re
from pathlib import Path
for path in ("frontend/src/data/tools.ts", "frontend/src/data/non-pdf-tools.ts"):
    p = Path(path); text = p.read_text(encoding="utf-8")
    text = re.sub(r'(\n(\s*)outputLabel: "(?:[^"\\\\]|\\\\.)*",)', lambda m: f'{m.group(1)}\n{m.group(2)}lastReviewed: "$DATE",', text)
    p.write_text(text, encoding="utf-8")
PY
grep -c 'lastReviewed:' frontend/src/data/tools.ts frontend/src/data/non-pdf-tools.ts   # expect 107 and 114
```
If any tool object lacks `outputLabel`, add its `lastReviewed` by hand; the registry test names the slug.

- [ ] **Step 4: Remove the generator default and run the tests**

In `gen-llms.mjs` line 73 change `lastmod: tool.lastReviewed || '2026-09-13'` to `lastmod: tool.lastReviewed` (the loop below already throws on an invalid date). Run the registry test and `npm run gen:llms` — Expected: PASS; `public/sitemap.xml` tool rows carry today's date.

- [ ] **Step 5: Backend: the manifest date reaches the review line and JSON-LD**

Add to `test_seo_meta.py` (reuse the manifest fixture pattern from the titles plan's parity test, adding `"lastReviewed": "2026-08-02"` to the merge-pdf row):
```python
    assert "Last reviewed 2026-08-02" in seo_meta._build_ssr_content("/tool/merge-pdf", *seo_meta.get_meta_for_path("/tool/merge-pdf"))
    graph = seo_meta._get_jsonld_for_path("/tool/merge-pdf", seo_meta.blog_content_mtime_ns())["@graph"]
    assert any(node.get("dateModified") == "2026-08-02" for node in graph)
```
Run it: it should already PASS because `_last_reviewed_for` reads `manifest[slug]["lastReviewed"]`; if it fails, the `_reviewed_date` mapping expects `reviewedAt`, and the fix is in `_last_reviewed_for` only. Delete `test_phase2_slug_has_fixed_review_date` (the Python dict is fallback-only now) and replace it with:
```python
@pytest.mark.parametrize("slug", P2_SLUGS)
def test_phase2_slug_has_a_review_date(slug: str):
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", seo_meta._last_reviewed_for(slug))
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/data/tools.ts frontend/src/data/non-pdf-tools.ts frontend/scripts/gen-llms.mjs frontend/src/test/tool-registry.test.ts backend/tests/test_seo_meta.py backend/tests/test_phase2_tool_catalog.py
git commit -m "Give every tool a real review date"
```

---

### Task 2: Sitemap priority in the generator and the fallback

**Files:**
- Create: `frontend/src/data/sitemap-priority.json`
- Modify: `frontend/scripts/gen-llms.mjs:67-83`
- Modify: `backend/app/routes/sitemap.py:209-265`
- Test: `frontend/src/test/seo-static.test.ts`, `backend/tests/test_editorial_manifests.py`

**Interfaces:**
- Produces: `sitemap-priority.json` = `{ "highPriorityTools": ["merge-pdf", ...] }` (the 30 slugs from `_HIGH_PRIORITY_TOOLS`); manifest rows gain `"priority": 0.8 | 0.6`; sitemap `<url>` gains `<priority>`.

- [ ] **Step 1: Write the failing frontend test** (in `seo-static.test.ts`, next to the sitemap assertions)

```ts
    it("emits a priority for every sitemap URL, with the priority tools ahead of the rest", () => {
        const sitemap = readFileSync(join(root, "public/sitemap.xml"), "utf8");
        const urls = [...sitemap.matchAll(/<url><loc>([^<]+)<\/loc><lastmod>[^<]+<\/lastmod><priority>([\d.]+)<\/priority><\/url>/g)];
        expect(urls.length).toBe((sitemap.match(/<url>/g) || []).length);
        const priority = Object.fromEntries(urls.map(([, url, value]) => [url.replace("https://privatools.me", "") || "/", Number(value)]));
        expect(priority["/"]).toBe(1);
        expect(priority["/tools"]).toBe(0.9);
        expect(priority["/tool/merge-pdf"]).toBe(0.8);
        expect(priority["/tool/reverse-pdf"]).toBe(0.6);
        expect(priority["/blog"]).toBe(0.5);
        expect(priority["/about"]).toBe(0.4);
    });
```

- [ ] **Step 2: Run it** — Expected: FAIL (no `<priority>`).

- [ ] **Step 3: Generator**

Create `sitemap-priority.json` from the Python set (`python3 -c "import sys; sys.path.insert(0,'backend'); from app.routes import sitemap; import json; print(json.dumps({'highPriorityTools': sorted(sitemap._HIGH_PRIORITY_TOOLS)}, indent=2))" > frontend/src/data/sitemap-priority.json`).

In `gen-llms.mjs`:
```js
import { readFileSync } from 'node:fs';
const { highPriorityTools } = JSON.parse(readFileSync(join(root, 'src/data/sitemap-priority.json'), 'utf8'));
const HIGH = new Set(highPriorityTools);
const priorityFor = path => path === '' ? 1 : path === '/tools' ? 0.9 : path.startsWith('/tool/') || path.startsWith('/tools/') ? (HIGH.has(path.split('/').pop()) ? 0.8 : 0.6) : path.startsWith('/blog') || path.startsWith('/compare') ? 0.5 : 0.4;
```
Give every `tool` object `priority: priorityFor(tool.path)` before `write('tool-content.json', …)`, add `priority: priorityFor(entry.path)` to each sitemap entry, and change the `<url>` template to `<url><loc>…</loc><lastmod>${entry.lastmod}</lastmod><priority>${entry.priority}</priority></url>`. Run `npm run gen:llms` and the test — Expected: PASS.

- [ ] **Step 4: Backend fallback test** (append to `test_editorial_manifests.py`)

```python
def test_fallback_sitemap_emits_priority_from_the_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(sitemap, "GENERATED_SITEMAP", tmp_path / "missing.xml")
    sitemap._render_sitemap.cache_clear()
    body = sitemap._build_sitemap_xml("2026-09-18").decode("utf-8")
    assert "<loc>https://privatools.me/tool/merge-pdf</loc><lastmod>" in body
    assert body.count("<priority>") == body.count("<url>")
    assert "<loc>https://privatools.me</loc><lastmod>2026-09-14</lastmod><priority>1.0</priority>" in body
```

- [ ] **Step 5: Backend implementation**

In `sitemap.py` change `_entries()` to return `dict[str, tuple[str | None, str]]` of `(lastmod, priority)`:
```python
def _priority(path: str, slug: str | None = None) -> str:
    if path == "":
        return "1.0"
    if path == "/tools":
        return "0.9"
    if slug is not None:
        row = (seo_meta._load_manifest(str(seo_meta._TOOL_JSON), seo_meta.blog_content_mtime_ns()) or {}).get(slug) or {}
        return f"{float(row.get('priority') or 0.6):.1f}"
    if path.startswith(("/blog", "/compare")):
        return "0.5"
    return "0.4"
```
and in `_render_sitemap` emit `f"  <url><loc>{escape(url)}</loc>{modified}<priority>{priority}</priority></url>"`. `_generated_body` needs no change. Update `test_sitemap_dates_do_not_change_with_request_day…` only if it compares full bodies (it compares two fallback renders, which both carry priorities).

- [ ] **Step 6: Run both suites and commit**

```bash
git add frontend/src/data/sitemap-priority.json frontend/scripts/gen-llms.mjs frontend/public/sitemap.xml frontend/public/tool-content.json backend/app/routes/sitemap.py backend/tests/test_editorial_manifests.py frontend/src/test/seo-static.test.ts
git commit -m "Emit sitemap priority from one shared list"
```
(Check whether `frontend/public/sitemap.xml` and `tool-content.json` are tracked; if `.gitignore` excludes them, leave them out.)

---

### Task 3: Delete the dead sitemap constants

**Files:**
- Modify: `backend/app/routes/sitemap.py:15-206`
- Test: `backend/tests/test_phase2_tool_catalog.py:38-40`

- [ ] **Step 1: Repoint the one live reference**

Replace `test_phase2_slug_is_in_sitemap_registry` with:
```python
@pytest.mark.parametrize("slug", P2_SLUGS)
def test_phase2_slug_is_in_sitemap_registry(slug: str):
    pdf, nonpdf = seo_meta._tool_registries()
    assert slug in nonpdf
```

- [ ] **Step 2: Delete** `PDF_TOOLS`, `NON_PDF_TOOLS`, `VIDEO_TOOLS`, `_VIDEO_TOOLS_NEW`, `_PDF_V12`, `COMPARE_PAGES`, `BLOG_POSTS`, `_FROZEN`, `_TOOLS_LAUNCH_DATE`, `_COMPARE_DATE`, `_HIGH_PRIORITY_TOOLS` and their comments. `grep -rn "sitemap\.\(PDF_TOOLS\|NON_PDF_TOOLS\|VIDEO_TOOLS\|COMPARE_PAGES\|BLOG_POSTS\|_HIGH_PRIORITY_TOOLS\)" backend` must return nothing.

- [ ] **Step 3: Run the backend suite** — Expected: PASS except the known font case.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/sitemap.py backend/tests/test_phase2_tool_catalog.py
git commit -m "Remove sitemap constants nothing reads"
```

---

### Task 4: Verify and open the PR

- [ ] `cd frontend && npm run build && npm run check:bundle`, then `curl -s http://127.0.0.1:8010/sitemap.xml | grep -c '<priority>'` against the locally served build equals the URL count, and two tool URLs show today's date.
- [ ] Type-check, lint, full Vitest, backend suite.
- [ ] Open the PR against `main` with the priority table, the review-date rule and verification; end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
