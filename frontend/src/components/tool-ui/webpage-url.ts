export function normalizeWebpageUrl(value: string): string | null {
    const trimmed=value.trim(); if(!trimmed) return null;
    try { const url=new URL(/^[a-z][a-z0-9+.-]*:/i.test(trimmed) ? trimmed : `https://${trimmed}`); return (url.protocol === "https:" || url.protocol === "http:") && !url.username && !url.password ? url.href : null; } catch { return null; }
}
