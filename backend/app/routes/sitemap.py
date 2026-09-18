"""Sitemap served from the current build, with a deterministic registry fallback."""
from datetime import date
from html import escape
from xml.etree import ElementTree
from functools import lru_cache
from fastapi import APIRouter, Request

from ..utils.caching import cache_response
from .. import seo_meta
from ..seo_meta import _last_reviewed_for

router = APIRouter()

# All tool slugs — must match frontend routes exactly
PDF_TOOLS = [
    "merge-pdf", "split-pdf", "split-by-bookmarks", "split-by-size",
    "organize-pages", "delete-pages", "extract-pages",
    "edit-pdf", "sign-pdf", "watermark", "header-footer",
    "page-numbers", "bates-numbering", "bookmarks",
    "compress-pdf", "flatten-pdf", "remove-watermark", "deskew-pdf", "repair-pdf",
    "resize-pdf", "rotate-pdf", "grayscale-pdf", "crop-pdf",
    "protect-pdf", "unlock-pdf", "redact-pdf", "strip-metadata",
    "delete-annotations", "metadata",
    "html-to-pdf", "image-to-pdf", "office-to-pdf",
    "pdf-to-excel", "pdf-to-image", "pdf-to-pptx", "pdf-to-text", "pdf-to-word",
    "alternate-mix", "compare-pdf", "extract-images", "fill-form",
    "nup", "ocr-pdf", "overlay", "qr-code", "pdf-to-pdfa",
    "remove-blank-pages", "auto-crop",
    "pdf-to-epub", "markdown-to-pdf", "csv-to-pdf",
    "invert-colors", "pdfa-validator", "verify-signature", "accessibility-check",
    "bates-remove",
    "translate-pdf",
    "sanitize-pdf", "add-hyperlinks", "form-creator",
    "transparent-background", "stamp-pdf", "esign-pdf",
    "word-to-pdf", "excel-to-pdf", "pptx-to-pdf-convert",
    "txt-to-pdf", "json-to-pdf", "xml-to-pdf", "epub-to-pdf", "rtf-to-pdf",
    "extract-tables", "pdf-to-markdown",
    "whiteout-pdf", "annotate-pdf", "add-shapes",
    "set-permissions", "add-attachment",
    "reverse-pdf", "booklet-pdf",
    "batch-compress-pdf", "pdf-page-counter",
    # Newly added — keep in sync with frontend/src/data/tools.ts
    "jpg-to-pdf", "png-to-pdf", "heic-to-pdf",
    "webp-to-pdf", "tiff-to-pdf", "bmp-to-pdf", "gif-to-pdf", "svg-to-pdf",
    "odt-to-pdf",
    "pdf-to-tiff", "pdf-to-bmp", "pdf-to-gif", "pdf-to-svg",
    "split-in-half", "highlight-pdf", "summarize-pdf",
    "smart-redact", "chat-with-pdf",
    # Round-O additions
    "pdf-to-jpg", "pdf-to-png", "pdf-to-long-image",
    # v1.2.0 PDF additions
    "web-optimize-pdf", "split-by-text", "pdf-to-html", "pdf-to-rtf",
]

# Newly-added video tools (also non-PDF — listed here so the route map stays
# in one place; sitemap iteration uses both lists).
VIDEO_TOOLS = [
    "video-to-pdf", "video-converter", "video-resizer", "video-thumbnail",
    "gif-to-mp4", "add-subtitles",
]

_VIDEO_TOOLS_NEW = [
    "video-to-pdf", "video-converter", "video-resizer", "video-thumbnail",
    "gif-to-mp4", "add-subtitles",
    # Round-O additions
    "video-merge", "audio-merge", "subtitle-converter",
    "password-generator", "uuid-generator", "lorem-ipsum",
    "word-counter", "color-converter", "url-encoder",
]

NON_PDF_TOOLS = [
    "image-compressor", "image-converter", "remove-exif", "resize-crop-image",
    "video-to-gif", "image-ocr",
    "extract-audio", "trim-media", "compress-video",
    "json-xml-formatter", "text-diff", "base64", "hash-generator",
    "extract-archive", "create-zip",
    "csv-json", "markdown-html", "heic-to-jpg",
    "remove-background", "svg-to-png", "image-watermark", "remove-image-watermark",
    "generate-favicon", "make-collage", "generate-barcode",
    "url-to-pdf", "qr-reader", "merge-images",
    "image-upscaler", "audio-converter", "transcribe-audio",
    # v1.2.0 additions
    "webp-to-jpg", "webp-to-png", "heic-to-png", "view-exif",
    "jwt-decoder", "regex-tester", "timestamp-converter",
    # v1.4.0 additions — image converter aliases
    "jpg-to-png", "png-to-jpg", "jpg-to-webp", "png-to-webp",
    "tiff-to-jpg", "tiff-to-png", "bmp-to-jpg", "bmp-to-png",
    "gif-to-jpg", "gif-to-png",
    # v1.4.0 additions — audio/video converter aliases
    "m4a-to-mp3", "mp4-to-mp3", "mov-to-mp4", "avi-to-mp4",
    "webm-to-mp4", "mp4-to-webm",
    # Phase 2 conversion alias pack
    "jpg-to-tiff", "png-to-tiff", "webp-to-tiff",
    "jpg-to-bmp", "png-to-bmp", "webp-to-bmp",
    "mp3-to-wav", "wav-to-mp3", "flac-to-mp3", "ogg-to-mp3",
    "aac-to-mp3", "mp3-to-ogg", "mp3-to-flac", "mp3-to-aac",
    "wav-to-flac", "wav-to-ogg",
    "mkv-to-mp4", "mp4-to-mov", "mov-to-webm", "mkv-to-webm",
    "mp4-to-avi", "avi-to-webm", "webm-to-mov", "mov-to-mkv",
    "webm-to-gif", "mov-to-gif",
    # P2 developer micro-tools
    "cron-parser", "sql-formatter", "graphql-formatter",
    "yaml-toml-converter", "gitignore-generator", "semver-bumper",
    "env-validator", "json-to-csv-schema",
    # v1.4.0 additions — browser-only dev converters
    "yaml-to-json", "json-to-yaml", "case-converter",
    # v1.5.0 / phase 7 — competitor-gap tools
    "mute-video", "reverse-video", "video-speed", "audio-trim",
    "image-palette", "pixelate-image",
    # v1.5.1 — image rotate/flip
    "rotate-image", "flip-image",
    # Video / audio / dev tools previously kept in _VIDEO_TOOLS_NEW —
    # merged here so the canonical NON_PDF_TOOLS list matches the frontend
    # data file exactly (used by the test_spa_fallback consistency check).
    "video-to-pdf", "video-converter", "video-resizer", "video-thumbnail",
    "gif-to-mp4", "add-subtitles",
    "video-merge", "audio-merge", "subtitle-converter",
    "password-generator", "uuid-generator", "lorem-ipsum",
    "word-counter", "color-converter", "url-encoder",
]

# v1.2.0 PDF additions (sitemap was missing these)
_PDF_V12 = [
    "web-optimize-pdf", "split-by-text", "pdf-to-html", "pdf-to-rtf",
]

COMPARE_PAGES = [
    "ilovepdf", "smallpdf", "adobe-acrobat", "sejda", "pdf24", "foxit", "lightpdf",
    "stirling-pdf", "dochub", "pdfescape", "nitro-pdf", "tinywow", "ihatepdf",
]

# Blog posts with their published dates. Must stay in sync with
# _BLOG_POSTS in app/seo_meta.py — otherwise crawlers see meta for a
# post but the sitemap omits the URL (or vice versa).
BLOG_POSTS: dict[str, str] = {
    "compress-pdf-without-losing-quality": "2026-03-22",
    "merge-pdf-files-online-free": "2026-03-22",
    "best-free-pdf-tools-2026": "2026-03-22",
    "remove-password-from-pdf": "2026-03-22",
    "convert-word-to-pdf-free": "2026-03-22",
    "edit-pdf-online-free-no-sign-up": "2026-03-29",
    "split-pdf-online-free": "2026-03-29",
    "redact-pdf-free-guide": "2026-03-29",
    "best-free-online-pdf-editors-2026": "2026-03-29",
    # May 2026 batch — were present in seo_meta but missing from the
    # sitemap, which meant Google never discovered them via the canonical
    # entry point.
    "ai-pdf-summarizer-browser-2026": "2026-05-15",
    "ilovepdf-alternatives-2026": "2026-05-15",
    "redact-pdf-permanently-guide": "2026-05-15",
    "online-pdf-tools-tracking-you": "2026-05-15",
    "heic-conversion-guide-2026": "2026-05-15",
    "decode-jwt-tokens-safely-guide": "2026-05-15",
    # August 2026 batch — the Daylight essays and the head-to-head comparisons.
    "reading-privacy-policies": "2026-05-21",
    "what-deleted-means": "2026-07-02",
    "how-local-first-works": "2026-08-14",
    "privatools-vs-ilovepdf": "2026-08-20",
    "privatools-vs-smallpdf": "2026-08-24",
    "privatools-vs-sejda": "2026-08-27",
    "privatools-vs-ihatepdf": "2026-08-30",    "chat-with-pdf-free-private": "2026-09-01",
    "ai-pdf-tools-no-upload-byok": "2026-09-01",
    "remove-background-without-uploading": "2026-09-01",
    "transcribe-audio-free-no-upload": "2026-09-01",
    "ocr-scanned-pdf-free-three-ways": "2026-09-01",
    "translate-pdf-free-private": "2026-09-01",
    "bring-your-own-ai-key-guide": "2026-09-01",
    "batch-process-files-free": "2026-09-01",
    "chatpdf-alternatives-private": "2026-09-01",
}

BASE_URL = "https://privatools.me"

# Dates for different content types
# Pages were originally added at these dates. We bump lastmod to today
# on every served sitemap so AI/search engines see fresh content
# (PrivaTools is iterated daily). If a particular page becomes legitimately
# stale, drop its slug into _FROZEN below.
_TOOLS_LAUNCH_DATE = "2026-03-15"
_COMPARE_DATE = "2026-03-22"
_FROZEN: set[str] = set()

# Tools that get a priority bump in the sitemap. These are the highest-
# search-volume PDF/utility verbs (merge, compress, split, etc.) — Google
# uses sitemap priority as a soft crawl-budget hint, so giving the
# headline tools 0.9 routes more attention to them than to the long tail.
_HIGH_PRIORITY_TOOLS: set[str] = {
    "merge-pdf", "split-pdf", "compress-pdf",
    "pdf-to-word", "pdf-to-excel", "pdf-to-jpg",
    "jpg-to-pdf", "word-to-pdf", "image-to-pdf",
    "edit-pdf", "sign-pdf", "ocr-pdf",
    "protect-pdf", "unlock-pdf", "rotate-pdf",
    "redact-pdf", "watermark",
    "image-compressor", "image-converter", "heic-to-jpg",
    "remove-background", "video-to-gif",
    # Free-winnable niche dev/utility tools. Per the keyword research, the PDF
    # heads are owned by DA80-90 incumbents, but these niche dev SERPs (GitHub
    # repos + small indie tools) are realistically rankable for a new site — so
    # concentrate crawl-budget priority here, where the wins are actually free.
    "semver-bumper", "env-validator", "cron-parser", "yaml-toml-converter",
    "graphql-formatter", "json-to-csv-schema", "gitignore-generator",
    "sql-formatter", "subtitle-converter", "remove-exif", "view-exif",
    "json-to-yaml", "yaml-to-json",
}


# Dates represent reviewed content changes, never the request date.
STATIC_LAST_REVIEWED = "2026-09-14"
GENERATED_SITEMAP = seo_meta._CONTENT_DIR / "sitemap.xml"
_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


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


def _entries() -> dict[str, tuple[str | None, str]]:
    public_pages = ("/", "/about", "/privacy", "/terms", "/batch", "/pipeline",
                    "/security", "/support", "/status", "/compare", "/blog", "/tools", "/trust", "/api", "/ai")
    rows = {BASE_URL + (path if path != "/" else ""): (STATIC_LAST_REVIEWED, _priority(path if path != "/" else ""))
            for path in public_pages if path not in seo_meta.NOINDEX_PATHS}
    for slug, post in seo_meta._blog_posts().items():
        rows[f"{BASE_URL}/blog/{slug}"] = (seo_meta._reviewed_date(post), _priority(f"/blog/{slug}"))
    for slug, comparison in seo_meta._comparisons().items():
        rows[f"{BASE_URL}/compare/{slug}"] = (seo_meta._reviewed_date(comparison), _priority(f"/compare/{slug}"))
    pdf, nonpdf = seo_meta._tool_registries()
    for prefix, tools in (("tool", pdf), ("tools", nonpdf)):
        for slug in tools:
            rows[f"{BASE_URL}/{prefix}/{slug}"] = (_last_reviewed_for(slug), _priority(f"/{prefix}/{slug}", slug))
    return rows


def _generated_body(expected: dict[str, tuple[str | None, str]]) -> bytes | None:
    """Only serve a generated sitemap that matches the current public route set."""
    try:
        body = GENERATED_SITEMAP.read_bytes()
        root = ElementTree.fromstring(body)
        if root.tag != _NS + "urlset":
            return None
        seen = set()
        for node in root:
            if node.tag != _NS + "url":
                return None
            url = node.findtext(_NS + "loc") or ""
            if url not in expected or url in seen:
                return None
            seen.add(url)
            lastmod = node.findtext(_NS + "lastmod")
            if lastmod:
                # Keep the generator's actual content dates, not an arbitrary future date.
                parsed = date.fromisoformat(lastmod)
                if parsed > date.today():
                    return None
        return body if seen == set(expected) else None
    except (OSError, ElementTree.ParseError, ValueError):
        return None


@lru_cache(maxsize=8)
def _render_sitemap(revision: int, generated_mtime: int) -> bytes:
    rows = _entries()
    generated = _generated_body(rows)
    if generated is not None:
        return generated
    entries = []
    for url, (lastmod, priority) in rows.items():
        modified = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        entries.append(f"  <url><loc>{escape(url)}</loc>{modified}<priority>{priority}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries) + "\n</urlset>").encode("utf-8")


def _build_sitemap_xml(_legacy_request_date: str | None = None) -> bytes:
    """The compatibility argument is intentionally ignored: dates describe content."""
    return _render_sitemap(seo_meta.blog_content_mtime_ns(), seo_meta._mtime(GENERATED_SITEMAP))


@router.get("/sitemap.xml")
async def sitemap(request: Request):
    # Content-based ETag is the validator. Avoid a fabricated daily Last-Modified
    # which could produce a false 304 after a same-day content build.
    return cache_response(
        _build_sitemap_xml(), media_type="application/xml", max_age=3600,
        stale_while_revalidate=3600, request=request,
    )
