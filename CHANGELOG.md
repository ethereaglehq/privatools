# Changelog

All notable changes to PrivaTools are documented in this file, newest first.
Dates are the tag dates. Release notes for recent tags are also on the
[GitHub Releases](https://github.com/ethereaglehq/privatools/releases) page.
Tool totals in older entries describe that release; the live catalogue is at
[privatools.me/tools](https://privatools.me/tools).

## [Unreleased]

## [2.6.1] — 2026-09-18 — Accurate tool copy, lighter pages, stricter CI

### Content

- Tool guides for 92 tools stop claiming more than the product does: storage wording matches the privacy policy (temporary per-request storage, response cleanup plus a background sweep), and unverifiable competitor pricing, invented timings and roadmap promises are removed. (#176)
- The guides of the 50 most popular tools (by registry `popularity` rank) are rewritten from their real UI and backend routes. (#176)
- False fragments in registry descriptions, search titles and meta descriptions are corrected on 21 tools: for example, Sign PDF places an image rather than a certificate signature, Video to GIF has no clip-range control, and PNG to JPG usually turns transparent areas black, not white. Two backend tests guard against retention and browser-only overclaims. (#176)

### Performance

- Blog data loads only on blog routes, about 41 KB gzip less on every other page. Tool pages read their guide links from the generated `frontend/src/data/tool-blog-links.json`, and the bundle check fails if blog data reaches the entry chunk, a preloaded chunk or anything they import statically. (#173)

### Backend

- The server-rendered homepage and `/tools` lists follow the registry's popularity order, as the client does, and JSON-LD subcategories come from each tool's registry category. (#174)
- The fallback tool names and descriptions come from the generated tool manifest (the committed `frontend/public/tool-content.json`, or the build's copy in the image) instead of a hand-kept copy that had drifted on most tools. A checkout without a build reads the committed manifest, and the app refuses to start when no manifest is readable. (#179, #181)
- The HEIF opener is registered once at startup. Hardening only: HEIC decoding was not broken in production. (#177)

### CI

- A pull request fails when a tool's copy changes without moving its `lastReviewed`, or when more than 25 dates move without `[bulk-review]`. (#175)
- The frontend job fails when committed `npm run gen:llms` output is stale. (#178)
- The image job boots the built image through `docker-compose.yml` and checks `/readyz` (including the build SHA), a 404 for an unknown tool, that the app user can read the tool manifest, the homepage tool count, two tool pages and the sitemap. Releases gate on it. (#180)

## [2.6.0] — 2026-09-18 — Visible tool guides, search titles, sitemap signals

### SEO and content

- Every tool page shows a guide under the tool: "How to use" steps, every FAQ answer written out, and "Mentioned in our guides" links when a guide mentions the tool. Steps and FAQ stay authored in `backend/app/tool_content.py` and export to `frontend/src/data/tool-guide/<slug>.json` through `scripts/seo/export-tool-guides.py`, replacing `tool-faq.json`. (#170)
- The server-rendered tool body carries only what visitors see (summary, intro, steps, full FAQ, guide links, three related tools, last-reviewed line), chosen as the client chooses them; the TL;DR, trust paragraph, templated depth sections, eight-item related list and CTA copy are removed, and guide text is HTML-escaped. (#170)
- Every tool has a hand-written `seoTitle` (40–60 characters, no brand suffix) and `metaDescription` (120–160 characters). Server and client take the tab title, H1, social titles and description from them; `tool-registry.test.ts` enforces the rules. (#171)
- Every sitemap URL has a `<priority>`: home 1.0, `/tools` 0.9, tools listed in `sitemap-priority.json` 0.8, other tools 0.6, blog and compare 0.5, other pages 0.4. (#172)
- Each tool's `lastReviewed` date drives its sitemap `lastmod`, the visible "Last reviewed" line and JSON-LD `dateModified`; unused constants are removed from `routes/sitemap.py`. (#172)

### Frontend

- Long tool headings fit on phones. (#171)

## [2.5.0] — 2026-09-17 — Default-on analytics and tool usage events; docs and scripts reorganized

### Analytics

- Google Analytics collects for every visitor by default; the switch on the Privacy page is the only opt-out. The consent record, regional policy and Do Not Track / Global Privacy Control checks are removed. `GET /api/analytics/policy` answers `default_on` whenever `GA_BROWSER_TAG_ENABLED=true`, so browsers holding the earlier opt-in bundle switch on; `GA_TRUSTED_COUNTRY_HEADER` and `GA_DEFAULT_ON_COUNTRIES` are removed. (#169)
- Every React Router navigation sends a page view. (#169)
- A new `tool_run` event per tool use carries `tool_slug`, `tool_category`, `run_mode`, `outcome` and `file_count`, never file names, sizes or contents. A test fails when a tool UI calls the backend without reporting. (#169)

### Docs

- Documentation and scripts moved into topic folders with `docs/README.md` and `scripts/README.md` indexes (for example, `scripts/local-backend.py` is now `scripts/dev/local-backend.py`); README, CLAUDE.md, PRODUCT.md and the frontend README describe Air and Play. (#167)

## [2.4.1] — 2026-09-14 — Account settings and security controls

- Account settings open from the header and footer, with persistent navigation between Settings & security and API keys & usage, and improved layouts across Air/Play, light/dark and mobile. (release, #166)
- Passwordless accounts can set a password inline; password, username and passkey changes go through Clerk's identity re-verification when Clerk requires it. (release, #166)
- Clearer active and revoked API key states; request activity sits above starter tips on mobile. (release)
- Account deletion verifies the identity before backend cleanup and warns when cleanup cannot be confirmed. (release, #166)

## [2.4.0] — 2026-09-14 — API playground, integration starters and account activity

- Run a sample PDF merge, compression or text extraction from the API page and inspect the status, request ID, result and allowance change. (release, #165)
- Downloadable Python and JavaScript clients, n8n workflows and a Postman collection. Clients support background jobs, bounded retries, recovery after connection loss and deletion after a successful local save. (release, #165)
- API key settings show the current allowance, seven days of request totals and recent request metadata, excluding document contents, filenames, credentials and query strings. (release, #165)
- Processing limits and one-hour result retention are unchanged. (release)

## [2.3.1] — 2026-09-14 — Debian OS advisories patched; image scan enforced

- Debian runtime packages are upgraded to clear nine high-severity advisories; the Docker build fails below the reviewed security floor. (#164)
- A release is signed and published only after a clean ARM64 image scan with no fixable HIGH/CRITICAL findings. (#164)
- The image scan targets the published ARM64 image. (#163)

## [2.3.0] — 2026-09-14 — Free API discovery, shared limits and durable PDF jobs

- A searchable reference for 147 API operations, a v1-only OpenAPI schema, current costs and limits, and request templates. (#162)
- Request admission and quota reservations are shared across web workers in SQLite, quotas count actual request-body bytes, validation refunds still apply, and retry and error information is consistent. (#162)
- Optional key-scoped background jobs for merge, compress, grayscale and PDF text extraction: idempotent retries share one charge, results can be downloaded repeatedly for one hour or deleted, and one job supervisor runs beside the two web workers within the existing 4 GB / 1.8 CPU limits. Jobs are disabled by default. (#162)

## [2.2.1] — 2026-09-14 — Clean URL navigation

- App navigation uses clean paths; legacy `#/…` bookmarks convert in place without extra history entries. (#161)
- Opening the Dev API page directly at `/api` works (nginx configuration). (#160)

## [2.2.0] — 2026-09-14 — Air and Play, Clerk, browser AI and analytics

### Product

- The Air and Play experiences cover the tool workspace, account pages, guides and comparisons, with persistent light/dark controls and improved mobile navigation. (#159)
- Clerk accounts with username, passkey and Google sign-in; file tools stay available to guests. (#159)
- Verified browser background removal and offline assets, specialist tool interfaces, explicit model progress, PWA improvements, updated branding and crawlable content manifests. (#159)
- Consent-aware Google browser analytics, opt-in by default; a deployment could enable default-on for a reviewed list of countries. Default-on for everyone from 2.5.0. (#159)
- The release pipeline verifies signed immutable images and keeps a rollback path. (#159)

### Security

- WeasyPrint 69.0 → 70.0 (a security release); HTML and URL rendering keep SSRF validation through a fetcher that never hands HTTP, redirect or file URLs to WeasyPrint's default. (027e92b)
- Vulnerable frontend build and test dependencies updated (vitest 4, sharp 0.35.4). (a48a453)
- Static files are served only from an inventory of files found in the build, so a request path never becomes a filesystem path; clean installs are reproducible. (c7f4997)
- Blog articles render through React from an allowlist of tags instead of raw HTML, and file previews accept only same-origin `blob:` URLs. (cdbe060)

## [2.1.8] — 2026-09-06 — Bounce rate measures sessions

- The beacon sends GA4's `session_engaged` flag (after ten seconds or a second page view), so bounce rate is no longer pinned at 100%. (#158)

## [2.1.7] — 2026-09-06 — First release under ethereaglehq

- The account rename is followed through 83 references in 26 files; this is the first release built, signed and deployed under the new GHCR namespace and cosign identity. (tag, #157)

## [2.1.6] — 2026-09-06 — Rename-safe deploy, correct X handle, automatic releases

- Deploy accepts the old and new GitHub owner for the image namespace and the cosign identity; verification stays fail-closed. (#156)
- Organization structured data and `rel=me` links point at the live X handle. (#155)
- Every tag publishes a GitHub Release once its image is built, scanned and signed. (#154)

## [2.1.5] — 2026-09-06 — Analytics measures real time on page

- Foreground time is accumulated and sent as GA4 `user_engagement` on `visibilitychange`/`pagehide`; the server's engagement floor drops from 100 ms to 1 ms; event names are an allowlist; navigation page views no longer carry the previous page's title. (#153, release)
- A synthetic production probe runs every 30 minutes (homepage, `/readyz` dependencies, a real merge round trip, per-path CSP) and opens or comments on one tracking issue on failure. (release, 2463788, 484b8dd)

## [2.1.4] — 2026-09-02 — GA4 events carry a session

- Beacon events carry a GA4 session id and real time-on-view; the backend replaces an invalid id with a fresh one instead of dropping the event. (001e8ba)

## [2.1.3] — 2026-09-02 — X profile linked

- The X account is linked from the footer, About and Organization `sameAs`; the footer gains a Source link. (a385d72)
- Dependabot alerts cleared: browserslist 4.28.8 and postcss-selector-parser 6.1.4, both build-time only. Unused shell components removed. (3442d8a, 61e7d10)

## [2.1.2] — 2026-09-02 — Releases gated on tests

- `release.yml` calls `test.yml`: no green suite, no image. (73fa653)
- Social sign-in stays GitHub only; Google and Apple are also disabled in the Clerk dashboard. (tag, 73fa653)

## [2.1.1] — 2026-09-02 — Conversion How-Tos meet the three-step guard

- The 26 conversion How-Tos added in 2.1.0 get the third step the catalog test requires. (ef09c08)

## [2.1.0] — 2026-09-02 — How-To and FAQ for every tool

- Tools that had no How-To steps (32) or no FAQ (6) get hand-written copy; the FAQ export is regenerated from Python. (47aab55)

## [2.0.14] — 2026-09-02 — Legacy 404 URLs redirect

- Six URLs Google still held as 404s now return 301: four `/tool/` vs `/tools/` mix-ups, `/tool/e-sign-pdf` → `/tool/esign-pdf` and `/batchprocess` → `/batch`. (27300e8)

## [2.0.13] — 2026-09-02 — OG cards noindexed; page views sent

- `/api/og-image` responses carry `X-Robots-Tag: noindex`. (e1e6af1)
- The browser sends one page view per view (none were sent before), honouring Do Not Track, GPC and the local opt-out; compose passes `GA4_MEASUREMENT_ID` and `GA4_API_SECRET` to the container. (e1e6af1)

## [2.0.12] — 2026-09-01 — Spent OAuth verification fix

- A spent OAuth verification, such as one left in a bookmarked return URL, no longer sends the visitor to Clerk's hosted Account Portal. (bd90586)

## [2.0.11] — 2026-09-01 — Finished OAuth stays on site

- A completed GitHub sign-up no longer bounces to Clerk's hosted portal: the callback runs only while the flow is unfinished, and an "already signed in" reply is ignored. (3f269cc)

## [2.0.10] — 2026-09-01 — Exact OAuth return detection

- The OAuth return is recognised by a marker the sign-in adds rather than inferred from Clerk's state, and the callback waits until Clerk has fully loaded. (c314368)

## [2.0.9] — 2026-09-01 — OAuth sign-in completes

- Returning from GitHub completes sign-in, and a signed-in visitor is no longer shown the login form when account state was read before Clerk was ready. (1735d9b)

## [2.0.8] — 2026-09-01 — Sign-in from every page; arm64-only release images

- Account links go to the `/account` path, whose CSP allows Clerk, so sign-in works from every page; stale `#/account` links are rewritten. (47482da)
- Release images build natively on arm64 with a layer cache; the amd64 image is no longer published. (1a4a650)

## [2.0.7] — 2026-09-01 — Blocked clerk-js explained

- When a browser extension blocks clerk-js, the account page says so, disables the sign-in controls and notes that every tool works without an account. (4af1b6a)

## [2.0.6] — 2026-09-01 — New logo; models fetched on arrival

- New logo mark and icons, including a real maskable icon; a tool that needs an on-device model fetches it on arrival unless the browser asks to save data; a global button reset no longer strips styled controls. (4d0ca21)

## [2.0.5] — 2026-09-01 — GitHub button, guarded Clerk calls, AI hub on phones

- GitHub brand button; account actions taken before Clerk loads fail with a clear message; the AI hub fits phones; model download progress no longer shows 99% before the weights start. (df0499f)

## [2.0.4] — 2026-09-01 — Account page is just the sign-in card

- `/account` shows only the sign-in card; social buttons appear only for providers configured in Clerk (GitHub); model download progress no longer runs backwards. (d680d5f)

## [2.0.3] — 2026-09-01 — Light by default; Clerk password recovery

- Light is the default theme for first-time visitors; password recovery under Clerk works through a two-step email code instead of throwing; OTP code inputs; restyled home and auth card. (8168cd5)

## [2.0.2] — 2026-09-01 — On-device models unblocked

- On-device model weights load in production (`connect-src` now names the Hugging Face CDN the weights redirect to); the auth card gains social sign-in buttons and a password strength meter. (f189b15)

## [2.0.1] — 2026-09-01 — Clerk live

- Clerk accounts go live; the sign-in page shows the free-tier limits, a copyable curl example and links to the API reference, security page and catalogue. (tag, f02fa3e)

## [2.0.0] — 2026-09-01 — Daylight is the product

### Breaking

- Daylight replaces the UI. The Signature, Aurora, Carbon and Structured skins, the design-import toolchain and the skin dock are removed. (#150)

### Added

- Chat with PDF: the PDF's text is extracted in the browser and questions go to the visitor's own AI provider. (#150)
- Transcribe Audio: Whisper runs in the browser, or the visitor's own OpenAI, Groq or self-hosted key is used; transcripts download as text or SRT. (#150)
- Remove Background gains an on-device engine (BRIA RMBG-1.4). OCR PDF and Image OCR gain an in-browser Tesseract engine and a bring-your-own-key vision engine, and Translate PDF gains a bring-your-own-key engine. (#150)
- An AI hub in the top bar manages bring-your-own-key settings and on-device models. (#150)
- Multi-file queues: tools on the shared runners take up to 25 files, and 36 more tools process several files at once, with per-file status, retry and a ZIP download. (#150)
- The PDF editor gains pen and arrow tools and an edits panel. (#150)
- A true-black midnight theme, vault import with sample entries, a PWA install prompt, and a blog grown to 31 posts. (#150)

### Changed

- Daylight renders the real tool components, accounts, vault and path routing; counts come from the registry. (#150)

### Fixed

- Multi-file runs through `useMultiFileProcessor` processed zero files. (#150)
- PDFs with up to 1024 bytes before the `%PDF-` header, which ISO 32000 allows, are no longer rejected as invalid. (#150)

## [1.11.1] — 2026-08-27 — Tool URLs in Aurora and Carbon

- Fixed: every tool URL rendered the homepage in Aurora and Carbon. (#149)
- Clerk production configuration is plumbed through the build and compose, so activation needs only keys; see `deploy/clerk-production.md`. (#133)

## [1.11.0] — 2026-08-23 — Sign in with Google, GitHub or Apple

- OAuth sign-in through Clerk, shown only where Clerk is configured; the sign-in page is rebuilt as one centred column. (#132)
- The count guard matches the shape of a count rather than one phrasing. (#132)
- In Carbon and Structured, the theme control repaints immediately instead of after a reload. (#131)
- Production still ran with Clerk unconfigured. (tag)

## [1.10.0] — 2026-08-23 — Clerk (opt-in), UI corrections, BYOK in Smart Redact

- Accounts can use Clerk behind a key check: without a publishable key nothing changes and the SDK is not downloaded. Sessions are verified with JWKS, and a signed `user.deleted` webhook removes API keys. (#126, #130)
- Smart Redact supports bring-your-own-key, with the document fenced and provider egress allowed on that page. (#129)
- In the ported designs: a reachable light/dark control on mobile, counts from the registry, the wrong `privatools.io` domain fixed in twelve places, and demo toggles and design-review routes removed. (#127)
- Fixed: `/account`, `/account/keys`, `/my-stuff/vault`, `/status` and `/support` returned HTTP 404. (#125)
- Dependencies: setup-qemu-action v4.2.0 and @radix-ui/react-slot 1.3.3; Clerk session verification adds pyjwt 2.13.0 and cryptography 50.0.0. (#124, #128, #126)

## [1.9.0] — 2026-08-23 — Frontend revamp, accounts, read-only container

- The default Signature design is rebuilt: new typefaces and palette, a two-tier header in place of the tool-tree sidebar, a footer tool index, and tool FAQs visible on tool pages. (#122)
- Three ported skins (Aurora, Carbon, Structured); Signature stays the default. (#122)
- Accounts with scrypt hashing on a thread pool, per-account lockout and recovery codes as the only way back in. (#122)
- Versioned `/api/v1` behind user-issued keys with a daily free quota; Bearer tokens accepted; requests rejected in validation are refunded. (#122)
- Bring-your-own-key AI foundation, used by Summarize PDF; the CSP allows provider egress on that page only, and document text is fenced with a random per-call id. (#117, #118, #122)
- New: PDF accessibility checker (PDF/UA and WCAG 2.2), on-device Translate PDF, continuous multi-file Bates numbering and Bates removal, redaction exemption codes with a withholding log, compression profiles and target size. (#120)
- Fixed: grayscale rasterised every PDF; merge and extract-pages destroyed accessibility structure; Flate images never compressed. (#120)
- The container runs on a read-only root filesystem; `/app/data` is created in the image so the first signup works; accounts backup added. (#122, #123)
- The installed deploy unit no longer overrides the deploy gate and rollback check with `/api/health`, so both use `/readyz`. (#122)
- react-router 6 → 7 and esbuild ≥ 0.28.1, clearing all Dependabot alerts. (#121)

## [1.8.1] — 2026-08-21 — Two tool pages returned 404

- `/tool/remove-watermark` and `/tools/remove-image-watermark` were missing from the backend tool tables and returned 404; a parity test now holds the registries together. (9df4033)

## [1.8.0] — 2026-08-21 — Untrusted-input parsers, Python 3.12

- Security: Pillow 12.3.0 (15 advisories), pypdf 6.16.1 (2), rembg 2.0.81 (2); pip-audit runs without ignore flags. (d234336, bf62928)
- Python 3.10 → 3.12; fastapi 0.141.1, uvicorn 0.52.3, pymupdf 1.28.2, mistune 3.3.4; high and critical npm advisories cleared; CodeQL at zero; the password generator's RNG no longer has modulo bias. (bf62928, 9918f4d, decfa00, 623a381)
- opencv-python-headless and numpy are declared directly, with a contract test for directly imported modules. (bf62928)
- PR CI builds the image; base images are pinned by digest and tracked by Dependabot; release write permissions are scoped to the job. (#116, 438fc39, 4acc082)
- Frontend build base node 26-slim; Dependabot bumps of CI actions and Radix packages. (#100, #102, #107, #109, #110, #113–#115)

## [1.7.0] — 2026-08-21 — Local-first personalization, watermark removal, pipeline round-trip

- Device-local encrypted password vault, named Bates counters, an asset library, remembered settings on 57 tools and `/my-stuff` to see and erase it all; no accounts. (6163307)
- Visible watermark removal for PDFs and images. (6163307)
- The pipeline runs the whole chain in one request, with 17 chainable steps instead of 2. (6163307)
- Fixed: search-engine verification files were corrupted by the runtime config injector, which broke Google Search Console verification. (3cf12e4)
- Dependabot bumps of CI actions (first release on docker/build-push-action v7 and setup-buildx-action v4) and Radix packages. (#16, #19, #55–#61)

## [1.6.13] — 2026-08-21 — Compress PDF and Bates Numbering no longer crash on upload

- A missing TooltipProvider crashed both tools as soon as a file was queued; broken since 1.6.0, which removed the root provider to trim the first-paint path. (1d14cb0)

## [1.6.12] — 2026-06-29 — Deploy rollback and request-timeout leaks

- Auto-deploy restores the previous image when the health gate fails and records the failed target. (#96)
- `run_bounded` gets its own bounded thread pool, and LibreOffice/qpdf subprocesses are killed on cancellation. (#98)
- A `process_pdf_upload` lifecycle helper, first used by grayscale. (#97)

## [1.6.11] — 2026-06-29 — Hashed lockfiles and deploy reliability

- Runtime dependencies install from fully hashed lockfiles with `--require-hashes` in the image and CI. (#94)
- The Docker healthcheck and the deploy script's default gate use `/readyz`; the recurring stuck image pull is fixed. (#95)
- Remaining PDF routes in `new_tools` stream uploads to disk. (#93)

## [1.6.10] — 2026-06-29 — Streaming uploads, readiness and observability

- Uploads stream to disk with first-chunk validation (office-to-pdf, video/audio/subtitle routes). (#88–#90)
- `/readyz` checks free disk and returns `build_sha`. (#87)
- Uvicorn logs join the JSON stream; in-flight gauge; janitor RSS heartbeat. (#86)
- The 14 floating native parsers are pinned to exact versions. (#91)
- nginx: per-IP connection limit on `/api/`, and a documented Cloudflare real-IP block. (#92)

## [1.6.9] — 2026-06-29 — Security response surface

- Production disables `/api-docs` and `/openapi.json`; 5xx `HTTPException` details are replaced with a generic message; CSV injection guard in table extraction. (#82)
- Native thread pools pinned to one thread; the URL-fetch connection cache is thread-local. (#83)
- office-to-pdf removes its intermediate copy on every path. (#84)
- Releases scan the built image before signing (report-only at this point). (#85)

## [1.6.8] — 2026-06-29 — Bounded heavy work

- `run_bounded` caps concurrent heavy work with one process-wide semaphore (`MAX_CONCURRENT_HEAVY`). (#81)
- Rate limits on the remaining media routes; batch compress off the event loop; a page cap on OCR. (#79)
- Auto-deploy verifies the cosign signature (fail-closed) and retries a failed pull. (#80)

## [1.6.7] — 2026-06-29 — Deep-research P0 fixes

- Fixed a cross-user leak: concurrent merges shared one output path. (#75)
- A crafted PDF can no longer exhaust memory through page rendering (about 100 MP cap on every render). (#77)
- Rate limits on the eight heaviest PDF and image routes. (#78)
- `TMPDIR=/app/temp` and Docker log rotation. (#76)
- Tests for API-key auth, error-status mapping and the SSRF DNS branch. (#74)

## [1.6.6] — 2026-06-29 — Security-property tests

- Tests prove redaction removes text, protect encrypts, unlock decrypts, metadata stripping clears fields and archive extraction rejects zip-slip. (#72)
- office-to-pdf file copies run off the event loop. (#73)

## [1.6.5] — 2026-06-29 — Backend correctness and SSRF hardening

- URL fetches with no Content-Type no longer bypass the allowlist. (#71)
- Correct media types for video and audio outputs; audio-trim rejects start ≥ end; embed-qr-in-pdf validates the page. (#71)

## [1.6.4] — 2026-06-29 — Backend audit fixes

- Fixed: split-by-size silently dropped pages; SVG conversions could read local files or internal URLs; image OCR had no timeout; video-merge turned 400/413 into 500; a compare leak. (#69)
- More CPU-bound handlers run off the event loop. (#70)

## [1.6.3] — 2026-06-29 — Flag-gated api.privatools.me split

- `PUBLIC_API_BASE_URL` moves the SPA's API traffic to a DNS-only host so the apex can sit behind Cloudflare without capping 500 MB uploads; off by default. (#68)

## [1.6.2] — 2026-06-29 — GEO citability; release deploys wait for the signed image

- Knowledge-graph topics and a citable homepage facts block; a GEO runbook for the account-gated steps. (#66)
- A release deploy waits for the signed image instead of racing a local build. (#67)

## [1.6.1] — 2026-06-29 — Deploy the signed image

- Auto-deploy pulls the signed GHCR image built per tag instead of rebuilding on the VM, with deploy-failure alerting. (#65)

## [1.6.0] — 2026-06-29 — Security and reliability hardening, CI test gate, deploy gate, PDF to Long Image

### Security

- url-to-pdf and html-to-pdf validate every WeasyPrint sub-resource and re-validate redirects. (#46)
- Rate limiting keys on the rightmost `X-Forwarded-For` entry (the one nginx appends) and covers the expensive routes that had no limit; archive extraction is capped by the real decompressed size; image, media and archive uploads are size-checked while being read. (#46)
- Nonce-based `script-src` CSP, build-time SRI, HSTS/COOP/COEP/CORP headers, `security.txt`, `SECURITY.md` and a `/security` page; self-hosted fonts; analytics through a first-party proxy with Do Not Track, GPC and local opt-out. (#1, #30)

### Reliability

- 96 route-to-service calls moved off the event loop into the thread pool; pikepdf/Pillow leaks closed; an empty-PDF booklet returns 400. (#46)
- Fixed: right after 1.5.2 deployed, `TrustedHostMiddleware` rejected every request; allowed hosts now fall back to the hostnames in `ALLOWED_ORIGINS`, and `/readyz` no longer fails when Ghostscript is absent. (512b336)

### New

- PDF to Long Image. (#52)
- Edit PDF rebuilt: select, move and resize edits, undo/redo, line, circle and image tools, keyboard shortcuts and page thumbnails. (dccc92e)
- Eight browser-only developer tools and 26 conversion alias pages. (#1)
- Developer pipeline API (templates, validation, a `compress-pdf → strip-metadata` runner), shareable `/pipeline?p=` recipes, optional `X-API-Key` gating, a local `privatools` CLI and a Manifest V3 extension skeleton. (#1)

### Performance and SEO

- Brotli for HTML and assets, fewer preloads, a prehydration brand shell and a faster mobile first paint. (#22–#28)
- Server-rendered content restored (routes had served an empty shell since 18 June); no self-canonical on 404s; a `/tools` hub; per-tool sitemap dates; MIT `LICENSE` file added. (#45, #50, #51)
- Top-50 tool pages carry at least 800 words of server-rendered content, enforced by a test; "Last reviewed" badges; tool-count claims aligned. (#1, #53, #29)

### CI and deploy

- Backend and frontend tests run on every pull request. (#48)
- A security workflow (npm and pip audits, CodeQL, OpenSSF Scorecard, Trivy), a tag-triggered release workflow that pushes cosign-signed images to GHCR, and Dependabot. (#1)
- GitHub Actions pinned to commit SHAs; the security workflow repaired and its write scopes narrowed. (#46, #31, #32)
- A systemd timer on the Oracle VM checks for a new deploy target every minute, rebuilds, and waits for `/api/health` to report the new build SHA; the nginx config redirects `www` to the apex. (505d473, 83c092a, 5ef8779, 19aa2ec)
- Auto-deploy gains a release-tag gate. (#47)
- Container: loopback-only bind, `cap_drop: ALL`, `no-new-privileges`, 4 GB memory, 1.8 CPUs, 512 PIDs. (#46, #63, #64)
- The `backend/requirements.txt` mirror is removed; `.env.example` domains and upload limit are aligned. (#46, #47)

### UI

- Persistent mobile bottom navigation and 44 px touch targets. (#1)
- Privacy copy corrected: server tools use isolated temporary per-request storage rather than memory only, and the Smart Redact and Summarize PDF banners no longer overstate what stays local. (70e0821, 3965d6b, #46)

## [1.5.2] — 2026-05-20 — Workshop UI overhaul + production hardening

### Frontend

- Workshop UI overhaul completed: ~180 files now use signal-green § / Fraunces / corner-marks aesthetic
- `friendlyError` + Cmd+Enter + `<kbd>⌘↵</kbd>` hint backfilled across all 68 stateful tool-UIs (was 39)
- Sticky reading-progress + TOC on blog/legal pages with hand-rolled rAF smooth-scroll
- Inline synonyms on all 179 tools (powers Cmd+K fuzzy search)
- PDF.js + Hugging Face Transformers now truly lazy-loaded
- Removed dead `@tanstack/react-query` and `EditorialMasthead`/`EditorialFooter` imports
- Multi-file support on 12 tools via shared `useMultiFileProcessor` + queue + pure-JS STORE-mode zip writer (`lib/zip.ts`)
- **ErrorBoundary** (class component, 208 LOC) wrapping app root AND each tool — one tool's render crash no longer white-screens the shell. Workshop-styled fallback + Reload/Go-home buttons + dev-only stack trace.
- **ToolSkeleton** suspense fallback replaces the blank-screen lazy-chunk load
- **useFocusTrap** hook + applied to NameDialog (PipelinePage); ShortcutsHelp/OnboardingTour/CommandPalette already had complete focus traps from earlier rounds
- Memory-leak audit: 6 fixes (object-URL revokes via `downloadBlob` helper in MarkdownHtmlUI + CsvJsonUI; stale-closure unmount cleanup in MergeImagesUI + ImageCompressorUI; AbortController unmount aborts on PipelinePage + BatchPage). Full inventory: 100 `addEventListener`, 8 rAF, 25 setTimeout, 22 object URLs — all paired with cleanup.
- Persistence: useFormPersist (400ms debounced localStorage envelope), useOnline, useGlobalErrorHandler, BatchResumeBanner for crash recovery
- Service worker: SWR app shell + last-10-tool-routes cache + `/api/*` bypass; CACHE_VERSION = "v1.5.0"
- First-run welcome card + sample files (`public/samples/`) + first-success toast
- 12 new keyframe animations (copy-flash, dragging, queue-row-enter, processing-pulse, dropzone-landed, button-press-ring, underline-reveal, toc-rail-marker) — all respect `prefers-reduced-motion`

### Backend

- 12 typed exceptions matching frontend `friendlyError` patterns (PdfEncryptedError, PageRangeError, FileTooLargeError, ToolTimeoutError, ExternalToolError, …)
- N-up orientation parameter (side / stack)
- QR code FG/BG colors + logo embed
- Create-ZIP compression level (0–9)
- Round 1 security: XXE (defusedxml), zip-slip, SSRF, command-injection, path-traversal
- **Round 2 security**: CRLF/header injection in 21 routes via centralized `safe_stem`/`safe_header_filename` helpers; MIME magic-byte validation (PNG/JPEG/GIF/BMP/TIFF/WEBP/HEIC + ZIP); tempfile race fixed (atomic `mkstemp` w/ 0600 perms); SSRF expanded to CGNAT, TEST-NET, IPv6 link-local, IPv4-mapped, IPv6-translation ranges; cache-control `no-store` on every `/api/*` dynamic output; ReDoS fix in phase7 timestamp regex; `TrustedHostMiddleware` with env-driven allowlist
- **Resource caps**: `Image.MAX_IMAGE_PIXELS = 150M` (decompression-bomb guard) + `DecompressionBombError` → 413 handler; tesseract timeout 90s; ffmpeg/LibreOffice/Ghostscript subprocess timeouts verified; per-IP rate limiting via slowapi (`@limiter.limit("5/minute")`) on `/api/ocr`, `/api/smart-redact`, `/api/pdf-to-word`, `/api/pdf-to-excel`, `/api/url-to-pdf`, `/api/extract-audio`; `UploadSizeLimitMiddleware` enforces `MAX_UPLOAD_MB` (default 500 MB) both at Content-Length pre-check and during streaming
- **Observability**: JSON structured logger (`utils/logging.py`) + `contextvars` propagation so every log line auto-tags `request_id`; `AccessLogMiddleware` logs one INFO per request with `duration_ms`, WARNING for `>5s`; `RequestTimeoutMiddleware` returns 504 with friendly message after 120s; all `print()` removed from `app/`
- **Health endpoints**: `/healthz` (liveness, always 200) + `/readyz` (readiness — checks pikepdf/fitz/PIL importability + tessdata path + temp-dir writable)
- **`X-Request-ID`** on every response
- **Shared utils**: `route_helpers.py` (safe_stem, read_upload, unique_arcname), `cleanup.py` (temp-file cleanup, MIME validation, content sniffing), `health.py`, `logging.py`, `caching.py` (ETag/304/Vary + 7d cache on OG images + 1h on sitemap), `filenames.py` (`temp_output` consolidating 113 call sites), `images.py` (`open_image_safe` context manager), `page_range.py`, `colors.py`, `exceptions.py`
- `/api/<unknown>` returns JSON 404 (not SPA HTML shell)
- Test count: 197 passed, 40 skipped (integration-gated), 0 failed (was 118 at round-3 start; +79 in this release)

### SEO + meta

- Tool title length: 174 over-60 → 0; tool descriptions: 113 over-160 → 0
- Sitemap: 202 → 213 URLs (added 11 `/compare/<competitor>` pages, real blog `publishedAt` dates, per-tool priority bumping)
- Static `public/sitemap.xml` written at build time + matching backend `/sitemap.xml` route (parity verified)
- All 179 tool pages have `SoftwareApplication` JSON-LD with inline `creator`. `aggregateRating` deliberately omitted (would violate Google's structured-data guidelines without a real review corpus).
- Per-competitor `reviewRating` on `/compare/*` pages with `ratingExplanation`
- `TOOL_LAST_REVIEWED` per-tool dict (44 entries) drives sitemap lastmod
- NotFound page: `noindex,nofollow` via React `useNoIndexMeta()` hook AND backend SSR for unknown paths
- FAQ depth (6–8 Q&A) on top 20 tools
- llms-full.txt (66 KB) verbose per-tool reference

### Deploy

- `deploy/nginx.conf` — TLS 1.2/1.3, HSTS preload-ready (2yr), strict CSP, security headers, gzip + brotli (commented), `/assets` 1yr immutable, `/sw.js` no-store, API proxy with 120s timeouts and 110MB body limit
- `deploy/privatool-backend.service` — systemd unit with hardening (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `MemoryMax=4G`, `CPUQuota=300%`, `TimeoutStopSec=60` for graceful shutdown)
- `deploy/deploy.sh` — minimal-blast-radius: git fetch + reset + frontend build + systemd restart + nginx reload + `/healthz` smoke check
- `deploy/README.md` — one-time setup + day-2 ops + rollback + troubleshooting
- `.env.example` — every tunable (APP_VERSION, MAX_UPLOAD_BYTES, TESSDATA_PREFIX, TRUSTED_HOSTS, ALLOWED_ORIGINS, LOG_LEVEL, EXPENSIVE_RATE_LIMIT)

## [1.5.1] — 2026-05-16 — UX polish + a11y + AEO/GEO push

### 🆕 New tools (2) — total now 179

- **Rotate Image** (`/tools/rotate-image`) — 90 / 180 / 270 / arbitrary angle via Pillow `Transpose` + `rotate(expand=True)`. Canvas auto-expands so nothing is cropped at non-right angles. Transparency preserved for PNG and WEBP.
- **Flip Image** (`/tools/flip-image`) — horizontal or vertical mirror.

### 🔍 SEO / AEO / GEO

- **Blog index, About, Compare hub, Privacy, Terms, Pipeline, Batch** — 7 pages that had no JSON-LD now have proper schema (`Blog` + `BlogPosting` list, `AboutPage` + `FAQPage`, `CollectionPage` + `ItemList`, `WebPage`, `WebApplication`, `BreadcrumbList`).
- **Homepage `FAQPage`** added with 6 voice-friendly Q&As, matched by visible SSR `<h3>/<p>` so Google's FAQ rich-result rules hold.
- **Homepage SSR** now explicitly surfaces **Pipeline** and **Batch** as differentiators that no competitor offers free.
- **`llms-full.txt`** (66 KB) added alongside `/llms.txt`. Verbose per-tool reference, architecture explainer, and citation-ready statements for AI crawlers. `robots.txt` advertises both.
- Stale "152+ / 90+ / 105 / 141+" tool counts swept across `LandingPage`, `ComparePage`, `DynamicHead`, `opensearch.xml`, `manifest.json`, and the Foxit compare meta — all now use dynamic counts or the current canonical number.

### ♿ Accessibility

- **Real skip-link** in `EditorialMasthead` (`sr-only focus:not-sr-only`) jumping to `#main-content`. `id="main-content"` added to `<main>` across all 12 page components. Index.html SSR fallback skip-link harmonised to the same target.
- **`inputMode="numeric"`** added to all 48 `type="number"` inputs across 19 tool components → triggers numeric keypad on mobile.

### 🐛 Bugs

- **File inputs across 60+ components** now reset `e.target.value = ""` in `onChange`. Re-selecting the same file after clearing it (X button or post-process) used to silently no-op because the browser short-circuits `onChange` on identical values.
- **404 page rebuilt** with a fuzzy match over all 179 tools against the requested URL's last segment — surfaces a top-6 "Did you mean…" list and a Cmd-K trigger. Tool count is now dynamic.

### ⌨️ UX

- **Command Palette: category chips** (PDF / Image / Video-Audio / Dev / Docs / Archive) shown on the right of each result for disambiguation when two tools share a name. Hidden on mobile to keep rows uncluttered.
- **Cmd-K synonyms** added for `rotate-image` (turn / spin / tilt / sideways) and `flip-image` (mirror / unmirror / selfie / reflect).

## [1.5.0] — 2026-05-15 — Phase 7: competitor-gap tools

### 🆕 New tools (6) — total now 177

Six tools competitors offer that PrivaTools didn't:

- **Mute Video** — stream-copy strips the audio track (lossless, instant) — MP4 / MOV / WebM / MKV / AVI
- **Reverse Video** — plays backwards with audio reversed in sync, output H.264 + AAC
- **Video Speed Changer** — 0.25× (slow-mo) to 4× (hyperlapse), audio pitch-corrected via FFmpeg's `atempo` so it doesn't sound chipmunk-y
- **Audio Trimmer** — standalone audio cutter, lossless stream-copy on MP3 / WAV / AAC / FLAC / OGG / M4A
- **Image Color Palette** — extract dominant colours from any image with HEX codes, `rgb()` values, and coverage percentages (octree quantisation)
- **Pixelate / Blur Image** — mosaic pixelation or Gaussian blur with adjustable strength for privacy-safe sharing (block faces, license plates, addresses)

### ⌨️ Discoverability

- **Command Palette rewrite** — multi-token fuzzy scoring with 6-tier rank (exact name → prefix → slug-exact → contains → synonym phrase → multi-token AND) plus a popularity tie-breaker. `SYNONYMS` map tripled from 39 entries to 145+. Result cap 12 → 16. Verified 16/18 (89%) fuzzy match rate on test queries.

### 💬 UX

- **Human-readable HTTP errors** in `lib/api.ts` — `describeError()` maps 413 / 415 / 422 / 429 / 502 / 503 / 504 each to tailored user-facing copy instead of `Request failed (500)`. The error card got a "Try again" + "Copy error" affordance.
- **Filename preservation** across server-side tools — output filenames are derived from the source name + a suffix (`document.pdf` → `document_compressed.pdf`), not generic `output.pdf`.

### 🔍 SEO / AEO / GEO

- **Hand-written TL;DRs expanded from 30 to 141 tools** with voice-friendly, 1-2 sentence answers tagged `data-speakable`.
- **HowTo JSON-LD** added to every tool's `@graph` with 3 step entries each.
- **`dateModified` dynamic** — uses `date.today()` so all tool pages show today's date as last-reviewed.
- **sitemap `lastmod` = today** for all evergreen content (tool pages, blog index, compare, etc.) so search engines see fresh signals.

### ♿ Accessibility

- **Colour contrast** bumped to WCAG-AA across compare / blog / tool pages: `text-green-600` → `text-green-700 dark:text-green-400`, `text-red-500` → `text-red-700 dark:text-red-400`, accent badges from `bg-accent/15 text-accent` to `bg-accent/25 text-foreground border-accent/40`.
- **Sidebar headings** changed from `<h3>` to `<h2>` for correct heading order on tool pages.
- **Form labels** added with `htmlFor` / `id` pairs and `aria-label` on the YAML-to-JSON textarea and password-generator input.
- **Icon-only `<a>`** on the blog "next post" arrow gained `aria-label="Read {title}"`.

### 📱 Mobile

- **CategoryToolNav overflow** — changed from `min-w-0 max-w-full` (didn't clip on certain viewports) to `-mx-4 sm:mx-0 overflow-hidden` edge-to-edge scroll pattern.
- **Wide markdown tables** in blog posts get `display: block; overflow-x: auto` so they don't horizontal-scroll the whole page.

## [1.4.0] — 2026-05-12 — Converter aliases + browser-only utilities

### 🆕 New tools (20+)

**Image converter aliases** (each is its own SEO landing page hitting the unified `image-converter` backend):

JPG ↔ PNG · JPG → WebP · PNG → WebP · TIFF → JPG/PNG · BMP → JPG/PNG · GIF → JPG/PNG

**Audio / video converter aliases:**

M4A → MP3 · MP4 → MP3 · MOV → MP4 · AVI → MP4 · WebM → MP4 · MP4 → WebM

**Browser-only dev tools:**

YAML ↔ JSON · Case Converter (camelCase ↔ snake_case ↔ kebab-case ↔ PascalCase ↔ CONSTANT_CASE ↔ Title Case ↔ sentence case)

### 🔍 SEO

- Each alias gets a dedicated landing page with its own meta, TLDR, HowTo, and FAQ — surfaces in long-tail "convert X to Y" searches without duplicating backend code.

## [1.3.0] — 2026-05-15 — SEO / AEO / GEO sweep

### 🔍 SEO (technical)

- **robots.txt rewritten** with explicit allows for every major AI crawler: GPTBot, ChatGPT-User, OAI-SearchBot, Google-Extended, GoogleOther, PerplexityBot, Perplexity-User, ClaudeBot, anthropic-ai, Claude-Web, Claude-SearchBot, cohere-ai, Cohere-Web, CCBot, Applebot, Applebot-Extended, Meta-ExternalAgent/Fetcher, FacebookBot, Mistral-AI, YouBot, Diffbot, PetalBot. Yandex/Baidu/DDG explicitly allowed. Aggressive crawlers (Bytespider, AhrefsBot, SemrushBot, MJ12bot, DotBot) blocked.
- **Google Search Console verification fix**: SPA middleware was intercepting `/google*.html` paths and returning index.html shell instead of the 53-byte verification token. Now passes through (`/google`, `/BingSiteAuth`, `/yandex`, `/baidu_verify`).
- **Schema upgrades** (`seo_meta.py`):
  - Tool pages: `WebApplication` → `SoftwareApplication` with richer fields (`applicationSubCategory`, `browserRequirements`, `isAccessibleForFree`, `softwareVersion`, full `Offer` with `availability` + `category`)
  - Homepage: new `ItemList` schema enumerating 25 featured tools as `SoftwareApplication`s
  - Organization: enriched with `alternateName`, `foundingDate`, `license`, `description`, `ImageObject` logo, `ContactPoint`
  - Blog posts: author upgraded from `Organization` to `Person` with `sameAs` + `worksFor`; added `image`, `keywords`, `mainEntityOfPage`
  - Compare pages: `Article` → `["Article", "Review"]` with `mainEntityOfPage` + `author`

### 🎙️ AEO (Answer Engine Optimisation)

- **`speakable` JSON-LD** added to FAQ entries on tool pages, blog posts, and compare pages — gives voice assistants and featured-snippet pickers an explicit "read this aloud" target.
- **TL;DR / Key facts boxes** on every blog post (15/15). Short, snippet-optimised summary at the top of each article, with `.post-tldr` CSS class referenced by the `speakable` selector.
- **Visible author byline** with semantic `<time>` elements (E-E-A-T signal).

### 🤖 GEO (Generative Engine Optimisation)

- **`llms.txt` substantially enriched** (now ~30 KB):
  - Quick-answer comparison matrix (PrivaTools vs 7 competitors)
  - "What makes PrivaTools different (for AI citation)" section with three architectural commitments + auditable source paths
  - Auto-generated section with the 10 most-recent blog posts including their TL;DRs (parsed from `blog.ts`)
  - Inline FAQ section with 7 direct-answer Q&As
  - All competitor comparison links with one-liner verdicts

### 🔗 Internal linking

- **Auto-derived "Related articles" sidebar** on every tool page (PDF + non-PDF) from each post's `relatedTools` field — replaces a stale hand-maintained map.
- **"Tools mentioned in this article" panel** at the bottom of every blog post (15/15), with cards linking to the specific tools each post references.
- All 15 blog posts now have a `relatedTools` array — distributes link equity + gives AI engines a clean entity graph.

### 📊 By the numbers

- AI crawlers explicitly allowed: 21 (was 9)
- TL;DR boxes on blog posts: 15/15
- Blog post → tool internal links: 15 posts × avg 4 tools = ~60 new internal links
- JSON-LD types emitted: SoftwareApplication, BreadcrumbList, FAQPage, BlogPosting, Article+Review, Organization, WebSite, Person, ImageObject, ItemList, SpeakableSpecification, ContactPoint, Offer

## [1.2.1] — 2026-05-15 — SEO content push

### 📝 6 new long-form blog posts (~17,000 words of new content)

- **AI PDF Summarizer: How to Summarize Long PDFs in Your Browser (2026 Guide)** — explains browser-side distilbart, step-by-step walkthrough, what cloud summarizers do with your data
- **10 Best iLovePDF Alternatives in 2026 (Free, Private, Open-Source)** — full comparison matrix, ranked
- **How to Redact a PDF Properly (Don't Use Black Boxes)** — proper redaction technique, common pitfalls, verification steps
- **Why Most Online PDF Tools Are Tracking You (And What to Do About It)** — privacy-policy analysis, tracker breakdown, the open-source test
- **How to Convert HEIC to PDF, JPG, and PNG on Any Device (2026)** — online + Mac + Windows + CLI + iPhone settings
- **How to Decode a JWT Token Safely (and What Each Part Means)** — JWT structure, claims reference, why public decoders are unsafe

### 🔍 Rich-result schemas added

- **HowTo + FAQPage JSON-LD** for 18 additional tools: highlight-pdf, summarize-pdf, smart-redact, split-in-half, pdf-to-svg, pdf-to-html, pdf-to-rtf, web-optimize-pdf, split-by-text, view-exif, jwt-decoder, regex-tester, timestamp-converter, batch-compress-pdf, pdf-page-counter, webp-to-jpg, webp-to-png, heic-to-png — for richer Google SERPs.
- All 6 new blog posts wired into seo_meta `_BLOG_POSTS` for BlogPosting + Article JSON-LD.

### 📊 Numbers

- HowTo coverage: 42 → **60** tools (39% of 152 → 76% of high-traffic tools)
- FAQ coverage: 42 → **60** tools
- Blog posts: 9 → **15**
- Words of content on the site: roughly doubled

## [1.2.0] — 2026-05-15

### 🆕 New tools (11) — total now 152

**PDF**
- **Web Optimize PDF** — `qpdf --linearize` for fast byte-range / first-page-fast-render serving
- **Split by Text** — split a PDF at every page containing a search keyword (with case-sensitive toggle)
- **PDF to HTML** — full HTML export preserving fonts and positioning
- **PDF to RTF** — Rich Text Format extraction, opens in WordPad / Pages / Word / LibreOffice

**Image**
- **View EXIF Data** — counterpart to Remove EXIF; inspect GPS / camera / timestamps / IPTC / XMP metadata as JSON
- **WebP to JPG** — SEO landing page hitting the existing image-converter
- **WebP to PNG** — same, target PNG
- **HEIC to PNG** — same, HEIC input

**Browser-only dev utilities**
- **JWT Decoder** — paste a JWT, see header + payload + signature + expiry status (decoded entirely client-side)
- **Regex Tester** — live JavaScript RegExp tester with match highlighting and capture groups
- **Timestamp Converter** — Unix epoch ↔ ISO 8601 ↔ UTC ↔ local ↔ relative ("in 3 days")

### 🐛 Bug fixes

- **office-to-pdf no longer 500s.** The LibreOffice path was failing with "User installation could not be completed" because the container's appuser had no `$HOME`. Each call now gets its own per-conversion `-env:UserInstallation` profile dir under `/tmp`.

### 🛠️ Backend

- New router `v12_tools.py` with `/api/web-optimize`, `/api/split-by-text`, `/api/pdf-to-html`, `/api/pdf-to-rtf`, `/api/view-exif`
- `pdf-to-html` uses PyMuPDF's HTML exporter; `pdf-to-rtf` does its own minimal RTF generation with Unicode escapes; `view-exif` uses PIL's getexif + GPS sub-IFD

## [1.1.0] — 2026-05-04

### 🆕 New tools (33)

**PDF**
- Image-to-PDF variants: JPG, PNG, HEIC, WebP, TIFF, BMP, GIF, SVG, ODT
- PDF-to-image variants: JPG, PNG, TIFF, BMP, GIF, SVG
- Split in Half — split each page horizontally or vertically (for two-up scans)
- Highlight PDF — yellow-highlight every match of a phrase
- Summarize PDF (AI) — local distilbart, runs in your browser via WebAssembly
- Smart Redact (AI) — local BERT-NER auto-detects PII (names, emails, phones, SSNs)
- Batch Compress PDF — compress up to 50 PDFs in parallel
- PDF Page Counter — count pages across up to 100 PDFs at once

**Video & Audio**
- Video to PDF — extract frames as PDF pages
- Video Converter — MP4/WebM/MOV/AVI/MKV via FFmpeg
- Video Resizer — change resolution/aspect ratio
- Video Thumbnail — extract poster frames at any timestamp
- Video Merge — concatenate clips
- GIF to MP4 — animated GIF → smaller, smoother MP4
- Burn Subtitles — embed .srt or .vtt into MP4
- Audio Converter — MP3/WAV/OGG/FLAC/AAC with bitrate control
- Audio Merge — concatenate audio tracks
- Image Upscaler — 2x or 4x with Lanczos resampling

**Browser-only utilities**
- Subtitle Converter — SRT ↔ VTT ↔ ASS in browser
- Password Generator — cryptographically-secure with custom rules
- UUID Generator — bulk v4 UUIDs
- Lorem Ipsum — placeholder text by paragraph/sentence/word
- Word Counter — live word/character/sentence/reading-time
- Color Converter — HEX ↔ RGB ↔ HSL with picker
- URL & JWT Encoder — percent-encode + JWT decode

### 🎨 Redesign
- Linear/Vercel/Smallpdf-inspired complete UI overhaul (monochrome primary + amber accent)
- 21 custom per-tool SVG illustrations replacing generic icons (Merge, Compress, Rotate, Sign, Watermark, Convert, OCR, Highlight, Lock, Unlock, Summarize, ImageCompress, RemoveBg, VideoToGif, QrCode, Hash, Base64, PageCounter, MergeMedia, etc.)
- Animated SVG hero artwork with floating category chips orbiting a shield
- Animated Pipeline diagram (CSS-keyframed file particle drifting through stages)
- Asymmetric homepage hero, 88px H1, search-shaped CTA opening ⌘K
- Dropzone-style skeleton loaders

### ⌨️ UX
- ⌘K palette: synonym scoring (typing "join" finds Merge, "shrink" finds Compress, "md5" finds Hash, etc.)
- Onboarding tour for first-time visitors (5 cards — keyboard-dismissible)
- Reduced-motion compliance — global safety net disables decorative animations
- Light + dark themes both at zero accessibility violations (axe-core verified)

### ♿ Accessibility
- WCAG-AA color contrast across all routes in both themes
- Proper landmark structure: every page wrapped in `<main>` with aria-labelled `<section>` children
- ARIA dialog semantics on CommandPalette + OnboardingTour
- All sliders forward `aria-label` to the Radix thumb
- Focus rings via `:focus-visible`
- 0 serious + 0 moderate axe violations across 6 audited routes × 2 themes

### 🔍 SEO / AI Discoverability
- llms.txt auto-generated from data files at build time (always in sync, currently 141 tools)
- Per-tool SEO meta on all 141 tools (title + 140-160 char description)
- Dynamic OG images per route via `/api/og-image?p=<path>`
- robots.txt allows GPTBot/Claudebot/Perplexity, blocks aggressive crawlers
- JSON-LD: Organization, Person, BlogPosting, BreadcrumbList, ItemList

### 🛠️ Backend
- Mtime-keyed SEO HTML cache → frontend deploys no longer need a worker restart
- 17 Tesseract language packs baked into image
- rembg model pre-warmed at build time (`/tmp/u2net`, NUMBA_DISABLE_JIT)
- Memory-safety caps on collage, json-to-pdf, split-by-size, compare
- video-merge auto-detects audio tracks (anullsrc padding for silent inputs)
- 6 dedicated UIs replacing single-file GenericUI fallback for batch/multi-file tools
- 94/94 endpoints pass regression sweep

## [1.0.0] — 2026-03-05

### 🚀 Launch

**90+ privacy-first file tools** — all processing happens locally.

### PDF Tools (70+)
- Organize: Merge, Split, Split by Bookmarks, Split by Size, Organize Pages, Delete Pages, Extract Pages, Alternate Mix, Overlay, Repair
- Edit: Edit PDF, Sign, E-Sign, Watermark, Stamp, Header/Footer, Page Numbers, Bates Numbering, Fill Form, Bookmarks, Add Hyperlinks, White-Out, Annotate, Add Shapes, Add Attachment
- Optimize: Compress, Flatten, Grayscale, Deskew, Crop, Auto Crop, Resize, Remove Blank Pages, Invert Colors
- Security: Protect, Unlock, Redact, Strip Metadata, Delete Annotations, Sanitize, Permissions, Verify Signature
- Convert to PDF: Image, HTML, Word, Excel, PowerPoint, TXT, Markdown, CSV, EPUB, RTF, JSON, XML
- Convert from PDF: Image, Text, Word, Excel, PPTX, EPUB, Markdown, Extract Tables

### Non-PDF Tools (16)
- Image: Compressor, Converter, Remove EXIF, Resize & Crop
- Video/Audio: Video→GIF, Extract Audio, Trim Media, Compress Video
- Developer: JSON/XML Formatter, Text Diff, Base64, Hash Generator
- Archive: Extract Archive, Create ZIP
- Document: CSV↔JSON, Markdown→HTML

### App Features
- ⌘K Command Palette with keyboard navigation
- History / Recent Tools tracking
- Dark/Light mode toggle with persistence
- Batch Process — apply one tool to many files
- PDF Pipeline — chain tools sequentially
- PWA support — install as desktop/mobile app
- Per-tool SEO (dynamic meta tags)
- Dynamic sitemap.xml
- Custom 404 page
