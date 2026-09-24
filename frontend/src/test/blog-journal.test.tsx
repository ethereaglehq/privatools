import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { blogPosts } from '@/data/blog';
import * as blogData from '@/data/blog';
import { toolBySlug } from '@/data/tools';
import { nonPdfToolBySlug } from '@/data/non-pdf-tools';
import { BlogIndexContent } from "@/pages/BlogPage";
import { filterGuides } from "../pages/blog-content";
import { BlogArticleContent } from "@/pages/BlogPostPage";
import { prepareBlogBody } from "../pages/blog-content";

const publishedSlugs = 'compress-pdf-without-losing-quality merge-pdf-files-online-free best-free-pdf-tools-2026 remove-password-from-pdf convert-word-to-pdf-free edit-pdf-online-free-no-sign-up split-pdf-online-free redact-pdf-free-guide best-free-online-pdf-editors-2026 ai-pdf-summarizer-browser-2026 ilovepdf-alternatives-2026 redact-pdf-permanently-guide online-pdf-tools-tracking-you heic-conversion-guide-2026 decode-jwt-tokens-safely-guide how-local-first-works what-deleted-means reading-privacy-policies privatools-vs-ilovepdf privatools-vs-smallpdf privatools-vs-sejda privatools-vs-ihatepdf chat-with-pdf-free-private ai-pdf-tools-no-upload-byok remove-background-without-uploading transcribe-audio-free-no-upload ocr-scanned-pdf-free-three-ways translate-pdf-free-private bring-your-own-ai-key-guide batch-process-files-free chatpdf-alternatives-private'.split(' ');
const newSlugs = 'markdown-editor-to-html-guide markdown-to-pdf-layout-checklist passkeys-and-optional-accounts where-your-files-go batch-or-pipeline-how-to-choose repeatable-document-workflow remove-bg-canva-alternative'.split(' ');
const markdown = blogPosts.find(post => post.slug === newSlugs[0])!;
const scrollIntoView = vi.fn();
beforeEach(() => {
  window.history.replaceState({}, '', '/blog/' + markdown.slug);
  HTMLElement.prototype.scrollIntoView = scrollIntoView;
  vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
  scrollIntoView.mockClear();
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('published journal content', () => {
  it('preserves every published URL and makes the new guides reachable', () => {
    const slugs = blogPosts.map(post => post.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
    expect(slugs).toEqual(expect.arrayContaining([...publishedSlugs, ...newSlugs]));
    const { container } = render(<BlogIndexContent />);
    const hrefs = [...container.querySelectorAll<HTMLAnchorElement>('a[href]')].map(link => link.getAttribute('href'));
    for (const slug of slugs) expect(hrefs).toContain('/blog/' + slug);
  });
  it('publishes attributed, reviewed summaries and valid related tool routes', () => {
    for (const post of blogPosts) {
      expect(post.author, post.slug).toBe('PrivaTools');
      expect(post.tldr?.length, post.slug).toBeGreaterThan(40);
      expect(post.reviewedAt, post.slug).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(Date.parse(post.reviewedAt!), post.slug).toBeGreaterThanOrEqual(Date.parse(post.publishedAt));
      expect(post.sources?.length, post.slug).toBeGreaterThan(0);
      for (const source of post.sources ?? []) {
        expect(source.label.trim(), post.slug).not.toBe('');
        expect(source.url, post.slug).toMatch(/^(https:\/\/|\/)/);
      }
      for (const slug of post.relatedTools ?? []) expect(Boolean(toolBySlug[slug] || nonPdfToolBySlug[slug]), `${post.slug}: ${slug}`).toBe(true);
      for (const [, slug] of post.body.matchAll(/href="\/blog\/([^"?#]+)/g)) expect(blogPosts.some(item => item.slug === slug), `${post.slug}: ${slug}`).toBe(true);
    }
  });
  it('distinguishes browser, service and external-provider processing in privacy guides', () => {
    const privacy = blogPosts.find(post => post.slug === 'where-your-files-go')!;
    expect(privacy.body).toMatch(/browser/i);
    expect(privacy.body).toMatch(/server|service/i);
    expect(privacy.body).toMatch(/provider/i);
    const background = blogPosts.find(post => post.slug === 'remove-background-without-uploading')!;
    expect(background.body).toMatch(/server.*default|default.*server/i);
    const chat = blogPosts.find(post => post.slug === 'chat-with-pdf-free-private')!;
    expect(chat.body).toMatch(/your own key/i);
    expect(chat.body).toMatch(/text.*provider|provider.*text/i);
  });
  it('dates the remove.bg migration notice and connects a real alternative workflow', () => {
    const guide = blogPosts.find(post => post.slug === 'remove-bg-canva-alternative')!;
    expect(guide.reviewedAt).toBe('2026-09-24');
    expect(guide.body).toContain('no longer be available from 1 December 2026');
    expect(guide.sources).toContainEqual({ label: 'remove.bg migration notice', url: 'https://www.remove.bg/faq' });
    expect(guide.body).toContain('href="/compare/remove-bg"');
    expect(guide.body).toContain('href="/tools/remove-background"');
    expect(guide.body).toContain('href="/blog/remove-background-without-uploading"');
    expect(guide.body).toContain('server engine uploads the image');
  });
});
describe('guide finding and reading', () => {
  it('combines words and topics, and gives a useful empty result', () => {
    expect(filterGuides(blogPosts, 'markdown HTML', 'Markdown').map(post => post.slug)).toContain(markdown.slug);
    expect(filterGuides(blogPosts, 'markdown HTML', 'Accounts')).toEqual([]);
    render(<BlogIndexContent />);
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search guides' }), { target: { value: 'nonexistent-article-zzq' } });
    expect(screen.getByText('No guide matches that yet.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Show all guides' }));
    expect(screen.getByRole('searchbox', { name: 'Search guides' })).toHaveValue('');
    fireEvent.click(within(screen.getByRole('navigation', { name: 'Guide topics' })).getByRole('button', { name: /^Accounts/ }));
    expect(screen.getByRole('status')).toHaveTextContent('about accounts');
    expect(document.querySelectorAll('.journal-entry')).toHaveLength(blogPosts.filter(post => post.tags.includes('Accounts')).length);
  });
  it('creates unique, shareable section addresses without replacing the application hash', () => {
    const result = prepareBlogBody('<h2>A &amp; B</h2><h3>A &amp; B</h3><h2>Résumé</h2>', 'guide');
    expect(result.headings.map(item => item.id)).toEqual(['a-b', 'a-b-2', 'resume']);
    expect(JSON.stringify(result.nodes)).toContain('"href":"/blog/guide?section=a-b-2"');
    expect(JSON.stringify(result.nodes)).not.toContain('"href":"#');
  });
  it('renders without Router context and makes TOC clicks focus a real heading', () => {
    window.history.replaceState({}, '', '/blog/' + markdown.slug + '#/blog/' + markdown.slug);
    render(<BlogArticleContent slug={markdown.slug} />);
    expect(screen.getByRole('heading', { level: 1, name: markdown.title })).toBeInTheDocument();
    expect(screen.getByText(markdown.tldr!)).toBeInTheDocument();
    const link = within(screen.getByRole('navigation', { name: 'Article contents' })).getAllByRole('link')[0];
    const id = new URL(link.getAttribute('href')!, window.location.origin).searchParams.get('section')!;
    fireEvent.click(link);
    expect(document.activeElement?.id).toBe(id);
    expect(new URL(window.location.href).searchParams.get('section')).toBe(id);
    expect(window.location.hash).toBe('#/blog/' + markdown.slug);
    expect(scrollIntoView).toHaveBeenCalled();
  });
  it('restores a direct link to source notes on mount', async () => {
    window.history.replaceState({}, '', '/blog/' + markdown.slug + '?section=sources-and-review');
    render(<BlogArticleContent slug={markdown.slug} />);
    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
    expect(within(screen.getByRole('navigation', { name: 'Article contents' })).getByRole('link', { name: 'Sources & review' })).toHaveAttribute('href', '/blog/' + markdown.slug + '?section=sources-and-review');
  });
  it('copies the real code example and reports a blocked clipboard honestly', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
    const { container } = render(<BlogArticleContent slug={markdown.slug} />);
    const example = container.querySelector('.journal-code code')?.textContent;
    expect(example).toBeTruthy();
    fireEvent.click(screen.getAllByRole('button', { name: 'Copy example' })[0]);
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(example));
    expect(await screen.findByRole('status')).toHaveTextContent('Example copied.');
    writeText.mockRejectedValueOnce(new Error('denied'));
    fireEvent.click(screen.getByRole('button', { name: 'Copy link' }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Copy was unavailable'));
  });
  it('handles an unknown address and then a known article without losing hook order', () => {
    const { rerender } = render(<BlogArticleContent slug="unknown-guide" />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('isn’t on the shelf');
    rerender(<BlogArticleContent slug={markdown.slug} />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(markdown.title);
  });
  it('renders article semantics while dropping active content, handler attributes and unsafe links', () => {
    vi.spyOn(blogData, 'getBlogPost').mockReturnValue({ ...markdown, body: '<h2 onclick="alert(1)">A &amp; <em>B</em></h2><script>alert(1)</script><svg onload="alert(1)"><a href="javascript:alert(1)">SVG</a></svg><iframe srcdoc="bad"></iframe><p style="background:url(https://example.invalid)"><img src=x onerror="alert(1)">Safe <strong>text</strong></p><a href="jav&#x61;script:alert(1)">Bad scheme</a><a href="//example.invalid">Remote path</a><a href="/\\example.invalid">Backslash path</a><a href="/tools/remove-background">Your tool</a><a href="https://example.com/guide">Reference</a><table><tbody><tr><th>Label</th><td>Value</td></tr></tbody></table><pre><code>&lt;img src=x onerror=alert(1)&gt;</code></pre>' });
    const { container } = render(<BlogArticleContent slug={markdown.slug} />);
    const prose = container.querySelector('.journal-prose')!;
    expect(prose.querySelector('script,svg,iframe,img,style,form,object')).toBeNull();
    expect(prose.querySelector('[onclick],[onerror],[onload],[style],[srcdoc]')).toBeNull();
    for (const text of ['Bad scheme', 'Remote path', 'Backslash path']) expect(within(prose as HTMLElement).getByText(text)).not.toHaveAttribute('href');
    expect(within(prose as HTMLElement).getByRole('link', { name: 'Your tool' })).toHaveAttribute('href', '/tools/remove-background');
    expect(within(prose as HTMLElement).getByRole('link', { name: 'Reference' })).toHaveAttribute('href', 'https://example.com/guide');
    expect(prose.querySelector('h2 em')).toHaveTextContent('B');
    expect(prose.querySelector('td')).toHaveTextContent('Value');
    expect(prose.querySelector('code')).toHaveTextContent('<img src=x onerror=alert(1)>');
    expect(within(prose as HTMLElement).getByRole('button', { name: 'Copy example' })).toBeInTheDocument();
  });
  it('preserves headings, article links and tables for every published guide', () => {
    const { container, rerender } = render(<BlogArticleContent slug={blogPosts[0].slug} />);
    for (const post of blogPosts) {
      rerender(<BlogArticleContent slug={post.slug} />);
      const original = new DOMParser().parseFromString(post.body, 'text/html');
      const prose = container.querySelector('.journal-prose')!;
      for (const tag of ['h2', 'h3', 'table', 'tr', 'th', 'td', 'pre', 'code']) expect(prose.querySelectorAll(tag).length, `${post.slug}: ${tag}`).toBe(original.querySelectorAll(tag).length);
      for (const anchor of original.querySelectorAll('a[href]')) expect([...prose.querySelectorAll('a:not([data-blog-heading])')].some(link => link.getAttribute('href') === anchor.getAttribute('href') && link.textContent === anchor.textContent), `${post.slug}: ${anchor.textContent}`).toBe(true);
    }
  });
  it('treats hostile section slugs as URL path text and decodes heading entities only as text', () => {
    const slug = 'guide"><img src=x onerror=alert(1)>';
    const result = prepareBlogBody('<h2>&lt;script&gt; &quot;Heading&quot;</h2>', slug);
    expect(result.headings[0].text).toBe('<script> "Heading"');
    const heading = result.nodes.find(node => typeof node !== 'string');
    expect(heading && typeof heading !== 'string' && heading.children[heading.children.length - 1]).toEqual({ tag: 'a', children: ['#'], section: 'script-heading', href: `/blog/${encodeURIComponent(slug)}?section=script-heading` });
    expect(result).not.toHaveProperty('html');
  });
});
