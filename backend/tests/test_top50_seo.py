import re

from backend.app import seo_meta


def _top_tool_paths(limit: int = 50) -> list[tuple[str, str]]:
    """The `limit` tools with the lowest registry `popularity`, read from the
    build manifest — the same ranks the client sorts by. The sort is stable,
    so equal ranks keep manifest order, like the client's registry sort."""
    manifest = seo_meta._load_manifest(str(seo_meta._TOOL_JSON), seo_meta.blog_content_mtime_ns())
    assert manifest, "tool-content.json manifest not found — run `npm run build` in frontend/ first"
    ranked = sorted(manifest.values(), key=lambda row: row.get("popularity", 999))
    return [(row["slug"], row["path"]) for row in ranked[:limit]]


def _word_count(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html)
    return len(re.findall(r"\w+", text))


def _jsonld_types(path: str) -> set[str]:
    jsonld = seo_meta.get_jsonld_for_path(path)
    assert jsonld is not None
    types: set[str] = set()
    for node in jsonld.get("@graph", []):
        value = node.get("@type")
        if isinstance(value, list):
            types.update(str(item) for item in value)
        elif value:
            types.add(str(value))
    return types


def test_top_50_tool_pages_have_required_geo_content():
    top = _top_tool_paths()
    assert len(top) == 50, "a truncated manifest would let this pass on a handful of pages"

    missing: list[str] = []
    for slug, path in top:
        body = seo_meta._build_ssr_content(path, *seo_meta.get_meta_for_path(path))
        types = _jsonld_types(path)
        checks = {
            "150_words": _word_count(body) >= 150,
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
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            missing.append(f"{slug} ({path}): {', '.join(failed)}")

    assert not missing, "Top-50 SEO/GEO coverage gaps:\n" + "\n".join(missing)
