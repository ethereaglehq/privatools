/** Aggregate per-file download events. 100% means the pipeline reported ready. */
export function modelProgress(onProgress: (percent: number) => void, expectedBytes = 0) {
    const files = new Map<string, { loaded: number; total: number }>();
    let best = 0;
    return (info: { status: string; file?: string; loaded?: number; total?: number }) => {
        if (info.status === "ready") { best = 100; onProgress(100); return; }
        if (info.status === "progress" && info.file && typeof info.loaded === "number" && typeof info.total === "number" && info.total > 0) {
            files.set(info.file, { loaded: info.loaded, total: info.total });
        } else if (info.status === "done" && info.file) {
            const file = files.get(info.file); if (file) file.loaded = file.total;
        } else return;
        let loaded = 0, total = 0;
        for (const file of files.values()) { loaded += file.loaded; total += file.total; }
        const percent = Math.min(99, Math.round(loaded / Math.max(1, total, expectedBytes) * 100));
        if (percent > best) { best = percent; onProgress(percent); }
    };
}
