"""Published frontend content is authoritative for metadata, SSR and discovery."""
import json
import os
import re
from xml.etree import ElementTree

import pytest

from backend.app import seo_meta as seo
from backend.app.routes import sitemap

SHELL = '<html><head><title>Old</title><meta name="robots" content="index,follow"><meta name="description" content="old"></head><body><div id="root"></div></body></html>'


@pytest.fixture
def manifests(tmp_path, monkeypatch):
    for name in ('BLOG', 'COMPARE', 'TOOL'):
        monkeypatch.setattr(seo, f'_{name}_JSON', tmp_path / f'{name.lower()}-content.json')
    monkeypatch.setattr(sitemap, 'GENERATED_SITEMAP', tmp_path / 'sitemap.xml')
    seo._load_manifest.cache_clear()
    seo._get_jsonld_for_path.cache_clear()
    sitemap._render_sitemap.cache_clear()
    def write(kind, rows, revision=1):
        path = getattr(seo, f'_{kind.upper()}_JSON')
        path.write_text(json.dumps(rows), encoding='utf-8')
        os.utime(path, ns=(revision * 1_000_000_000, revision * 1_000_000_000))
    return write


def article(**overrides):
    return {'slug': 'updated-guide', 'title': 'A current & useful guide', 'description': 'Current description.',
            'publishedAt': '2026-03-22', 'reviewedAt': '2026-09-14', 'body': '<h2>Real article</h2><p>Visible current body.</p>',
            'relatedTools': ['merge-pdf'], 'sources': [{'label': 'Source documentation', 'url': 'https://example.com/docs'}], **overrides}


def test_manifest_overrides_legacy_metadata_and_removes_unpublished_routes(manifests):
    row = article(slug='compress-pdf-without-losing-quality')
    manifests('blog', [row])
    assert seo.get_meta_for_path('/blog/' + row['slug']) == (row['title'], row['description'])
    assert not seo.path_is_known('/blog/merge-pdf-files-online-free')
    assert seo.get_jsonld_for_path('/blog/merge-pdf-files-online-free') is None
    html = seo.inject_seo(SHELL, '/blog/' + row['slug'])
    assert 'Visible current body' in html and 'Source documentation' in html
    assert '90%' not in html
    assert 'A current &amp; useful guide' in html
    assert '/tool/merge-pdf' in html


def test_blog_author_review_date_and_sources_match_visible_content(manifests):
    row = article()
    manifests('blog', [row])
    graph = seo.get_jsonld_for_path('/blog/updated-guide')['@graph']
    post = next(node for node in graph if node['@type'] == 'BlogPosting')
    assert post['author']['@type'] == 'Organization'
    assert post['author']['name'] == 'PrivaTools'
    assert post['dateModified'] == row['reviewedAt']
    assert post['datePublished'] == row['publishedAt']
    assert post['citation'] == [row['sources'][0]['url']]
    html = seo.inject_seo(SHELL, '/blog/updated-guide')
    assert row['reviewedAt'] in html and 'By PrivaTools' in html
    assert 'speakable' not in json.dumps(graph)


def test_empty_valid_manifest_is_authoritative_and_missing_manifest_falls_back(manifests):
    assert seo.path_is_known('/blog/merge-pdf-files-online-free')
    manifests('blog', [])
    assert not seo.path_is_known('/blog/merge-pdf-files-online-free')
    assert seo._blog_posts() == {}
    manifests('compare', {})
    assert not seo.path_is_known('/compare/ilovepdf')
    assert seo.get_jsonld_for_path('/compare/ilovepdf') is None


def test_comparison_source_is_article_without_fabricated_ratings(manifests):
    entry = {'slug': 'ilovepdf', 'name': 'iLovePDF', 'title': 'A reviewed comparison',
             'description': 'Current tradeoffs.', 'summary': 'Choose by workflow.',
             'reviewedAt': '2026-09-14', 'choosePrivaTools': ['Guest file tasks'],
             'chooseCompetitor': ['An existing team workflow'], 'tradeoffs': ['Review deployment needs'],
             'features': [{'label': 'Processing', 'privatools': 'Browser or server', 'competitor': 'See deployment docs', 'sourceUrl': 'https://example.com/processing'}],
             'sources': [{'label': 'Official docs', 'url': 'https://example.com/docs'}]}
    manifests('compare', [entry])
    assert not seo.path_is_known('/compare/smallpdf')
    schema = seo.get_jsonld_for_path('/compare/ilovepdf')
    assert schema['@graph'][0]['@type'] == 'Article'
    assert not any(term in json.dumps(schema) for term in ('reviewRating', 'ratingValue', 'itemReviewed', 'speakable'))
    body = seo._build_ssr_content('/compare/ilovepdf', *seo.get_meta_for_path('/compare/ilovepdf'))
    for text in ('Guest file tasks', 'An existing team workflow', 'Review deployment needs', 'See deployment docs', 'Official docs'):
        assert text in body
    assert 'No file size limits' not in body


def test_content_refresh_updates_metadata_schema_and_sitemap_without_restart(manifests):
    manifests('blog', [article()], 1)
    first = seo.get_jsonld_for_path('/blog/updated-guide')
    manifests('blog', [article(title='Updated again')], 2)
    assert seo.get_meta_for_path('/blog/updated-guide')[0] == 'Updated again'
    assert seo.get_jsonld_for_path('/blog/updated-guide')['@graph'][0]['headline'] == 'Updated again'
    assert first['@graph'][0]['headline'] != 'Updated again'
    manifests('compare', [{'slug': 'new-comparison', 'title': 'New comparison', 'name': 'Example'}], 3)
    assert '/compare/new-comparison' in sitemap._build_sitemap_xml().decode()
    assert '/compare/ilovepdf' not in sitemap._build_sitemap_xml().decode()


def test_jsonld_cannot_close_its_script_element(manifests):
    manifests('blog', [article(title='Literal </script><script>alert(1)</script>')])
    html = seo.inject_seo(SHELL, '/blog/updated-guide')
    assert html.count('<script') == 1
    payload = html.split('id="jsonld-seo">', 1)[1].split('</script>', 1)[0]
    assert '\\u003c/script>' in payload
    assert json.loads(payload)['@graph'][0]['headline'].startswith('Literal </script>')


def test_tool_manifest_drives_routes_and_descriptions_without_stale_tables(manifests):
    manifests('tool', [{'slug': 'merge-pdf', 'name': 'Merge PDF', 'description': 'A current summary',
                        'longDescription': 'Review and combine selected PDFs.', 'path': '/tool/merge-pdf'}])
    assert seo.path_is_known('/tool/merge-pdf')
    assert not seo.path_is_known('/tool/split-pdf')
    assert seo.get_meta_for_path('/tool/merge-pdf')[1] == 'Review and combine selected PDFs.'
    assert '/tool/split-pdf' not in sitemap._build_sitemap_xml().decode()


def test_sitemap_dates_do_not_change_with_request_day_and_private_pages_are_absent(manifests):
    manifests('blog', [article()])
    assert sitemap._build_sitemap_xml('2026-09-14') == sitemap._build_sitemap_xml('2030-01-01')
    body = sitemap._build_sitemap_xml().decode()
    root = ElementTree.fromstring(body)
    namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = {node.find('s:loc', namespace).text: node.findtext('s:lastmod', namespaces=namespace) for node in root}
    assert urls[seo.BASE_URL + '/blog/updated-guide'] == '2026-09-14'
    for path in seo.NOINDEX_PATHS:
        assert seo.BASE_URL + path not in urls
        assert 'noindex,follow' in seo.inject_seo(SHELL, path)
    assert seo.BASE_URL + '/api' in urls and seo.BASE_URL + '/ai' in urls


def test_valid_generated_sitemap_is_primary_and_stale_generated_routes_are_rejected(manifests):
    fallback = sitemap._build_sitemap_xml()
    # A fixture must not inherit review dates that are tomorrow in the UTC CI
    # runner's timezone. Exercise acceptance with an explicitly past date.
    root = ElementTree.fromstring(fallback)
    for lastmod in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod'):
        lastmod.text = '2000-01-01'
    valid = ElementTree.tostring(root)
    sitemap.GENERATED_SITEMAP.write_bytes(valid)
    assert sitemap._build_sitemap_xml() == valid
    stale = valid.replace(b'https://privatools.me/about', b'https://privatools.me/account/settings')
    sitemap.GENERATED_SITEMAP.write_bytes(stale)
    assert sitemap._build_sitemap_xml() == fallback


def test_home_and_tool_templates_do_not_promote_false_processing_or_unlimited_claims(manifests):
    for path in ('/', '/tools', '/tool/merge-pdf', '/tools/image-compressor', '/about'):
        output = seo.inject_seo(SHELL, path)
        assert 'no daily quota' not in output.lower()
        assert 'only free PDF suite' not in output
        assert 'no third-party AI APIs' not in output
        assert 'no outbound calls' not in output
        assert '"speakable"' not in output


def test_home_brand_name_and_publisher_logo_are_consistent(manifests):
    manifests('blog', [article()])
    graph = seo.get_jsonld_for_path('/')['@graph']
    websites = [node for node in graph if node.get('@type') == 'WebSite']
    assert len(websites) == 1
    assert websites[0]['name'] == 'PrivaTools'
    assert websites[0]['alternateName'] == ['Priva Tools', 'PrivaTools.me']
    organization = next(node for node in graph if node.get('@type') == 'Organization')
    expected_logo = 'https://privatools.me/brand/privatools-icon-512.png'
    assert organization['logo']['url'] == expected_logo
    assert websites[0]['publisher']['logo']['url'] == expected_logo
    assert seo._organization()['logo']['url'] == expected_logo
    html = seo.inject_seo(SHELL, '/')
    assert 'property="og:site_name" content="PrivaTools"' in html
    assert '/icons/icon-512.png' not in html


def test_internal_editorial_sources_are_visible_and_canonical(manifests):
    row = article()
    row['sources'] = [
        {'label': 'Processing disclosure', 'url': '/trust'},
        {'label': 'Privacy', 'url': '/privacy'},
        {'label': 'Invalid scheme', 'url': 'javascript:alert(1)'},
        {'label': 'Network-relative URL', 'url': '//other.example'},
    ]
    manifests('blog', [row])
    output = seo.inject_seo(SHELL, '/blog/updated-guide')
    for path in ('/trust', '/privacy'):
        assert f'href="https://privatools.me{path}"' in output
    assert 'javascript:alert' not in output
    assert '//other.example' not in output
    graph = seo.get_jsonld_for_path('/blog/updated-guide')['@graph']
    post = next(node for node in graph if node.get('@type') == 'BlogPosting')
    assert post['citation'] == ['https://privatools.me/trust', 'https://privatools.me/privacy']


def test_fallback_sitemap_emits_priority_from_the_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(sitemap, "GENERATED_SITEMAP", tmp_path / "missing.xml")
    sitemap._render_sitemap.cache_clear()
    body = sitemap._build_sitemap_xml("2026-09-18").decode("utf-8")
    assert "<loc>https://privatools.me/tool/merge-pdf</loc><lastmod>" in body
    assert body.count("<priority>") == body.count("<url>")
    assert "<loc>https://privatools.me</loc><lastmod>2026-09-14</lastmod><priority>1.0</priority>" in body
    # Priority comes from the manifest's own per-tool value (sitemap-priority.json's
    # highPriorityTools for merge-pdf, the 0.6 default for reverse-pdf) — not a
    # blanket tool-path constant. The lastmod literal is deliberately not pinned.
    assert re.search(
        r"<loc>https://privatools\.me/tool/merge-pdf</loc><lastmod>[^<]*</lastmod><priority>0\.8</priority>",
        body,
    )
    assert re.search(
        r"<loc>https://privatools\.me/tool/reverse-pdf</loc><lastmod>[^<]*</lastmod><priority>0\.6</priority>",
        body,
    )


def test_fallback_sitemap_shows_each_tools_own_review_date(tmp_path, monkeypatch):
    """Two tools with different manifest lastReviewed values must each keep
    their own date in the fallback sitemap — not a shared/static one."""
    manifest = {
        "merge-pdf": {"slug": "merge-pdf", "name": "Merge PDF", "path": "/tool/merge-pdf",
                      "description": "Combine PDFs", "lastReviewed": "2026-08-02"},
        "split-pdf": {"slug": "split-pdf", "name": "Split PDF", "path": "/tool/split-pdf",
                      "description": "Split PDFs", "lastReviewed": "2026-09-01"},
    }
    path = tmp_path / "tool-content.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(seo, "_TOOL_JSON", path)
    seo._load_manifest.cache_clear()
    monkeypatch.setattr(sitemap, "GENERATED_SITEMAP", tmp_path / "missing-sitemap.xml")
    sitemap._render_sitemap.cache_clear()

    body = sitemap._build_sitemap_xml().decode("utf-8")
    assert "<loc>https://privatools.me/tool/merge-pdf</loc><lastmod>2026-08-02</lastmod>" in body
    assert "<loc>https://privatools.me/tool/split-pdf</loc><lastmod>2026-09-01</lastmod>" in body
