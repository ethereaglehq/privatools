import { type BlogHeading, prepareBlogBody } from "./blog-content";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, ArrowUp, ArrowUpRight, BookOpen, Check, Clock3, Link2, List, Printer } from "lucide-react";
import { getBlogPost, blogPosts } from "@/data/blog";
import { toolBySlug } from "@/data/tools";
import { nonPdfToolBySlug } from "@/data/non-pdf-tools";
import { useDocumentReader } from "@/skins/experience/useDocumentReader";
import { GuideCover } from "./BlogPage";
import { guideTopic, journalDate } from "./blog-content";
import "./blog-journal.css";
function toolFor(slug: string) {
  const tool = toolBySlug[slug];
  if (tool) return { name: tool.name, description: tool.description, href: `/tool/${slug}` };
  const other = nonPdfToolBySlug[slug];
  return other ? { name: other.name, description: other.description, href: `/tools/${slug}` } : null;
}

/** Also mounted directly by the class-based Air/Play shell, without Router context. */
export function BlogArticleContent({ slug }: { slug: string }) {
  const post = getBlogPost(slug);
  const prepared = useMemo(() => prepareBlogBody(post?.body ?? "", slug), [post?.body, slug]);
  const readerSections = useMemo(() => [...prepared.headings, { id: "sources-and-review" }], [prepared.headings]);
  const reader = useDocumentReader(readerSections);
  const [copyNotice, setCopyNotice] = useState("");
  const related = useMemo(() => (post?.relatedTools ?? []).map(toolFor).filter((tool): tool is NonNullable<ReturnType<typeof toolFor>> => Boolean(tool)), [post]);
  const next = useMemo(() => blogPosts.filter(item => item.slug !== post?.slug).map(item => ({ post: item, score: item.tags.filter(tag => post?.tags.includes(tag)).length })).sort((a, b) => b.score - a.score || b.post.publishedAt.localeCompare(a.post.publishedAt)).slice(0, 2).map(item => item.post), [post]);
  async function copy(value: string, label: string) {
    try { await navigator.clipboard.writeText(value); setCopyNotice(`${label} copied.`); }
    catch { setCopyNotice("Copy was unavailable. Select the text or copy the address from your browser."); }
  }
  if (!post) return <div className="pt-journal journal-missing"><BookOpen size={33} /><h1>This guide isn’t on the shelf.</h1><p>The address may have changed. All available guides are in the journal.</p><a href="/blog">Browse the guides <ArrowRight size={17} /></a></div>;
  const sectionHref = (id: string) => `/blog/${post.slug}?section=${encodeURIComponent(id)}`;
  return <div className="pt-journal journal-article-page">
    <div className="journal-reading-progress" role="progressbar" aria-label="Article reading progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(reader.progress)}><span style={{ transform: `scaleX(${reader.progress / 100})` }} /></div>
    <div className="journal-article-nav"><a href="/blog"><ArrowLeft size={16} />All guides</a><div><button type="button" onClick={() => void copy(window.location.href, "Article link")}><Link2 size={15} />Copy link</button><button type="button" onClick={() => window.print()}><Printer size={15} />Print</button></div></div>
    <header className="journal-article-header"><div><p className="journal-eyebrow">{guideTopic(post)} · A PrivaTools guide</p><h1>{post.title}</h1><p className="journal-article-description">{post.description}</p><div className="journal-byline"><a href="/about">By {post.author || "PrivaTools"}</a><span><Clock3 size={14} />{post.readTime}</span><span>Published <time dateTime={post.publishedAt}>{journalDate(post.publishedAt)}</time></span></div><p className="journal-reviewed"><Check size={13} />Content reviewed <time dateTime={post.reviewedAt || post.updatedAt || post.publishedAt}>{journalDate(post.reviewedAt || post.updatedAt || post.publishedAt)}</time></p></div><GuideCover post={post} compact /></header>
    <div className="journal-article-layout">
      <aside className="journal-outline"><details open><summary><List size={17} />On this page</summary><nav aria-label="Article contents">{prepared.headings.map(item => <a key={item.id} href={sectionHref(item.id)} data-level={item.level} aria-current={reader.activeId === item.id ? "location" : undefined} onClick={event => { event.preventDefault(); reader.scrollToHeading(item.id); }}>{item.text}</a>)}<a href={sectionHref("sources-and-review")} aria-current={reader.activeId === "sources-and-review" ? "location" : undefined} onClick={event => { event.preventDefault(); reader.scrollToHeading("sources-and-review"); }}>Sources &amp; review</a></nav></details><p className="journal-outline-note">Read a little.<br />Try it for yourself.</p></aside>
      <article ref={reader.articleRef} className="journal-article-paper">
        {post.tldr && <aside className="journal-answer" aria-labelledby="journal-answer-title"><span><BookOpen size={20} strokeWidth={1.5} /></span><div><h2 id="journal-answer-title">The short answer</h2><p>{post.tldr}</p></div></aside>}
        <div className="journal-prose blog-prose" onClick={event => { const target = event.target as HTMLElement; const link = target.closest<HTMLAnchorElement>("a[data-blog-heading]"); if (link?.dataset.blogHeading) { event.preventDefault(); reader.scrollToHeading(link.dataset.blogHeading); } const button = target.closest<HTMLButtonElement>("button[data-copy-code]"); if (button) void copy(button.parentElement?.querySelector("code")?.textContent || "", "Example"); }} dangerouslySetInnerHTML={{ __html: prepared.html }} />
        <section className="journal-sources" id="sources-and-review" tabIndex={-1}><p className="journal-eyebrow">A note on the evidence</p><h2>Sources &amp; review</h2><p>Written by PrivaTools. Product behaviour was checked against the current implementation on <time dateTime={post.reviewedAt || post.updatedAt || post.publishedAt}>{journalDate(post.reviewedAt || post.updatedAt || post.publishedAt)}</time>. External references support the specific claims linked in the guide; they do not certify this service or every possible output.</p>{Boolean(post.sources?.length) && <ul>{post.sources!.map(source => <li key={source.url}><a href={source.url} {...(source.url.startsWith("https://") ? { target: "_blank", rel: "noopener noreferrer" } : {})}>{source.label}<ArrowUpRight size={14} /></a></li>)}</ul>}<a className="journal-correction" href="/support">Something changed? Suggest a correction <ArrowUpRight size={15} /></a></section>
        <div className="journal-article-end"><span>Ready for the next step?</span><a href="/tools">Find your tool <ArrowRight size={17} /></a></div>
      </article>
      <aside className="journal-practice"><span className="journal-eyebrow">Put it into practice</span><h2>Your next step.</h2>{related.length ? related.map(tool => <a key={tool.href} href={tool.href}><div><h3>{tool.name}</h3><p>{tool.description}</p></div><ArrowUpRight size={17} /></a>) : <a href="/account/settings"><div><h3>{post.tags.includes("Accounts") ? "Account settings" : "Make the space yours"}</h3><p>Choose your appearance and review account access.</p></div><ArrowUpRight size={17} /></a>}<a className="journal-practice-trust" href="/trust">Understand the processing <ArrowUpRight size={15} /></a></aside>
    </div>
    <section className="journal-next" aria-labelledby="journal-next-title"><div><p className="journal-eyebrow">Keep a little curiosity</p><h2 id="journal-next-title">Something else<br />worth knowing.</h2><a href="/blog">All guides <ArrowRight size={16} /></a></div>{next.map(item => <a href={`/blog/${item.slug}`} key={item.slug}><span>{guideTopic(item)} · {item.readTime}</span><h3>{item.title}</h3><p>{item.description}</p><ArrowUpRight size={20} /></a>)}</section>
    {copyNotice && <p className="journal-copy-notice" role="status">{copyNotice}<button type="button" aria-label="Dismiss copy message" onClick={() => setCopyNotice("")}>×</button></p>}
    {reader.showTop && <button className="journal-back-top" type="button" onClick={reader.scrollToTop} aria-label="Back to article top"><ArrowUp size={19} /></button>}
  </div>;
}
export default function BlogPostPage() { const { slug = "" } = useParams<{ slug: string }>(); return <BlogArticleContent slug={slug} />; }
