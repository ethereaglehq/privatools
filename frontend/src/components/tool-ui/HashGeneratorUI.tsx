import { type HashResult, hashBytes } from "./hash-bytes";
import { useCallback, useEffect, useRef, useState } from "react";
import { Hash, Loader2 } from "lucide-react";
import { useToolDefaults } from "@/hooks/useToolDefaults";
import { emitToolRun } from "@/lib/toolRun";
import { FileUploadZone } from "./FileUploadZone";
import { LabPair, LabWorkspace, ToolCopyButton } from "./SpecialistTools";

type Mode = "text" | "file";
const DEFAULTS: { mode: Mode } = { mode: "text" };
export function HashGeneratorUI() {
    const [config, , { setField }] = useToolDefaults("hash-generator", DEFAULTS);
    const { mode } = config;
    const [input, setInput] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [results, setResults] = useState<HashResult[]>([]);
    const [computing, setComputing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const generation = useRef(0);
    useEffect(() => () => { generation.current++; }, []);
    const invalidate = useCallback(() => { generation.current++; setResults([]); setError(null); setComputing(false); }, []);
    const run = async () => {
        if (computing || (mode === "file" && !file)) return;
        const current = ++generation.current;
        setComputing(true); setError(null); setResults([]);
        try {
            const bytes = mode === "file" ? await file!.arrayBuffer() : new TextEncoder().encode(input).buffer;
            const next = await hashBytes(bytes);
            if (generation.current === current) { setResults(next); emitToolRun({ outcome: "success" }); }
        } catch { if (generation.current === current) { setError("Couldn't calculate the hashes. Try a smaller file or a browser with Web Crypto support."); emitToolRun({ outcome: "error" }); } }
        finally { if (generation.current === current) setComputing(false); }
    };
    return <LabWorkspace kind="hash" note="SHA hashes are calculated by Web Crypto on this device. Files and text stay in your browser.">
        <LabPair input={<><div className="pt-lab-toolbar"><h2>Start with your source</h2></div><div className="pt-lab-tabs" role="group" aria-label="Hash input mode">{(["text", "file"] as const).map(value => <button key={value} aria-pressed={mode === value} onClick={() => { setField("mode", value); invalidate(); }}>{value === "text" ? "Text" : "A file"}</button>)}</div><div className="pt-lab-spaced">{mode === "text" ? <label className="pt-lab-field"><span className="sr-only">Text to hash</span><textarea className="pt-lab-textarea" value={input} onChange={e => { setInput(e.target.value); invalidate(); }} onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); void run(); } }} placeholder="Type or paste text. Every space counts." spellCheck={false}/></label> : <FileUploadZone file={file} onFileSelect={value => { setFile(value); invalidate(); }} onClear={() => { setFile(null); invalidate(); }} label="Choose a file to fingerprint" hint="Any file type · read on your device"/>}</div><p className="pt-lab-caption">The same bytes always produce the same fingerprint. Text uses UTF-8; empty text is valid too.</p><button className="pt-lab-button is-primary pt-lab-spaced" disabled={computing || (mode === "file" && !file)} onClick={() => void run()}>{computing ? <Loader2 size={16} className="animate-spin"/> : <Hash size={16}/>} {computing ? "Calculating…" : "Calculate hashes"}</button>{error && <p className="pt-lab-issue is-error" role="alert">{error}</p>}</>} output={<><div className="pt-lab-toolbar"><h2>Three fingerprints</h2><span className="pt-lab-caption">Hexadecimal</span></div>{results.length ? <div className="pt-hash-results">{results.map(row => <article key={row.algo}><div className="pt-lab-toolbar"><h3>{row.algo}</h3><ToolCopyButton value={row.value} label={`Copy ${row.algo}`}/></div><code tabIndex={0}>{row.value}</code></article>)}</div> : <div className="pt-specialist-empty" role="status"><Hash size={38}/><h3>{computing ? "Reading every byte…" : "Your fingerprints belong here"}</h3><p>{computing ? "Large files can take a moment." : "Calculate to compare SHA-1, SHA-256 and SHA-512 side by side."}</p></div>}</>}/>
    </LabWorkspace>;
}
