export type Target = "srt" | "vtt";

interface Cue { index: number; start: number; end: number; text: string }

function parseTime(t: string): number {
    const match = t.trim().replace(",", ".").match(/^(?:(\d+):)?(\d{2}):(\d{2})(?:\.(\d+))?$/);
    if (!match || +match[2] > 59 || +match[3] > 59) throw new Error(`Invalid subtitle timestamp: ${t}`);
    return +(match[1] || 0) * 3600 + +match[2] * 60 + +match[3] + (match[4] ? Number(`0.${match[4]}`) : 0);
}

function formatTime(sec: number, sep: "," | "."): string {
    const total = Math.round(sec*1000), h=Math.floor(total/3_600_000), m=Math.floor(total/60_000)%60, s=Math.floor(total/1000)%60, ms=total%1000;
    return `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}${sep}${String(ms).padStart(3,"0")}`;
}

function parseSrtVtt(text: string): Cue[] {
    const body = text.replace(/^\uFEFF/, "").replace(/^WEBVTT[^\n]*\n/, "").trim();
    const blocks = body.split(/\r?\n\r?\n+/).filter(Boolean);
    const cues: Cue[] = [];
    for (const blk of blocks) {
        const lines = blk.split(/\r?\n/);
        let idx = cues.length + 1;
        let timeLine = lines[0];
        const hasIdentifier = !lines[0].includes("-->") && Boolean(lines[1]?.includes("-->"));
        if (hasIdentifier) { if (/^\d+$/.test(lines[0])) idx = +lines[0]; timeLine = lines[1]; }
        const m = timeLine.match(/^([\d:.,]+)\s*-->\s*([\d:.,]+)/);
        if (!m) { if (/^(NOTE|STYLE|REGION)(?:\s|$)/.test(lines[0])) continue; throw new Error("A subtitle block has no valid timing line. Check its cue identifier and timestamps."); }
        const text = lines.slice(hasIdentifier ? 2 : 1).join("\n");
        const start = parseTime(m[1]), end = parseTime(m[2]);
        if (end < start) throw new Error(`Cue ${idx} ends before it starts.`);
        cues.push({ index: idx, start, end, text });
    }
    return cues;
}

function parseAss(text: string): Cue[] {
    const lines = text.split(/\r?\n/);
    const cues: Cue[] = [];
    for (const line of lines) {
        if (!line.startsWith("Dialogue:")) continue;
        const parts = line.slice(9).split(",");
        if (parts.length < 10) continue;
        const start = parseTime(parts[1].trim());
        const end = parseTime(parts[2].trim());
        const txt = parts.slice(9).join(",").replace(/\\N/g, "\n").replace(/\{[^}]+\}/g, "");
        cues.push({ index: cues.length + 1, start, end, text: txt });
    }
    return cues;
}

function toSrt(cues: Cue[]): string {
    return cues.map(c => `${c.index}\n${formatTime(c.start, ",")} --> ${formatTime(c.end, ",")}\n${c.text}`).join("\n\n") + "\n";
}

function toVtt(cues: Cue[]): string {
    return "WEBVTT\n\n" + cues.map(c => `${formatTime(c.start, ".")} --> ${formatTime(c.end, ".")}\n${c.text}`).join("\n\n") + "\n";
}

export function convertSubtitles(text: string, target: Target): { ok: boolean; output: string; count: number; error: string } {
    if (!text.trim()) return { ok: false, output: "", count: 0, error: "Upload a subtitle file." };
    try {
        const isAss = /^\[Script Info\]/.test(text) || /^Dialogue:/m.test(text);
        const cues = isAss ? parseAss(text) : parseSrtVtt(text);
        if (!cues.length) return { ok: false, output: "", count: 0, error: "Couldn't find any cues — is the file valid?" };
        const output = target === "srt" ? toSrt(cues) : toVtt(cues);
        return { ok: true, output, count: cues.length, error: "" };
    } catch (err) {
        return { ok: false, output: "", count: 0, error: err instanceof Error ? err.message : String(err) };
    }
}
