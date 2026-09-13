import { ArrowRight, ArrowUpRight, BookOpen, FileCheck2, FileText, Fingerprint, HardDrive, KeyRound, Laptop, LifeBuoy, LockKeyhole, Radio, Server, Shield, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";
import { StudioPage, StudioHeader, StudioAction } from "./Studio";
import "./secondary-pages.css";

const paths: { id: string; label: string; title: string; description: string; note: string; source: string; destination: string; icon: LucideIcon; href: string; link: string }[] = [
    {
        id: "local", label: "In this browser", title: "Some things can stay right here.",
        description: "Browser tools process your input on this device. Supported local AI models also run here after their first download.",
        note: "Examples: JSON formatting, text utilities and supported on-device AI. Each tool explains its options.",
        source: "Your device", destination: "Your result", icon: Laptop,
        href: "/tools/json-xml-formatter", link: "Try a browser tool",
    },
    {
        id: "server", label: "PrivaTools server", title: "A temporary trip for heavier work.",
        description: "Server tools upload files to PrivaTools for processing. The job’s temporary files are removed after the response.",
        note: "Examples: PDF merge and many document or media conversions. This is processing, not a cloud file library.",
        source: "Your file", destination: "PrivaTools", icon: Server,
        href: "/security", link: "Read about file handling",
    },
    {
        id: "provider", label: "Your chosen AI provider", title: "Your choice of model, directly.",
        description: "With your own AI key, requests go from this browser straight to the provider you select. Their pricing and data terms apply.",
        note: "A tool can combine paths: Smart Redact detects details locally or with your provider, then applies approved redactions on our server.",
        source: "Your browser", destination: "Your provider", icon: Sparkles,
        href: "/ai", link: "Explore your AI choices",
    },
];

const resources: { href: string; label: string; title: string; description: string; icon: LucideIcon }[] = [
    { href: "/security", label: "How it works", title: "Security", description: "File handling, the threat model and the limits of our protections.", icon: Shield },
    { href: "/privacy", label: "Your choices", title: "Privacy", description: "Storage, account data, analytics choices and third-party services.", icon: Fingerprint },
    { href: "/terms", label: "The agreement", title: "Terms", description: "What using PrivaTools means, in one place.", icon: BookOpen },
    { href: "/status", label: "Check right now", title: "Service status", description: "A live check of your connection, server access and offline readiness.", icon: Radio },
];

export default function TrustCenter() {
    const [selected, setSelected] = useState("local");
    const path = paths.find(item => item.id === selected)!;
    return <StudioPage className="pt-trust-page">
        <StudioHeader kicker={<><Shield size={16} /> The trust center</>} title={<>A clear view <br />of your privacy.</>} description="Your files deserve a clear explanation. Follow their journey, understand the choices, and stay in control." actions={<StudioAction href="/privacy" variant="secondary">Read our privacy policy</StudioAction>} visual={<div className="pt-trust-route-art"><FileCheck2 size={40} strokeWidth={1.3} /><span>Clarity, before <br />you start.</span></div>} />
        <section className="pt-trust-journey" aria-labelledby="processing-title">
            <div className="pt-trust-journey-intro"><p className="pt-workspace-caption">Follow the file</p><h2 id="processing-title">Where does <br />your work happen?</h2><p>A tool’s processing path matters. Each tool tells you where it runs.</p><div className="pt-trust-path-picker" aria-label="Explore processing paths">{paths.map(item => <button key={item.id} className={selected === item.id ? "is-selected" : ""} aria-pressed={selected === item.id} onClick={() => setSelected(item.id)}><item.icon size={21} strokeWidth={1.5} /><span>{item.label}</span><ArrowRight size={16} /></button>)}</div></div>
            <div className={`pt-trust-journey-detail pt-trust-${path.id}`}>
                <div className="pt-trust-route" aria-label={`${path.source} to ${path.destination}`}><div className="pt-trust-node"><span>{path.id === "server" ? <FileText size={30} strokeWidth={1.3} /> : <Laptop size={30} strokeWidth={1.3} />}</span><p>{path.source}</p></div><div className="pt-trust-connection" aria-hidden="true"><i /><ArrowRight size={19} /></div><div className="pt-trust-node"><span>{path.id === "local" ? <FileCheck2 size={30} strokeWidth={1.3} /> : <path.icon size={30} strokeWidth={1.3} />}</span><p>{path.destination}</p></div></div>
                <div className="pt-trust-path-copy" key={path.id}><p className="pt-workspace-caption">{path.label}</p><h3>{path.title}</h3><p>{path.description}</p><a href={path.href} className="pt-studio-link">{path.link} <ArrowUpRight size={16} /></a><p className="pt-trust-path-note">{path.note}</p></div>
            </div>
        </section>
        <section className="pt-trust-personal" aria-labelledby="device-title"><div className="pt-trust-personal-intro"><HardDrive size={26} strokeWidth={1.5} /><p className="pt-workspace-caption">This browser, this device</p><h2 id="device-title">A little memory. <br />Under your control.</h2><p>Preferences make the next visit easier. My Stuff shows what this browser remembers, with controls to export your setup or erase local data.</p><a href="/my-stuff" className="pt-studio-link">Open My Stuff <ArrowUpRight size={16} /></a></div><a href="/my-stuff/vault" className="pt-trust-personal-note pt-trust-vault"><LockKeyhole size={29} strokeWidth={1.4} /><h3>Your password vault</h3><p>Document passwords are encrypted with a key bound to this browser profile. Clearing site data erases them. They do not sync or leave in a setup export.</p><span>Manage saved passwords <ArrowUpRight size={16} /></span></a><a href="/ai" className="pt-trust-personal-note pt-trust-keys"><KeyRound size={29} strokeWidth={1.4} /><h3>Your AI connections</h3><p>Provider keys can be saved encrypted or kept for this session. They must be readable during a request, so use a browser profile you trust.</p><span>Manage AI settings <ArrowUpRight size={16} /></span></a></section>
        <section className="pt-trust-library" aria-labelledby="resource-title"><div className="pt-section-title"><div><p className="pt-workspace-caption">The details are open</p><h2 id="resource-title">Read, check, ask.</h2></div><a className="pt-studio-link" href="https://github.com/ethereaglehq/privatools" target="_blank" rel="noopener noreferrer">Explore the source <ArrowUpRight size={16} /></a></div><div className="pt-trust-resource-list">{resources.map(item => <a key={item.href} href={item.href}><item.icon size={24} strokeWidth={1.4} /><span><small>{item.label}</small><strong>{item.title}</strong></span><p>{item.description}</p><ArrowUpRight size={19} /></a>)}</div></section>
        <section className="pt-trust-support"><LifeBuoy size={35} strokeWidth={1.3} /><div><h2>Something unclear?</h2><p>We’re here to help. Describe the problem without sending private files.</p></div><a href="/support" className="pt-studio-button is-secondary">Get support <ArrowRight size={16} /></a></section>
        <p className="pt-trust-footnote">This overview describes current processing paths. The linked policies contain the full details.</p>
    </StudioPage>;
}
