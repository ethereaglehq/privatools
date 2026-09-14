import { useEffect, useRef, useState } from "react";
import { ArrowRight, Check, Code2, Copy, KeyRound, Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import { apiUrl } from "@/lib/api";
import { StudioPage, StudioHeader, StudioAction } from "@/skins/experience/Studio";
import "@/skins/experience/secondary-pages.css";
import ApiReference from "@/components/ApiReference";
import ApiPlayground from "@/components/ApiPlayground";
import ApiStarters from "@/components/ApiStarters";

type Language = "curl" | "JavaScript" | "Python";
type KeyIdentity = { key_id: string; label: string; created_at: string };
type Usage = { key_id: string; label: string; units: { used: number; limit: number; remaining: number }; bytes: { used: number; limit: number }; resets_at: string };

function apiBase() {
    const path = apiUrl("/v1");
    return typeof window === "undefined" ? path : new URL(path, window.location.origin).toString();
}

function codeFor(language: Language) {
    const base = apiBase();
    if (language === "JavaScript") return `// Run on your server. Keep the key in an environment variable.\nimport { readFile, writeFile } from 'node:fs/promises';\n\nconst form = new FormData();\nform.append('files', new Blob([await readFile('first.pdf')]), 'first.pdf');\nform.append('files', new Blob([await readFile('second.pdf')]), 'second.pdf');\n\nconst response = await fetch('${base}/merge', {\n  method: 'POST',\n  headers: { 'X-API-Key': process.env.PRIVATOOLS_API_KEY },\n  body: form,\n});\nif (!response.ok) throw new Error(await response.text());\nawait writeFile('merged.pdf', Buffer.from(await response.arrayBuffer()));`;
    if (language === "Python") return `import os\nimport requests\n\nwith open('first.pdf', 'rb') as first, open('second.pdf', 'rb') as second:\n    response = requests.post(\n        '${base}/merge',\n        headers={'X-API-Key': os.environ['PRIVATOOLS_API_KEY']},\n        files=[('files', first), ('files', second)],\n        timeout=120,\n    )\nresponse.raise_for_status()\nwith open('merged.pdf', 'wb') as output:\n    output.write(response.content)`;
    return `# Set PRIVATOOLS_API_KEY in your environment first.\ncurl --fail-with-body '${base}/merge' \\\n  -H "X-API-Key: $PRIVATOOLS_API_KEY" \\\n  -F 'files=@first.pdf' \\\n  -F 'files=@second.pdf' \\\n  --output merged.pdf`;
}

function validUsage(value: unknown): value is Usage {
    const v = value as Usage | null;
    return !!v && typeof v.key_id === "string" && typeof v.label === "string" && typeof v.resets_at === "string"
        && [v.units?.used, v.units?.limit, v.units?.remaining, v.bytes?.used, v.bytes?.limit].every(n => typeof n === "number" && Number.isFinite(n) && n >= 0);
}

function usagePercent(used: number, limit: number) { return limit ? Math.min(100, Math.round(used / limit * 100)) : 0; }
function bytes(value: number) { return `${(value / 1024 / 1024).toFixed(1)} MB`; }

export default function ApiPage() {
    const [language, setLanguage] = useState<Language>("curl");
    const [copied, setCopied] = useState(false);
    const [copyError, setCopyError] = useState("");
    const [hasKey, setHasKey] = useState(false);
    const [busy, setBusy] = useState(false);
    const [identity, setIdentity] = useState<KeyIdentity | null>(null);
    const [usage, setUsage] = useState<Usage | null>(null);
    const [error, setError] = useState("");
    const keyInput = useRef<HTMLInputElement>(null);
    const request = useRef<AbortController | null>(null);

    useEffect(() => () => { request.current?.abort(); request.current = null; }, []);

    function invalidate() {
        request.current?.abort(); request.current = null;
        setBusy(false); setIdentity(null); setUsage(null); setError("");
        setHasKey(Boolean(keyInput.current?.value.trim()));
    }

    async function checkKey() {
        const key = keyInput.current?.value.trim();
        if (!key || request.current) return;
        const controller = new AbortController(); request.current = controller;
        setBusy(true); setIdentity(null); setUsage(null); setError("");
        const timer = window.setTimeout(() => controller.abort(), 15000);
        try {
            const get = async (path: string) => {
                const response = await fetch(apiUrl(`/v1/${path}`), { headers: { "X-API-Key": key }, signal: controller.signal, cache: "no-store", credentials: "omit", referrerPolicy: "no-referrer" });
                if (!response.ok) throw new Error(response.status === 401 ? "That key is not recognised or has been revoked." : response.status === 429 ? "Requests are temporarily limited. Try again later." : `The API could not complete this check (HTTP ${response.status}).`);
                return response.json();
            };
            const [who, current] = await Promise.all([get("whoami"), get("usage")]);
            if (request.current !== controller || controller.signal.aborted) return;
            if (!who || typeof who.key_id !== "string" || typeof who.label !== "string" || typeof who.created_at !== "string" || !validUsage(current)) throw new Error("The API returned an unexpected response. Try again later.");
            // Only documented fields reach the UI. Never reflect a credential echoed by a server.
            const safe = (value: string) => value.split(key).join("[redacted]");
            setIdentity({ key_id: safe(who.key_id), label: safe(who.label), created_at: safe(who.created_at) });
            setUsage({ ...current, key_id: safe(current.key_id), label: safe(current.label) });
        } catch (cause) {
            if (request.current !== controller) return;
            setError(controller.signal.aborted ? "The check timed out. Check your connection and try again." : cause instanceof Error && !/fetch|network|load failed/i.test(cause.message) ? cause.message.split(key).join("[redacted]") : "Could not reach the API. Check your connection and try again.");
        } finally {
            window.clearTimeout(timer);
            if (request.current === controller) { request.current = null; setBusy(false); }
        }
    }

    async function copy() {
        try { await navigator.clipboard.writeText(codeFor(language)); setCopied(true); setCopyError(""); }
        catch { setCopied(false); setCopyError("Copy is unavailable. Select and copy the example below."); }
    }

    return <StudioPage className="pt-api-page">
        <StudioHeader kicker="Developer API" title={<>Your workflow. <br />Our toolbox.</>} description="Give your scripts the same tools you use here. Send a file, get your result, keep moving."
            actions={<StudioAction href="/account/keys">Manage API keys</StudioAction>}
            visual={<div className="pt-api-route-art"><Code2 size={46} strokeWidth={1.3} /><span>A little automation goes a long way.</span><div><b>Your files</b><ArrowRight size={19}/><b>Your result</b></div><small>One request through the PrivaTools API</small></div>} />
        <div className="pt-api-console">
            <section className="pt-api-connect" aria-labelledby="key-check-title">
                <span className="pt-connection-symbol"><KeyRound size={26} strokeWidth={1.5} /></span>
                <span className="pt-workspace-caption">Your connection</span><h2 id="key-check-title">Make yourself <br />known.</h2>
                <p>Paste a PrivaTools key to check your access and see today’s allowance.</p>
                <form onSubmit={event => { event.preventDefault(); void checkKey(); }}>
                    <label className="pt-input-label">PrivaTools API key<input ref={keyInput} onChange={invalidate} type="password" autoComplete="off" spellCheck={false} placeholder="Paste your key" className="pt-input" /></label>
                    <button disabled={!hasKey || busy} className="pt-studio-button">{busy ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}{busy ? "Checking…" : "Check key & usage"}</button>
                    <button type="button" onClick={() => { if (keyInput.current) keyInput.current.value = ""; invalidate(); }} className="pt-studio-link">Clear key</button>
                </form>
                {error && <p role="alert" className="pt-form-error">{error}</p>}
                {identity && usage && <div role="status" className="pt-api-usage">
                    <p className="pt-form-success"><ShieldCheck size={18} /> Key verified: {identity.label || "Untitled key"}</p>
                    <small>Key ID {identity.key_id}</small>
                    <div className="pt-usage-meter"><div><span>Daily units</span><strong>{usage.units.used} / {usage.units.limit}</strong></div><progress value={usagePercent(usage.units.used, usage.units.limit)} max={100} aria-label="Daily API units used" /></div>
                    <div className="pt-usage-meter"><div><span>Upload allowance</span><strong>{bytes(usage.bytes.used)} / {bytes(usage.bytes.limit)}</strong></div><progress value={usagePercent(usage.bytes.used, usage.bytes.limit)} max={100} aria-label="Daily API bytes used" /></div>
                    <p>Resets {Number.isNaN(Date.parse(usage.resets_at)) ? "at the time reported by your deployment" : new Date(usage.resets_at).toLocaleString()}.</p>
                </div>}
                <div className="pt-api-key-note"><ShieldCheck size={16} /><p>This form never saves your key or sends a file. It contacts only the configured PrivaTools API.</p></div>
                <a href="/account/keys" className="pt-studio-link">Need a key? Create one <ArrowRight size={14} /></a>
            </section>

            <section className="pt-api-example" aria-labelledby="example-title">
                <header><div><span className="pt-workspace-caption">Start with something useful</span><h2 id="example-title">Two PDFs. One request.</h2><p>A complete merge example, ready for your script.</p></div><span className="pt-api-method">POST /merge</span></header>
                <div className="pt-api-code-toolbar"><div aria-label="Example language">{(["curl", "JavaScript", "Python"] as Language[]).map(value => <button key={value} type="button" aria-pressed={language === value} onClick={() => { setLanguage(value); setCopied(false); setCopyError(""); }}>{value}</button>)}</div><button onClick={() => void copy()} type="button" aria-label={copied ? "Copied" : "Copy code"}>{copied ? <Check size={15} /> : <Copy size={15} />}<span>{copied ? "Copied" : "Copy code"}</span></button></div>
                <pre tabIndex={0} aria-label={`${language} merge example`}><code>{codeFor(language)}</code></pre>
                {copyError && <p role="alert" className="pt-form-error">{copyError}</p>}
                <footer><span><ShieldCheck size={15} />Keep keys in your server environment.</span><span>Successful requests return the file directly.</span></footer>
            </section>

            <ApiPlayground />
            <ApiStarters />
            <ApiReference />
        </div>
    </StudioPage>;
}
