/** Page selections use the same ordered, deduplicated semantics as /api/merge. */
export type MergeSelection = { pages: number[] | null; error: string | null };
export type MergeSourcePage = { filename: string; page: number };
export type MergeSourceMap = { outputPages: MergeSourcePage[] | null; excludedPages: { filename: string; pages: number[] }[] };

/** Snapshot identities in memory only, so result captions survive later state changes. */
export function mergeSourceMap(sources: { filename: string; total: number | null; range: string }[]): MergeSourceMap {
    const selections = sources.map(source => mergePageSelection(source.range, source.total));
    return {
        outputPages: selections.every(selection => selection.pages !== null && !selection.error)
            ? sources.flatMap((source, index) => selections[index].pages!.map(page => ({ filename: source.filename, page }))) : null,
        excludedPages: sources.flatMap((source, index) => {
            const selected = selections[index].pages;
            if (source.total === null || !selected || selections[index].error) return [];
            const included = new Set(selected);
            const pages = Array.from({ length: source.total }, (_, index) => index + 1).filter(page => !included.has(page));
            return pages.length ? [{ filename: source.filename, pages }] : [];
        }),
    };
}

export function compactMergePages(pages: number[]): string {
    const ranges: string[] = [];
    for (let index = 0; index < pages.length; index++) {
        const first = pages[index];
        while (index + 1 < pages.length && pages[index + 1] === pages[index] + 1) index++;
        ranges.push(first === pages[index] ? `${first}` : `${first}–${pages[index]}`);
    }
    return ranges.join(", ");
}

/** Existing workflow contract stores operation slugs only, never source data/settings. */
export function saveMergeWorkflow(storage: Pick<Storage, "getItem" | "setItem"> = localStorage): string {
    const key = "privatools_pipeline_saved";
    const saved: unknown = JSON.parse(storage.getItem(key) || "[]");
    if (!Array.isArray(saved)) throw new Error("Stored workflows could not be read.");
    const existing = saved.find(item => item && Array.isArray(item.slugs) && item.slugs.length === 1 && item.slugs[0] === "merge-pdf" && typeof item.name === "string");
    let name = existing?.name || "Merge PDFs";
    if (!existing) {
        for (let suffix = 2; saved.some(item => item?.name === name); suffix++) name = `Merge PDFs ${suffix}`;
    }
    const entry = { name, slugs: ["merge-pdf"], savedAt: Date.now() };
    storage.setItem(key, JSON.stringify([entry, ...saved.filter(item => item !== existing)].slice(0, 10)));
    return name;
}

export function mergePageSelection(value: string, total: number | null): MergeSelection {
    const spec = value.trim().toLowerCase();
    if (total !== null && total < 1) return { pages: null, error: "This PDF has no pages." };
    if (!spec || spec === "all") {
        return { pages: total === null ? null : Array.from({ length: total }, (_, i) => i + 1), error: null };
    }
    const out = new Set<number>();
    const read = (token: string): number => {
        if (!/^\d{1,9}$/.test(token) || Number(token) < 1) throw new Error("Use page numbers starting at 1.");
        const page = Number(token);
        if (total !== null && page > total) throw new Error(`This PDF has ${total} page${total === 1 ? "" : "s"}. Choose pages from 1 to ${total}.`);
        return page;
    };
    try {
        const tokens = spec.split(",").map(part => part.trim()).filter(Boolean);
        if (!tokens.length) throw new Error('Enter pages such as "1-3,5", or leave this blank for all.');
        for (const token of tokens) {
            if (token.includes("-")) {
                const parts = token.split("-").map(part => part.trim());
                if (parts.length !== 2 || (!parts[0] && !parts[1])) throw new Error('Use a range such as "1-3" or "2-end".');
                const first = parts[0] ? read(parts[0]) : 1;
                const last = !parts[1] || parts[1] === "end" ? total : read(parts[1]);
                if (last !== null && first > last) throw new Error("The first page in a range must come before the last.");
                // Unknown page counts still get syntax validation, without expanding an untrusted range.
                if (total !== null && last !== null) for (let page = first; page <= last; page++) out.add(page);
            } else if (token === "end") {
                if (total !== null) out.add(total);
            } else {
                const page = read(token);
                if (total !== null) out.add(page);
            }
        }
        return { pages: total === null ? null : [...out], error: null };
    } catch (error) {
        return { pages: null, error: error instanceof Error ? error.message : "Check the page range." };
    }
}

export function toggleMergePage(value: string, total: number, page: number): string | null {
    const selection = mergePageSelection(value, total);
    if (!selection.pages || selection.error) return null;
    const pages = selection.pages.includes(page)
        ? selection.pages.filter(number => number !== page)
        : [...selection.pages, page];
    // The merge API requires at least one page in each source. Empty means all there.
    if (!pages.length) return null;
    const isAllInOrder = pages.length === total && pages.every((number, index) => number === index + 1);
    return isAllInOrder ? "" : pages.join(",");
}

export function moveMergeFile<T>(files: T[], from: number, to: number): T[] {
    if (from < 0 || to < 0 || from >= files.length || to >= files.length || from === to) return files;
    const next = [...files];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    return next;
}

export function mergeOutputFilename(input: string, fallback = "Combined.pdf"): string {
    const printable = Array.from(input).filter(character => character.charCodeAt(0) >= 32 && character.charCodeAt(0) !== 127).join("");
    const clean = printable.replace(/[/\\:*?"<>|]/g, "").trim().replace(/\.+$/, "");
    if (!clean) return fallback;
    const stem = clean.replace(/\.pdf$/i, "").slice(0, 180);
    return stem ? `${stem}.pdf` : fallback;
}
