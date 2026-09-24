<div align="center">

# 🛡️ PrivaTools

**Every file task, done privately.**

Free, open-source tools for PDFs, images, video, audio, and developer work — use them at privatools.me or run them on your own server.
AI two private ways: on-device models that download once into your browser, or your own API key going straight to the provider.
PrivaTools never passes your files to third parties. No account needed. No watermarks. No premium tier.

[![Live Demo](https://img.shields.io/badge/Live-privatools.me-blue?style=for-the-badge)](https://privatools.me)
[![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Security](https://github.com/ethereaglehq/privatools/actions/workflows/security.yml/badge.svg)](https://github.com/ethereaglehq/privatools/actions/workflows/security.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/ethereaglehq/privatools/badge)](https://securityscorecards.dev/viewer/?uri=github.com/ethereaglehq/privatools)
[![SBOM](https://img.shields.io/badge/SBOM-Trivy%20CycloneDX-0f766e?style=for-the-badge)](https://github.com/ethereaglehq/privatools/actions/workflows/security.yml)
[![Stars](https://img.shields.io/github/stars/ethereaglehq/privatools?style=for-the-badge&logo=github)](https://github.com/ethereaglehq/privatools/stargazers)

</div>

---

## ✨ Why PrivaTools?

| Feature | PrivaTools | iLovePDF / Smallpdf / Adobe |
|---|---|---|
| **Truly free** | No paid tier and no daily quota on the website (fair-use rate limits apply); the API has a free daily allowance | Limited free / paid tier |
| **No account** | Just open and use | Email / sign-up required |
| **Privacy** | Server tools delete their temporary files after the response, and a sweep clears leftovers; many tools never leave your browser | Uploaded to vendor cloud |
| **Tool range** | PDF, image, video, audio and developer tools in one place ([full list](https://privatools.me/tools)) | 20–95 tools, PDF only |
| **On-device AI** | 6 models (summarize, PII detection, translation, background removal, 2× Whisper speech-to-text) download once into the browser cache, then run offline without uploading their input | Cloud APIs |
| **Bring your own AI key** | Chat with PDF, vision OCR, translation, redaction, transcription through *your* Anthropic/OpenAI/Gemini/Groq/Mistral/OpenRouter/DeepSeek/Together or self-hosted key — requests go browser → provider, never through PrivaTools | Not offered |
| **Batch everywhere** | Many tools take several files per run (up to 25 on the standard tool page): per-file status, retry failed, one ZIP | Batch is a paid feature |
| **Pipeline** | Chain steps such as Compress → Watermark → Page numbers → Strip metadata on one PDF | Not offered free |
| **Self-hostable** | `docker compose up --build` | No |
| **Open source** | MIT — fork, modify, deploy | Proprietary |

---

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/ethereaglehq/privatools.git
cd privatools
docker compose up --build
```

Open **http://localhost:8000** — that's it!

### Option 2: Manual setup

```bash
git clone https://github.com/ethereaglehq/privatools.git
cd privatools

# Install the pinned Python environment (requires uv) and frontend packages.
npm run setup:backend
npm --prefix frontend ci

# Build Air + Play and serve the frontend and API together.
npm start
```

Open **http://127.0.0.1:8000**. The same-origin server supports real uploads,
account sessions (Clerk with a development key, or native accounts in a build
with `VITE_AUTH_PROVIDER=local`), API keys, downloads, scoped security policies
and the production PWA. Local accounts persist in `data/local/`; job files use
`temp/local/` and are deleted after responses or by the cleanup worker. Both
directories are ignored by Git. The launcher does not load production secrets.

For active development, run `npm run backend:dev` and `npm run frontend` in
separate terminals. Vite runs on port 5173 and proxies `/api/` to port 8000;
the public `/api` documentation page remains a frontend route. Preview the PWA
on port 8000 after rebuilding. To change the local backend port, use
`npm run backend -- --port 8001` (set `VITE_DEV_API_TARGET` when using Vite).

The consumer UI uses Clerk for Google, GitHub, email or username with a
password, and passkey sign-in, with password recovery by email. Configure
matching public frontend/backend instance keys; localhost uses a Development
instance with a separate user list.
Without a key, tools work and account controls show an unavailable state.
Existing self-hosted native accounts require explicit `VITE_AUTH_PROVIDER=local`
and no Clerk key. See [the Clerk deployment guide](deploy/clerk-production.md).
AI provider calls
require the user's own provider key; browser models are installed from the AI
studio as needed.

To run the backend test suite with the installed environment:

```bash
.venv/bin/python -m pytest backend/tests -q
```

On macOS, native-library interactions may require running each test module in
a separate Python process; Linux CI runs the complete suite together.

### System dependencies (for full feature set)

```bash
# macOS
brew install tesseract ffmpeg qpdf poppler pango cairo zbar
brew install --cask libreoffice

# Ubuntu / Debian
sudo apt install tesseract-ocr ffmpeg qpdf libreoffice poppler-utils libzbar0 libcairo2 libpango-1.0-0 libpangocairo-1.0-0
```

---

## 🛠️ All tools

The full, always-current catalogue, with each tool's page and guide, lives at [privatools.me/tools](https://privatools.me/tools). The families:

| Family | What's inside |
|---|---|
| 📄 **PDF — organize** | Merge, Split (by bookmarks/size/text/half), Organize, Delete/Extract Pages, Remove Blank Pages, Reverse, Booklet |
| 📄 **PDF — edit** | Edit PDF (text, ink pen, arrows, shapes, images, whiteout, layers panel), Sign & E-Sign, Watermark + Remove Watermark, Stamp, Header/Footer, Page Numbers, Bates, Bookmarks, White-Out, Shapes, Attachments, Hyperlinks, Highlight, Annotate, Transparent Background |
| 📄 **PDF — optimize** | Compress (presets, custom settings or a target size) and Batch Compress, Web Optimize, Flatten, Grayscale, Deskew, Repair, Crop, Auto Crop, Resize, Rotate, Invert Colors |
| 📄 **PDF — security** | Protect, Unlock (vault auto-try), Redact, Smart Redact (AI), Sanitize, Strip Metadata, Metadata Editor, Delete Annotations, Permissions, Remove Bates Numbering, Accessibility Checker, PDF/A Validator, Verify Signature |
| 📄 **PDF — convert to** | Images/HTML and web pages/Office/ODT/TXT/Markdown/CSV/EPUB/RTF/JSON/XML → PDF |
| 📄 **PDF — convert from** | PDF → images/Word/Excel/PowerPoint/Text/HTML/RTF/EPUB/Markdown, Extract Tables, Long Image |
| 📄 **PDF — advanced** | **Chat with PDF (AI)**, Summarize (AI), **Translate (AI)**, OCR (3 engines), Compare, N-up, Overlay, Alternate Mix, Fill Form, Form Creator, Extract Images, PDF to PDF/A, QR Code, Page Counter |
| 🖼️ **Images** | Compress, Convert, Resize & Crop, **Background Remover (server or on-device)**, Upscale, Watermark ± removal, EXIF scrub/view, **Image OCR (3 engines)**, Collage, Merge Images, Favicon, QR Code Reader, Rotate/Flip, Pixelate/Blur, Color Palette, HEIC/WebP/TIFF/BMP/GIF/SVG ↔ JPG/PNG |
| 🎬 **Video & Audio** | Convert, Resize, Merge, Trim, GIF ↔ MP4, Mute/Reverse/Speed, Compress, Extract Audio, **Transcribe Audio (AI, on-device Whisper or your key)**, Subtitles (convert + burn), thumbnails |
| 💻 **Developer & Text** | JSON/XML/SQL/GraphQL formatters, YAML ↔ JSON/TOML, JSON to CSV schema, Diff, Counter, Base64, Hashes, JWT, Regex, Timestamps, Cron, UUID/Password/Barcode generators, Case, Colors, URL encoder, URL to PDF |
| 📦 **Archive & documents** | Extract Archive, Create ZIP, CSV ↔ JSON, Markdown editor with HTML export |

### 🤖 AI, two private ways

**On-device models** — download once into the browser, then work on every visit, even offline: the transformers.js models from the Hugging Face CDN and the background-removal model from privatools.me itself. No key, no account, and the model's input stays in the browser. Managed from the **AI hub** in the top bar (install, sizes, remove):

| Model | Powers | Size |
|---|---|---|
| DistilBART CNN 6-6 | Summarize PDF | ~275 MB |
| BERT-base-NER | Smart Redact PII detection | ~110 MB |
| OPUS-MT (per language pair) | Translate PDF | ~107 MB |
| U²-Net-P | Background Remover (optional on-device engine; the server engine is the default) | ~4.4 MB + runtime |
| Whisper tiny / base | Transcribe Audio | ~41 / ~74 MB |

The OCR tools' optional browser engine loads tesseract.js and its language data (a few MB per language) from jsDelivr; the server engine is their default.

**Bring your own key (BYOK)** — paste an API key once (encrypted on-device, never sent to PrivaTools) and these tools can use it: **Chat with PDF**, **Summarize**, **Translate** (any language), **Smart Redact** NER, **Transcribe Audio** — plus **vision OCR** on both OCR tools for hard scans. Eight hosted providers (Anthropic, OpenAI, Gemini, OpenRouter, Groq, Mistral, DeepSeek, Together) plus any self-hosted OpenAI-compatible endpoint (Ollama, vLLM). Every request goes **browser → provider directly**; the page's Content-Security-Policy only permits provider egress on the pages that actually use a key.

## 📊 Compare & guides

Honest, side-by-side comparisons with the popular paid tools:

- [PrivaTools vs iLovePDF](https://privatools.me/compare/ilovepdf) · [vs Smallpdf](https://privatools.me/compare/smallpdf) · [vs Adobe Acrobat](https://privatools.me/compare/adobe-acrobat) · [vs Sejda](https://privatools.me/compare/sejda) · [vs PDF24](https://privatools.me/compare/pdf24) · [all comparisons →](https://privatools.me/compare)

In-depth guides on the [blog](https://privatools.me/blog):

- [Best Free PDF Tools in 2026](https://privatools.me/blog/best-free-pdf-tools-2026)
- [10 Best iLovePDF Alternatives in 2026](https://privatools.me/blog/ilovepdf-alternatives-2026)
- [How to Compress a PDF Without Losing Quality](https://privatools.me/blog/compress-pdf-without-losing-quality)
- [How to Redact a PDF Properly (Don't Use Black Boxes)](https://privatools.me/blog/redact-pdf-permanently-guide)
- [How to Chat With a PDF for Free — Without Uploading It](https://privatools.me/blog/chat-with-pdf-free-private)
- [AI PDF Tools, No Upload Required: Your Own Key or On-Device Models](https://privatools.me/blog/ai-pdf-tools-no-upload-byok)
- [Remove an Image Background Without Uploading It Anywhere](https://privatools.me/blog/remove-background-without-uploading)

---

## 🔗 Power features

### Pipeline

Chain tools sequentially and download one final PDF. Drafts auto-save locally,
named pipelines can be saved, and share links use `/pipeline?p=<base64url>`
payloads so recipes are portable without an account. Available at `/pipeline`.

The pipeline API runs up to 12 of its 17 PDF steps (compress, repair, deskew,
grayscale, flatten, rotate, reverse, N-up, booklet, page numbers, Bates
numbering, header/footer, watermark, stamp, strip metadata, delete annotations
and PDF/A) on one uploaded PDF. The same routes exist under `/api/v1/` for
account keys:

- API reference: [privatools.me/api](https://privatools.me/api) and
  `GET /api/v1/openapi.json` (FastAPI's `/api-docs` is disabled when
  `ENVIRONMENT=production`, as Docker Compose sets it)
- Templates and the supported steps: `GET /api/pipeline/templates`
- Validate/share: `POST /api/pipeline/validate`
- Run a PDF pipeline: `POST /api/pipeline` with `file` and JSON `steps`
  (`POST /api/v1/pipeline` with an account key costs the sum of its steps)
- Optional auth on a self-hosted server: set `PRIVATOOLS_API_KEYS` in the
  backend's environment and send `X-API-Key`

### Accounts and `/api/v1`

An account exists only to hold API keys — the tools themselves never ask for
one. Sign up at `/account`, create a key, and call the versioned API:

```
curl -X POST https://api.privatools.me/api/v1/compress \
  -H "X-API-Key: $PRIVATOOLS_API_KEY" \
  -F files=@in.pdf -F level=recommended -o out.pdf
```

`Authorization: Bearer pk_…` works too, for clients that default to it.

- `GET /api/v1/whoami` — confirm a key works
- `GET /api/v1/usage` — what today's quota looks like without spending any
- `GET /api/v1/operations` — public operation catalog, current costs/limits and background-job availability
- `GET /api/v1/openapi.json` — public schema containing only the versioned API
- Free tier: 500 cost units and 250 MiB of actual request-body bytes per key
  per day, reset at 00:00 UTC. Multipart boundaries and fields count too.
  Authenticated replies carry `X-RateLimit-Limit`, `-Remaining` and `-Reset`, so a
  client never has to call `/usage` to find out it is nearly out.
- Over quota is a `429` with `Retry-After`.
- Errors carry a machine-readable `code` beside the human `message`, so a
  client can branch without matching on prose. Existing `detail` fields remain.
- Authenticated processing has a shared 30-request/minute token bucket with
  a burst of six, three admitted HTTP requests per key, and a default ceiling
  of six across web workers. These are admission limits, not a promise that
  an arbitrary native thread stops when its HTTP client disconnects.
- Published operation costs are explicit; pipelines cost the sum of their steps.
  Framework validation rejections refund the original reservation. Failures
  after processing starts can still consume units.

V1 processing and account/usage queries require a key. Its catalog and schema
are public and do not spend processing quota. The website continues to use
the unversioned `/api/*` routes.

Background processing is enabled on api.privatools.me and optional when
self-hosting (`API_V1_JOBS_ENABLED=true`; off by default in
`docker-compose.yml`). It adds
`POST /api/v1/jobs` with an `Idempotency-Key`, authenticated status/result
retrieval, and explicit deletion. The initial adapters are `merge`, `compress`,
`grayscale`, and `pdf-to-text`; the catalog reports actual availability.
One worker shares the existing web container's 4 GB / 1.8 CPU limits.
Results expire one hour after completion; repeat downloads are supported
until expiry or deletion. See [API integration and rollout](docs/api/usage.md).

Clerk accounts recover access by email; users do not need to save a recovery
code. When Clerk is configured, native password/recovery endpoints are retired.
Explicit legacy self-hosted deployments retain their existing account records
and recovery-code flow.

Developer clients live under `packages/`:

- CLI: `npx --no-install privatools --help`
- Browser extension: load `packages/extension` unpacked in a Manifest V3 browser

### Multi-file, everywhere

Many tools accept several files directly on the tool page (up to 25 on the standard tool page) — same settings applied to each, bounded concurrency, per-file status rows, retry-failed, and a single ZIP (one file keeps the classic direct download). The dedicated `/batch` page takes larger drops for a single tool and processes them file by file.

### The AI hub

The **AI** button in the top bar opens one dialog for everything AI: manage the encrypted provider keys (BYOK) and see, pre-download, or delete the on-device models with their true cached sizes — introspected live from the browser cache, so it can't lie.

---

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Open search — matches tool names, synonyms, descriptions, categories, file types and site pages |
| `↑` `↓` | Move through results |
| `Enter` | Open the selected result |
| `Escape` | Close search |
| `/` | Jump to the filter on the tools page |
| `⌘↵` / `Ctrl+↵` | Start processing (when a file is selected) |

---

## 📁 Project structure

```text
privatools/
├── backend/                  # FastAPI application and Python tests
│   ├── app/                  # Routes, services, auth, API jobs and SEO
│   └── tests/
├── frontend/                 # React, Vite and TypeScript
│   ├── src/                  # Shared tools, pages and Air/Play interfaces
│   ├── public/               # Public assets and generated starter downloads
│   ├── scripts/              # Frontend build and content generators
│   └── tests/                # Browser checks
├── packages/                 # CLI and browser extension
├── examples/api/             # Runnable API integration examples
├── scripts/
│   ├── api/                  # Capacity checks and starter generation/tests
│   ├── analytics/            # Public analytics configuration verification
│   ├── ci/                   # Boot the built image and probe what it serves
│   ├── dev/                  # Local application launcher
│   └── seo/                  # Tool guide export, registry copy merge, manifest checks
├── deploy/                   # Deployment profiles and operational guides
│   └── oracle-vm/            # Oracle deployment, backup and systemd files
├── docs/
│   ├── api/                  # API integration and maintainer guides
│   ├── verification/         # Account and API verification evidence
│   ├── seo/                  # Search visibility runbook
│   ├── superpowers/          # Engineering plans and specifications
│   └── archive/              # Explicitly historical research, roadmap and analysis
├── Dockerfile
├── docker-compose.yml
├── package.json              # Root development commands and CLI workspace
└── requirements*.txt/.lock   # Pinned runtime, development and CI dependencies
```

See the [documentation index](docs/README.md), [frontend guide](frontend/README.md)
and [script guide](scripts/README.md) for the relevant commands and conventions.

---

## 🔍 SEO / AEO / GEO

PrivaTools ships with serious AI / answer-engine optimisation:

- **SSR meta + JSON-LD** for every route via Python middleware (Organization, WebSite, WebPage, SoftwareApplication, BreadcrumbList, HowTo, FAQPage, Blog, BlogPosting, Article, AboutPage, CollectionPage, ItemList)
- **Visible tool guides** — each tool page shows the same "How to use" steps and FAQ the server renders for crawlers, written in `backend/app/tool_content.py` and exported by `scripts/seo/export-tool-guides.py`
- **HowTo + FAQ schema** on every tool page, matching the visible guide
- **Hand-written search titles and descriptions** — every registry entry has its own `seoTitle` and `metaDescription`; a test enforces length, format and uniqueness
- **Sitemap priorities and real review dates** — tools listed in `frontend/src/data/sitemap-priority.json` get priority 0.8 and other tool pages 0.6; each tool's `lastReviewed` drives its `lastmod`, JSON-LD `dateModified` and visible "Last reviewed" line, and a pull request that changes a tool's copy without moving its date fails CI
- **`llms.txt` + `llms-full.txt`** — auto-generated index and full corpus for AI crawlers (ChatGPT, Claude, Perplexity, Gemini)
- **Dynamic OG images** per route via `/api/og-image?p=<path>`
- **robots.txt** — one policy for every crawler, AI assistants included: public pages allowed, `/api/` closed except `/api/og-image`; eight scraper and SEO-tool bots are blocked

---

## 🤝 Contributing

PrivaTools is MIT-licensed and PRs are welcome.

### Adding a new tool

**1. Service** — `backend/app/services/my_tool_service.py`

```python
from ..utils.filenames import temp_output

def my_tool(input_path: str) -> str:
    output_path = temp_output("my_tool", "pdf")
    # processing logic: read input_path, write output_path
    return str(output_path)
```

**2. Route** — add to an existing `routes/*.py` or create a new module. For one
PDF in and one file out, `process_pdf_upload` handles the whole lifecycle: it
checks and streams the upload to disk, runs the service off the event loop
under the heavy-work gate (`run_bounded`) and deletes both temporary files
after the response. This is `backend/app/routes/grayscale.py`:

```python
from fastapi import APIRouter, File, UploadFile

from ..services import grayscale_service
from ..utils.upload_helper import process_pdf_upload

router = APIRouter()


@router.post("/grayscale")
async def grayscale_pdf(file: UploadFile = File(...)):
    return await process_pdf_upload(
        file,
        grayscale_service.convert_to_grayscale,
        output_filename="grayscale.pdf",
    )
```

Bind extra form fields to the service with a lambda. Register a new router in
`backend/app/main.py` under `/api`, and in the `api_v1.mount` list to expose it
at `/api/v1`. Heavy routes also take `request: Request` and
`@limiter.limit(EXPENSIVE_RATE_LIMIT)`, as `routes/ocr.py` does.

**3. Tool entry** — `frontend/src/data/tools.ts` (PDF) or `non-pdf-tools.ts`

```typescript
{
  slug: "my-tool",                  // the frontend calls /api/my-tool unless lib/tool-endpoints.ts maps it
  icon: FileText,                   // any Lucide icon
  name: "My Tool",
  description: "Short description",
  longDescription: "Detailed description for the tool page.",
  seoTitle: "Do the Task to Any PDF Online – Free and Private",  // 40–60 characters, no brand
  metaDescription: "My Tool does the task to every page of a PDF in seconds. It is free, needs no sign-up, and adds no watermark to the result.", // 120–160 characters, ends with a period
  synonyms: "other words people search for",
  popularity: 42,                   // lower = higher up the listing
  category: "edit",                 // organize | edit | optimize | security | to-pdf | from-pdf | advanced
  accepts: ".pdf",
  outputLabel: "output.pdf",
  lastReviewed: "2026-09-18",       // ISO date; move it only when this tool's copy changes
}
```

Non-PDF tools use the categories `image`, `video-audio`, `developer`, `archive`
and `document-office`. Set `clientOnly: true` for a tool that runs entirely in
the browser and `byok: true` for one that can use the visitor's own AI key.
`frontend/src/test/tool-registry.test.ts` checks the title, description,
synonyms and date rules. Add HowTo steps and FAQs in
`backend/app/tool_content.py` (then run
`.venv/bin/python scripts/seo/export-tool-guides.py`), and run
`npm run gen:llms` so the manifest and sitemap pick the tool up — the sitemap
reads that manifest, not a per-tool list in `backend/app/routes/sitemap.py`.
`backend/app/seo_meta.py` holds no tool copy either: it reads the manifest
`npm run gen:llms` writes (the build's `tool-content.json`, or the committed
`frontend/public/tool-content.json` without a build) and refuses to start if
neither is readable. `GenericUI` handles upload, a queue of up to 25 files and
download automatically; a dedicated component under
`frontend/src/components/tool-ui/` must call `emitToolRun` from
`lib/toolRun.ts` when it succeeds or fails. [CONTRIBUTING.md](CONTRIBUTING.md)
lists the checks, and [CLAUDE.md](CLAUDE.md) keeps the full list of places a
new slug touches.

### Guidelines

- **Privacy first** — the server never sends file content to third parties. The one sanctioned exception is BYOK, and it lives entirely in the browser: the client may call the user's *chosen* AI provider with the user's *own* key, directly, with CSP scoping that egress to the specific tool pages that use it
- **Test before PR** — build the frontend first (`npm --prefix frontend run build`; some backend tests read the build), then run `.venv/bin/python -m pytest backend/tests -q` and the frontend checks listed in [CONTRIBUTING.md](CONTRIBUTING.md#testing--required-before-a-pr). CI also checks review dates on pull requests and boots the Docker image
- **Match the style** — follow existing patterns in similar tools
- **Update the copy with the code** — tool text lives in the registry entry (move its `lastReviewed`), steps and FAQ in `backend/app/tool_content.py` (then run `export-tool-guides.py`); run `npm run gen:llms` and commit the result, and add a line under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for a user-visible change

---

## 🔒 Privacy promise

- ✅ Server tools write uploads and results to **temporary files** with unique names; response cleanup deletes them once the result is sent, and a background sweep removes leftovers older than ten minutes. An interrupted request or a failed cleanup leaves a file until that sweep, so deletion is not instant erasure
- ✅ Many tools (JWT Decoder, Regex Tester, Password Generator, Hash Generator, Base64, JSON/XML Formatter, and others) **run entirely in your browser** — no upload at all. Summarize PDF does too with its on-device model; its optional bring-your-own-key mode sends the PDF's text to the provider you choose. Smart Redact finds personal data in your browser, then uploads the PDF and your selected terms to apply the redaction
- ✅ **No account, sign-up, email or payment needed to use any tool**
- ✅ **No watermarks, no premium tier, no daily quota on the website** — fair-use rate limits apply, such as five runs a minute per IP on the heaviest tools
- ✅ **Uploads are capped at 500 MB per request.** Most tool pages send each file in a request of its own, so a file can be up to 500 MB; tools that send several files in one request, such as Merge, share the 500 MB between them, and some tools set a lower limit of their own, such as 200 MB for Mute Video and Trim Media
- ✅ On-device AI (Summarize PDF, Smart Redact detection, Translate PDF, Transcribe Audio) runs via WebAssembly **in your browser** by default — models download once, cache locally, and work offline; no AI provider is involved. Background Remover and the OCR tools default to PrivaTools' own server and offer an in-browser engine; Chat with PDF always uses the provider you choose
- ✅ Optional **bring-your-own-key** AI sends requests from **your browser straight to the provider you chose**, authenticated with your key (stored encrypted on your device) — PrivaTools is never in the path, and CSP confines provider egress to the AI tool pages
- ✅ Saved PDF passwords live in a **device-local encrypted vault** (WebCrypto, non-extractable key) — never synced; Unlock tries them in your browser and sends only the one that works, with the PDF, to unlock it
- ✅ privatools.me runs **Google Analytics by default**: page views (the first page view of each page load also records where it came from, another site only by its origin, and keeps any `utm_` campaign tags that pass a filter against phone numbers, identifiers and tokens), one event per tool run (the tool and its category, single/batch/pipeline, the outcome, the file count and, for most failed runs, a fixed failure category — never file names, contents or error messages) and Google's scroll, outbound-link and video measurement. Browsers that identify themselves as automated or headless are not measured. It uses cookies and pseudonymous identifiers and Google receives your IP address, so it is not anonymous. Turn it off with the **Allow Google Analytics** switch on the Privacy page. Advertising features and Google Signals are off, and there are no ad networks. A self-hosted copy sends nothing unless its operator sets `GA_BROWSER_TAG_ENABLED=true`
- ✅ **Open source under MIT** — audit `backend/app/utils/cleanup.py` and `backend/app/main.py` yourself

---

## 📜 License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with care for privacy**

[Live Demo](https://privatools.me) · [Report Bug](https://github.com/ethereaglehq/privatools/issues) · [Request Feature](https://github.com/ethereaglehq/privatools/issues) · [llms.txt](https://privatools.me/llms.txt)

</div>
