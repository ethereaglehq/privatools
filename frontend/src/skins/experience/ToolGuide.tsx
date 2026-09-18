import { useEffect, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import type { ToolGuide as ToolGuideData } from "@/lib/tool-guide";
import { useToolBlogLinks } from "@/lib/tool-blog-links";

/** Steps, questions and related reading under the tool. Same text the server sends to crawlers. */
export function ToolGuide({ slug, name }: { slug: string; name: string }) {
    const [guide, setGuide] = useState<ToolGuideData | null>(null);
    const links = useToolBlogLinks(slug);
    useEffect(() => {
        let active = true;
        setGuide(null);
        // Dynamic: lib/tool-guide.ts globs every tool's JSON (~24 KB) so it
        // can lazy-load any one of them — that map must never sit in the
        // entry chunk, so it's imported here instead of at module scope.
        import("@/lib/tool-guide").then(({ loadToolGuide }) => loadToolGuide(slug)).then(data => { if (active) setGuide(data); }).catch(() => {});
        return () => { active = false; };
    }, [slug]);
    if (!guide || (guide.howto.length === 0 && guide.faq.length === 0)) return null;
    return <div className="tw-guide" id="guide">
        {guide.howto.length > 0 && <section className="tw-guide-steps"><p className="tw-kicker">Step by step</p><h2>How to use {name}</h2><ol role="list">{guide.howto.map((step, index) => <li key={step.name} id={`step-${index + 1}`}><strong>{step.name}</strong><span>{step.text}</span></li>)}</ol></section>}
        {guide.faq.length > 0 && <section className="tw-guide-questions"><p className="tw-kicker">Good to know</p><h2>Questions about {name}</h2>{guide.faq.map(item => <section key={item.q}><h3>{item.q}</h3><p>{item.a}</p></section>)}</section>}
        {links.length > 0 && <section className="tw-guide-links"><p className="tw-kicker">Read more</p><h2>Mentioned in our guides</h2><ul>{links.map(link => <li key={link.slug}><a href={`/blog/${link.slug}`}>{link.title} <ArrowUpRight size={15} /></a></li>)}</ul></section>}
    </div>;
}
