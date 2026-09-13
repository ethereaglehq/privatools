import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowRight, Check, Copy, Laptop } from "lucide-react";
import './SpecialistTools.css';

/** Clipboard confirmation is based on the browser result, never the click. */
export function ToolCopyButton({ value, label = "Copy", className = "" }: { value: string; label?: string; className?: string }) {
    const [copied, setCopied] = useState(false);
    const [failed, setFailed] = useState(false);
    const alive = useRef(true);
    const timer = useRef<ReturnType<typeof setTimeout>>();
    useEffect(() => { alive.current = true; return () => { alive.current = false; clearTimeout(timer.current); }; }, []);
    useEffect(() => { setCopied(false); setFailed(false); }, [value]);
    async function copy() {
        try { await navigator.clipboard.writeText(value); if (!alive.current) return; setCopied(true); setFailed(false); clearTimeout(timer.current); timer.current = setTimeout(() => setCopied(false), 1800); }
        catch { if (alive.current) { setCopied(false); setFailed(true); } }
    }
    return <span className="pt-lab-copy"><button type="button" className={`pt-lab-button ${className}`} disabled={!value} onClick={() => void copy()}>{copied ? <Check size={15} /> : <Copy size={15} />}{copied ? "Copied" : label}</button>{failed && <span role="status">Copy unavailable. Select the result and copy it manually.</span>}</span>;
}

export function LabNote({ children }: { children: ReactNode }) {
    return <p className="pt-lab-note"><Laptop size={18} aria-hidden="true" /><span><strong>On your device</strong>{children}</span></p>;
}

export function LabWorkspace({ note, children, kind = "text" }: { note?: ReactNode; children: ReactNode; kind?: string }) {
    return <section className={`pt-specialist pt-specialist-${kind}`}>{note && <LabNote>{note}</LabNote>}{children}</section>;
}

export function LabPair({ input, output }: { input: ReactNode; output: ReactNode }) {
    return <div className="pt-lab-pair"><section className="pt-lab-input-pane">{input}</section><div className="pt-lab-direction" aria-hidden="true"><ArrowRight size={19}/></div><section className="pt-lab-output-pane">{output}</section></div>;
}

export function LabOutput({ value, label = "Result" }: { value: string; label?: string }) {
    return <pre className="pt-lab-output" tabIndex={0} aria-label={label}>{value || <span>Your result will appear here.</span>}</pre>;
}
