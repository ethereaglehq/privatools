/** Deliberately bounded config syntax. Unsupported YAML/TOML fails instead of losing data. */
export function stripConfigComment(text: string): string {
    let quote = "";
    for (let i = 0; i < text.length; i++) {
        const c = text[i];
        if (quote) { if (c === "\\" && quote === '"') i++; else if (c === quote) { if (quote === "'" && text[i + 1] === "'") i++; else quote = ""; } }
        else if (c === '"' || c === "'") quote = c;
        else if (c === "#" && (!i || /\s/.test(text[i - 1]))) return text.slice(0, i).trimEnd();
    }
    return text.trimEnd();
}
function splitFlow(text: string): string[] {
    const parts: string[] = []; let quote = "", depth = 0, start = 0;
    for (let i = 0; i < text.length; i++) { const c = text[i]; if (quote) { if (c === "\\" && quote === '"') i++; else if (c === quote) quote = ""; } else if (c === '"' || c === "'") quote = c; else if (c === "[" || c === "{") depth++; else if (c === "]" || c === "}") depth--; else if (c === "," && depth === 0) { parts.push(text.slice(start, i)); start = i + 1; } }
    if (quote || depth !== 0) throw new Error("Check closing quotes and brackets.");
    if (text.slice(start).trim()) parts.push(text.slice(start));
    return parts;
}
export function parseConfigScalar(raw: string): unknown {
    const value = raw.trim();
    if (value.startsWith('"')) { try { return JSON.parse(value); } catch { throw new Error("Use a complete double-quoted string with valid escapes."); } }
    if (value.startsWith("'")) { if (!value.endsWith("'") || value.length < 2) throw new Error("A single-quoted string is not closed."); return value.slice(1, -1).replace(/''/g, "'"); }
    if (/^(?:true|false|null|~)$/.test(value)) return value === "true" ? true : value === "false" ? false : null;
    if (/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(value)) { const number = Number(value); if (!Number.isFinite(number) || (Number.isInteger(number) && !Number.isSafeInteger(number))) throw new Error("Quote numbers outside JavaScript's safe range to preserve them exactly."); return number; }
    if (value.startsWith("[")) { if (!value.endsWith("]")) throw new Error("An array is not closed."); return splitFlow(value.slice(1, -1)).map(parseConfigScalar); }
    if (value.startsWith("{")) { try { return JSON.parse(value); } catch { throw new Error("Inline objects must use JSON-style quoted keys."); } }
    if (/^[&*!|>]/.test(value)) throw new Error("Anchors, tags and multiline scalar syntax are not supported in this editor.");
    return value;
}
function colonAt(text: string) {
    let quote = "";
    for (let i = 0; i < text.length; i++) { const c = text[i]; if (quote) { if (c === "\\" && quote === '"') i++; else if (c === quote) quote = ""; } else if (c === '"' || c === "'") quote = c; else if (c === ":" && (i + 1 === text.length || /\s/.test(text[i + 1]))) return i; }
    return -1;
}
export function parseYaml(text: string): unknown {
    const lines: {indent:number; text:string; line:number}[] = []; let marker = false, ended = false;
    for (const [index, raw] of text.replace(/^\uFEFF/, "").split(/\r?\n/).entries()) {
        const clean = stripConfigComment(raw); if (!clean.trim()) continue;
        if (/^\s*\t/.test(clean)) throw new Error(`Use spaces for indentation on line ${index + 1}.`);
        if (clean.trim() === "---") { if (marker || lines.length) throw new Error("Only one YAML document can be converted at a time."); marker = true; continue; }
        if (clean.trim() === "...") { ended = true; continue; }
        if (ended) throw new Error("Unexpected content after the YAML document end.");
        lines.push({indent:clean.match(/^ */)![0].length,text:clean.trim(),line:index+1});
    }
    if (!lines.length) return null;
    let cursor = 0;
    function node(indent: number): unknown {
        const current = lines[cursor]; if (!current || current.indent < indent) return null;
        const list = /^-(?:\s|$)/.test(current.text);
        if (!list && colonAt(current.text) < 0) { cursor++; return parseConfigScalar(current.text); }
        const output: unknown[] | Record<string, unknown> = list ? [] : Object.create(null);
        while (cursor < lines.length && lines[cursor].indent === indent) {
            const line = lines[cursor];
            if (list) {
                if (!/^-(?:\s|$)/.test(line.text)) throw new Error(`Mixed list and mapping on line ${line.line}.`);
                const rest = line.text.slice(1).trim(); cursor++;
                if (!rest) (output as unknown[]).push(cursor < lines.length && lines[cursor].indent > indent ? node(lines[cursor].indent) : null);
                else if (colonAt(rest) >= 0) { lines.splice(cursor, 0, {...line, indent:indent + 2, text:rest}); (output as unknown[]).push(node(indent + 2)); }
                else (output as unknown[]).push(parseConfigScalar(rest));
            } else {
                const colon = colonAt(line.text); if (colon < 0) throw new Error(`Expected key: value on line ${line.line}.`);
                const rawKey = line.text.slice(0, colon).trim(); const key = rawKey.startsWith('"') || rawKey.startsWith("'") ? String(parseConfigScalar(rawKey)) : rawKey;
                if (!key || key === "<<" || Object.prototype.hasOwnProperty.call(output, key)) throw new Error(`Empty, duplicate or merge key on line ${line.line}.`);
                const value = line.text.slice(colon + 1).trim(); cursor++;
                (output as Record<string, unknown>)[key] = value ? parseConfigScalar(value) : cursor < lines.length && lines[cursor].indent > indent ? node(lines[cursor].indent) : null;
            }
            if (cursor < lines.length && lines[cursor].indent > indent) throw new Error(`Unexpected indentation on line ${lines[cursor].line}.`);
        }
        return output;
    }
    const result = node(lines[0].indent);
    if (cursor !== lines.length) throw new Error(`Couldn't read line ${lines[cursor].line}. Check its indentation.`);
    return result;
}
export function writeYaml(value: unknown, indent = 0): string {
    const pad = " ".repeat(indent);
    if (value === null) return "null";
    if (typeof value === "string") return JSON.stringify(value);
    if (typeof value !== "object") return JSON.stringify(value);
    const entries = Array.isArray(value) ? value.map(v => ["-", v] as const) : Object.entries(value as Record<string,unknown>);
    if (!entries.length) return Array.isArray(value) ? "[]" : "{}";
    return entries.map(([key, nested]) => {
        const prefix = Array.isArray(value) ? "-" : `${/^[A-Za-z_][\w-]*$/.test(key) ? key : JSON.stringify(key)}:`;
        if (nested && typeof nested === "object" && Object.keys(nested).length) return `${pad}${prefix}\n${writeYaml(nested, indent + 2)}`;
        return `${pad}${prefix} ${writeYaml(nested, indent + 2)}`;
    }).join("\n");
}
export function parseTomlConfig(text: string): Record<string, unknown> {
    const root: Record<string,unknown> = Object.create(null); let section = root;
    for (const raw of text.split(/\r?\n/)) {
        const line = stripConfigComment(raw).trim(); if (!line) continue;
        if (line.startsWith("[")) {
            if (!/^\[[\w-]+(?:\.[\w-]+)*\]$/.test(line)) throw new Error("Use simple table names. Array tables and quoted table paths are not supported.");
            section = root;
            for (const part of line.slice(1,-1).split(".")) { if (Object.prototype.hasOwnProperty.call(section,part) && (!section[part] || typeof section[part] !== "object" || Array.isArray(section[part]))) throw new Error(`Table ${part} conflicts with an existing value.`); if (!Object.prototype.hasOwnProperty.call(section,part)) section[part] = Object.create(null); section = section[part] as Record<string,unknown>; }
        } else {
            const match = line.match(/^([\w-]+|"(?:\\.|[^"\\])*"|'[^']*')\s*=\s*(.+)$/);
            if (!match) throw new Error("Expected a simple key = value. Dotted keys and multiline values are not supported.");
            const key = /^["']/.test(match[1]) ? String(parseConfigScalar(match[1])) : match[1];
            if (Object.prototype.hasOwnProperty.call(section,key)) throw new Error(`Duplicate key: ${key}`);
            const value = parseConfigScalar(match[2]);
            if (value === null || (typeof value === "string" && !/^["']/.test(match[2]) && !/^\d{4}-\d\d-\d\d/.test(match[2]))) throw new Error(`Quote the string value for ${key}.`);
            section[key] = value;
        }
    }
    return root;
}
export function writeToml(value: unknown): string {
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("TOML needs a mapping at the document root.");
    const lines: string[] = [];
    const keyText = (key:string) => /^[\w-]+$/.test(key) ? key : JSON.stringify(key);
    const scalar = (item:unknown): string => { if (item === null) throw new Error("TOML has no null value. Remove or replace null values before converting."); if (Array.isArray(item)) return `[${item.map(scalar).join(", ")}]`; if (typeof item === "object") throw new Error("Arrays of objects require TOML array tables, which this editor does not support."); return JSON.stringify(item); };
    function walk(obj: Record<string,unknown>, path: string[]) { if (path.length) lines.push(`\n[${path.map(keyText).join(".")}]`); for (const [key, item] of Object.entries(obj)) if (!item || typeof item !== "object" || Array.isArray(item)) lines.push(`${keyText(key)} = ${scalar(item)}`); for (const [key, item] of Object.entries(obj)) if (item && typeof item === "object" && !Array.isArray(item)) walk(item as Record<string,unknown>, [...path,key]); }
    walk(value as Record<string,unknown>, []); return lines.join("\n").trim();
}
