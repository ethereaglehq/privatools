# GEO / AI-Search Runbook

Concrete steps to raise PrivaTools' visibility in AI answers (ChatGPT, Claude,
Perplexity, Gemini, AI Overviews). The **in-repo** citability work is already
shipped (knowledge-graph–anchored `knowsAbout`, server-rendered tool pages that
match the visible guide, JSON-LD, llms.txt). The items below need an external
account, so they're handed off here rather than done in code.

## 1. Activate Cloudflare (free tier) — perf + makes the CDN claim true

**Done.** Checked from outside on 18 September 2026: `privatools.me` and `www`
answer with `server: cloudflare`, `api.privatools.me` resolves straight to the
VM, and a hashed asset returns `cf-cache-status: HIT` with Brotli after a
warm-up. The domain's nameservers are Cloudflare's
(`oaklyn`/`rudy.ns.cloudflare.com`).

> **Do NOT proxy the api host.** Cloudflare's free/pro plans cap a
> **proxied** request body at **100 MB**, but PrivaTools accepts **500 MB**, so
> proxying `/api` uploads silently 413s every large one. That is why the
> **api-subdomain split** exists: the SPA's `/api` traffic goes to a grey-clouded
> `api.privatools.me` (direct to the VM, uncapped, off Cloudflare), while the
> apex/`www` are proxied for static. It is controlled by
> `PUBLIC_API_BASE_URL`; **[deploy/api-subdomain-split.md](../../deploy/api-subdomain-split.md)**
> records the ordered activation and the rollback.

Cloudflare-dashboard settings to keep (confirm them in the dashboard; only the
cache status and Brotli are visible from outside):

- **SSL/TLS** mode → **Full (strict)** (the VM has a real Let's Encrypt cert).
- **Speed** → enable **Brotli**; leave **Auto Minify** off (Vite pre-minifies); **Early Hints** on.
- **Caching** → Cache Level Standard; Cache Rule: cache `*/assets/*` and `*.woff2`
  (the app already sends 1-year immutable headers on hashed assets), **bypass
  cache for `/api/*`**.
- Verify: `curl -sI https://privatools.me/assets/<hashed>.js | grep -i cf-cache-status` returns `HIT` after a warm-up.

Outcome: real edge caching + Brotli for static assets and lower global LCP,
while large uploads keep working via the direct api host.

## 2. Mint a Wikidata Q-number — entity disambiguation for AI

AI engines resolve "PrivaTools" against the knowledge graph. A Wikidata item
makes the entity unambiguous and citable.

1. Create a Wikidata account, then **Create a new Item** at wikidata.org.
2. Label: `PrivaTools`. Description: `free, open-source, privacy-first online file-tools suite`.
3. Statements: `instance of (P31)` → *web service* + *free software*; `official website (P856)` → `https://privatools.me`; `source code repository (P1324)` → the GitHub URL; `license (P275)` → *MIT License*; `programmed in (P277)` → *Python*, *TypeScript*.
4. Copy the resulting `Q…` id.
5. In `backend/app/seo_meta.py`, add `"https://www.wikidata.org/wiki/Q…"` to the Organization `sameAs` array (the comment there marks the spot).

## 3. OpenSSF Best Practices badge — trust/authority signal

PrivaTools now **meets** most passing criteria, so submission is mostly a form:
automated test suite in CI (`.github/workflows/test.yml`), public VCS, `LICENSE`
(MIT), `CONTRIBUTING.md`, `SECURITY.md` + `/.well-known/security.txt`, signed
releases (cosign in `release.yml`), SBOM + dependency scanning (`security.yml`).

1. Sign in at <https://www.bestpractices.dev> with GitHub.
2. Add the project (the GitHub repo URL); answer the criteria — most map directly to the files above.
3. Add the earned badge markdown to `README.md` (next to the existing Scorecard/SBOM badges).

## Do NOT add fake `aggregateRating`

Tempting for stars in search, but `aggregateRating` without a **real, verifiable
review corpus** violates Google's structured-data guidelines and risks a manual
action. Only add it once there's a genuine review source (e.g. a real ratings
widget or an external review aggregator) to back it.

## Quick wins already shipped (for reference)

- The homepage's server-rendered body says where files are processed (browser, temporary server processing, optional AI providers) and carries a visible FAQ that matches its FAQPage JSON-LD. (The earlier "PrivaTools at a glance" facts block was removed in v2.2.0.)
- `knowsAbout` topics upgraded to knowledge-graph `Thing` entities with Wikipedia `sameAs`.
- Server-rendered tool pages carry exactly what visitors see: summary, intro, "How to use" steps, the full FAQ, "Mentioned in our guides" links, related tools and the "Last reviewed" line, with HowTo and FAQPage JSON-LD. `backend/tests/test_top50_seo.py` holds the 50 most popular tools to at least 150 words and those blocks.
- Each tool has a hand-written search title and meta description, and its `lastReviewed` date drives the sitemap `lastmod`, the visible review line and JSON-LD `dateModified`.
- `llms.txt` + `llms-full.txt` regenerated from the registry on every build.
