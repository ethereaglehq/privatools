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

BASE_URL = "https://privatools.me"

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
