export type Delimiter = "," | ";" | "\t" | "|";

export function parseCsv(text: string, delimiter: string): string[][] {
    if (!text.length) return [];
    const rows: string[][] = []; let row: string[] = [], field = "", quoted = false, closed = false;
    text = text.replace(/^\uFEFF/, "");
    for (let i = 0; i < text.length; i++) {
        const c = text[i];
        if (quoted) {
            if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else { quoted = false; closed = true; } }
            else field += c;
        } else if (c === '"') {
            if (field || closed) throw new Error(`Unexpected quote near character ${i + 1}. Quote the whole field and double quotes inside it.`);
            quoted = true;
        } else if (c === delimiter) { row.push(field); field = ""; closed = false; }
        else if (c === "\n" || c === "\r") {
            if (c === "\r" && text[i + 1] === "\n") i++;
            row.push(field); rows.push(row); row = []; field = ""; closed = false;
        } else { if (closed) throw new Error(`Unexpected text after a quoted field near character ${i + 1}.`); field += c; }
    }
    if (quoted) throw new Error("An opening quote has no closing quote. Check the last quoted field.");
    if (row.length || field.length || closed) { row.push(field); rows.push(row); }
    return rows;
}

export function detectDelimiter(csv: string): Delimiter {
    const candidates: Delimiter[] = [",", ";", "\t", "|"];
    const counts = new Map(candidates.map(d => [d, 0])); let quoted = false;
    for (let i = 0; i < csv.length; i++) {
        const c = csv[i];
        if (c === '"') { if (quoted && csv[i + 1] === '"') i++; else quoted = !quoted; }
        else if (!quoted && (c === "\r" || c === "\n")) break;
        else if (!quoted && counts.has(c as Delimiter)) counts.set(c as Delimiter, counts.get(c as Delimiter)! + 1);
    }
    return candidates.reduce((best, d) => counts.get(d)! > counts.get(best)! ? d : best, ",");
}

export function csvToJson(csv: string, delimiter: string): string {
    const [headers, ...rows] = parseCsv(csv, delimiter);
    if (!headers) return "[]";
    if (headers.some(h => !h.trim())) throw new Error("Every column needs a name in the first row.");
    if (new Set(headers).size !== headers.length) throw new Error("Column names must be unique so no values are lost.");
    return JSON.stringify(rows.map((values, index) => {
        if (values.length !== headers.length) throw new Error(`Row ${index + 2} has ${values.length} fields; the header has ${headers.length}. Check the delimiter or quote fields that contain it.`);
        return Object.fromEntries(headers.map((header, i) => [header, values[i]]));
    }), null, 2);
}

export function jsonToCsv(json: string, delimiter: string): string {
    const data: unknown = JSON.parse(json);
    if (!Array.isArray(data) || data.some(row => !row || typeof row !== "object" || Array.isArray(row))) throw new Error("Use a JSON array of objects, such as [{\"name\":\"Alex\"}].");
    if (!data.length) return "";
    const headers = [...new Set(data.flatMap(row => Object.keys(row)))];
    const escape = (value: unknown) => { const text = value == null ? "" : typeof value === "object" ? JSON.stringify(value) : String(value); return text.includes(delimiter) || /["\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text; };
    return [headers.map(escape).join(delimiter), ...data.map(row => headers.map(header => escape(row[header])).join(delimiter))].join("\r\n");
}
