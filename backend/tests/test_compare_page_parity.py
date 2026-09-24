"""Comparison source, generated manifest and served discovery must agree."""
import json
import re
from html import escape
from pathlib import Path
from xml.etree import ElementTree

import pytest
from backend.app import seo_meta as seo
from backend.app.routes import sitemap

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'frontend/public'
SOURCE = ROOT / 'frontend/src/data/comparisons.ts'


@pytest.fixture
def comparisons(monkeypatch):
    path = PUBLIC / 'compare-content.json'
    assert path.exists(), 'Run frontend/scripts/gen-llms.mjs before the content checks'
    data = json.loads(path.read_text())
    assert data, 'A missing comparison artifact must not pass parity vacuously'
    monkeypatch.setattr(seo, '_COMPARE_JSON', path)
    monkeypatch.setattr(sitemap, 'GENERATED_SITEMAP', PUBLIC / 'sitemap.xml')
    return {row['slug']: row for row in data}


def test_generated_comparisons_cover_the_literal_source_without_orphans(comparisons):
    slugs = re.findall(r'slug:\s*["\']([a-z0-9-]+)["\']', SOURCE.read_text())
    assert slugs and len(slugs) == len(set(slugs))
    assert set(slugs) == set(comparisons)
    assert {'tinywow', 'ihatepdf'} <= set(slugs)


def test_metadata_ssr_and_structured_data_use_the_same_reviewed_entries(comparisons):
    for slug, row in comparisons.items():
        path = '/compare/' + slug
        assert seo.path_is_known(path)
        assert seo.get_meta_for_path(path) == (row['title'], row['description'])
        graph = seo.get_jsonld_for_path(path)['@graph']
        article = next(node for node in graph if node['@type'] == 'Article')
        assert article['dateModified'] == row['reviewedAt']
        assert article['citation'] == [source['url'] for source in row['sources']]
        assert 'reviewRating' not in json.dumps(graph)
        body = seo._build_ssr_content(path, *seo.get_meta_for_path(path))
        assert row['reviewedAt'] in body
        assert row['sources'][0]['url'] in body
    assert not seo.path_is_known('/compare/definitely-not-a-competitor')


def _words(html):
    return len(re.findall(r'\w+', re.sub(r'<[^>]+>', ' ', html)))


def test_server_rendered_comparisons_carry_the_whole_dated_page(comparisons):
    """Crawlers read the same sections the React page renders, not a stub.

    Five comparisons once rendered about 300 words on a shared template and
    Google folded them into /compare as duplicates."""
    for slug, row in comparisons.items():
        body = seo._build_ssr_content('/compare/' + slug, *seo.get_meta_for_path('/compare/' + slug))
        assert f'checked on <time datetime="{row["reviewedAt"]}">' in body
        headings = [f'Choose {row["name"]} when…', 'Choose PrivaTools when…', f'About {row["name"]}']
        headings += [section['heading'] for section in row['sections']]
        for text in headings + [feature['label'] for feature in row['features']]:
            assert escape(text) in body, f'{slug}: {text!r} is missing from the server-rendered page'
        for feature in row['features']:
            assert f'<a href="{escape(feature["sourceUrl"], quote=True)}">Source</a>' in body
        for link in row.get('relatedLinks') or []:
            assert f'href="{escape(link["url"], quote=True)}"' in body
        assert _words(body) >= 700, f'{slug} renders only {_words(body)} words'


def test_directory_links_every_comparison_with_its_distinguishing_points(comparisons):
    body = seo._build_ssr_content('/compare', *seo.get_meta_for_path('/compare'))
    for slug, row in comparisons.items():
        assert f'<a href="/compare/{slug}">{escape(row["title"])}</a>' in body
        for point in row['highlights']:
            assert escape(point) in body, f'{slug}: highlight {point!r} is missing from /compare'


def test_directory_title_matches_the_title_the_react_page_sets():
    title = re.search(r'COMPARE_DIRECTORY_TITLE\s*=\s*"([^"]+)"', SOURCE.read_text()).group(1)
    assert seo.get_meta_for_path('/compare')[0] == title


def _comparison_paths(xml):
    root = ElementTree.fromstring(xml)
    urls = [node.text for node in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    return {url.removeprefix(seo.BASE_URL + '/compare/') for url in urls if url.startswith(seo.BASE_URL + '/compare/')}


def test_generated_and_served_sitemaps_match_current_comparisons(comparisons):
    assert _comparison_paths((PUBLIC / 'sitemap.xml').read_bytes()) == set(comparisons)
    assert _comparison_paths(sitemap._build_sitemap_xml()) == set(comparisons)
