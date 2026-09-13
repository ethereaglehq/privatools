import { JOURNAL_TOPICS, journalDate, filterGuides, guideTopic } from "./blog-content";
import { useMemo, useState } from "react";
import { ArrowRight, ArrowUpRight, BookOpen, Clock3, Rss, Search, X } from "lucide-react";
import { blogPosts, type BlogPost } from "@/data/blog";
import { useExperience } from "@/lib/experience";
import "./blog-journal.css";
export function GuideCover({ post, compact = false }: { post: BlogPost; compact?: boolean }) {
  const topic = guideTopic(post);
  const marks: Record<string, [string, string]> = { Markdown: [".md", "<html>"], Accounts: ["@", "you"], Workflow: ["01", "03"], Comparison: ["A", "B"], AI: ["Aa", "?"], Privacy: ["file", "you"], PDF: ["PDF", "↗"] };
  const [first, second] = marks[topic] || ["Aa", "↗"];
  return <div className={`journal-cover journal-cover-${topic.toLowerCase()}`} data-compact={compact} aria-hidden="true"><span className="journal-cover-rule" /><span className="journal-cover-sheet"><b>{first}</b><i /><i /><i /></span><span className="journal-cover-note">{second}</span><span className="journal-cover-index">{topic}<i>↗</i></span></div>;
}
function GuideEntry({ post, index }: { post: BlogPost; index: number }) {
  return <article className="journal-entry"><a href={`/blog/${post.slug}`} className="journal-entry-link"><span className="journal-entry-number" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span><GuideCover post={post} compact /><div className="journal-entry-copy"><div className="journal-entry-meta"><span>{guideTopic(post)}</span><span>{post.readTime}</span></div><h3>{post.title}</h3><p>{post.description}</p><span className="journal-entry-open">Read the guide <ArrowUpRight size={16} /></span></div><ArrowUpRight className="journal-entry-arrow" size={20} /></a></article>;
}

/** Router-independent so the production Air/Play shell uses the same journal. */
export function BlogIndexContent({ tag, onTagChange }: { tag?: string; onTagChange?: (tag: string) => void } = {}) {
  const { experience } = useExperience();
  const [query, setQuery] = useState("");
  const [localTag, setLocalTag] = useState("");
  const topic = tag ?? localTag;
  const setTopic = (value: string) => { setLocalTag(value); onTagChange?.(value); };
  const sorted = useMemo(() => [...blogPosts].sort((a, b) => b.publishedAt.localeCompare(a.publishedAt) || a.title.localeCompare(b.title)), []);
  const filtered = useMemo(() => filterGuides(sorted, query, topic), [sorted, query, topic]);
  const featured = blogPosts.find(post => post.slug === "markdown-editor-to-html-guide") ?? sorted[0];
  const searching = Boolean(query.trim() || topic);
  const visible = !searching && featured ? filtered.filter(post => post.slug !== featured.slug) : filtered;
  const starters = ["where-your-files-go", "passkeys-and-optional-accounts", "batch-or-pipeline-how-to-choose"].map(slug => blogPosts.find(post => post.slug === slug)).filter((post): post is BlogPost => Boolean(post));
  const clear = () => { setQuery(""); setTopic(""); };
  return <div className="pt-journal journal-index">
    <header className="journal-masthead"><div className="journal-masthead-top"><p><BookOpen size={16} /> The PrivaTools journal</p><a href="/feed.xml" aria-label="Subscribe to the guides RSS feed"><Rss size={15} /> RSS</a></div><div className="journal-masthead-main"><h1>{experience === "air" ? <>A little know-how.<br /><span>A clearer next step.</span></> : <>Good things<br /><span>to know.</span></>}</h1><div><p>Practical notes for the files you’re working on. A little guidance, a useful check, and a better idea of what happens next.</p><span>{blogPosts.length} guides · written by PrivaTools</span></div></div></header>
    {!searching && featured && <section className="journal-opening" aria-label="Recommended reading"><a className="journal-feature" href={`/blog/${featured.slug}`}><div className="journal-feature-copy"><span className="journal-eyebrow">Start with what you have</span><h2>{featured.title}</h2><p>{featured.description}</p><div><span><Clock3 size={14} />{featured.readTime}</span><b>Open the guide <ArrowRight size={18} /></b></div></div><GuideCover post={featured} /></a><aside className="journal-start-here"><div className="journal-start-heading"><span className="journal-eyebrow">A few good starting points</span><h2>Worth knowing.</h2></div>{starters.map((post, index) => <a href={`/blog/${post.slug}`} key={post.slug}><span>0{index + 1}</span><div><p>{guideTopic(post)}</p><h3>{post.title}</h3></div><ArrowUpRight size={17} /></a>)}</aside></section>}
    <section className="journal-library" aria-labelledby="journal-library-title"><div className="journal-library-heading"><div><span className="journal-eyebrow">Find your next useful thing</span><h2 id="journal-library-title">The reading shelf.</h2></div><form role="search" onSubmit={event => event.preventDefault()} className="journal-search"><Search size={19} /><input type="search" aria-label="Search guides" placeholder="Markdown, privacy, a smaller PDF…" value={query} onChange={event => setQuery(event.target.value)} />{query && <button type="button" aria-label="Clear guide search" onClick={() => setQuery("")}><X size={17} /></button>}</form></div>
      <nav className="journal-topics" aria-label="Guide topics"><button type="button" aria-pressed={!topic} onClick={() => setTopic("")}>Everything <span>{blogPosts.length}</span></button>{JOURNAL_TOPICS.map(value => <button type="button" key={value} aria-pressed={topic === value} onClick={() => setTopic(topic === value ? "" : value)}>{value}<span>{blogPosts.filter(post => post.tags.includes(value)).length}</span></button>)}</nav>
      <div className="journal-results-line"><p role="status">{filtered.length} {filtered.length === 1 ? "guide" : "guides"}{topic ? ` about ${topic.toLowerCase()}` : " to explore"}{query.trim() ? ` matching “${query.trim()}”` : ""}{!searching ? " · latest first" : ""}</p>{searching && <button type="button" onClick={clear}>Clear filters <X size={14} /></button>}</div>
      {visible.length ? <div className="journal-entries">{visible.map((post, index) => <GuideEntry key={post.slug} post={post} index={index} />)}</div> : <div className="journal-empty"><Search size={28} /><h3>No guide matches that yet.</h3><p>Try a shorter phrase or another topic. You can also search the tools directly.</p><div><button type="button" onClick={clear}>Show all guides <ArrowRight size={16} /></button><a href="/tools">Explore the tools <ArrowUpRight size={16} /></a></div></div>}
    </section>
    <aside className="journal-editorial"><div><span className="journal-eyebrow">Behind these notes</span><h2>Useful, specific,<br />open to correction.</h2></div><div><p>These guides are written by PrivaTools, the project behind the tools. We describe the implementation we reviewed and link primary sources for external claims. Product comparisons are not independent lab benchmarks.</p><p>Each guide shows its review date. Features and service limits can change, so check the current workspace before running your task.</p><a href="/support">Suggest a correction <ArrowUpRight size={16} /></a></div></aside>
  </div>;
}
export default function BlogPage() { return <BlogIndexContent />; }
