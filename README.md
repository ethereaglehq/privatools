<div align="center">

# 🛡️ PrivaTools

**Every file task, done privately.**

221 free, open-source tools for PDFs, images, video, audio, and developer work — all running on your own server.
AI two private ways: on-device models that download once into your browser, or your own API key going straight to the provider.
Zero uploads to third parties. No account needed. No watermarks. No premium tier.

[![Live Demo](https://img.shields.io/badge/Live-privatools.me-blue?style=for-the-badge&logo=vercel)](https://privatools.me)
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
| **Truly free** | 100%, no quota | Limited free / paid tier |
| **No account** | Just open and use | Email / sign-up required |
| **Privacy** | Files processed in an isolated container, deleted on response; many tools never leave your browser | Uploaded to vendor cloud |
| **Tool count** | **221** (PDF + image + video + audio + dev) | 20–95 (PDF only) |
| **On-device AI** | 6 models (summarize, PII detection, translation, background removal, 2× Whisper speech-to-text) download once into the browser cache, then run offline — nothing uploads | Cloud APIs |
| **Bring your own AI key** | Chat with PDF, vision OCR, translation, redaction, transcription through *your* Anthropic/OpenAI/Gemini/Groq/Mistral/OpenRouter/DeepSeek/Together or self-hosted key — requests go browser → provider, never through PrivaTools | Not offered |
| **Batch everywhere** | ~160 tools take up to 25 files per run: per-file status, retry failed, one ZIP | Batch is a paid feature |
| **Pipeline** | Chain Merge → Compress → Watermark → Sign in one click | Not offered free |
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
native account sessions, API keys, downloads, scoped security policies and the
production PWA. Local accounts persist in `data/local/`; job files use
`temp/local/` and are deleted after responses or by the cleanup worker. Both
directories are ignored by Git. The launcher does not load production secrets.

For active development, run `npm run backend:dev` and `npm run frontend` in
separate terminals. Vite runs on port 5173 and proxies `/api/` to port 8000;
the public `/api` documentation page remains a frontend route. Preview the PWA
on port 8000 after rebuilding. To change the local backend port, use
`npm run backend -- --port 8001` (set `VITE_DEV_API_TARGET` when using Vite).

The consumer UI uses Clerk for Google, username/password and passkey sign-in,
with password recovery by email. Configure matching public frontend/backend
instance keys; localhost uses a Development instance with a separate user list.
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

## 🛠️ All Tools (221)

Counts come straight from the tool registry (2026-09-01) — the full, always-current catalogue lives at [privatools.me/tools](https://privatools.me/tools).

| Family | Count | What's inside |
|---|---|---|
| 📄 **PDF — organize** | 12 | Merge, Split (by size/bookmarks/text/half), Organize, Delete/Extract Pages, Reverse, Booklet, Alternate Mix, Repair |
| 📄 **PDF — edit** | 17 | Edit PDF (text, ink pen, arrows, shapes, images, whiteout, layers panel), Sign & E-Sign, Watermark + Remove Watermark, Stamp, Header/Footer, Page Numbers, Bates, Bookmarks, Forms, Hyperlinks, Highlight, Annotate |
| 📄 **PDF — optimize** | 12 | Compress (9 profiles + target size), Web Optimize, Flatten, Grayscale, Deskew, Crop, Auto Crop, Resize, Rotate, Remove Blank Pages, Invert Colors |
| 📄 **PDF — security** | 13 | Protect, Unlock (vault auto-try), Redact, Smart Redact (AI), Sanitize, Strip Metadata, Permissions, Verify Signature, Metadata Editor |
| 📄 **PDF — convert to** | 22 | Images/HTML/URL/Office/ODT/TXT/Markdown/CSV/EPUB/RTF/JSON/XML → PDF |
| 📄 **PDF — convert from** | 17 | PDF → images/Word/Excel/PPTX/Text/HTML/RTF/EPUB/Markdown/PDF-A, Extract Tables & Images, Long Image |
| 📄 **PDF — advanced** | 14 | **Chat with PDF (AI)**, Summarize (AI), **Translate (AI)**, OCR (3 engines), Compare, N-up, Overlay, PDF/A Validator, Page Counter |
| 🖼️ **Images** | 40 | Compress, Convert, Resize & Crop, **Remove Background (on-device AI)**, Upscale, Watermark ± removal, EXIF scrub/view, **Image OCR (3 engines)**, Collage, Favicon, QR/Barcode, HEIC/WebP/TIFF/BMP/GIF ↔ JPG/PNG |
| 🎬 **Video & Audio** | 44 | Convert, Resize, Merge, Trim, GIF ↔ MP4, Mute/Reverse/Speed, Compress, Extract Audio, **Transcribe Audio (AI, on-device Whisper or your key)**, Subtitles (convert + burn), thumbnails |
| 💻 **Developer & Text** | 26 | JSON/XML/YAML/CSV converters, Markdown ↔ HTML, Diff, Counter, Base64, Hashes, JWT, Regex, Timestamps, UUID/Password generators, Case, Colors |
| 📦 **Archive & Office** | 4 | Extract Archive, Create ZIP, office document tools |

### 🤖 AI, two private ways

**On-device models** — download once from the Hugging Face CDN into the browser cache, then work on every visit, even offline. No key, no account, nothing uploads. Managed from the **AI hub** in the top bar (install, sizes, remove):

| Model | Powers | Size |
|---|---|---|
| DistilBART CNN 6-6 | Summarize PDF | ~250 MB |
| BERT-base-NER | Smart Redact PII detection | ~250 MB |
| OPUS-MT (per language pair) | Translate PDF | ~107 MB |
| RMBG-1.4 | Remove Background | ~44 MB |
| Whisper tiny / base | Transcribe Audio | ~41 / ~74 MB |
| tesseract.js + language packs | OCR PDF · Image OCR | few MB per language |

**Bring your own key (BYOK)** — paste an API key once (encrypted on-device, never sent to PrivaTools) and five tools use frontier models: **Chat with PDF**, **Summarize**, **Translate** (any language), **Smart Redact** NER, **Transcribe Audio** — plus **vision OCR** on both OCR tools for hard scans. Eight hosted providers (Anthropic, OpenAI, Gemini, OpenRouter, Groq, Mistral, DeepSeek, Together) plus any self-hosted OpenAI-compatible endpoint (Ollama, vLLM). Every request goes **browser → provider directly**; the page's Content-Security-Policy only permits provider egress on the pages that actually use a key.

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

The public pipeline API starts with the safe automation subset
`compress-pdf` and `strip-metadata`:

- API docs: `/api-docs`
- Templates: `GET /api/pipeline/templates`
- Validate/share: `POST /api/pipeline/validate`
- Run a PDF pipeline: `POST /api/pipeline` with `file` and JSON `steps`
- Optional auth: set `PRIVATOOLS_API_KEYS` and send `X-API-Key`

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

Background processing is optional (`API_V1_JOBS_ENABLED=true`). It adds
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

Roughly 160 tools accept up to 25 files directly on the tool page — same settings applied to each, bounded concurrency, per-file status rows, retry-failed, and a single ZIP (one file keeps the classic direct download). The dedicated `/batch` page still handles the "drop 50 PDFs" case with drag-reordering.

### The AI hub

The **AI** button in the top bar opens one dialog for everything AI: manage the encrypted provider keys (BYOK) and see, pre-download, or delete the on-device models with their true cached sizes — introspected live from the browser cache, so it can't lie.

---

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Open Command Palette (multi-token fuzzy search, 145+ synonyms, lazy-loaded) |
| `↑` `↓` | Navigate results |
| `Enter` | Open selected tool |
| `Escape` | Close palette |
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
│   ├── dev/                  # Local application launcher
│   └── seo/                  # Public manifest verification
├── deploy/                   # Deployment profiles and operational guides
│   └── oracle-vm/            # Oracle deployment, backup and systemd files
├── docs/
│   ├── api/                  # API integration and maintainer guides
│   ├── verification/         # Account and API verification evidence
│   ├── seo/                  # Search visibility analysis and runbooks
│   ├── superpowers/          # Engineering plans and specifications
│   └── archive/              # Explicitly historical research and roadmap
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

- **SSR meta + JSON-LD** for every route via Python middleware (Organization, WebSite, SoftwareApplication, BreadcrumbList, HowTo, FAQPage, BlogPosting, Article+Review, AboutPage, CollectionPage, ItemList, SpeakableSpecification)
- **`speakable` CSS-selector targets** on every TL;DR and FAQ so voice assistants and featured-snippet pickers get a clean read-aloud target
- **`llms.txt` + `llms-full.txt`** — auto-generated index and full corpus for AI crawlers (ChatGPT, Claude, Perplexity, Gemini)
- **HowTo + FAQ schema** on every one of the 221 tools
- **Dynamic OG images** per route via `/api/og-image?p=<path>`
- **robots.txt** explicitly allows 21 AI crawlers and blocks aggressive ones

---

## 🤝 Contributing

PrivaTools is MIT-licensed and PRs are welcome.

### Adding a new tool — 3-step pattern

**1. Service** — `backend/app/services/my_tool_service.py`

```python
import uuid
from ..utils.cleanup import get_temp_path, ensure_temp_dir

def my_tool(input_path: str, option: str = "default") -> str:
    ensure_temp_dir()
    output_path = get_temp_path(f"output_{uuid.uuid4().hex}.pdf")
    # processing logic
    return str(output_path)
```

**2. Route** — add to an existing `routes/*.py` or create a new module

```python
@router.post("/my-tool")
async def my_tool_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    temp = get_temp_path(f"upload_{uuid.uuid4().hex}.pdf")
    temp.write_bytes(content)
    out = my_tool_service.my_tool(str(temp))
    cleanup = BackgroundTask(remove_files, str(temp), out)
    return FileResponse(out, filename="output.pdf", background=cleanup)
```

**3. Tool entry** — `frontend/src/data/tools.ts` (PDF) or `non-pdf-tools.ts`

```typescript
{
  slug: "my-tool",                  // must match the API path
  icon: FileText,                   // any Lucide icon
  name: "My Tool",
  description: "Short description",
  longDescription: "Detailed description for the tool page.",
  popularity: 42,                   // lower = higher up the listing
  category: "edit",                 // organize | edit | optimize | security | to-pdf | from-pdf | advanced
  accepts: ".pdf",
  outputLabel: "output.pdf",
}
```

Add an endpoint mapping in `frontend/src/lib/tool-endpoints.ts`, a TLDR + SEO entry in `backend/app/seo_meta.py` (`_TLDR_OVERRIDES`, `_PDF_TOOLS` or `_NONPDF_TOOLS`), HowTo steps + FAQs in `backend/app/tool_content.py`, and the slug to `backend/app/routes/sitemap.py`. The `GenericUI` component handles single-file upload/download automatically; for richer interactions add a dedicated component under `frontend/src/components/tool-ui/`.

### Guidelines

- **Privacy first** — the server never sends file content to third parties. The one sanctioned exception is BYOK, and it lives entirely in the browser: the client may call the user's *chosen* AI provider with the user's *own* key, directly, with CSP scoping that egress to the specific tool pages that use it
- **Test before PR** — `python -m pytest backend/tests -q` for backend, `npm run build && npm test` for frontend
- **Match the style** — follow existing patterns in similar tools
- **Update docs** — add a CHANGELOG entry and a TLDR in `seo_meta.py`

---

## 🔒 Privacy promise

- ✅ Files processed in an **isolated Docker container**, unlinked from disk immediately after the response
- ✅ Many tools (Summarize PDF, Smart Redact, JWT Decoder, Regex Tester, Password Generator, Hash Generator, Base64, JSON/XML Formatter, and others) **run entirely in your browser** — no upload at all
- ✅ **No account, sign-up, email or payment needed to use any tool**
- ✅ **No watermarks, no daily quota, no premium tier**
- ✅ **500 MB upload limit per file**, unlimited files per day
- ✅ Default AI runs via WebAssembly **in your browser** — models download once, cache locally, and work offline; no third-party AI APIs are involved
- ✅ Optional **bring-your-own-key** AI sends requests from **your browser straight to the provider you chose**, authenticated with your key (stored encrypted on your device) — PrivaTools is never in the path, and CSP confines provider egress to the AI tool pages
- ✅ Saved PDF passwords live in a **device-local encrypted vault** (WebCrypto, non-extractable key) — never synced, never uploaded
- ✅ The public demo at privatools.me uses **anonymous GA4 pageview telemetry only** (IP-anonymized; blockable by any extension). No other trackers, no ad networks, no behavioural profiling
- ✅ **Open source under MIT** — audit `backend/app/utils/cleanup.py` and `backend/app/main.py` yourself

---

## 📜 License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with care for privacy**

[Live Demo](https://privatools.me) · [Report Bug](https://github.com/ethereaglehq/privatools/issues) · [Request Feature](https://github.com/ethereaglehq/privatools/issues) · [llms.txt](https://privatools.me/llms.txt)

</div>
