"""SEO/AEO/GEO guardrails for server-rendered metadata.

These tests validate the route-aware JSON-LD generator directly. They avoid
calling external validators, but catch the regressions that usually hurt rich
results and AI answer surfaces: missing graph roots, unknown-tool schema,
stale privacy overclaims, and malformed tool FAQ/HowTo nodes.
"""

from __future__ import annotations

import json
import os
import re
from html import escape

from backend.app import seo_meta
from backend.app.seo_meta import TOOL_META, get_jsonld_for_path, get_meta_for_path, inject_seo
from backend.app.tool_content import TOOL_FAQ, TOOL_HOWTO


STALE_PRIVACY_CLAIMS = (
    "All processing happens on your device",
    "All processing happens locally",
    "Zero uploads",
    "No accounts, no tracking",
    "no tracking, no ads",
    # Optional developer accounts exist (they issue API keys), so any phrasing
    # that says accounts do not exist is now false. "No account needed" and
    # "no account required" stay true and are what the copy should say.
    "No accounts,",
    "no accounts,",
    "no accounts exist",
)

STALE_STORAGE_CLAIMS = (
    "temp memory",
    "temporary memory",
    "temporary server memory",
    "memory only",
    "processed in memory",
    "self-hostable via Docker, so files stay on your own infrastructure",
    "never written to disk",
    "never persisted to disk",
    "No copy is kept on any disk",
    "files never leave the processing container",
    "files never leave the container",
    "File content never leaves the processing container",
    "The redacted PDF is then constructed in your browser",
    "the original is never uploaded",
    "Smart Redact uses BERT-base-NER for PII detection. Neither sends data",
)


def _graph_for(path: str) -> list[dict]:
    data = get_jsonld_for_path(path)
    assert isinstance(data, dict)
    assert data.get("@context") == "https://schema.org"
    graph = data.get("@graph")
    assert isinstance(graph, list)
    assert graph, f"{path} emitted an empty JSON-LD graph"
    json.dumps(data)
    return graph


def _types(graph: list[dict]) -> set[str]:
    found: set[str] = set()
    for node in graph:
        node_type = node.get("@type")
        if isinstance(node_type, list):
            found.update(str(t) for t in node_type)
        elif node_type:
            found.add(str(node_type))
    return found


def test_homepage_jsonld_has_entity_and_answer_graph():
    graph = _graph_for("/")
    types = _types(graph)

    assert {"WebSite", "Organization", "ItemList", "FAQPage"} <= types
    website = next(node for node in graph if node.get("@type") == "WebSite")
    assert website["potentialAction"]["@type"] == "SearchAction"
    item_list = next(node for node in graph if node.get("@type") == "ItemList")
    assert item_list["numberOfItems"] == len(item_list["itemListElement"])
    assert item_list["numberOfItems"] >= 20


def test_tool_jsonld_has_application_howto_faq_and_breadcrumbs():
    graph = _graph_for("/tool/merge-pdf")
    types = _types(graph)

    assert {"WebPage", "SoftwareApplication", "BreadcrumbList", "HowTo", "FAQPage"} <= types
    app = next(node for node in graph if node.get("@type") == "SoftwareApplication")
    assert app["@id"].endswith("#app")
    assert app["isAccessibleForFree"] is True
    assert app["offers"]["price"] == "0"
    assert app["featureList"]
    assert app["creator"]["sameAs"] == ["https://github.com/ethereaglehq/privatools"]

    howto = next(node for node in graph if node.get("@type") == "HowTo")
    assert howto["name"] == "How to use Merge PDF"
    assert len(howto["step"]) >= 3
    assert all(step["@type"] == "HowToStep" for step in howto["step"])

    html = "<html><head><title>Old</title></head><body><div id='root'></div></body></html>"
    injected = inject_seo(html, "/tool/merge-pdf")
    assert f"<h2>{howto['name']}</h2>" in injected

    faq = next(node for node in graph if node.get("@type") == "FAQPage")
    assert len(faq["mainEntity"]) >= 3


def test_non_pdf_tool_jsonld_uses_tools_route_and_utility_category():
    graph = _graph_for("/tools/image-compressor")
    app = next(node for node in graph if node.get("@type") == "SoftwareApplication")

    assert app["url"] == "https://privatools.me/tools/image-compressor"
    assert app["applicationCategory"] == "UtilitiesApplication"
    assert app["applicationSubCategory"] == "Image tools"


def test_tool_jsonld_application_subcategories_are_specific():
    examples = {
        "/tool/merge-pdf": "PDF organization tools",
        "/tool/pdf-to-word": "Convert from PDF tools",
        "/tool/word-to-pdf": "Convert to PDF tools",
        "/tools/video-converter": "Video and audio tools",
        "/tools/generate-barcode": "Developer tools",
        "/tools/extract-archive": "Archive tools",
        "/tools/csv-json": "Document and data tools",
    }

    for path, expected in examples.items():
        graph = _graph_for(path)
        app = next(node for node in graph if node.get("@type") == "SoftwareApplication")

        assert app["applicationSubCategory"] == expected, path


def test_barcode_meta_does_not_advertise_unsupported_svg_output():
    title, description = get_meta_for_path("/tools/generate-barcode")
    combined = f"{title}\n{description}"

    assert "SVG" not in combined
    assert "PNG" in description


def test_tool_meta_does_not_overclaim_unlimited_file_sizes():
    offenders = [
        slug
        for slug, meta in TOOL_META.items()
        if "no file size limits" in f"{meta['description']} {meta['long_description']}".lower()
    ]

    assert offenders == []


def test_extract_archive_meta_does_not_advertise_unsupported_formats():
    title, description = get_meta_for_path("/tools/extract-archive")
    combined = f"{title}\n{description}"

    assert "RAR" not in combined
    assert "7Z" not in combined
    assert "ZIP" in combined
    assert "TAR" in combined


def test_extract_archive_faq_does_not_claim_password_support():
    graph = _graph_for("/tools/extract-archive")
    faq = next(node for node in graph if node.get("@type") == "FAQPage")
    faq_text = json.dumps(faq)

    assert "Password input is supported" not in faq_text
    assert "not supported yet" in faq_text


def test_create_zip_faq_does_not_claim_password_encryption_support():
    graph = _graph_for("/tools/create-zip")
    faq = next(node for node in graph if node.get("@type") == "FAQPage")
    faq_text = json.dumps(faq)

    assert "AES-256" not in faq_text
    assert "password-protect" in faq_text
    assert "Not yet" in faq_text


def test_noun_tool_howto_names_are_readable_in_jsonld_and_ssr_html():
    graph = _graph_for("/tools/generate-barcode")
    howto = next(node for node in graph if node.get("@type") == "HowTo")
    expected = "How to use Barcode Generator"

    assert howto["name"] == expected
    assert "How to Barcode Generator" not in howto["name"]

    html = "<html><head><title>Old</title></head><body><div id='root'></div></body></html>"
    injected = inject_seo(html, "/tools/generate-barcode")

    assert f"<h2>{expected}</h2>" in injected
    assert "How to Barcode Generator" not in injected


def test_unknown_tool_does_not_emit_soft_404_schema():
    assert get_jsonld_for_path("/tool/not-a-real-tool") is None
    assert get_jsonld_for_path("/tools/not-a-real-tool") is None


def test_security_route_is_known_and_has_meta():
    assert seo_meta.path_is_known("/security")
    title, description = get_meta_for_path("/security")

    assert "Security" in title
    assert "threat model" in description


def test_meta_descriptions_do_not_repeat_stale_privacy_overclaims():
    paths = [
        "/",
        "/tool/merge-pdf",
        "/tools/video-converter",
        "/about",
        "/compare/ilovepdf",
        "/blog/how-to-merge-pdfs-online-free",
    ]

    for path in paths:
        title, description = get_meta_for_path(path)
        combined = f"{title}\n{description}"
        for stale in STALE_PRIVACY_CLAIMS:
            assert stale not in combined, f"{path} contains stale claim: {stale!r}"


def test_server_side_storage_claims_match_temp_file_architecture():
    surfaces = [
        json.dumps(get_jsonld_for_path("/"), sort_keys=True),
        json.dumps(get_jsonld_for_path("/tool/merge-pdf"), sort_keys=True),
        json.dumps(get_jsonld_for_path("/tools/image-compressor"), sort_keys=True),
        inject_seo("<html><head></head><body><div id='root'></div></body></html>", "/"),
        inject_seo("<html><head></head><body><div id='root'></div></body></html>", "/about"),
        inject_seo("<html><head></head><body><div id='root'></div></body></html>", "/privacy"),
        inject_seo("<html><head></head><body><div id='root'></div></body></html>", "/terms"),
        json.dumps(TOOL_FAQ, sort_keys=True),
        json.dumps(TOOL_HOWTO, sort_keys=True),
    ]
    combined = "\n".join(surfaces)

    for stale in STALE_STORAGE_CLAIMS:
        assert stale not in combined, f"stale storage claim leaked: {stale!r}"
    assert "temporary per-request storage" in combined
    assert "isolated temporary storage" in combined


def test_generated_blog_content_refreshes_by_mtime(tmp_path, monkeypatch):
    blog_json = tmp_path / "blog-content.json"
    html = "<html><head></head><body><div id='root'></div></body></html>"

    def write_blog(body: str, title: str, mtime_ns: int) -> None:
        blog_json.write_text(
            json.dumps([
                {
                    "slug": "heic-conversion-guide-2026",
                    "title": title,
                    "tldr": "Short generated summary.",
                    "body": body,
                    "relatedTools": ["split-in-half"],
                }
            ]),
            encoding="utf-8",
        )
        os.utime(blog_json, ns=(mtime_ns, mtime_ns))

    monkeypatch.setattr(seo_meta, "_BLOG_JSON", blog_json)
    seo_meta._load_blog_bodies.cache_clear()
    seo_meta._tool_to_blogs_for_mtime.cache_clear()
    seo_meta._get_jsonld_for_path.cache_clear()

    write_blog("<p>first generated body</p>", "First generated guide", 1_000_000_000)
    first_blog = inject_seo(html, "/blog/heic-conversion-guide-2026")
    first_tool = inject_seo(html, "/tool/split-in-half")

    assert "first generated body" in first_blog
    assert "First generated guide" in first_tool

    write_blog("<p>second generated body</p>", "Second generated guide", 2_000_000_000)
    second_blog = inject_seo(html, "/blog/heic-conversion-guide-2026")
    second_tool = inject_seo(html, "/tool/split-in-half")

    assert "second generated body" in second_blog
    assert "first generated body" not in second_blog
    assert "Second generated guide" in second_tool
    assert "First generated guide" not in second_tool


def test_tool_pages_use_registry_search_copy(tmp_path, monkeypatch):
    """Tool title/description/H1/og:title come from the registry's seoTitle
    and metaDescription — not the old "<name> — Free Online | PrivaTools"
    formula. `_tool_seo_fields` is the read path both `get_meta_for_path`
    and the SSR `<h1>` share."""
    manifest = {
        "merge-pdf": {"slug": "merge-pdf", "name": "Merge PDF", "path": "/tool/merge-pdf", "category": "organize",
                      "description": "Combine PDFs", "longDescription": "Long intro text for the page.",
                      "seoTitle": "Merge PDF Files Online Free – Combine PDFs Privately",
                      "metaDescription": "Combine PDF files in the order you choose. Free, no sign-up, temporary server processing.",
                      "lastReviewed": "2026-08-02"},
        "image-compressor": {"slug": "image-compressor", "name": "Image Compressor", "path": "/tools/image-compressor", "category": "image",
                             "description": "Shrink images", "longDescription": "Long intro for images.",
                             "seoTitle": "Compress Images Online Free – Smaller JPG, PNG and WebP",
                             "metaDescription": "Reduce JPG, PNG and WebP file size with a quality preset you control. Free, no sign-up, temporary server processing."},
    }
    path = tmp_path / "tool-content.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(seo_meta, "_TOOL_JSON", path)
    seo_meta._load_manifest.cache_clear()

    title, description = get_meta_for_path("/tool/merge-pdf")
    assert title == "Merge PDF Files Online Free – Combine PDFs Privately"
    assert description == manifest["merge-pdf"]["metaDescription"]
    assert "| PrivaTools" not in title

    # og:title comes from a real template with a pre-existing tag — inject_seo
    # updates a meta tag's `content` in place and never invents a missing one.
    from pathlib import Path

    template = (Path(__file__).resolve().parents[2] / "frontend" / "index.html").read_text("utf-8")
    html = inject_seo(template, "/tools/image-compressor")
    assert "<h1>Compress Images Online Free – Smaller JPG, PNG and WebP</h1>" in html
    assert '<meta property="og:title" content="Compress Images Online Free – Smaller JPG, PNG and WebP">' in html

    # The manifest's lastReviewed date reaches both the visible review line
    # and the JSON-LD dateModified — `_last_reviewed_for` is the shared read
    # path for both.
    assert "Last reviewed 2026-08-02" in seo_meta._build_ssr_content("/tool/merge-pdf", *seo_meta.get_meta_for_path("/tool/merge-pdf"))
    graph = seo_meta._get_jsonld_for_path("/tool/merge-pdf", seo_meta.blog_content_mtime_ns())["@graph"]
    assert any(node.get("dateModified") == "2026-08-02" for node in graph)


def test_compare_tool_count_claims_match_catalog_size():
    total = len(seo_meta._PDF_TOOLS) + len(seo_meta._NONPDF_TOOLS)
    breadth_feature = f"{total} tools (PDF, image, video, audio, dev)"
    comparison_copy = json.dumps(
        [seo_meta._PRIVATOOLS_FEATURES, seo_meta._COMPARE_DATA],
        sort_keys=True,
    )

    assert seo_meta._TOTAL_TOOL_COUNT == total
    assert breadth_feature in comparison_copy
    assert f"Yes ({total} tools)" in comparison_copy
    assert "175+" not in comparison_copy


def test_public_tool_count_claims_match_catalog_size():
    total = len(seo_meta._PDF_TOOLS) + len(seo_meta._NONPDF_TOOLS)
    html = "<html><head></head><body><div id='root'></div></body></html>"
    surfaces = "\n".join(
        [
            seo_meta.get_meta_for_path("/")[1],
            seo_meta.get_meta_for_path("/compare/smallpdf")[1],
            seo_meta.get_meta_for_path("/compare/adobe-acrobat")[1],
            seo_meta.get_meta_for_path("/definitely-missing")[1],
            inject_seo(html, "/"),
            inject_seo(html, "/definitely-missing"),
        ]
    )

    assert f"{total} free" in surfaces
    assert f"{total} tools" in surfaces
    assert "179" not in surfaces


def test_injected_html_has_single_route_aware_jsonld_script():
    html = "<html><head><title>Old</title></head><body><div id='root'></div></body></html>"
    injected = inject_seo(html, "/tool/merge-pdf")

    assert injected.count('type="application/ld+json"') == 1
    assert injected.count('id="jsonld-seo"') == 1
    assert "Merge PDF" in injected


def test_ssr_body_injected_into_real_nonempty_root_template():
    """Regression guard for the prepaint-shell bug.

    The production template ships a NON-empty `<div id="root">` (a pre-hydration
    brand shell for LCP). The SSR body MUST still be injected into it. A
    bare-empty-root fixture hides this bug, so this test reads the REAL
    frontend/index.html template the backend serves in production.
    """
    from pathlib import Path

    index_html = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    template = index_html.read_text("utf-8")
    # Sanity: confirm the root is genuinely non-empty (the condition that broke
    # the old empty-root regex). If a future refactor empties it, that's fine —
    # the assertions below still guarantee the body ships.
    assert '<div id="root">' in template

    out = inject_seo(template, "/tool/merge-pdf")
    body = out.split("</head>", 1)[-1]
    assert "<h1" in body, "tool <h1> missing from SSR body — injection regex regressed"
    assert 'href="/tool/' in body, "internal tool links missing from SSR body"
    # The injected root must not be left empty.
    assert '<div id="root"></div>' not in out


def test_ssr_injects_into_built_dist_style_template():
    """Regression guard for the BUILT template shape.

    Production serves frontend/dist/index.html, where Vite hoists the entry
    `<script type="module">` into <head> and the only script AFTER `<div id="root">`
    is a plain inline `<script>`. An injector that anchors on a type="module"
    script following root matches the source index.html but NOT the built file —
    which shipped an empty SSR body to production. This fixture mirrors the built
    structure exactly.
    """
    # Mirrors the real built dist/index.html: entry module script hoisted to
    # <head>, and an HTML COMMENT (not a script) immediately follows root. Both
    # earlier regex anchors (type="module"-after-root, then any-script-after-root)
    # failed on this exact shape and shipped an empty body to production.
    template = (
        "<html><head><title>x</title>"
        '<meta name="robots" content="index,follow" />'
        '<script type="module" crossorigin src="/assets/index-abc123.js"></script>'
        "</head><body>"
        '<div id="prepaint-brand" aria-hidden="true">Privatools</div>'
        '<div id="root">\n'
        '      <div style="min-height:100vh;background:#0b0b0c">\n'
        "        <header><span>Privatools</span></header>\n"
        "      </div>\n"
        "    </div>\n"
        "    <!-- Service worker registration lives in src/lib/sw-register.ts -->\n"
        '    <script nonce="z">/* analytics */</script>'
        "</body></html>"
    )
    out = inject_seo(template, "/tool/merge-pdf")
    body = out.split("</head>", 1)[-1]
    assert "<h1" in body, "SSR body not injected into built-dist-style template"
    assert 'href="/tool/' in body, "internal tool links missing from built-style body"
    assert "min-height:100vh" not in body, "prepaint shell not replaced by SSR content"
    assert '<div id="root"></div>' not in out
    # The comment and trailing script after root must survive intact.
    assert "sw-register.ts" in out and 'nonce="z"' in out


def test_unknown_path_is_noindex_and_not_self_canonical():
    """A 404/unknown route must be noindex and must NOT self-canonicalize
    (self-canonical on a missing URL is the classic Soft-404 trigger). Uses the
    real template so the robots-meta and canonical handling match production."""
    from pathlib import Path

    index_html = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    template = index_html.read_text("utf-8")
    out = inject_seo(template, "/tool/this-slug-does-not-exist-zzz")
    assert 'content="noindex,nofollow"' in out
    assert 'rel="canonical"' not in out, "404/unknown path must not emit a canonical"


def test_tools_hub_is_known_and_renders_full_directory():
    """The /tools hub must be a known route that server-renders crawlable links
    to both PDF (/tool/) and non-PDF (/tools/) tools, plus CollectionPage JSON-LD."""
    from pathlib import Path

    assert seo_meta.path_is_known("/tools")
    index_html = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    template = index_html.read_text("utf-8")
    out = inject_seo(template, "/tools")
    body = out.split("</head>", 1)[-1]
    assert "<h1>All Free Online Tools</h1>" in body
    assert 'href="/tool/merge-pdf"' in body
    assert 'href="/tools/jwt-decoder"' in body
    assert '"CollectionPage"' in out
    # canonical points at the hub itself
    assert 'rel="canonical" href="https://privatools.me/tools"' in out


def test_tool_body_matches_visible_blocks_in_order():
    """The trimmed SSR body keeps only current blocks, in the order the visible page renders them.

    Related-tools content itself (which tools, in which order) is pinned
    exhaustively by test_related_tools_and_blog_links_match_client_construction
    below — this test only guards structure/ordering, so it no longer asserts
    on the related-tools slugs themselves.
    """
    body = seo_meta._build_ssr_content("/tool/merge-pdf", *seo_meta.get_meta_for_path("/tool/merge-pdf"))
    assert "compare-cta" not in body and "tool-depth" not in body and "TL;DR" not in body
    assert body.index('class="tool-steps"') < body.index('class="tool-faq"') < body.index("Last reviewed")


def test_related_tools_and_blog_links_match_client_construction():
    """Server related-tools and blog-link blocks must match the client's construction.

    `SkinApp.tsx` builds `related` as: same category, exclude self, sort by
    the registry `popularity` field ascending (stable, so equal popularity
    keeps registry order), first three. `postsForTool(slug, 4)` sorts
    mentioning posts by `publishedAt` descending and caps at four. Both are
    reconstructed here directly from the build-owned manifest/blog artifacts
    — the same source of truth the client's registry is generated from — for
    *every* tool, not a sample, and compared against what `_build_ssr_content`
    actually renders.
    """
    manifest = seo_meta._load_manifest(str(seo_meta._TOOL_JSON), seo_meta.blog_content_mtime_ns())
    assert manifest, "tool-content.json manifest not found — run `npm run build` in frontend/ first"
    rows = list(manifest.items())  # preserves the manifest's own iteration/tiebreak order

    checked_related = 0
    checked_guides = 0
    for slug, row in rows:
        category = row.get("category")
        candidates = [(s, r) for s, r in rows if s != slug and r.get("category") == category]
        candidates.sort(key=lambda item: item[1].get("popularity", 999))
        expected_related_hrefs = [r["path"] for _, r in candidates[:3]]

        title, description = seo_meta.get_meta_for_path(row["path"])
        body = seo_meta._build_ssr_content(row["path"], title, description)

        related_html = (
            body.split('class="tool-related"', 1)[1].split("</ul>", 1)[0]
            if 'class="tool-related"' in body
            else ""
        )
        actual_related_hrefs = re.findall(r'<li><a href="([^"]+)">', related_html)
        assert actual_related_hrefs == expected_related_hrefs, (
            f"{slug}: related tools must match the client's same-category popularity sort "
            f"(got {actual_related_hrefs}, expected {expected_related_hrefs})"
        )
        if expected_related_hrefs:
            checked_related += 1

        mentioning = seo_meta._tool_to_blogs().get(slug, [])
        assert len(mentioning) <= 4, f"{slug}: server blog links must be capped at 4 like postsForTool(slug, 4)"
        published = [post.get("publishedAt", "") for post in mentioning]
        assert published == sorted(published, reverse=True), f"{slug}: blog links must be newest-first"

        guide_html = (
            body.split('class="tool-guides"', 1)[1].split("</ul>", 1)[0]
            if 'class="tool-guides"' in body
            else ""
        )
        actual_guide_hrefs = re.findall(r'<li><a href="([^"]+)">', guide_html)
        assert actual_guide_hrefs == [f"/blog/{post['slug']}" for post in mentioning], (
            f"{slug}: rendered blog links must match _tool_to_blogs() order exactly"
        )
        if mentioning:
            checked_guides += 1

    # Sanity: the manifest actually exercises both branches, so a vacuous
    # pass (e.g. an empty/broken manifest) can't slip through.
    assert checked_related > 50, "expected most of the 221 tools to have same-category peers"
    assert checked_guides > 10, "expected multiple tools to have blog mentions capped by this test"


def test_tool_guide_text_and_names_are_html_escaped_in_ssr_body():
    """Hand-written guide prose and tool names can contain literal `<tag>`
    examples or a bare `&` — both must render as HTML entities in the SSR
    body, or the "literal tag" breaks the page's real markup for crawlers.
    JSON-LD is untouched by this (it is JSON, not HTML)."""
    body = seo_meta._build_ssr_content("/tools/gif-to-mp4", *seo_meta.get_meta_for_path("/tools/gif-to-mp4"))
    assert "&lt;video" in body
    assert "<video" not in body

    pdf_registry, _ = seo_meta._tool_registries()
    name = pdf_registry["header-footer"][0]
    assert "&" in name, "header-footer is the fixture for the bare-& regression; update this if its name changes"
    pdf_body = seo_meta._build_ssr_content("/tool/header-footer", *seo_meta.get_meta_for_path("/tool/header-footer"))
    assert escape(name) in pdf_body
    assert name not in pdf_body

    # _howto_name_for() feeds both the JSON-LD HowTo.name and this visible
    # <h2> — they must stay readable-text-identical modulo HTML escaping.
    assert f"<h2>{escape(seo_meta._howto_name_for(name))}</h2>" in pdf_body
