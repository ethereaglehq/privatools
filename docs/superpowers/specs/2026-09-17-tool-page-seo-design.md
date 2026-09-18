# Tool page SEO: visible guide, search titles, sitemap signals

Design, 17 September 2026. Approved in conversation; implementation follows
the plan in `docs/superpowers/plans/`.

## Problem

Search Console for the last 28 days: 46 clicks, 4,692 impressions, average
position 56.9. Brand queries earn 28 clicks; the other 710 queries, 2,552
impressions, earn zero. Two tool pages already sit on page one (split-pdf at
6.6, crop-pdf at 8.0) and still get no clicks. The causes are in the code:

1. The server injects about 1,100 words per tool page (TL;DR, intro, a rotated
   trust paragraph, five templated "depth" sections, steps, FAQ, related
   tools, guide links) into `#root`, and `createRoot` replaces all of it on
   mount. The visitor sees the H1, one paragraph, the tool and a collapsed
   FAQ. Google indexes the rendered DOM, so the injected copy never ranks and
   the HowTo/FAQ structured data has no visible counterpart.
2. 198 of 221 meta descriptions exceed 160 characters and are machine-cut
   with an ellipsis mid-sentence.
3. Every title is `{name} — Free Online | PrivaTools`, 27 fixed characters,
   no synonyms, no modifiers, mean length 42 of 60.
4. A tool page carries four title strings: the server title, the server H1
   `{name} Online Free — PrivaTools`, the client H1 (bare name) and the client
   document title `{name} Online Free — No Sign Up | PrivaTools`.
5. Sibling tool pages are about 55% identical because the trust paragraph
   rotates through three variants and the depth sections through six pools.
6. `_HIGH_PRIORITY_TOOLS` in `backend/app/routes/sitemap.py` is never emitted;
   the served sitemap has no `priority`. All 221 tool URLs share one
   `lastmod`, because `_last_reviewed_for` reads a manifest key that the
   build never writes and falls back to a constant for every slug. The same
   bug flattens the visible "Last reviewed" line and the JSON-LD
   `dateModified`.

## Goals

- Visitors and crawlers see the same tool-page content.
- Every tool page has one title, one H1 and one description, all written to
  budget and unique across the catalogue.
- The sitemap carries the priority the code already defines and a real
  per-page review date.
- Nothing about tool processing, routing, CSP or the Air/Play experiences
  changes.

## Non-goals

- Category hub pages and internal-link restructuring (follow-up).
- Moving steps/FAQ authoring from Python to TypeScript (follow-up).
- Deleting the dead default exports of `ToolPage.tsx` / `NonPdfToolPage.tsx`
  (the live tool page is `skins/daylight/SkinApp.tsx` →
  `skins/experience/ToolWorkspace.tsx`; the page components' default exports
  never mount). Only their imports are kept compiling.
- Static and blog page titles keep their current form.

## 1. Data and ownership

### Registry fields

`Tool` in `frontend/src/data/tools.ts` and `NonPdfTool` in
`frontend/src/data/non-pdf-tools.ts` gain three required fields:

| Field | Rule |
| --- | --- |
| `seoTitle` | The whole `<title>`, 40–60 characters, no brand suffix, unique across all tools. Query-first: opens with the natural search form of the task, then one synonym or differentiator, e.g. `Merge PDF Files Online Free – Combine PDFs Privately`. |
| `metaDescription` | 120–160 characters, at most two sentences, ends with a period, no ellipsis, unique. States what the tool does plus one differentiator (free, no sign-up, temporary processing, batch). |
| `lastReviewed` | ISO date, not in the future. Set to the date the copy is rewritten for every tool; later edits move it per tool. |

Copy rules shared with the tests: no three-digit tool counts; no claims the
existing tests forbid ("no file size limits", "never written to disk",
"everything stays in your browser" unless the tool is `clientOnly`,
password or encryption claims on Create ZIP, SVG output claims on raster
converters); browser-only tools may say "in your browser", server tools say
"temporary server processing".

The brand suffix is dropped from tool titles on purpose: Google renders the
site name separately from the `WebSite` schema, so `| PrivaTools` spent 13 of
60 characters on a word already shown.

### Manifest projection

`frontend/scripts/gen-llms.mjs` serialises the parsed registries to
`public/tool-content.json`; the new fields flow through automatically. Python
reads them from that manifest via `_tool_registries()`. The hand-written
Python fallback tables stay as the no-manifest fallback and derive the fields:
`seoTitle` → the old `{name} — Free Online | PrivaTools` formula,
`metaDescription` → `_tool_desc(long_description)`, `lastReviewed` → the
existing default.

### Guide export

Steps and FAQ stay authored in `backend/app/tool_content.py`. A new
`scripts/seo/export-tool-guides.py` writes one file per registered slug to
`frontend/src/data/tool-guide/<slug>.json`:

```json
{ "howto": [{ "name": "...", "text": "..." }], "faq": [{ "q": "...", "a": "..." }] }
```

`frontend/src/data/tool-faq.json` is deleted. `backend/tests/test_tool_guide_export.py`
replaces `test_tool_faq_export.py` with the same contract: the file set equals
the registry, every file is byte-identical to the exporter's output, every
entry is non-trivial, questions are unique per tool.

### Guide links

"Mentioned in our guides" uses `postsForTool()` from `frontend/src/data/blog.ts`
through a dynamic import, so the 128 KB blog module becomes its own chunk that
loads once, only when a guide mounts. No new generated file.

## 2. Visible guide

`frontend/src/skins/experience/ToolGuide.tsx`, props `{ slug, name }`,
rendered by `ToolWorkspace` between the working area and the "What's next"
afterword. The collapsed `<details className="tw-questions">` FAQ in
`ToolWorkspace` is removed; the guide replaces it.

- Loading: `frontend/src/lib/tool-guide.ts` exposes `loadToolGuide(slug)`
  over `import.meta.glob("../data/tool-guide/*.json")`, so each page fetches
  only its own file (about 2 KB). Unknown slug resolves to `null` and the
  guide renders nothing.
- Sections, in order, each a `<section>` with an `<h2>`:
  1. "How to use {name}": `<ol>` of steps, `<strong>` step name then text.
  2. "Questions about {name}": every Q&A visible as `<h3>` and `<p>`; nothing
     collapsed.
  3. "Mentioned in our guides": links to blog posts from `postsForTool`,
     omitted when empty.
- Related tools stay in the existing afterword; the guide does not repeat
  them.
- The workspace H1 becomes `tool.seoTitle`; `tw-description` keeps
  `tool.description`. `SkinApp.tsx` sets `document.title` to `seoTitle`
  (the one live title path). The unused `NonPdfToolPage` title assignment is
  aligned for consistency.
- Styling lives in `tool-workspace.css` using the workspace tokens
  (`--pt-ink`, `--pt-muted`, `--pt-line`, `--pt-radius`), the `.tw-afterword`
  heading scale and `.tw-kicker`. Play differences go under
  `html[data-experience=play]`. `content.css` is not imported.
- Copy inside the guide never contains a three-digit count and uses the
  storage wording the static-claims test allows.
- `frontend/src/skins/features.ts` gets a `guide` feature entry so the skin
  parity test tracks the new surface.
- `components/ToolFaq.tsx` (dead path) switches to `loadToolGuide` so it keeps
  compiling without the deleted JSON.

## 3. Titles, H1 and descriptions on the server

In `backend/app/seo_meta.py`:

- `_tool_registries()` returns `seoTitle`, `metaDescription` and
  `lastReviewed` from the manifest rows.
- `get_meta_for_path()` for `/tool/<slug>` and `/tools/<slug>` uses
  `seoTitle` as title (also OG and Twitter title) and `metaDescription` as
  description. `_tool_title` / `_tool_desc` remain as the fallback for rows
  without the fields.
- `_build_ssr_content` emits `<h1>{seoTitle}</h1>`.
- `_last_reviewed_for` reads the manifest `lastReviewed` value; the fallback
  branch is unchanged.
- A shared TypeScript helper `frontend/src/lib/tool-seo.ts` exports
  `toolSeo(tool)` returning `{ title, h1, description }` for the client. A
  backend parity test asserts the server title, H1 and description for a
  sample of slugs equal the manifest fields.

## 4. Server body

`_build_ssr_content` tool branches emit exactly, in order: H1, short
description paragraph, intro paragraph (`longDescription`), "How to use"
steps (`class="tool-steps"`), FAQ (`class="tool-faq"`), the same three related
tools the client shows (same category, popularity order, excluding self),
"Mentioned in our guides", the "Last reviewed" line. Removed: the trust
paragraph, the depth section, the compare and cross CTAs, and their helpers
(`_trust_paragraph`, `_TRUST_VARIANTS`, `_deep_tool_content`,
`_use_cases_for`, `_use_case_category`, `_USE_CASE_POOLS`) once no other
caller remains. `backend/tests/test_top50_seo.py` requires the steps and FAQ
blocks, the review line and at least 250 words instead of 800 words and
`tool-depth`.

## 5. Sitemap priority and review dates

- `frontend/src/data/sitemap-priority.json` holds `highPriorityTools`, moved
  from `_HIGH_PRIORITY_TOOLS`. `gen-llms.mjs` emits `<priority>`: `/` 1.0,
  `/tools` 0.9, listed tools 0.8, other tools 0.6, blog index and posts 0.5,
  compare hub and pages 0.5, remaining static pages 0.4. It also writes
  `priority` into each `tool-content.json` row so the Python fallback
  (`sitemap.py:_render_sitemap`) emits the same value.
- Tool `lastmod` comes from `lastReviewed`; the `|| '2026-09-13'` default is
  removed so a missing date fails the build.
- `_generated_body()` keeps accepting the generated file (it does not inspect
  `priority`).
- Dead constants in `sitemap.py` (`PDF_TOOLS`, `NON_PDF_TOOLS`, `VIDEO_TOOLS`,
  `_VIDEO_TOOLS_NEW`, `_PDF_V12`, `COMPARE_PAGES`, `BLOG_POSTS`, `_FROZEN`,
  `_TOOLS_LAUNCH_DATE`, `_COMPARE_DATE`, `_HIGH_PRIORITY_TOOLS`) are deleted;
  `test_phase2_tool_catalog.py` checks the registry manifest instead, and its
  fixed-review-date test asserts a valid manifest date rather than the old
  Python dict.

## 6. Testing

Frontend (Vitest):
- `tool-registry.test.ts`: `seoTitle` 40–60 chars, unique, no "PrivaTools";
  `metaDescription` 120–160 chars, unique, ends with a period, no ellipsis;
  `lastReviewed` valid ISO date not after today; forbidden-claim scan over
  the new fields.
- `ToolWorkspace.test.tsx`: renders the guide steps, visible FAQ and guide
  links for a slug (glob mocked), H1 equals `seoTitle`, no `tw-questions`.
- `seo-static.test.ts` / content tests: generated sitemap has `priority` on
  every URL and per-tool `lastmod` equal to the registry.
- `check-bundle-size.mjs` budgets unchanged; the entry chunk must not grow.

Backend (pytest):
- `test_tool_guide_export.py` drift contract.
- `test_seo_meta.py`: title, H1 and description parity with the manifest;
  body contains steps and FAQ and no `tool-depth`; JSON-LD `dateModified`
  equals the manifest date.
- `test_top50_seo.py` updated floor.
- Sitemap tests: `priority` present in generated and fallback output; lastmod
  varies per tool with the manifest.

Verification before each PR: type-check, lint, full Vitest, full backend
suite, then the built app served locally with a tool page checked after
hydration (title, H1, guide visible, single FAQ).

## 7. Delivery

Three PRs, each shippable alone, in this order:

1. Guide export, `ToolGuide`, workspace changes, server body trim.
2. Registry `seoTitle` / `metaDescription`, server and client title, H1 and
   description, parity tests. The 221 titles and descriptions are written by
   parallel agents under the rules in section 1, validated by the registry
   tests, then sampled by hand.
3. `lastReviewed`, sitemap priority, dead-constant removal.

## 8. Risks

- Google re-evaluates after recrawl; expect weeks, not days. The leading
  indicator is the Search Console CTR on split-pdf and crop-pdf, which already
  rank on page one.
- Trimming the crawler body lowers word count per page; the removed text was
  template, and Google's rendered view never contained it.
- Hand-written copy at this scale can drift in tone; the tests enforce
  budgets and claims, and the plan includes a sampled read.
