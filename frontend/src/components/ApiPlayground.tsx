import { useEffect, useRef, useState } from "react";
import { Copy, Download, FileText, Loader2, Play, ShieldCheck } from "lucide-react";
import { apiUrl } from "@/lib/api";
import { playgroundCurl, playgroundForm, playgroundOperations, samplePdf, type PlaygroundOperation } from "./api-playground-samples";
import "./api-playground.css";

type Allowance = { key_id: string; resets_at: string; units: { used: number; remaining: number }; bytes: { used: number } };
type RunResult = {
    ok: boolean; status: number | null; requestId: string; duration: number; message: string;
    code?: string; retryAfter?: number; preview?: string; url?: string; filename?: string;
    before: Allowance | null; after: Allowance | null;
};
type ActiveRun = { controller: AbortController; timer: number };
const REQUEST_TIMEOUT = 120_000;
const USAGE_TIMEOUT = 5_000;
const MAX_PDF_BYTES = 2 * 1024 * 1024;
const MAX_JSON_BYTES = 64 * 1024;

function safeText(value: unknown, key: string, limit = 500): string {
    if (typeof value !== "string") return "";
    const redacted = value.split(key).join("[redacted]").replace(/pk_[a-zA-Z0-9_-]+/g, "[redacted]");
    return Array.from(redacted).filter(character => {
        const code = character.charCodeAt(0);
        return (code >= 32 && code !== 127) || code === 9 || code === 10 || code === 13;
    }).join("").slice(0, limit);
}

function allowance(value: unknown): Allowance | null {
    const candidate = value as Allowance | null;
    if (!candidate || typeof candidate.key_id !== "string" || typeof candidate.resets_at !== "string"
        || ![candidate.units?.used, candidate.units?.remaining, candidate.bytes?.used].every(n => Number.isSafeInteger(n) && n >= 0)) return null;
    return { key_id: candidate.key_id, resets_at: candidate.resets_at, units: { used: candidate.units.used, remaining: candidate.units.remaining }, bytes: { used: candidate.bytes.used } };
}

async function boundedBody(response: Response, limit: number): Promise<Uint8Array> {
    if (Number(response.headers.get("Content-Length")) > limit) {
        await response.body?.cancel();
        throw new Error("The response was larger than this sample playground can display.");
    }
    const reader = response.body?.getReader();
    if (!reader) throw new Error("The API returned an empty response.");
    const parts: Uint8Array[] = [];
    let length = 0;
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            length += value.byteLength;
            if (length > limit) {
                await reader.cancel();
                throw new Error("The response was larger than this sample playground can display.");
            }
            parts.push(value);
        }
    } finally { reader.releaseLock(); }
    const bytes = new Uint8Array(length);
    let offset = 0;
    for (const part of parts) { bytes.set(part, offset); offset += part.byteLength; }
    return bytes;
}

async function readAllowance(key: string, parent: AbortSignal): Promise<Allowance | null> {
    if (parent.aborted) return null;
    const controller = new AbortController();
    const abort = () => controller.abort();
    parent.addEventListener("abort", abort, { once: true });
    const timer = window.setTimeout(abort, USAGE_TIMEOUT);
    try {
        const response = await fetch(apiUrl("/v1/usage"), {
            headers: { "X-API-Key": key }, signal: controller.signal, credentials: "omit",
            cache: "no-store", referrerPolicy: "no-referrer", redirect: "error",
        });
        if (!response.ok) { await response.body?.cancel(); return null; }
        const body = await boundedBody(response, MAX_JSON_BYTES);
        return allowance(JSON.parse(new TextDecoder().decode(body)));
    } catch { return null; }
    finally { window.clearTimeout(timer); parent.removeEventListener("abort", abort); }
}

function usageChange(before: Allowance | null, after: Allowance | null) {
    if (!before || !after || before.key_id !== after.key_id || before.resets_at !== after.resets_at
        || after.units.used < before.units.used || after.bytes.used < before.bytes.used) return null;
    return { units: after.units.used - before.units.used, bytes: after.bytes.used - before.bytes.used };
}

export default function ApiPlayground() {
    const [operation, setOperation] = useState<PlaygroundOperation>("merge");
    const [hasKey, setHasKey] = useState(false);
    const [phase, setPhase] = useState("");
    const [result, setResult] = useState<RunResult | null>(null);
    const [notice, setNotice] = useState("");
    const [copyMessage, setCopyMessage] = useState("");
    const [samples, setSamples] = useState<string[]>([]);
    const keyInput = useRef<HTMLInputElement>(null);
    const active = useRef<ActiveRun | null>(null);
    const resultUrl = useRef<string | null>(null);
    const config = playgroundOperations[operation];
    const endpoint = new URL(apiUrl(`/v1/${operation}`), window.location.origin).toString();
    const code = playgroundCurl(operation, endpoint);

    useEffect(() => {
        const urls = ([1, 2] as const).map(page => URL.createObjectURL(new Blob([samplePdf(page)], { type: "application/pdf" })));
        setSamples(urls);
        return () => {
            if (active.current) { active.current.controller.abort(); window.clearTimeout(active.current.timer); active.current = null; }
            if (resultUrl.current) { URL.revokeObjectURL(resultUrl.current); resultUrl.current = null; }
            urls.forEach(url => URL.revokeObjectURL(url));
        };
    }, []);

    function invalidate(message = "") {
        if (active.current) { active.current.controller.abort(); window.clearTimeout(active.current.timer); active.current = null; }
        if (resultUrl.current) { URL.revokeObjectURL(resultUrl.current); resultUrl.current = null; }
        setPhase(""); setResult(null); setNotice(message);
        setHasKey(Boolean(keyInput.current?.value.trim()));
    }

    async function run() {
        const key = keyInput.current?.value.trim();
        if (!key || active.current) return;
        invalidate();
        const controller = new AbortController();
        const current = { controller, timer: window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT) };
        active.current = current;
        setPhase("Checking allowance…");
        let before: Allowance | null = null;
        let status: number | null = null;
        let requestId = "";
        let started = performance.now();
        let duration = 0;
        let output: Blob | null = null;
        let details: Partial<RunResult> = {};
        try {
            before = await readAllowance(key, controller.signal);
            if (active.current !== current) return;
            if (controller.signal.aborted) throw new Error("Request aborted");
            setPhase("Converting sample…");
            started = performance.now();
            const response = await fetch(apiUrl(`/v1/${operation}`), {
                method: "POST", headers: { "X-API-Key": key }, body: playgroundForm(operation),
                signal: controller.signal, credentials: "omit", cache: "no-store", referrerPolicy: "no-referrer", redirect: "error",
            });
            if (active.current !== current) return;
            if (controller.signal.aborted) throw new Error("Request aborted");
            status = response.status;
            requestId = safeText(response.headers.get("X-Request-ID"), key, 128);
            const mime = response.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase();
            const bytes = await boundedBody(response, response.ok && operation !== "pdf-to-text" ? MAX_PDF_BYTES : MAX_JSON_BYTES);
            if (controller.signal.aborted) throw new Error("Request aborted");
            duration = Math.max(0, Math.round(performance.now() - started));
            if (!response.ok) {
                let error: { code?: unknown; message?: unknown; request_id?: unknown } = {};
                if (mime === "application/json") {
                    try { error = JSON.parse(new TextDecoder().decode(bytes)) || {}; } catch { /* Use the safe HTTP fallback. */ }
                }
                requestId ||= safeText(error.request_id, key, 128);
                const retry = Number(response.headers.get("Retry-After"));
                details = {
                    ok: false, code: safeText(error.code, key, 80),
                    message: safeText(error.message, key) || (status === 401 ? "That key is not recognised or has been revoked." : status === 429 ? "The API is temporarily limiting requests. Check your allowance and try later." : `The API could not complete this sample (HTTP ${status}).`),
                    retryAfter: Number.isSafeInteger(retry) && retry > 0 && retry <= 86400 ? retry : undefined,
                };
            } else if (operation === "pdf-to-text") {
                if (mime !== "application/json") throw new Error("The API returned an unexpected response type.");
                const data = JSON.parse(new TextDecoder().decode(bytes));
                if (!data || typeof data.text !== "string" || !Array.isArray(data.pages)) throw new Error("The API returned an unexpected text response.");
                const text = safeText(data.text, key, 16_000);
                const pages = data.pages.slice(0, 10).filter((page: { page?: number; text?: unknown }) => Number.isSafeInteger(page?.page) && page.page > 0 && typeof page.text === "string")
                    .map((page: { page: number; text: string }) => ({ page: page.page, text: safeText(page.text, key, 8_000) }));
                output = new Blob([JSON.stringify({ text, pages, characters: text.length }, null, 2)], { type: "application/json" });
                details = { ok: true, message: "Your sample is ready.", preview: text.slice(0, 4_000) };
            } else {
                if (mime !== "application/pdf" || new TextDecoder().decode(bytes.subarray(0, 5)) !== "%PDF-") throw new Error("The API returned an unexpected PDF response.");
                if (new TextDecoder().decode(bytes).includes(key)) throw new Error("The response could not be safely displayed. Please check the API deployment.");
                output = new Blob([bytes], { type: "application/pdf" });
                details = { ok: true, message: "Your sample is ready." };
            }
        } catch (cause) {
            if (active.current !== current) return;
            duration = Math.max(0, Math.round(performance.now() - started));
            const known = cause instanceof Error && /^(The API returned|The response)/.test(cause.message);
            details = { ok: false, message: controller.signal.aborted
                ? "Stopped waiting after two minutes. The server may still finish and use allowance. Check usage before sending another request."
                : known ? safeText(cause.message, key) : "Could not complete the request. Check your connection and usage before trying again; the server may have processed it." };
        } finally { window.clearTimeout(current.timer); }
        try {
            if (active.current !== current) return;
            if (!controller.signal.aborted) setPhase("Refreshing allowance…");
            const after = await readAllowance(key, controller.signal);
            if (active.current !== current) return;
            if (output && !controller.signal.aborted) { resultUrl.current = URL.createObjectURL(output); }
            setResult({ ok: false, message: "", ...details, status, requestId, duration, before, after,
                url: resultUrl.current || undefined, filename: output ? config.output : undefined });
        } finally {
            window.clearTimeout(current.timer);
            if (active.current === current) { active.current = null; setPhase(""); }
        }
    }

    async function copy() {
        try { await navigator.clipboard.writeText(code); setCopyMessage("Copied sample request."); }
        catch { setCopyMessage("Copy is unavailable. Select the request below to copy it."); }
    }

    const delta = result ? usageChange(result.before, result.after) : null;
    return <section className="pt-api-playground" aria-labelledby="playground-title">
        <header className="pt-section-title"><div><span className="pt-workspace-caption">Try a real request</span><h2 id="playground-title">Your first result, right here.</h2><p>Use our small sample PDFs to see the API in action.</p></div><FileText size={32} strokeWidth={1.4} aria-hidden="true" /></header>
        <div className="pt-playground-workspace">
            <form onSubmit={event => { event.preventDefault(); void run(); }} className="pt-playground-controls">
                <label className="pt-input-label" htmlFor="playground-operation">Sample operation<select id="playground-operation" className="pt-input" value={operation} disabled={!!phase} onChange={event => { invalidate(); setOperation(event.target.value as PlaygroundOperation); setCopyMessage(""); }}>{Object.entries(playgroundOperations).map(([id, item]) => <option key={id} value={id}>{item.label}</option>)}</select></label>
                <p className="pt-playground-description">{config.description}</p>
                <div className="pt-playground-samples" aria-label="Sample PDF downloads">{samples.slice(0, config.files).map((url, index) => <a key={url} href={url} download={`sample-${index + 1}.pdf`}><Download size={14} aria-hidden="true" />sample-{index + 1}.pdf</a>)}</div>
                <label className="pt-input-label" htmlFor="playground-key">Playground API key<input id="playground-key" ref={keyInput} type="password" autoComplete="off" spellCheck={false} maxLength={200} placeholder="Paste your key" className="pt-input" onChange={() => invalidate()} aria-describedby="playground-privacy" /></label>
                <p id="playground-cost" className="pt-playground-cost">Each run uses your normal allowance: {config.units} {config.units === 1 ? "unit" : "units"}, plus the uploaded request bytes. Usage checks cost no processing units.</p>
                <div className="pt-inline-actions"><button type="submit" className="pt-studio-button" disabled={!hasKey || !!phase} aria-describedby="playground-cost">{phase ? <Loader2 size={16} className="animate-spin" aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}{phase ? "Running sample…" : "Run sample"}</button>{phase && <button type="button" className="pt-studio-link" onClick={() => invalidate("Stopped waiting. The server may still finish and use allowance. Check usage before sending another request.")}>Stop waiting</button>}<button type="button" className="pt-studio-link" onClick={() => { if (keyInput.current) keyInput.current.value = ""; invalidate(); }}>Clear playground key</button></div>
                <p id="playground-privacy" className="pt-playground-privacy"><ShieldCheck size={15} aria-hidden="true" /><span>Your key stays in this page’s memory and goes only to the configured PrivaTools API. Run sends the sample PDFs shown above.</span></p>
                <p className="pt-playground-note">Stopping or leaving the page stops waiting for the response; it may not cancel server processing. This playground never retries a conversion automatically.</p>
            </form>
            <div className="pt-playground-request"><div className="pt-playground-request-heading"><span className="pt-api-method">POST /{operation}</span><button className="pt-studio-link" type="button" onClick={() => void copy()} aria-label="Copy sample request"><Copy size={15} aria-hidden="true" />Copy request</button></div><pre tabIndex={0} aria-label="Sample curl request"><code>{code}</code></pre>{copyMessage && <p role="status" className="pt-playground-note">{copyMessage}</p>}<p className="pt-playground-note">The command uses the same sample files and form fields as Run. Set <code>PRIVATOOLS_API_KEY</code> in your terminal environment.</p></div>
        </div>
        {phase && <p role="status" className="pt-playground-progress">{phase}</p>}
        {notice && <p role="status" className="pt-playground-note">{notice}</p>}
        {result && <div className="pt-playground-result" aria-labelledby="playground-result-title"><h3 id="playground-result-title">Request result</h3><p role={result.ok ? "status" : "alert"} className={result.ok ? "pt-form-success" : "pt-form-error"}>{result.message}{result.code && ` (${result.code})`}</p>
            <dl className="pt-playground-facts"><div><dt>Response</dt><dd>{result.status === null ? "No HTTP response" : `HTTP ${result.status}`}</dd></div><div><dt>Request time</dt><dd>{result.duration.toLocaleString()} ms</dd></div><div><dt>Request ID</dt><dd>{result.requestId || "Not provided"}</dd></div></dl>
            {result.retryAfter && <p className="pt-playground-note">The API asks you to wait {result.retryAfter} seconds before another request.</p>}
            <div className="pt-playground-allowance"><h4>Usage change during this run</h4>{delta ? <><p>{delta.units} {delta.units === 1 ? "unit" : "units"} · {delta.bytes.toLocaleString()} request bytes</p><small>Measured from before/after usage checks. Includes any other activity on this key.</small></> : <p>Usage change unavailable. The before/after allowance readings could not be compared.</p>}{result.after && <p>{result.after.units.remaining.toLocaleString()} units remaining today.</p>}</div>
            {result.preview !== undefined && <div className="pt-playground-preview"><h4>Extracted text preview</h4><pre tabIndex={0}>{result.preview || "No readable text returned."}</pre></div>}
            {result.url && <a className="pt-studio-button is-secondary" href={result.url} download={result.filename}><Download size={16} aria-hidden="true" />Download {result.filename}</a>}
        </div>}
    </section>;
}
