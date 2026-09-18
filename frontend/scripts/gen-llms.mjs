// One source feeds visible pages, server-rendered articles, sitemap, RSS, and
// the optional LLM reference. llms.txt is a convenience, not a ranking signal.
// The outputs are committed and CI fails when a fresh run differs from them,
// so keep them deterministic: dates come from the content, never the clock.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readContentArray } from './content-data.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const BASE = 'https://privatools.me';
// Change only when the corresponding content is materially reviewed.
const SITE_REVIEWED = '2026-09-14';
const { highPriorityTools } = JSON.parse(readFileSync(join(root, 'src/data/sitemap-priority.json'), 'utf8'));
const HIGH = new Set(highPriorityTools);
const priorityFor = path => path === '' ? 1 : path === '/tools' ? 0.9 : path.startsWith('/tool/') || path.startsWith('/tools/') ? (HIGH.has(path.split('/').pop()) ? 0.8 : 0.6) : path.startsWith('/blog') || path.startsWith('/compare') ? 0.5 : 0.4;
const read = (name, variable, ignored) => readContentArray(join(root, `src/data/${name}.ts`), variable, ignored);
const pdfTools = read('tools', '_toolsRaw', ['icon']);
const nonPdfTools = read('non-pdf-tools', '_nonPdfToolsRaw', ['icon']);
const blogPosts = read('blog', 'blogPosts').sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
const comparisons = existsSync(join(root, 'src/data/comparisons.ts')) ? read('comparisons', 'comparisons') : [];
const tools = [...pdfTools.map(t => ({ ...t, path: `/tool/${t.slug}` })), ...nonPdfTools.map(t => ({ ...t, path: `/tools/${t.slug}` }))];
const total = tools.length;
const xml = value => String(value).replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[c]);
const modified = post => post.reviewedAt || post.updatedAt || post.publishedAt || SITE_REVIEWED;
const write = (name, content) => writeFileSync(join(root, `public/${name}`), content);

const facts = `PrivaTools offers ${total} tools for PDFs, images, video, audio, documents, archives, and developer tasks. The source is MIT-licensed and can be self-hosted.

## Processing and accounts

- Everyday tools and downloads are available without signing in. Accounts manage identity and developer API keys.
- Processing depends on the tool: browser-only utilities keep the input on the device; server tools upload files for isolated temporary processing in temporary per-request storage.
- Server cleanup is designed to remove temporary input and output after the response, with a background sweep for leftover files. This is a cleanup policy, not a claim of forensic erasure or instantaneous cleanup after every failure.
- AI Studio offers on-device models and user-selected external providers. Provider mode sends the selected content to that provider and may incur its own charges. Smart Redact detects locally, then uploads the PDF and approved terms to apply redactions.
- The current Vault, saved signatures, and tool preferences are browser-local. Signing in does not sync them across devices or back them up.
- Public processing has file-size, rate, resource, and tool-specific limits. Available native codecs and AI models depend on the deployment. Self-hosting has its own infrastructure costs.
- PrivaTools does not add a promotional watermark to downloads. Watermark tools add marks only when requested.
- Public pages use Google Analytics, on by default, for page visits, sessions, engagement and tool runs: which tool, how it ran, how many files and whether it succeeded. It receives no file contents, filenames, document text or account identity; advertising features and Google Signals are off. Visitors can turn analytics off on the privacy page.

## Authoritative pages

- [All tools](${BASE}/tools): Browse the current catalogue and each tool's processing notice.
- [Trust center](${BASE}/trust): Understand local, server, and provider processing.
- [Privacy](${BASE}/privacy): File handling, account data, and telemetry.
- [Security](${BASE}/security): Security boundaries and reporting.
- [Developer API](${BASE}/api): API access and key management.
- [API operation catalog](https://api.privatools.me/api/v1/operations): Public machine-readable operations, request fields, response media types, current costs, limits, and async availability. Browser-only website tools are listed as unavailable through HTTP.
- [Versioned OpenAPI](https://api.privatools.me/api/v1/openapi.json): The public v1 contract for developer and AI/workflow integrations. Processing requires a PrivaTools API key; discovery does not.
- [About](${BASE}/about): Project context and source code.
- [Source code](https://github.com/ethereaglehq/privatools): Implementation and issue tracker.
`;

let index = `# PrivaTools\n\n> Free file tools with explicit processing choices and optional accounts.\n\n${facts}\n## Tool directory\n`;
for (const tool of tools) index += `\n- [${tool.name}](${BASE}${tool.path}): ${tool.description}`;
index += `\n\n## Guides\n\n- [PrivaTools Journal](${BASE}/blog): Practical guides, limitations, and sources.\n`;
for (const post of blogPosts) index += `\n- [${post.title}](${BASE}/blog/${post.slug}): ${post.tldr || post.description}`;
index += `\n\n## Comparisons\n\n- [Compare file tools](${BASE}/compare): Choose by workflow, processing location, and trade-offs.\n`;
for (const comparison of comparisons) index += `\n- [PrivaTools and ${comparison.name}](${BASE}/compare/${comparison.slug}): ${comparison.description || comparison.summary}`;
write('llms.txt', `${index}\n`);

let full = `# PrivaTools — Content Reference\n\nThis optional reference describes public product content. It contains no account records, uploads, or API credentials. It does not guarantee inclusion in any AI answer or search result.\n\n${facts}\n## Tool reference\n`;
for (const tool of tools) full += `\n### ${tool.name}\n\nURL: ${BASE}${tool.path}\n\n${tool.description}\n\n${tool.longDescription || ''}\n`;
full += '\n## Guides\n';
for (const post of blogPosts) {
  full += `\n### ${post.title}\n\nURL: ${BASE}/blog/${post.slug}\nPublished: ${post.publishedAt}\nReviewed: ${modified(post)}\n\n${post.tldr || post.description}\n\n${post.body}\n`;
  for (const source of post.sources || []) full += `\nSource: [${source.label}](${source.url})\n`;
}
write('llms-full.txt', full.replace(/[ \t]+$/gm, '').trimEnd() + '\n');
write('blog-content.json', JSON.stringify(blogPosts, null, 2));
write('compare-content.json', JSON.stringify(comparisons, null, 2));
for (const tool of tools) tool.priority = priorityFor(tool.path);
write('tool-content.json', JSON.stringify(tools, null, 2));

// "Mentioned in our guides" on a tool page: the newest four posts naming the
// tool, the selection postsForTool(slug, 4) makes and backend/app/seo_meta.py
// repeats for crawlers. Tool pages import this index, not the blog module,
// which is over a hundred kilobytes of article HTML. blogPosts is already
// newest-first and the sort is stable, so same-day posts keep blog.ts order
// here exactly as they do there. Committed; src/test/tool-blog-links.test.ts
// fails when it falls behind blog.ts.
const toolBlogLinks = {};
for (const post of blogPosts) for (const slug of new Set(post.relatedTools || [])) {
  const links = toolBlogLinks[slug] ||= [];
  if (links.length < 4) links.push({ slug: post.slug, title: post.title });
}
writeFileSync(join(root, 'src/data/tool-blog-links.json'), JSON.stringify(Object.fromEntries(Object.keys(toolBlogLinks).sort().map(slug => [slug, toolBlogLinks[slug]])), null, 2) + '\n');

// Personal state and authentication routes deliberately stay out of discovery.
const publicPages = ['', '/tools', '/about', '/trust', '/api', '/compare', '/pipeline', '/batch', '/blog', '/privacy', '/terms', '/security', '/support', '/status', '/ai'];
const entries = [
  ...publicPages.map(path => ({ path, lastmod: SITE_REVIEWED })),
  ...tools.map(tool => ({ path: tool.path, lastmod: tool.lastReviewed })),
  ...blogPosts.map(post => ({ path: `/blog/${post.slug}`, lastmod: modified(post) })),
  ...comparisons.map(comparison => ({ path: `/compare/${comparison.slug}`, lastmod: modified(comparison) })),
].map(entry => ({ ...entry, priority: priorityFor(entry.path) }));
const paths = new Set();
for (const entry of entries) {
  if (paths.has(entry.path)) throw new Error(`Duplicate sitemap path: ${entry.path}`);
  paths.add(entry.path);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.lastmod)) throw new Error(`Invalid review date: ${entry.path}`);
}
write('sitemap.xml', `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries.map(entry => `  <url><loc>${xml(BASE + entry.path)}</loc><lastmod>${entry.lastmod}</lastmod><priority>${entry.priority.toFixed(1)}</priority></url>`).join('\n')}\n</urlset>\n`);

const feed = blogPosts.map(post => `    <item><title>${xml(post.title)}</title><link>${BASE}/blog/${post.slug}</link><guid isPermaLink="true">${BASE}/blog/${post.slug}</guid><description>${xml(post.description)}</description><pubDate>${new Date(`${post.publishedAt}T12:00:00Z`).toUTCString()}</pubDate></item>`).join('\n');
write('feed.xml', `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>PrivaTools Journal</title><link>${BASE}/blog</link><description>Practical file guides, with processing details and sources.</description><language>en</language>\n${feed}\n</channel></rss>\n`);
console.log(`[content] ${total} tools, ${blogPosts.length} articles, ${comparisons.length} comparisons; ${entries.length} canonical sitemap URLs`);
