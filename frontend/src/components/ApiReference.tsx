import { useEffect, useState } from "react";
import { ArrowRight, Copy } from "lucide-react";
import { apiUrl } from "@/lib/api";
import "./api-reference.css";

type Schema = { $ref?: string; type?: string; format?: string; contentMediaType?: string; properties?: Record<string, Schema>; items?: Schema; required?: string[]; anyOf?: Schema[]; default?: unknown; enum?: unknown[]; minimum?: number; minItems?: number; description?: string; [key: string]: unknown };
type Content = Record<string, { schema?: Schema }>;
type ApiOperation = { id: string; method: string; path: string; summary: string; description: string; category: string; request_body: { content: Content } | null; parameters: { name: string; in: string; required?: boolean; schema?: Schema }[]; responses: Record<string, { description: string; content?: Content }>; cost: { units: number | null; description: string; mode: string }; async: { supported: boolean }; constraints: string[]; tool_aliases?: string[] };
type Catalog = { schema_version: string; operations: ApiOperation[]; components: { schemas?: Record<string, Schema> }; limits: { daily_units: number; daily_bytes: number; concurrent_requests_per_key?: number; global_concurrent_requests?: number; requests_per_minute?: number; request_burst?: number; bytes_definition?: string }; async?: { enabled: boolean; available: boolean; operations: string[]; result_retention_seconds: number }; unavailable_tools: { slug: string; name: string; reason: string }[] };
type Language = "curl" | "Python" | "JavaScript";

function validCatalog(value: unknown): value is Catalog {
    if (!value || typeof value !== "object") return false;
    const v = value as Catalog;
    return v.schema_version === "1" && Array.isArray(v.operations) && !!v.components && !!v.limits
        && Number.isFinite(v.limits.daily_units) && Number.isFinite(v.limits.daily_bytes)
        && (!v.async || (typeof v.async.available === "boolean" && Array.isArray(v.async.operations) && v.async.operations.every(o => typeof o === "string") && Number.isFinite(v.async.result_retention_seconds)))
        && Array.isArray(v.unavailable_tools) && v.unavailable_tools.every(t => typeof t.slug === "string" && typeof t.name === "string" && typeof t.reason === "string")
        && v.operations.every(o => typeof o.id === "string" && typeof o.summary === "string" && typeof o.description === "string" && typeof o.category === "string"
            && /^(GET|POST|PUT|PATCH|DELETE|HEAD)$/.test(o.method) && /^\/api\/v1\/[a-zA-Z0-9_{}./-]+$/.test(o.path)
            && !!o.responses && typeof o.responses === "object" && Array.isArray(o.parameters) && Array.isArray(o.constraints)
            && o.constraints.every(c => typeof c === "string") && typeof o.cost?.description === "string" && typeof o.async?.supported === "boolean"
            && (o.request_body === null || typeof o.request_body?.content === "object"));
}

function resolve(schema: Schema | undefined, catalog: Catalog): Schema {
    if (!schema) return {};
    if (!schema.$ref) return schema;
    return catalog.components.schemas?.[schema.$ref.replace("#/components/schemas/", "")] || schema;
}

function fieldType(schema: Schema, catalog: Catalog): string {
    const s = resolve(schema, catalog);
    if (s.format === "binary" || s.contentMediaType === "application/octet-stream") return "file";
    if (s.anyOf) return s.anyOf.map(part => fieldType(part, catalog)).join(" or ");
    if (s.type === "array") return `${fieldType(s.items || {}, catalog)}[]`;
    return s.type || "see schema";
}

function endpointUrl(path: string) {
    return new URL(apiUrl(path.replace(/^\/api/, "")), window.location.origin).toString();
}

function requestTemplate(operation: ApiOperation, catalog: Catalog, language: Language) {
    const isJobSubmission = operation.path === "/api/v1/jobs" && operation.method === "POST";
    const address = new URL(endpointUrl(operation.path));
    operation.parameters.filter(p => p.in === "query" && p.required).forEach(p => address.searchParams.set(p.name, "REPLACE_ME"));
    const url = address.toString();
    const [mime, body] = Object.entries(operation.request_body?.content || {})[0] || [];
    const schema = resolve(body?.schema, catalog);
    const fields = Object.entries(schema.properties || {});
    const values = fields.filter(([name, value]) => schema.required?.includes(name) || (value.default !== undefined && value.default !== null)).map(([name, value]) => {
        const field = resolve(value, catalog);
        const type = fieldType(field, catalog);
        const sample = field.default ?? field.enum?.[0] ?? (type === "integer" || type === "number" ? field.minimum ?? 1 : type === "boolean" ? false : field.type === "object" ? {} : field.type === "array" ? [] : "REPLACE_ME");
        return { name, type, sample, count: Math.max(1, Math.min(field.minItems || 1, 3)) };
    });
    const inputFile = isJobSubmission || operation.path === "/api/v1/compress" ? "input.pdf" : "input.bin";
    const files = values.filter(v => v.type.includes("file")).flatMap(v => Array.from({ length: v.count }, (_, i) => ({ name: v.name, file: operation.path === "/api/v1/merge" ? `${i === 0 ? "first" : "second"}.pdf` : inputFile })));
    const textFields = values.filter(v => !v.type.includes("file"));
    const payload = Object.fromEntries(textFields.map(v => [v.name, v.sample]));
    const extraHeaders = operation.parameters.filter(p => p.in === "header" && p.required && !/^(X-API-Key|Authorization)$/i.test(p.name));
    const retryHint = isJobSubmission ? "Retry a job submission only with the identical Idempotency-Key and payload." : "Do not automatically retry processing POSTs.";
    const hint = `Request template: replace sample values and files to meet the schema. ${retryHint}`;
    if (language === "curl") {
        const quote = (value: string) => `'${value.replace(/'/g, "'\\''")}'`;
        const parts = [`# ${hint}`, `curl --fail-with-body -X ${operation.method} ${quote(url)}`, '  -H "X-API-Key: $PRIVATOOLS_API_KEY"'];
        extraHeaders.forEach(h => parts.push(`  -H ${quote(`${h.name}: REPLACE_ME`)}`));
        if (mime === "application/json") parts.push("  -H 'Content-Type: application/json'", `  --data ${quote(JSON.stringify(payload))}`);
        else {
            files.forEach(f => parts.push(`  -F ${quote(`${f.name}=@${f.file}`)}`));
            textFields.forEach(f => parts.push(`  --form-string ${quote(`${f.name}=${typeof f.sample === "object" ? JSON.stringify(f.sample) : String(f.sample)}`)}`));
        }
        parts.push("  --output result");
        return `${parts[0]}\n${parts.slice(1).join(" \\\n")}`;
    }
    if (language === "Python") {
        const jsonLiteral = JSON.stringify(JSON.stringify(payload));
        const lines = [`# ${hint}`, "import os, json", "from contextlib import ExitStack", "import requests", "", "with ExitStack() as stack:", "    headers = {'X-API-Key': os.environ['PRIVATOOLS_API_KEY']}"];
        extraHeaders.forEach(h => lines.push(`    headers[${JSON.stringify(h.name)}] = 'REPLACE_ME'`));
        lines.push(`    fields = json.loads(${jsonLiteral})`);
        if (files.length) lines.push(`    files = [${files.map(f => `(${JSON.stringify(f.name)}, stack.enter_context(open(${JSON.stringify(f.file)}, 'rb')))` ).join(", ")}]`);
        lines.push(`    response = requests.request(${JSON.stringify(operation.method)}, ${JSON.stringify(url)},`, `        headers=headers, ${mime === "application/json" ? "json=fields" : `data=fields${files.length ? ", files=files" : ""}`}, timeout=120)`, "    response.raise_for_status()", "    with open('result', 'wb') as output:", "        output.write(response.content)");
        return lines.join("\n");
    }
    const lines = [`// ${hint}`, "// Run on your server; keep the key in an environment variable.", "import { readFile, writeFile } from 'node:fs/promises';", "", "const headers = { 'X-API-Key': process.env.PRIVATOOLS_API_KEY };"];
    extraHeaders.forEach(h => lines.push(`headers[${JSON.stringify(h.name)}] = 'REPLACE_ME';`));
    if (mime === "application/json") lines.push("headers['Content-Type'] = 'application/json';", `const body = JSON.stringify(${JSON.stringify(payload)});`);
    else if (mime) {
        lines.push("const body = new FormData();");
        files.forEach(f => lines.push(`body.append(${JSON.stringify(f.name)}, new Blob([await readFile(${JSON.stringify(f.file)})]), ${JSON.stringify(f.file)});`));
        textFields.forEach(f => lines.push(`body.append(${JSON.stringify(f.name)}, ${JSON.stringify(typeof f.sample === "object" ? JSON.stringify(f.sample) : String(f.sample))});`));
    }
    lines.push(`const response = await fetch(${JSON.stringify(url)}, {`, `  method: ${JSON.stringify(operation.method)}, headers${mime ? ", body" : ""},`, "});", "if (!response.ok) throw new Error(await response.text());", "await writeFile('result', Buffer.from(await response.arrayBuffer()));");
    return lines.join("\n");
}

function OperationDetail({ operation, catalog }: { operation: ApiOperation; catalog: Catalog }) {
    const [language, setLanguage] = useState<Language>("curl");
    const [copyMessage, setCopyMessage] = useState("");
    const [mime, body] = Object.entries(operation.request_body?.content || {})[0] || [];
    const schema = resolve(body?.schema, catalog);
    const code = requestTemplate(operation, catalog, language);
    const additionalConstraints = operation.constraints.filter(c => !operation.description.includes(c));
    const isJobOperation = /^\/api\/v1\/jobs(?:\/|$)/.test(operation.path);
    async function copy() {
        try { await navigator.clipboard.writeText(code); setCopyMessage("Copied"); }
        catch { setCopyMessage("Select and copy the template below."); }
    }
    return <div className="pt-api-operation-detail">
        <p>{operation.description || operation.summary}</p>
        <p>{operation.cost.description}{!isJobOperation && ` ${operation.async.supported ? "Async submission available." : "Use the documented HTTP request; async submission is not available for this operation."}`}</p>
        {additionalConstraints.length > 0 && <ul>{additionalConstraints.map(c => <li key={c}>{c}</li>)}</ul>}
        <h3>Request{mime ? ` · ${mime}` : ""}</h3>
        {Object.entries(schema.properties || {}).length > 0 && <div className="pt-api-fields"><table><thead><tr><th>Field</th><th>Type</th><th>Requirement</th></tr></thead><tbody>{Object.entries(schema.properties || {}).map(([name, field]) => <tr key={name}><td><code>{name}</code></td><td>{fieldType(field, catalog)}</td><td>{schema.required?.includes(name) ? "required" : "optional"}{field.default !== undefined && ` · default ${JSON.stringify(field.default)}`}</td></tr>)}</tbody></table></div>}
        {operation.parameters.map(p => <p key={`${p.in}-${p.name}`}><code>{p.name}</code> · {p.in} · {p.required ? "required" : "optional"}</p>)}
        {mime && <details><summary>Exact request schema and constraints</summary><pre tabIndex={0}><code>{JSON.stringify(schema, null, 2)}</code></pre></details>}
        <h3>Responses</h3>
        <dl className="pt-api-responses">{Object.entries(operation.responses).map(([status, response]) => <div key={status}><dt>{status}</dt><dd>{Object.keys(response.content || {}).map(type => <code key={type}>{type}</code>)}<span>{response.description}</span></dd></div>)}</dl>
        <div className="pt-api-code-toolbar"><div aria-label={`Template language for ${operation.summary}`}>{(["curl", "Python", "JavaScript"] as Language[]).map(l => <button type="button" key={l} aria-pressed={l === language} onClick={() => { setLanguage(l); setCopyMessage(""); }}>{l}</button>)}</div><button type="button" onClick={() => void copy()} aria-label={`Copy ${operation.summary} template`}><Copy size={15} />Copy</button></div>
        <pre tabIndex={0} aria-label={`${language} request template`}><code>{code}</code></pre>
        {copyMessage && <p role="status">{copyMessage}</p>}
    </div>;
}

export default function ApiReference() {
    const [catalog, setCatalog] = useState<Catalog | null>(null);
    const [error, setError] = useState(false);
    const [attempt, setAttempt] = useState(0);
    const [query, setQuery] = useState("");
    const [category, setCategory] = useState("");
    const [opened, setOpened] = useState<string[]>([]);
    useEffect(() => {
        const controller = new AbortController();
        fetch(apiUrl("/v1/operations"), { signal: controller.signal, credentials: "omit", referrerPolicy: "no-referrer" })
            .then(async response => { if (!response.ok) throw new Error("catalog"); const data: unknown = await response.json(); if (!validCatalog(data)) throw new Error("catalog"); if (!controller.signal.aborted) { setCatalog(data); setError(false); } })
            .catch(() => { if (!controller.signal.aborted) setError(true); });
        return () => controller.abort();
    }, [attempt]);
    const filtered = catalog?.operations.filter(o => (!category || o.category === category) && [o.path, o.summary, o.description, ...(o.tool_aliases || [])].join(" ").toLowerCase().includes(query.toLowerCase())) || [];
    return <section className="pt-api-reference" aria-labelledby="reference-title">
        <div className="pt-section-title"><h2 id="reference-title">The API reference.</h2><p>Explore the operations available on this deployment. No key needed to browse.</p></div>
        <div className="pt-api-discovery-links"><a href={apiUrl("/v1/openapi.json")}>OpenAPI JSON</a><a href={apiUrl("/v1/operations")}>Operation catalog</a></div>
        {!catalog && !error && <p role="status">Loading API reference…</p>}
        {error && <div role="alert"><p>The API reference could not be loaded. The quick-start example above is still available.</p><button className="pt-studio-link" type="button" onClick={() => { setError(false); setAttempt(a => a + 1); }}>Retry reference</button></div>}
        {catalog && <>
            <div className="pt-api-limits">
                <p>Free allowance: {catalog.limits.daily_units} units and {(catalog.limits.daily_bytes / 1024 / 1024).toLocaleString()} MiB per key per day. {catalog.limits.bytes_definition}</p>
                {catalog.limits.concurrent_requests_per_key !== undefined && <p>Up to {catalog.limits.concurrent_requests_per_key} simultaneous admitted HTTP processing requests per key{catalog.limits.global_concurrent_requests !== undefined && ` and ${catalog.limits.global_concurrent_requests} across all keys`}. These limits cover synchronous processing and job submission; background execution has separate queue limits.</p>}
                {catalog.limits.requests_per_minute !== undefined && <p>Sustained rate: {catalog.limits.requests_per_minute} processing requests per minute per key{catalog.limits.request_burst !== undefined && `, with a burst capacity of ${catalog.limits.request_burst}`}. Job submissions share this rate limit.</p>}
                <p>Information calls, including key and usage checks, plus job polling, result downloads, and deletion do not consume processing units, processing request slots, or the shared per-key request burst. Separate endpoint and IP protections can still apply.</p>
            </div>
            {catalog.async && <div className="pt-api-workflow"><h3>Background jobs</h3><p>{catalog.async.available ? `Background processing is available for: ${catalog.async.operations.join(", ")}.` : "Background processing is currently unavailable on this deployment."}</p><p>Submit supported operations to <code>POST /jobs</code> with an <code>Idempotency-Key</code>, then poll the returned job ID and download the completed result. Completed results remain available for {catalog.async.result_retention_seconds / 60} minutes; delete a job to remove its artifacts sooner. Polling and downloading do not spend processing units.</p></div>}
            <div className="pt-api-filters"><label>Search API operations<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search name, path, or tool" className="pt-input" /></label><label>Category<select value={category} onChange={e => setCategory(e.target.value)} className="pt-input"><option value="">All categories</option>{[...new Set(catalog.operations.map(o => o.category))].sort().map(c => <option key={c}>{c}</option>)}</select></label></div>
            <p role="status">{catalog.operations.length} operations available{filtered.length !== catalog.operations.length && ` · ${filtered.length} matching`}</p>
            {filtered.length === 0 && <p>No operations match. Try another name, path, or category.</p>}
            <div className="pt-api-endpoints">{filtered.map(o => <details key={o.id} data-testid={`api-operation-${o.id}`} className="pt-api-endpoint" onToggle={e => { if (e.currentTarget.open) setOpened(current => current.includes(o.id) ? current : [...current, o.id]); }}><summary><span>{o.method}</span><code>{o.path.replace("/api/v1", "")}</code><strong>{o.summary}</strong><ArrowRight size={16} /></summary>{opened.includes(o.id) && <OperationDetail operation={o} catalog={catalog} />}</details>)}</div>
            <details className="pt-api-browser-only"><summary>Browser-only tools: no API endpoint</summary><p>These website tools cannot be called through v1. AI tools may run on your device or through your chosen provider.</p><ul>{catalog.unavailable_tools.map(tool => <li key={tool.slug}><strong>{tool.name}</strong> — {tool.reason}</li>)}</ul></details>
        </>}
        <div className="pt-api-workflow"><h3>Connect an HTTP workflow</h3><p>In n8n, add an HTTP Request node. Use the method and full URL from the operation’s template. Create a Header Auth credential with the header name <code>X-API-Key</code> and your key as its value.</p><ol><li>For a file operation, choose Form-Data. Add an n8n Binary File parameter using the exact field name from the request schema. Set Input Data Field Name to the incoming binary property. For multiple files, repeat the API field name.</li><li>Add text options as form fields. Fields described as JSON-encoded strings still belong in the multipart form. For JSON endpoints, choose a JSON body instead.</li><li>For a binary result, set Response Format to File. For JSON results, select JSON. Enable Include Response Headers and Status to inspect status and retry information.</li><li>Check <code>code</code>, <code>message</code>, <code>X-Request-ID</code>, and <code>Retry-After</code>. Do not automatically retry processing requests after an uncertain result.</li></ol><p><a href="https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/">HTTP Request node documentation</a></p><p>AI/workflow clients can import the OpenAPI document and use the same authenticated HTTP requests. Only operations explicitly marked for async support can be submitted as jobs.</p></div>
        <div className="pt-api-base"><span>Your API base</span><code>{endpointUrl("/api/v1")}</code><p>Authenticate with <code>X-API-Key</code> or <code>Authorization: Bearer</code>. Keep keys in server or workflow credentials. Request templates use placeholder inputs; check the exact schema before running them.</p></div>
    </section>;
}
