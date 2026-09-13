import { ArrowUpRight, Cpu, FileText, Image, KeyRound, Languages, MessageSquare, Mic, ScanText, Sparkles } from "lucide-react";
import { AiHubContent } from "@/components/byok/AiHubDialog";
import { StudioPage, StudioHeader } from "@/skins/experience/Studio";
import "@/skins/experience/secondary-pages.css";

const tasks = [
    { name: "Chat with PDF", detail: "Ask your document.", href: "/tool/chat-with-pdf", label: "Your provider", icon: MessageSquare },
    { name: "Summarize PDF", detail: "Find the important bits.", href: "/tool/summarize-pdf", label: "Device or provider", icon: FileText },
    { name: "Translate PDF", detail: "Make it your language.", href: "/tool/translate-pdf", label: "Device or provider", icon: Languages },
    { name: "Smart Redact", detail: "Keep personal details private.", href: "/tool/smart-redact", label: "Local detection · server apply", icon: ScanText },
    { name: "Transcribe Audio", detail: "Put your recording into words.", href: "/tools/transcribe-audio", label: "Device or provider", icon: Mic },
    { name: "Remove Background", detail: "Let your subject stand out.", href: "/tools/remove-background", label: "Device or server", icon: Image },
];

export default function AiPage() {
    return <StudioPage className="pt-ai-page">
        <StudioHeader kicker="AI studio" title={<>Your own <br />kind of AI.</>} description="Ask, translate, tidy up. Choose a helper and decide where it works."
            visual={<div className="pt-ai-route-art" aria-label="Choose between your device and an AI provider"><div className="pt-ai-art-star"><Sparkles size={54} strokeWidth={1.2} /></div><span className="pt-ai-art-device"><Cpu size={25} />On your device</span><span className="pt-ai-art-provider"><KeyRound size={25} />With your provider</span><p>You choose the company <br />your files keep.</p></div>} />
        <section className="pt-ai-task-section" aria-labelledby="ai-task-title"><div className="pt-section-title"><h2 id="ai-task-title">What shall we work on?</h2><p>Pick a task. Each tool explains its processing options.</p></div>
            <div className="pt-ai-task-shelf">{tasks.map((task,i) => <a className={`pt-ai-task pt-task-tone-${i%3}`} href={task.href} key={task.name}><span className="pt-ai-task-icon"><task.icon size={27} strokeWidth={1.5} /></span><span className="pt-ai-task-copy"><strong>{task.name}</strong><small>{task.detail}</small></span><ArrowUpRight className="pt-ai-task-arrow" size={17} /><span className="pt-ai-task-mode">{task.label}</span></a>)}</div>
        </section>
        <AiHubContent studio />
        <div className="pt-ai-bottom-note"><Sparkles size={23} /><p><strong>Smart tools. Considered choices.</strong> Provider pricing and terms apply when you connect your own key. Local models need a first download and enough storage.</p><a href="/trust">The privacy details<ArrowUpRight size={15} /></a></div>
    </StudioPage>;
}
