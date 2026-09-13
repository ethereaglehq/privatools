/**
 * Base64UI — text ↔ Base64 with workshop aesthetic.
 *
 * Tabbed encode/decode, code-editor I/O panels, live conversion,
 * swap action to flip input/output, mono everything.
 */
import { useEffect, useMemo, useState, useCallback} from "react";
import { ArrowDownUp, Sparkles } from "lucide-react";
import { LabWorkspace, LabPair, LabOutput, ToolCopyButton } from "./SpecialistTools";
import { useToolDefaults } from "@/hooks/useToolDefaults";

type Mode = "encode" | "decode";

// A reasonably tight test for whether a blob of text "looks like" Base64.
function looksLikeBase64(s: string): boolean {
    const trimmed = s.trim();
    if (trimmed.length < 8) return false;
    if (/^[A-Za-z0-9+/=\s]+$/.test(trimmed) && trimmed.replace(/\s+/g, "").length % 4 === 0) {
        // Avoid matching plain words (e.g. "Hello") that happen to be base64-charset only.
        const compact = trimmed.replace(/\s+/g, "");
        if (!/[A-Z]/.test(compact) || !/[a-z]/.test(compact) || !/[0-9+/]/.test(compact)) {
            return compact.length >= 16; // longer strings of mixed chars likely real base64
        }
        return true;
    }
    return false;
}

const BASE64_DEFAULTS: { mode: Mode } = {
    mode: "encode",
};

export function Base64UI() {
    const [config, , { setField }] = useToolDefaults("base64", BASE64_DEFAULTS);
    const { mode } = config;
    const setMode = useCallback((v: React.SetStateAction<typeof BASE64_DEFAULTS["mode"]>) => setField("mode", v), [setField]);

    const [input, setInput] = useState("");
    const [output, setOutput] = useState("");
    const [error, setError] = useState<string | null>(null);

    const autoHint = useMemo(() => {
        return mode === "encode" && looksLikeBase64(input);
    }, [mode, input]);

    // Live convert when input changes
    useEffect(() => {
        if (!input.length) { setOutput(""); setError(null); return; }
        try {
            if (mode === "encode") {
                setOutput(btoa(unescape(encodeURIComponent(input))));
            } else {
                setOutput(decodeURIComponent(escape(atob(input.replace(/\s+/g, "")))));
            }
            setError(null);
        } catch {
            setError(mode === "decode" ? "Invalid Base64 input." : "Could not encode.");
            setOutput("");
        }
    }, [input, mode]);

    const swap = () => { setMode(m => m === "encode" ? "decode" : "encode"); setInput(output); };
    return <LabWorkspace note="Text is encoded or decoded here in your browser. No upload is needed." kind="base64">
        <div className="pt-lab-toolbar"><div className="pt-lab-tabs" role="group" aria-label="Encoding mode">{(["encode", "decode"] as const).map(m => <button key={m} aria-pressed={mode === m} onClick={() => setMode(m)}>{m === "encode" ? "Encode text" : "Decode Base64"}</button>)}</div><div className="pt-lab-controls"><button className="pt-lab-button" onClick={() => setInput(mode === "encode" ? "Hello, world. 你好 🌿" : "SGVsbG8sIHdvcmxkLg==")}><Sparkles size={15}/>Try sample</button><button className="pt-lab-button" onClick={swap} disabled={!output}><ArrowDownUp size={15}/>Swap sides</button></div></div>
        {autoHint && <button className="pt-lab-issue" onClick={() => setMode("decode")}>This looks like Base64. Switch to decoding?</button>}
        <LabPair input={<><label className="pt-lab-field"><span>{mode === "encode" ? "Your original text" : "Your encoded text"}</span><textarea className="pt-lab-textarea" aria-label="Base64 source" value={input} onChange={e => setInput(e.target.value)} placeholder={mode === "encode" ? "Type anything, in any language…" : "Paste a Base64 string…"} spellCheck={false}/></label><p className="pt-lab-caption">{input.length.toLocaleString()} characters · UTF-8 text</p></>} output={<><div className="pt-lab-toolbar"><h2>{mode === "encode" ? "Ready to use" : "Back to plain text"}</h2><ToolCopyButton value={output}/></div>{error ? <p role="alert" className="pt-lab-issue is-error">{error}</p> : <LabOutput value={output} label="Base64 result"/>}</>}/>
    </LabWorkspace>;
}
