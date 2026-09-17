import { useEffect, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { loadToolGuide, type ToolGuide as ToolGuideData } from "@/lib/tool-guide";

type GuideLink = { slug: string; title: string };

/** Steps, questions and related reading under the tool. Same text the server sends to crawlers. */
export function ToolGuide({ slug, name }: { slug: string; name: string }) {
    const [guide, setGuide] = useState<ToolGuideData | null>(null);
    const [links, setLinks] = useState<GuideLink[]>([]);
    useEffect(() => {
        let active = true;
        setGuide(null); setLinks([]);
        loadToolGuide(slug).then(data => { if (active) setGuide(data); });
        // The blog module is large; it becomes its own chunk and loads once.
        import("@/data/blog").then(({ postsForTool }) => { if (active) setLinks(postsForTool(slug, 4).map(post => ({ slug: post.slug, title: post.title }))); }).catch(() => {});
        return () => { active = false; };
    }, [slug]);
    if (!guide || (guide.howto.length === 0 && guide.faq.length === 0)) return null;
    return <div className="tw-guide" id="guide">
        {guide.howto.length > 0 && <section className="tw-guide-steps"><p className="tw-kicker">Step by step</p><h2>How to use {name}</h2><ol>{guide.howto.map(step => <li key={step.name}><strong>{step.name}</strong><span>{step.text}</span></li>)}</ol></section>}
        {guide.faq.length > 0 && <section className="tw-guide-questions"><p className="tw-kicker">Good to know</p><h2>Questions about {name}</h2>{guide.faq.map(item => <section key={item.q}><h3>{item.q}</h3><p>{item.a}</p></section>)}</section>}
        {links.length > 0 && <section className="tw-guide-links"><p className="tw-kicker">Read more</p><h2>Mentioned in our guides</h2><ul>{links.map(link => <li key={link.slug}><a href={`/blog/${link.slug}`}>{link.title} <ArrowUpRight size={15} /></a></li>)}</ul></section>}
    </div>;
}
