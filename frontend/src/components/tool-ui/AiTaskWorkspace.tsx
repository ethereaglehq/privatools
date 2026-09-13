import type { ReactNode } from "react";
import { ArrowUpRight, Cpu, ScanText } from "lucide-react";
import './SpecialistTools.css';
export function AiTaskWorkspace({kind, title, description, engine, phase, children}: {kind:string;title:string;description:string;engine:"local"|"byok"|"server";phase:string;children:ReactNode}) {
    const active = !["idle", "done", "review", "error"].includes(phase);
    return <section className={`pt-specialist pt-ai-workbench pt-ai-workbench-${kind}`} data-phase={phase} aria-busy={active}>
        <div className="pt-ai-workbench-intro"><div className="pt-ai-workbench-mark" aria-hidden="true"><ScanText size={25}/></div><div><h2>{title}</h2><p>{description}</p></div><span className="pt-ai-engine">{engine === "byok" ? <ArrowUpRight size={15}/> : <Cpu size={15}/>} {engine === "local" ? "On this device" : engine === "byok" ? "Your AI provider" : "Server processing"}</span></div>
        <div className="pt-ai-workbench-body">{children}</div>
    </section>;
}
