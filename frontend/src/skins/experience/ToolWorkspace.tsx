import { useState, type CSSProperties, type ElementType, type ReactNode } from "react";
import { ArrowLeft, ArrowRight, ArrowUpRight, CircleHelp, FileText, Laptop, Server, Sparkles, X } from "lucide-react";
import { FavoriteButton } from "../daylight/consumer/ConsumerChrome";
import { nonPdfTools } from "@/data/non-pdf-tools";
import { toolSeo } from "@/lib/tool-seo";
import { ToolGuide } from "./ToolGuide";
import "./tool-workspace.css";

type CatalogTool = { slug: string; name: string; description: string; category: string; accepts?: string; outputLabel?: string; byok?: boolean; clientOnly?: boolean; icon?: ElementType; seoTitle?: string; metaDescription?: string; longDescription?: string };
const NON_PDF_SLUGS = new Set(nonPdfTools.map(tool => tool.slug));

export function ToolWorkspace({ tool, categoryLabel, related, children, onFindTool }: {
    tool: CatalogTool; categoryLabel: string; related: CatalogTool[]; children: ReactNode; onFindTool: () => void;
}) {
    const [helpOpen, setHelpOpen] = useState(false);
    const Icon = tool.icon || FileText;
    const browserOrServer = tool.slug === "remove-background";
    const ProcessingIcon = tool.byok || browserOrServer ? Sparkles : tool.clientOnly ? Laptop : Server;
    const processing = browserOrServer ? "Browser or server · your choice" : tool.byok ? "Your choice of AI" : tool.clientOnly ? "Stays on your device" : "Temporary server processing";
    const tone = tool.category === "image" ? "image" : tool.category === "video-audio" ? "media" : tool.category === "developer" ? "code" : "pdf";
    return <article className="tw-workspace" data-tool={tool.slug} style={{ "--tw-tone": `var(--pt-${tone})`, "--tw-tone-ink": `var(--pt-${tone}-ink)` } as CSSProperties}>
        <div className="tw-wayfinding"><a href="/tools"><ArrowLeft size={15} /> All tools</a><span>{categoryLabel}</span><button type="button" onClick={onFindTool}>Find another tool <ArrowUpRight size={14} /></button></div>
        <header className="tw-heading"><div className="tw-heading-copy"><h1>{toolSeo(tool).h1}</h1><p className="tw-description">{tool.description}</p></div><span className="tw-tool-emblem" aria-hidden="true"><Icon size={48} strokeWidth={1.3} /><i /></span></header>
        <div className="tw-task-shelf"><div className="tw-processing"><ProcessingIcon size={16} /><span>{processing}</span><a href="/trust" aria-label="Learn where your file goes"><CircleHelp size={15} /></a></div><span className="tw-free">Free to use. No account needed.</span><div className="tw-utilities"><FavoriteButton slug={tool.slug} /><button type="button" onClick={() => setHelpOpen(open => !open)} aria-expanded={helpOpen} aria-controls="tw-help"><CircleHelp size={16} /> How it works</button></div></div>
        {helpOpen && <section className="tw-help" id="tw-help"><div className="tw-help-intro"><h2>Before you begin</h2><button type="button" className="ts-icon-button" aria-label="Close tool help" onClick={() => setHelpOpen(false)}><X size={17} /></button></div><dl><div><dt>Bring</dt><dd>{tool.accepts?.replace(/,/g, " · ") || "Text or supported files"}</dd></div><div><dt>Take away</dt><dd>{tool.outputLabel || "Your finished result"}</dd></div></dl><p>{browserOrServer ? "Choose where to process before running. On this device downloads the model and processes images in your browser. The default server engine uploads images for temporary processing. Both options work without an account or an AI provider key." : tool.byok ? "Review your AI settings before running. Your provider receives requests you choose to send; some document steps also use PrivaTools." : tool.clientOnly ? "Processing happens in this browser. Your input stays on this device." : "Files are uploaded only when you run the tool. PrivaTools processes them in temporary storage and removes the job’s files after the response."}</p><a href="/trust">Read about file handling <ArrowUpRight size={14} /></a></section>}
        <div className="tw-working-area"><div className="dl-toolui">{children}</div></div>
        <ToolGuide slug={tool.slug} name={tool.name} />
        <section className="tw-afterword"><div><p className="tw-kicker">Keep going</p><h2>What’s next for your file?</h2><a href="/tools">Explore all tools <ArrowRight size={17} /></a></div><div className="tw-related">{related.slice(0, 3).map(item => <a key={item.slug} href={`${NON_PDF_SLUGS.has(item.slug) ? "/tools" : "/tool"}/${item.slug}`}><span><strong>{item.name}</strong><small>{item.description}</small></span><ArrowUpRight size={20} /></a>)}</div></section>
    </article>;
}
