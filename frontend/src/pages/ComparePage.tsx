/** One sourced comparison directory and detail surface, shared by every skin. */
import { useDeferredValue, useEffect, useMemo, useState, type MouseEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, Check, Search, SlidersHorizontal } from "lucide-react";
import { comparisons, COMPARE_DIRECTORY_TITLE, type ProductComparison } from "@/data/comparisons";
import { TOTAL_TOOL_COUNT, TOOL_BREADTH_LABEL } from "@/data/site-stats";
import { StudioAction, StudioEmpty, StudioHeader, StudioPage } from "@/skins/experience/Studio";
import "@/skins/experience/comparison-studio.css";

const categories = ["All products", ...new Set(comparisons.map(comparison => comparison.category))];
const latestReview = comparisons.map(comparison => comparison.reviewedAt).sort().slice(-1)[0] ?? "";
function reviewDate(date: string) {
  return new Intl.DateTimeFormat("en", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`));
}

function jumpTo(id: string) {
  return (event: MouseEvent<HTMLAnchorElement>) => { event.preventDefault(); document.getElementById(id)?.scrollIntoView({ block: "start" }); };
}

function SourcesInline({ comparison, only }: { comparison: ProductComparison; only?: string }) {
  return <span className="cmp-inline-sources">{comparison.sources.map((source, index) => (!only || source.url === only) && <a key={source.url} href={source.url} target="_blank" rel="noreferrer" aria-label={`Official source ${index + 1}: ${source.label}`}>[{index + 1}]</a>)}</span>;
}

function ProcessingNote() {
  return <section className="cmp-processing-note" aria-labelledby="comparison-processing-title">
    <div><span className="cmp-eyebrow">The PrivaTools approach</span><h2 id="comparison-processing-title">Know where your task runs.</h2><p>{TOOL_BREADTH_LABEL}</p></div>
    <div><p>Browser tools process on your device. Hosted jobs run on our disclosed server. PrivaTools is also self-hostable on your own infrastructure.</p><p>File tools are free to use without an account. File, resource and rate limits still apply; external AI providers may charge for usage.</p><Link to="/trust" className="cmp-text-link">Read the processing details <ArrowRight size={15}/></Link></div>
  </section>;
}

export function ComparisonLinks() {
  return <nav className="cmp-related-links" aria-label="Detailed comparisons">{comparisons.map(comparison => <Link key={comparison.slug} to={`/compare/${comparison.slug}`}>{comparison.name}<ArrowUpRight size={15}/></Link>)}</nav>;
}

function ReviewNote({ date }: { date: string }) {
  return <p className="cmp-review-note"><BookOpen size={14}/><span>Checked <time dateTime={date}>{reviewDate(date)}</time> · By PrivaTools</span></p>;
}

export default function ComparePage({ competitorSlug }: { competitorSlug?: string } = {}) {
  const params = useParams<{ competitor: string }>();
  const slug = competitorSlug ?? params.competitor;
  const comparison = comparisons.find(item => item.slug === slug);
  useEffect(() => {
    document.title = comparison ? comparison.title : slug ? "Comparison not found · PrivaTools" : COMPARE_DIRECTORY_TITLE;
  }, [comparison, slug]);
  if (!slug) return <ComparisonDirectory/>;
  if (!comparison) return <StudioPage className="pt-comparison-page"><StudioEmpty title="That comparison isn’t here." description="Explore the published comparisons to find a product you’re considering."><StudioAction href="/compare">All comparisons <ArrowRight size={16}/></StudioAction></StudioEmpty></StudioPage>;
  return <ComparisonDetail comparison={comparison}/>;
}

function ComparisonDirectory() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [category, setCategory] = useState("All products");
  const [sort, setSort] = useState("name");
  const filtered = useMemo(() => {
    const search = deferredQuery.trim().toLocaleLowerCase();
    return comparisons.filter(item => (category === "All products" || item.category === category) && (!search || `${item.name} ${item.category} ${item.summary} ${item.highlights.join(" ")}`.toLocaleLowerCase().includes(search))).sort((a, b) => sort === "category" ? a.category.localeCompare(b.category) || a.name.localeCompare(b.name) : a.name.localeCompare(b.name));
  }, [deferredQuery, category, sort]);
  return <StudioPage className="pt-comparison-page cmp-directory">
    <StudioHeader kicker="Product comparisons" title={<>A good fit for<br/><em>your kind of work.</em></>} description="Start with the task, then choose the tool. Each comparison sets PrivaTools beside one product: its plans and limits, where files are processed, the account it needs and the platforms it runs on." visual={<div className="cmp-directory-mark"><span>Different workflows.</span><strong>{comparisons.length}<i>alternatives</i></strong><p>One considered choice.</p></div>}/>
    <div className="cmp-directory-intro"><p>Desktop editing, quick conversions, forms, signatures or your own server: each option has a place. Every fact about another product comes from its own official pages, with the page linked beside it, and each comparison ends with when to choose it and when to choose PrivaTools.</p><ReviewNote date={latestReview}/></div>
    <div className="cmp-directory-controls">
      <label className="cmp-search"><Search size={19}/><span className="sr-only">Search comparisons</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Find a product or workflow" type="search"/></label>
      <label className="cmp-sort"><SlidersHorizontal size={15}/><span>Sort</span><select aria-label="Sort comparisons" value={sort} onChange={event => setSort(event.target.value)}><option value="name">Name A–Z</option><option value="category">Workflow</option></select></label>
    </div>
    <div className="cmp-browse-layout">
      <aside className="cmp-workflow-filter"><h2>What matters today?</h2><div role="group" aria-label="Filter comparison workflows">{categories.map(value => <button type="button" key={value} aria-pressed={category === value} onClick={() => setCategory(value)}>{value}{category === value && <Check size={14}/>}</button>)}</div></aside>
      <section className="cmp-directory-results" aria-label="Product comparisons">
        <p className="cmp-result-count" role="status">{filtered.length} {filtered.length === 1 ? "comparison" : "comparisons"}{category !== "All products" && ` · ${category}`}</p>
        {filtered.length ? <div className="cmp-product-list">{filtered.map(item => <article key={item.slug} className="cmp-product-entry"><Link to={`/compare/${item.slug}`} className="cmp-product-link" aria-label={`Read PrivaTools vs ${item.name}`}><div className="cmp-product-title"><span className="cmp-eyebrow">{item.category}</span><h2>{item.name}</h2><p>{item.description}</p></div><div className="cmp-product-fit"><span>What sets it apart</span><ul>{item.highlights.map(point => <li key={point}>{point}</li>)}</ul></div><span className="cmp-product-open">Compare <ArrowUpRight size={19}/></span></Link></article>)}</div> : <div className="cmp-empty"><h2>No matching comparisons.</h2><p>Try another product name or explore the full list.</p><button type="button" className="cmp-text-link" onClick={() => { setQuery(""); setCategory("All products"); }}>Show all comparisons <ArrowRight size={15}/></button></div>}
      </section>
    </div>
    <section className="cmp-methodology"><span className="cmp-eyebrow">How to read these comparisons</span><h2>Useful differences, with the sources attached.</h2><p>We publish PrivaTools, so this is our editorial perspective. Plans, limits, processing locations and platforms for other products come only from their official pages, checked on the date shown; a fact we could not confirm there is left out. PrivaTools facts describe the current public service at privatools.me.</p><p>Prices are shown in the currency the vendor displayed to us and can differ by country, and plans change. We did not benchmark speed, output quality or accuracy. Review the current product page for the exact edition you need, and try a representative file before moving a regular workflow.</p></section>
    <ProcessingNote/>
  </StudioPage>;
}

function ComparisonDetail({ comparison }: { comparison: ProductComparison }) {
  const checked = reviewDate(comparison.reviewedAt);
  return <StudioPage className="pt-comparison-page cmp-detail">
    <nav className="cmp-breadcrumb" aria-label="Comparison breadcrumb"><Link to="/compare"><ArrowLeft size={15}/>All comparisons</Link><span>{comparison.category}</span></nav>
    <StudioHeader kicker="A closer look" title={<>PrivaTools <span className="cmp-versus">vs</span><br/><em>{comparison.name}</em></>} description={comparison.description} actions={<><StudioAction href="/tools">Explore PrivaTools <ArrowRight size={16}/></StudioAction><StudioAction variant="text" onClick={() => document.getElementById("comparison-sources")?.scrollIntoView({ block: "start" })}>See the sources <ArrowUpRight size={15}/></StudioAction></>}/>
    <div className="cmp-detail-reading">
      <aside className="cmp-reading-rail"><ReviewNote date={comparison.reviewedAt}/><p>Facts from official product pages.<br/>Practical editorial guidance.</p><nav aria-label="On this comparison"><a href="#comparison-details" onClick={jumpTo("comparison-details")}>Side by side</a><a href="#comparison-choices" onClick={jumpTo("comparison-choices")}>Choose by workflow</a><a href="#comparison-sources" onClick={jumpTo("comparison-sources")}>Official sources</a></nav></aside>
      <div className="cmp-detail-content">
        <section className="cmp-answer" aria-labelledby="comparison-answer"><span className="cmp-eyebrow">Start with your workflow</span><h2 id="comparison-answer">Where each one fits.</h2><p className="comparison-summary">{comparison.summary}</p></section>
        <section className="cmp-overview" aria-labelledby="comparison-overview"><span className="cmp-eyebrow">In its own words</span><h2 id="comparison-overview">About {comparison.name}.</h2>{comparison.overview.map(paragraph => <p key={paragraph}>{paragraph}</p>)}</section>
        <section className="cmp-details" id="comparison-details" aria-labelledby="comparison-details-title"><div className="cmp-section-intro"><span className="cmp-eyebrow">Side by side</span><h2 id="comparison-details-title">The facts that differ.</h2><p className="cmp-checked">Every {comparison.name} fact here was checked on <time dateTime={comparison.reviewedAt}>{checked}</time> against the official page linked beside it. PrivaTools facts describe the current public service.</p></div><div className="cmp-detail-rows">{comparison.features.map(feature => <article className="cmp-detail-row" key={feature.label}><h3>{feature.label}</h3><div><span className="cmp-row-product">PrivaTools</span><p>{feature.privatools}</p></div><div><span className="cmp-row-product">{comparison.name}</span><p>{feature.competitor} <SourcesInline comparison={comparison} only={feature.sourceUrl}/></p></div></article>)}</div></section>
        {comparison.sections.map((section, index) => <section className="cmp-deep" key={section.heading} aria-labelledby={`comparison-section-${index + 1}`}><h2 id={`comparison-section-${index + 1}`}>{section.heading}</h2>{section.body.map(paragraph => <p key={paragraph}>{paragraph}</p>)}</section>)}
        <section className="cmp-choices" id="comparison-choices" aria-label="Reasons to choose each product">
          <article className="cmp-choice cmp-choice-other"><span className="cmp-choice-caption">Another good direction</span><h2>Choose {comparison.name}<br/><em>when…</em></h2><ul>{comparison.chooseCompetitor.map(text => <li key={text}><ArrowUpRight size={16}/><span>{text}</span></li>)}</ul><SourcesInline comparison={comparison}/></article>
          <article className="cmp-choice cmp-choice-us"><span className="cmp-choice-caption">A fit for everyday file tasks</span><h2>Choose PrivaTools<br/><em>when…</em></h2><ul>{comparison.choosePrivaTools.map(text => <li key={text}><Check size={16}/><span>{text}</span></li>)}</ul><Link to="/tools" className="cmp-text-link">Explore {TOTAL_TOOL_COUNT} tools <ArrowRight size={15}/></Link></article>
        </section>
        <section className="cmp-tradeoffs" aria-labelledby="comparison-tradeoffs-title"><span className="cmp-eyebrow">Before you decide</span><h2 id="comparison-tradeoffs-title">A few details to keep in view.</h2><ul>{comparison.tradeoffs.map((text, index) => <li key={text}><span className="cmp-tradeoff-number" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span><p>{text}</p></li>)}</ul></section>
        {comparison.relatedLinks?.length ? <nav className="cmp-related-links" aria-label="Related tools and guides">{comparison.relatedLinks.map(link => <Link key={link.url} to={link.url}>{link.label}<ArrowUpRight size={15}/></Link>)}</nav> : null}
        <section className="cmp-sources" id="comparison-sources" aria-labelledby="comparison-sources-title"><div className="cmp-section-intro"><span className="cmp-eyebrow">The reading behind this page</span><h2 id="comparison-sources-title">Official sources.</h2></div><p>Checked on <time dateTime={comparison.reviewedAt}>{checked}</time>. These are {comparison.name}’s own descriptions of its product, not independent tests: we did not benchmark speed, output quality or accuracy. Choose-when notes are our editorial interpretation.</p><ol>{comparison.sources.map((source, index) => <li key={source.url}><span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span><a href={source.url} target="_blank" rel="noreferrer"><strong>{source.label}</strong><small>{new URL(source.url).hostname}</small><ArrowUpRight size={18}/></a></li>)}</ol><Link to="/support" className="cmp-text-link">Spotted something that changed? Tell us <ArrowRight size={15}/></Link></section>
      </div>
    </div>
    <ProcessingNote/>
    <section className="cmp-next"><div><span className="cmp-eyebrow">Keep exploring</span><h2>There’s more than one good choice.</h2></div><Link to="/compare" className="cmp-text-link">All comparisons <ArrowRight size={16}/></Link></section>
  </StudioPage>;
}
