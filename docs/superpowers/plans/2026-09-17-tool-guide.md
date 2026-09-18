# Visible tool guide Implementation Plan

> **Status, 18 September 2026:** implemented in v2.6.0 by #170; the checkboxes were never ticked. Task 4's word floor shipped as 150 words, not 250, and in v2.6.1 #173 replaced Task 3's dynamic `@/data/blog` import for guide links with the generated `frontend/src/data/tool-blog-links.json`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Visitors see the steps, FAQ and guide links on every tool page, loaded from per-tool files exported from the Python content module, and the crawler body is trimmed to the same blocks.

**Architecture:** `scripts/seo/export-tool-guides.py` writes `frontend/src/data/tool-guide/<slug>.json` from `TOOL_HOWTO`/`TOOL_FAQ`; a drift test keeps Python authoritative. `ToolGuide` in the experience workspace lazy-loads one file per slug through `import.meta.glob` and renders visible sections. `seo_meta._build_ssr_content` emits only the blocks the visitor sees.

**Tech Stack:** React 18 + Vite glob imports, Vitest + Testing Library, Python 3.12 + pytest.

**Spec:** `docs/superpowers/specs/2026-09-17-tool-page-seo-design.md` (sections 1, 2 and 4)

## Global Constraints

- Guide copy never contains a three-digit tool count; storage wording is "temporary server processing" / "isolated temporary" for server tools.
- The live tool page is `skins/daylight/SkinApp.tsx` → `skins/experience/ToolWorkspace.tsx`; `pages/ToolPage.tsx` and `pages/NonPdfToolPage.tsx` default exports are dead but must keep compiling.
- Same JSX for Air and Play; Play differences go under `html[data-experience=play]` in `tool-workspace.css`. Do not import `content.css`.
- Bundle budget per chunk: 1200 KiB raw / 350 KiB gzip (`frontend/scripts/check-bundle-size.mjs`); the entry chunk must not grow.
- Type-check with `npx tsc --noEmit -p tsconfig.app.json` from `frontend/`. Backend: `.venv/bin/python -m pytest backend/tests -q --deselect backend/tests/test_api.py` from the repo root.
- Branch `feat/tool-page-seo`; commit after every task.

---

### Task 1: Per-tool guide export with a drift test

**Files:**
- Create: `scripts/seo/export-tool-guides.py`
- Create: `frontend/src/data/tool-guide/<slug>.json` (221 files, generated)
- Create: `backend/tests/test_tool_guide_export.py`
- Delete: `backend/tests/test_tool_faq_export.py`, `frontend/src/data/tool-faq.json`
- Modify: `scripts/README.md` (document the exporter under `seo/`)

**Interfaces:**
- Produces: file `frontend/src/data/tool-guide/<slug>.json` = `{"howto": [{"name","text"}], "faq": [{"q","a"}]}`, pretty-printed with 2-space indent, `ensure_ascii=False`, trailing newline. Tasks 2–3 import these files.
- Produces: `guide_json(slug) -> str` in the exporter, used by the test.

- [ ] **Step 1: Write the failing test**

```python
"""Per-tool guide files must not drift from backend/app/tool_content.py.

Regenerate with: .venv/bin/python scripts/seo/export-tool-guides.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app import seo_meta
from app.tool_content import TOOL_FAQ, TOOL_HOWTO

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "frontend" / "src" / "data" / "tool-guide"
SCRIPT = ROOT / "scripts" / "seo" / "export-tool-guides.py"


def _exporter():
    spec = importlib.util.spec_from_file_location("export_tool_guides", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _registry_slugs() -> set[str]:
    pdf, nonpdf = seo_meta._tool_registries()
    return set(pdf) | set(nonpdf)


def test_export_covers_exactly_the_registered_tools():
    exported = {path.stem for path in EXPORT_DIR.glob("*.json")}
    assert exported == _registry_slugs()
    assert not (ROOT / "frontend" / "src" / "data" / "tool-faq.json").exists()


def test_export_content_matches_python_exactly():
    exporter = _exporter()
    drifted = [slug for slug in _registry_slugs()
               if (EXPORT_DIR / f"{slug}.json").read_text(encoding="utf-8") != exporter.guide_json(slug)]
    assert not drifted, f"Regenerate the export; stale: {drifted[:8]}"


def test_every_tool_has_steps_and_answers():
    for slug in _registry_slugs():
        guide = json.loads((EXPORT_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        assert set(guide) == {"howto", "faq"}
        assert guide["howto"] == TOOL_HOWTO[slug] and len(guide["howto"]) >= 2
        assert guide["faq"] == TOOL_FAQ[slug] and guide["faq"]
        for step in guide["howto"]:
            assert set(step) == {"name", "text"} and step["name"].strip() and len(step["text"].strip()) > 20
        for entry in guide["faq"]:
            assert set(entry) == {"q", "a"} and entry["q"].strip() and len(entry["a"].strip()) > 20
        questions = [entry["q"] for entry in guide["faq"]]
        assert len(questions) == len(set(questions)), f"{slug} asks the same question twice"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest backend/tests/test_tool_guide_export.py -q` — Expected: FAIL (script and directory missing).

- [ ] **Step 3: Write the exporter**

```python
#!/usr/bin/env python3
"""Export one guide file per tool (steps + FAQ) for the frontend.

Python stays authoritative: backend/tests/test_tool_guide_export.py fails when
these files drift from backend/app/tool_content.py. Run from the repo root:

    .venv/bin/python scripts/seo/export-tool-guides.py          # write
    .venv/bin/python scripts/seo/export-tool-guides.py --check  # verify only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app import seo_meta  # noqa: E402
from app.tool_content import TOOL_FAQ, TOOL_HOWTO  # noqa: E402

OUT = ROOT / "frontend" / "src" / "data" / "tool-guide"


def guide_json(slug: str) -> str:
    guide = {"howto": TOOL_HOWTO.get(slug, []), "faq": TOOL_FAQ.get(slug, [])}
    return json.dumps(guide, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if any file is missing or stale")
    args = parser.parse_args()
    pdf, nonpdf = seo_meta._tool_registries()
    slugs = sorted(set(pdf) | set(nonpdf))
    OUT.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for slug in slugs:
        path = OUT / f"{slug}.json"
        content = guide_json(slug)
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(slug)
        else:
            path.write_text(content, encoding="utf-8")
    extra = sorted(path.stem for path in OUT.glob("*.json") if path.stem not in set(slugs))
    for path in ([] if args.check else extra):
        (OUT / f"{path}.json").unlink()
    if args.check and (stale or extra):
        print(f"stale: {stale}\nextra: {extra}", file=sys.stderr)
        return 1
    print(f"{'checked' if args.check else 'wrote'} {len(slugs)} guide files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Generate, delete the old export, run the test**

```bash
.venv/bin/python scripts/seo/export-tool-guides.py
git rm -q frontend/src/data/tool-faq.json backend/tests/test_tool_faq_export.py
.venv/bin/python -m pytest backend/tests/test_tool_guide_export.py -q
```
Expected: 3 passed. Note `_tool_registries()` reads `frontend/dist/tool-content.json` when present, else the Python tables; both list 221 slugs.

- [ ] **Step 5: Document and commit**

Add to `scripts/README.md` under `seo/`: "`export-tool-guides.py` writes `frontend/src/data/tool-guide/*.json` from `backend/app/tool_content.py`; run it after editing steps or FAQ, and `--check` in CI-style verification."

```bash
git add scripts/seo/export-tool-guides.py scripts/README.md backend/tests/test_tool_guide_export.py frontend/src/data/tool-guide
git commit -m "Export one guide file per tool from the Python content module"
```

---

### Task 2: Guide loader

**Files:**
- Create: `frontend/src/lib/tool-guide.ts`
- Test: `frontend/src/lib/tool-guide.test.ts`
- Modify: `frontend/src/components/ToolFaq.tsx:29-37`

**Interfaces:**
- Produces: `loadToolGuide(slug: string): Promise<ToolGuide | null>`, `interface ToolGuide { howto: { name: string; text: string }[]; faq: { q: string; a: string }[] }`.

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { loadToolGuide } from "./tool-guide";

describe("loadToolGuide", () => {
  it("loads the exported steps and questions for a registered slug", async () => {
    const guide = await loadToolGuide("merge-pdf");
    expect(guide?.howto.length).toBeGreaterThan(1);
    expect(guide?.howto[0]).toEqual(expect.objectContaining({ name: expect.any(String), text: expect.any(String) }));
    expect(guide?.faq[0]).toEqual(expect.objectContaining({ q: expect.any(String), a: expect.any(String) }));
  });
  it("resolves null for an unknown slug instead of throwing", async () => {
    await expect(loadToolGuide("../secret")).resolves.toBeNull();
    await expect(loadToolGuide("not-a-tool")).resolves.toBeNull();
  });
});
```

- [ ] **Step 2: Run it** — `cd frontend && npx vitest run src/lib/tool-guide.test.ts` — Expected: FAIL, module not found.

- [ ] **Step 3: Implement**

```ts
/** Per-tool guide files exported from backend/app/tool_content.py (see scripts/seo/export-tool-guides.py). */
export interface ToolGuideStep { name: string; text: string }
export interface ToolGuideQuestion { q: string; a: string }
export interface ToolGuide { howto: ToolGuideStep[]; faq: ToolGuideQuestion[] }

// One chunk per tool; only the visited tool's file is fetched.
const guides = import.meta.glob<ToolGuide>("../data/tool-guide/*.json", { import: "default" });

export function loadToolGuide(slug: string): Promise<ToolGuide | null> {
  const loader = guides[`../data/tool-guide/${slug}.json`];
  return loader ? loader().catch(() => null) : Promise.resolve(null);
}
```

- [ ] **Step 4: Run the test** — Expected: PASS.

- [ ] **Step 5: Point the dead FAQ component at the loader**

In `ToolFaq.tsx` replace the `import("@/data/tool-faq.json")…` block with:
```ts
        loadToolGuide(slug)
            .then(guide => { if (!cancelled) setEntries(guide?.faq ?? null); })
            .catch(() => { /* the FAQ is a bonus; the tool still works without it */ });
```
and add `import { loadToolGuide } from "@/lib/tool-guide";`. Run `npx tsc --noEmit -p tsconfig.app.json` — Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/tool-guide.ts frontend/src/lib/tool-guide.test.ts frontend/src/components/ToolFaq.tsx
git commit -m "Load a tool's guide from its exported file"
```

---

### Task 3: ToolGuide component in the workspace

**Files:**
- Create: `frontend/src/skins/experience/ToolGuide.tsx`
- Test: `frontend/src/skins/experience/ToolGuide.test.tsx`
- Modify: `frontend/src/skins/experience/ToolWorkspace.tsx:14-19,30-32`
- Modify: `frontend/src/skins/experience/ToolWorkspace.test.tsx:6`
- Modify: `frontend/src/skins/experience/tool-workspace.css`
- Modify: `frontend/src/skins/features.ts` (FEATURES + NATIVE_SURFACES.daylight)

**Interfaces:**
- Consumes: `loadToolGuide` (Task 2), `postsForTool(slug, limit)` from `@/data/blog` via dynamic import.
- Produces: `<ToolGuide slug name />` rendering `div.tw-guide#guide`.

- [ ] **Step 1: Write the failing component test**

```tsx
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToolGuide } from "./ToolGuide";

vi.mock("@/lib/tool-guide", () => ({ loadToolGuide: vi.fn(async (slug: string) => slug === "merge-pdf"
  ? { howto: [{ name: "Add PDF files", text: "Drop two or more PDFs." }, { name: "Merge", text: "Download the combined file." }], faq: [{ q: "Is there a limit?", a: "Server capacity limits apply to each request." }] }
  : null) }));
vi.mock("@/data/blog", () => ({ postsForTool: (slug: string) => slug === "merge-pdf" ? [{ slug: "merge-pdf-files-online-free", title: "How to merge PDF files in the right order" }] : [] }));
afterEach(cleanup);

describe("ToolGuide", () => {
  it("renders visible steps, questions and guide links for the tool", async () => {
    await act(async () => { render(<ToolGuide slug="merge-pdf" name="Merge PDF" />); });
    expect(screen.getByRole("heading", { level: 2, name: "How to use Merge PDF" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map(item => item.textContent)).toEqual(expect.arrayContaining([expect.stringContaining("Add PDF files")]));
    expect(screen.getByRole("heading", { level: 3, name: "Is there a limit?" })).toBeVisible();
    expect(screen.getByText("Server capacity limits apply to each request.")).toBeVisible();
    expect(screen.getByRole("link", { name: /How to merge PDF files in the right order/ })).toHaveAttribute("href", "/blog/merge-pdf-files-online-free");
    expect(document.querySelector("details")).toBeNull();
  });
  it("renders nothing for a tool without a guide", async () => {
    const { container } = render(<ToolGuide slug="unknown" name="Unknown" />);
    await act(async () => {});
    expect(container).toBeEmptyDOMElement();
  });
});
```

- [ ] **Step 2: Run it** — Expected: FAIL, component missing.

- [ ] **Step 3: Implement the component**

```tsx
import { useEffect, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { loadToolGuide, type ToolGuide as ToolGuideData } from "@/lib/tool-guide";

type GuideLink = { slug: string; title: string };

/** Steps, questions and related reading under the tool. Same text the server sends to crawlers. */
export function ToolGuide({ slug, name }: { slug: string; name: string }) {
    const [guide, setGuide] = useState<ToolGuideData | null>(null);
    const [links, setLinks] = useState<GuideLink[]>([]);
    useEffect(() => {
        let active = true;
        setGuide(null); setLinks([]);
        loadToolGuide(slug).then(data => { if (active) setGuide(data); });
        // The blog module is large; it becomes its own chunk and loads once.
        import("@/data/blog").then(({ postsForTool }) => { if (active) setLinks(postsForTool(slug, 4).map(post => ({ slug: post.slug, title: post.title }))); }).catch(() => {});
        return () => { active = false; };
    }, [slug]);
    if (!guide || (guide.howto.length === 0 && guide.faq.length === 0)) return null;
    return <div className="tw-guide" id="guide">
        {guide.howto.length > 0 && <section className="tw-guide-steps"><p className="tw-kicker">Step by step</p><h2>How to use {name}</h2><ol>{guide.howto.map(step => <li key={step.name}><strong>{step.name}</strong><span>{step.text}</span></li>)}</ol></section>}
        {guide.faq.length > 0 && <section className="tw-guide-questions"><p className="tw-kicker">Good to know</p><h2>Questions about {name}</h2>{guide.faq.map(item => <section key={item.q}><h3>{item.q}</h3><p>{item.a}</p></section>)}</section>}
        {links.length > 0 && <section className="tw-guide-links"><p className="tw-kicker">Read more</p><h2>Mentioned in our guides</h2><ul>{links.map(link => <li key={link.slug}><a href={`/blog/${link.slug}`}>{link.title} <ArrowUpRight size={15} /></a></li>)}</ul></section>}
    </div>;
}
```

- [ ] **Step 4: Run the component test** — Expected: PASS.

- [ ] **Step 5: Mount it in the workspace and drop the collapsed FAQ**

In `ToolWorkspace.tsx`: delete the `questions` state and its `useEffect` (lines 14–19), delete line 32 (`<details className="tw-questions">…`) and `PlusMark`, import `ToolGuide` from `./ToolGuide`, and insert `<ToolGuide slug={tool.slug} name={tool.name} />` directly after the `tw-working-area` div (before `tw-afterword`).

In `ToolWorkspace.test.tsx` replace `vi.mock("@/data/tool-faq.json", …)` with
```ts
vi.mock("./ToolGuide", () => ({ ToolGuide: ({ slug }: { slug: string }) => <div data-testid="guide">{slug}</div> }));
```
and extend the existing "ordinary server tool" test with:
```ts
    expect(screen.getByTestId("guide")).toHaveTextContent("compress-pdf");
    expect(document.querySelector(".tw-questions")).toBeNull();
```

- [ ] **Step 6: Style it** (append to `tool-workspace.css`)

```css
.tw-guide{display:grid;gap:44px;margin:56px 0 12px;max-width:760px}
.tw-guide h2{font-size:31px;font-weight:500;letter-spacing:-.04em;margin:6px 0 18px;color:var(--pt-ink)}
.tw-guide-steps ol{display:grid;gap:14px;padding-left:0;list-style:none;counter-reset:step}
.tw-guide-steps li{display:grid;grid-template-columns:38px 1fr;gap:6px 14px;align-items:baseline;padding:16px 18px;border:1px solid var(--pt-line);border-radius:var(--pt-radius);background:var(--pt-panel)}
.tw-guide-steps li::before{counter-increment:step;content:counter(step);font-weight:600;color:var(--pt-muted);font-size:14px}
.tw-guide-steps li strong{display:block;font-weight:600;color:var(--pt-ink)}
.tw-guide-steps li span{grid-column:2;color:var(--pt-muted);font-size:15px;line-height:1.7}
.tw-guide-questions section{padding:14px 0;border-top:1px solid var(--pt-line)}
.tw-guide-questions h3{font-size:17px;font-weight:600;margin:0 0 8px;color:var(--pt-ink)}
.tw-guide-questions p{margin:0;color:var(--pt-muted);font-size:15px;line-height:1.75}
.tw-guide-links ul{list-style:none;padding:0;margin:0;display:grid;gap:8px}
.tw-guide-links a{display:inline-flex;align-items:center;gap:6px;color:var(--pt-ink);text-decoration:none;border-bottom:1px solid var(--pt-line)}
.tw-guide-links a:hover{border-color:var(--pt-ink)}
html[data-experience=play] .tw-guide h2{font-size:38px;font-weight:600}
html[data-experience=play] .tw-guide-steps li{background:var(--pt-surface);border:0;border-radius:10px}
```
Delete the now-unused `.tw-questions` rules from the same file.

- [ ] **Step 7: Feature manifest**

In `features.ts` add `{ id: "guide", label: "Tool guide", path: "/tool/:slug#guide", why: "the steps and answers visitors and crawlers both see" }` after the `tool` entry and `"guide"` to `NATIVE_SURFACES.daylight`. Run `npx vitest run src/test/skin-parity.test.ts`.

- [ ] **Step 8: Run the workspace tests, type-check, lint**

Run: `cd frontend && npx vitest run src/skins/experience src/test/skin-parity.test.ts && npx tsc --noEmit -p tsconfig.app.json && npm run lint` — Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/skins/experience/ToolGuide.tsx frontend/src/skins/experience/ToolGuide.test.tsx frontend/src/skins/experience/ToolWorkspace.tsx frontend/src/skins/experience/ToolWorkspace.test.tsx frontend/src/skins/experience/tool-workspace.css frontend/src/skins/features.ts
git commit -m "Show the tool guide to visitors under the tool"
```

---

### Task 4: Trim the crawler body to the visible blocks

**Files:**
- Modify: `backend/app/seo_meta.py:2420-2545` (`_build_ssr_content` tool branches), delete `_trust_paragraph`, `_TRUST_VARIANTS`, `_deep_tool_content`, `_use_cases_for`, `_use_case_category`, `_USE_CASE_POOLS`, `_tldr_for`, `_TLDR_OVERRIDES` when nothing else references them (grep first)
- Test: `backend/tests/test_top50_seo.py:33-51`, `backend/tests/test_seo_meta.py` (the `test_deep_tool_content_has_no_citation_ready_boilerplate` test at ~430 is deleted with the helper)

**Interfaces:**
- Produces: `_related_tools(slug: str, registry: dict, prefix: str) -> list[tuple[str, str, str]]` returning `(slug, name, href)` for the three most popular tools in the same category, excluding `slug`.
- Consumes: `TOOL_HOWTO`, `TOOL_FAQ`, `_tool_to_blogs`, `_by_popularity`, `_last_reviewed_for`.

- [ ] **Step 1: Rewrite the top-50 test expectations first**

Replace the `checks` dict in `test_top50_seo.py` with:
```python
        checks = {
            "250_words": _word_count(body) >= 250,
            "intro": 'class="tool-intro"' in body,
            "steps": 'class="tool-steps"' in body,
            "faq": 'class="tool-faq"' in body,
            "no_template_depth": 'class="tool-depth"' not in body,
            "visible_review": "Last reviewed" in body,
            "related": body.count('class="tool-related"') == 1,
            "howto_schema": "HowTo" in types,
            "faq_schema": "FAQPage" in types,
            "software_schema": "SoftwareApplication" in types,
        }
```
Add to `test_seo_meta.py`:
```python
def test_tool_body_matches_visible_blocks_and_related_tools_share_a_category():
    body = seo_meta._build_ssr_content("/tool/merge-pdf", *seo_meta.get_meta_for_path("/tool/merge-pdf"))
    assert "compare-cta" not in body and "tool-depth" not in body and "TL;DR" not in body
    related = re.findall(r'<li><a href="/tool/([a-z0-9-]+)">', body.split('class="tool-related"', 1)[1].split("</ul>", 1)[0])
    assert 1 <= len(related) <= 3 and "merge-pdf" not in related
    assert body.index('class="tool-steps"') < body.index('class="tool-faq"') < body.index("Last reviewed")
```

- [ ] **Step 2: Run both tests** — Expected: FAIL (`tool-steps` missing, `tool-depth` present).

- [ ] **Step 3: Rewrite the two tool branches**

Replace the body of each branch from the `<h1>` line to `return "\n".join(parts)` with (PDF branch shown; the non-PDF branch is identical with `_NONPDF_TOOLS`, `"tools"` and the heading "Related Tools"):
```python
            parts.append(f"<h1>{name}</h1>")  # the titles plan swaps in the registry seoTitle
            short = _tool_registry_short_description(slug) or desc
            parts.append(f'<p class="tool-summary">{short}</p>')
            parts.append(f'<p class="tool-intro">{desc}</p>')
            if slug in TOOL_HOWTO:
                parts.append(f'<section class="tool-steps"><h2>How to use {name}</h2><ol>')
                for step in TOOL_HOWTO[slug]:
                    parts.append(f"<li><strong>{step['name']}</strong> {step['text']}</li>")
                parts.append("</ol></section>")
            if slug in TOOL_FAQ:
                parts.append(f'<section class="tool-faq"><h2>Questions about {name}</h2>')
                for faq in TOOL_FAQ[slug]:
                    parts.append(f"<h3>{faq['q']}</h3><p>{faq['a']}</p>")
                parts.append("</section>")
            mentioning_posts = _tool_to_blogs().get(slug, [])
            if mentioning_posts:
                parts.append('<section class="tool-guides"><h2>Mentioned in our guides</h2><ul>')
                for post in mentioning_posts:
                    parts.append(f'<li><a href="/blog/{post["slug"]}">{post["title"]}</a></li>')
                parts.append("</ul></section>")
            related = _related_tools(slug, _PDF_TOOLS, "tool")
            if related:
                parts.append('<section class="tool-related"><h2>Related PDF Tools</h2><ul>')
                for related_slug, related_name, href in related:
                    parts.append(f'<li><a href="{href}">{related_name}</a></li>')
                parts.append("</ul></section>")
            reviewed = _last_reviewed_for(slug)
            parts.append(
                f'<p class="meta-trust"><em>Last reviewed {reviewed} by the PrivaTools maintainers. '
                f'Source code on <a href="https://github.com/ethereaglehq/privatools" rel="author">GitHub</a> '
                f'(MIT-licensed, self-hostable).</em></p>'
            )
            return "\n".join(parts)
```
Keep the JSON-LD HowTo `name` in sync: `_howto_name_for` currently yields "How to use the X tool on PrivaTools" and `test_noun_tool_howto_names_are_readable_in_jsonld_and_ssr_html` asserts the `<h2>` matches it. Change `_howto_name_for` to `return f"How to use {normalized}"` and update that test's expected string to `"How to use Barcode Generator"` so the visible heading, the SSR heading and the JSON-LD name stay identical.

Add the helpers near `_by_popularity`:
```python
def _tool_registry_short_description(slug: str) -> str | None:
    data = _load_manifest(str(_TOOL_JSON), blog_content_mtime_ns())
    row = (data or {}).get(slug) or {}
    return row.get("description") or None


def _tool_category(slug: str) -> str | None:
    data = _load_manifest(str(_TOOL_JSON), blog_content_mtime_ns())
    row = (data or {}).get(slug) or {}
    return row.get("category") or None


def _related_tools(slug: str, registry: dict, prefix: str) -> list[tuple[str, str, str]]:
    """The three most popular tools in the same category, matching the workspace's afterword."""
    category = _tool_category(slug)
    candidates = [(s, name) for s, (name, _) in registry.items()
                  if s != slug and (category is None or _tool_category(s) == category)]
    return [(s, name, f"/{prefix}/{s}") for s, name in _by_popularity(candidates)[:3]]
```
Delete the unused helpers and their pools; delete `test_deep_tool_content_has_no_citation_ready_boilerplate`. `_TOTAL_TOOLS` stays (homepage meta uses it).

- [ ] **Step 4: Run the backend suite**

Run: `.venv/bin/python -m pytest backend/tests -q --deselect backend/tests/test_api.py` — Expected: PASS except the known font case. Fix any test that asserted the removed blocks by updating its expectation to the new block names, never by restoring the template text.

- [ ] **Step 5: Commit**

```bash
git add backend/app/seo_meta.py backend/tests/test_top50_seo.py backend/tests/test_seo_meta.py
git commit -m "Send crawlers the same tool page blocks visitors see"
```

---

### Task 5: Build, browser check, PR

- [ ] **Step 1: Build and budget** — `cd frontend && npm run build && npm run check:bundle`. Confirm `dist/assets` contains many small `tool-guide` chunks and no `tool-faq` chunk, and the entry chunk size is unchanged within 5 KiB.
- [ ] **Step 2: Serve locally** — from the repo root `.venv/bin/python scripts/dev/local-backend.py --port 8010` (check `--help` for the flag; port 8000 is taken on this VM). `curl -s http://127.0.0.1:8010/tool/merge-pdf | grep -c 'tool-steps\|tool-faq\|tool-depth'` → steps and FAQ present, depth absent. In a browser (Playwright: `npx playwright screenshot --full-page http://127.0.0.1:8010/tool/merge-pdf /tmp/guide.png` if Chromium is installed, else the built-in `frontend/tests/app.spec.ts` pattern), confirm the guide is visible below the tool after hydration and there is exactly one FAQ.
- [ ] **Step 3: Full verification** — type-check, lint, `npx vitest run`, backend suite, `.venv/bin/python scripts/seo/export-tool-guides.py --check`.
- [ ] **Step 4: Open the PR** against `main` from `feat/tool-page-seo` with a body describing the guide, the export contract, the trimmed body and the verification; end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
