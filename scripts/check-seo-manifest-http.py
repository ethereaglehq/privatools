#!/usr/bin/env python3
"""Read-only local HTTP release checks against generated editorial/public assets.

No credentials, browser, private dashboard, collection event or remote URL request.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import struct
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'frontend/public'
DIST = ROOT / 'frontend/dist'
CANONICAL = 'https://privatools.me'
PRIVATE = ['/account', '/account/sign-in', '/account/sign-up', '/account/settings', '/account/keys', '/settings', '/my-stuff', '/my-stuff/vault']
sha = lambda data: hashlib.sha256(data).hexdigest()


class Document(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.title = ''; self.metas = {}; self.links = []; self.anchors = []; self.times = []; self.graph = []; self.text = []
        self.in_title = False; self.json_script = False; self.script = ''
        self.feed(body)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'title': self.in_title = True
        if tag == 'meta': self.metas[attrs.get('name') or attrs.get('property')] = attrs.get('content')
        if tag == 'link': self.links.append(attrs)
        if tag == 'a': self.anchors.append(attrs.get('href'))
        if tag == 'time': self.times.append(attrs.get('datetime'))
        if tag == 'script' and attrs.get('type') == 'application/ld+json': self.json_script = True; self.script = ''

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.json_script:
            data = json.loads(self.script)
            self.graph.extend(data.get('@graph', [data]) if isinstance(data, dict) else data)
            self.json_script = False

    def handle_data(self, value):
        if self.in_title: self.title += value
        if self.json_script: self.script += value
        self.text.append(value)

    @property
    def canonical(self):
        return [entry.get('href') for entry in self.links if entry.get('rel') == 'canonical']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:8000')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/backend-integration/seo-manifest-http-checks.json')
    args = parser.parse_args()
    origin = urlsplit(args.base)
    if origin.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        raise SystemExit('This release harness is restricted to a local HTTP backend.')
    report = {'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'environment': args.base,
              'credentialsSubmitted': False, 'httpMethod': 'Read-only GET', 'deployed': False,
              'source': 'Generated public/build artifacts compared with actual local initial HTML/XML/binary responses', 'checks': [], 'sourceManifests': {}}

    def get(path):
        request = Request(args.base.rstrip('/') + path, headers={'User-Agent': 'PrivaTools-local-release-verifier/1.0'})
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, dict(response.headers), response.read()
        except HTTPError as error:
            return error.code, dict(error.headers), error.read()

    def record(path, kind, assertions, details=None):
        report['checks'].append({'path': path, 'kind': kind, 'passed': all(assertions.values()), 'assertions': assertions, **(details or {})})

    manifests = {}
    for name in ['blog-content.json', 'compare-content.json', 'tool-content.json']:
        raw = (PUBLIC / name).read_bytes(); built = (DIST / name).read_bytes()
        manifests[name] = json.loads(raw)
        report['sourceManifests'][name] = {'entries': len(manifests[name]), 'sha256': sha(raw), 'matchesBuiltArtifact': raw == built}
        record('/' + name, 'source/build consistency', {'publicMatchesBuild': raw == built})

    blogs, comparisons, tools = (manifests[n] for n in ['blog-content.json', 'compare-content.json', 'tool-content.json'])
    jobs = [(post, '/blog/' + post['slug'], 'BlogPosting') for post in blogs] + [(post, '/compare/' + post['slug'], 'Article') for post in comparisons]

    def editorial(job):
        item, path, expected_type = job
        status, _, raw = get(path); html = raw.decode(); doc = Document(html)
        entities = [entry for entry in doc.graph if entry.get('@type') == expected_type]
        article = entities[0] if len(entities) == 1 else {}
        expected_url = CANONICAL + path
        expected_sources = [(CANONICAL + s['url']) if s['url'].startswith('/') else s['url'] for s in item.get('sources', [])]
        reviewed = item.get('reviewedAt') or item.get('updatedAt') or item.get('publishedAt')
        assertions = {
            'http200': status == 200, 'exactTitle': doc.title == item['title'],
            'exactDescription': doc.metas.get('description') == item.get('description', item.get('summary', '')),
            'oneCanonical': doc.canonical == [expected_url], 'indexable': 'noindex' not in (doc.metas.get('robots') or ''),
            'oneArticleEntity': len(entities) == 1, 'exactHeadline': article.get('headline') == item['title'],
            'exactSchemaDescription': article.get('description') == item.get('description', item.get('summary', '')),
            'exactSchemaUrl': article.get('url') == expected_url,
            'exactReviewedDate': article.get('dateModified') == reviewed,
            'visibleReviewedDate': reviewed in doc.times,
            'exactCitations': article.get('citation') == expected_sources,
            'visibleSourceLinks': all(url in doc.anchors for url in expected_sources),
            'transparentAuthor': article.get('author', {}).get('@type') == 'Organization' and article.get('author', {}).get('name') == 'PrivaTools',
            'currentPublisherLogo': article.get('publisher', {}).get('logo', {}).get('url') == CANONICAL + '/brand/privatools-icon-512.png',
            'noInventedRating': not any('aggregateRating' in entry or entry.get('@type') == 'Review' for entry in doc.graph),
        }
        if expected_type == 'BlogPosting':
            assertions['exactPublishedDate'] = article.get('datePublished') == item.get('publishedAt')
            assertions['fullInitialArticleBody'] = item['body'].strip() in html
        else:
            visible = ' '.join(' '.join(doc.text).split())
            fields = item.get('choosePrivaTools', []) + item.get('chooseCompetitor', []) + item.get('tradeoffs', [])
            fields += [item.get('summary', '')]
            fields += [feature[key] for feature in item.get('features', []) for key in ['label', 'privatools', 'competitor']]
            assertions['fullInitialComparisonContent'] = all(' '.join(unescape(value).split()) in visible for value in fields)
        return path, expected_type, assertions, {'reviewedAt': reviewed, 'citations': len(expected_sources), 'httpStatus': status}

    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(editorial, jobs): record(*result)

    status, _, sitemap_raw = get('/sitemap.xml'); sitemap = ET.fromstring(sitemap_raw)
    urls = [entry.text for entry in sitemap.findall('{*}url/{*}loc')]
    expected_urls = [entry.text for entry in ET.fromstring((PUBLIC / 'sitemap.xml').read_bytes()).findall('{*}url/{*}loc')]
    expected_editorial = {CANONICAL + path for _, path, _ in jobs}
    record('/sitemap.xml', 'discovery', {'http200': status == 200, 'matchesSourceBytes': sitemap_raw == (PUBLIC / 'sitemap.xml').read_bytes(),
        'matchesSourceUrls': urls == expected_urls, 'uniqueUrls': len(urls) == len(set(urls)), 'allEditorialPresent': expected_editorial <= set(urls),
        'allToolsPresent': all(CANONICAL + tool['path'] in urls for tool in tools),
        'noPrivateRoutes': not any(urlsplit(url).path in PRIVATE for url in urls),
        'canonicalOriginAndCleanPaths': all(url.startswith(CANONICAL + '/') or url == CANONICAL for url in urls) and all(not urlsplit(url).query and not urlsplit(url).fragment for url in urls)}, {'urls': len(urls)})
    status, _, feed_raw = get('/feed.xml'); feed = ET.fromstring(feed_raw); items = feed.findall('./channel/item')
    record('/feed.xml', 'RSS', {'http200': status == 200, 'matchesSourceBytes': feed_raw == (PUBLIC / 'feed.xml').read_bytes(),
        'exactArticleCount': len(items) == len(blogs), 'allArticlesPresent': {i.findtext('link') for i in items} == {CANONICAL + '/blog/' + post['slug'] for post in blogs},
        'uniqueArticles': len({i.findtext('link') for i in items}) == len(items)}, {'items': len(items)})

    for path in PRIVATE:
        status, _, raw = get(path); doc = Document(raw.decode())
        record(path, 'private route', {'http200': status == 200, 'noindexFollow': doc.metas.get('robots') == 'noindex,follow', 'noCanonical': doc.canonical == [], 'notInSitemap': CANONICAL + path not in urls})
    for path in ['/ai', '/api', '/trust', '/tools/remove-background']:
        status, _, raw = get(path); doc = Document(raw.decode())
        record(path, 'public route', {'http200': status == 200, 'oneCanonical': doc.canonical == [CANONICAL + path], 'indexable': 'noindex' not in (doc.metas.get('robots') or '')})
    for path in ['/blog/privatools-release-check-missing', '/compare/privatools-release-check-missing', '/tools/privatools-release-check-missing', '/models/privatools-release-check-missing.onnx']:
        status, _, raw = get(path)
        assertions = {'genuine404': status == 404}
        if not path.startswith('/models/'):
            doc = Document(raw.decode()); assertions.update(noindex='noindex' in (doc.metas.get('robots') or ''), noCanonical=doc.canonical == [])
        record(path, 'negative route', assertions)

    status, _, home = get('/'); doc = Document(home.decode())
    sites = [item for item in doc.graph if item.get('@type') == 'WebSite']
    brand_links = [link.get('href') for link in doc.links if link.get('rel') in ['icon', 'apple-touch-icon']]
    record('/', 'site identity', {'http200': status == 200, 'preferredSiteName': any(item.get('name') == 'PrivaTools' for item in sites),
        'faviconSvg': '/brand/privatools-favicon.svg' in brand_links, 'faviconPng': '/brand/privatools-icon-96.png' in brand_links,
        'appleTouchIcon': '/brand/privatools-icon-180.png' in brand_links, 'runtimeAnalyticsOff': doc.metas.get('privatools:google-analytics') != 'enabled'})

    manifest_status, _, manifest_raw = get('/manifest.json'); manifest = json.loads(manifest_raw)
    record('/manifest.json', 'PWA identity', {'http200': manifest_status == 200, 'matchesSource': manifest_raw == (PUBLIC / 'manifest.json').read_bytes(),
        'name': manifest.get('short_name') == 'PrivaTools', 'standalone': manifest.get('display') == 'standalone',
        'fourPwaScreenshots': len(manifest.get('screenshots', [])) == 4, 'maskableIcon': any(i.get('purpose') == 'maskable' for i in manifest['icons'])})
    binary_paths = set(brand_links + ['/brand/privatools-icon-512.png', '/favicon.ico'])
    binary_paths.update(item['src'] for item in manifest.get('icons', []) + manifest.get('screenshots', []))
    binary_paths.update('/' + file.name for file in PUBLIC.glob('google*.html'))
    dimensions = {item['src']: item.get('sizes') for item in manifest.get('icons', []) + manifest.get('screenshots', [])}
    for path in sorted(binary_paths):
        status, headers, raw = get(path); source = (PUBLIC / path.lstrip('/')).read_bytes(); built = (DIST / path.lstrip('/')).read_bytes()
        assertions = {'http200': status == 200, 'matchesCurrentSource': raw == source, 'matchesBuiltArtifact': raw == built}
        if path.endswith('.png'):
            actual = struct.unpack('>II', raw[16:24]) if raw[:8] == b'\x89PNG\r\n\x1a\n' else (0, 0)
            assertions['validPng'] = actual != (0, 0)
            if dimensions.get(path): assertions['declaredDimensions'] = f'{actual[0]}x{actual[1]}' == dimensions[path]
        record(path, 'branding/verification asset', assertions, {'sha256': sha(raw), 'bytes': len(raw)})
    for path, mime in [('/models/u2netp.onnx', 'application/octet-stream'), ('/models/ort-wasm-simd-threaded.wasm', 'application/wasm'), ('/models/ort-wasm-simd-threaded.mjs', 'javascript'), ('/models/NOTICE.txt', 'text/plain')]:
        status, headers, raw = get(path); source = (PUBLIC / path.lstrip('/')).read_bytes()
        ctype = next((value for key, value in headers.items() if key.lower() == 'content-type'), '')
        record(path, 'same-origin model artifact', {'http200': status == 200, 'matchesReviewedSource': raw == source, 'expectedContentType': mime in ctype}, {'sha256': sha(raw), 'bytes': len(raw), 'contentType': ctype})
    status, headers, raw = get('/sw.js')
    cache = next((value for key, value in headers.items() if key.lower() == 'cache-control'), '')
    record('/sw.js', 'service worker', {'http200': status == 200, 'matchesBuiltWorker': raw == (DIST / 'sw.js').read_bytes(), 'onlyExpectedVersionSubstitution': re.sub(r'const CACHE_VERSION = \"[^\"]+\";', 'const CACHE_VERSION = \"v2.0.0\";', raw.decode(), count=1) == (PUBLIC / 'sw.js').read_text(), 'versionedBuild': 'const CACHE_VERSION = \"v2.0.0\";' not in raw.decode(), 'notImmutable': 'immutable' not in cache}, {'cacheControl': cache, 'sha256': sha(raw)})
    status, headers, raw = get('/api/analytics/policy'); policy = json.loads(raw)
    cache = next((value for key, value in headers.items() if key.lower() == 'cache-control'), '')
    record('/api/analytics/policy', 'safe runtime default', {'http200': status == 200, 'optIn': policy == {'mode': 'opt_in'}, 'privateNoStore': 'private' in cache and 'no-store' in cache})
    for name, info in report['sourceManifests'].items():
        record('/' + name, 'no build race', {'sourceUnchangedDuringRun': sha((PUBLIC / name).read_bytes()) == info['sha256'], 'buildStillMatchesSource': sha((DIST / name).read_bytes()) == info['sha256']})
    report['completedAtUtc'] = datetime.now(timezone.utc).isoformat()
    failed = [item for item in report['checks'] if not item['passed']]
    report['summary'] = {'passed': len(report['checks']) - len(failed), 'failed': len(failed), 'blogArticles': len(blogs), 'comparisonArticles': len(comparisons), 'canonicalSitemapUrls': len(urls), 'rssItems': len(items), 'privateRoutesNoindexFollow': len(PRIVATE)}
    report['limitations'] = ['Local HTTP proof only; not deployment, search indexing, Google-selected branding or GA ingestion.', 'No credentials, private dashboards, real user files, provider actions or model inference performed.', 'Binary hash/dimension checks establish correct release artifacts, not a new visual-design audit.']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        old = args.output.read_bytes(); backup = args.output.with_name(args.output.stem + '.previous-' + sha(old)[:12] + '.json')
        if not backup.exists(): shutil.copyfile(args.output, backup)
        report['previousReportPreserved'] = str(backup.relative_to(ROOT))
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'summary': report['summary'], 'failures': failed, 'report': str(args.output)}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
