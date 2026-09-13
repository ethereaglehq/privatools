export interface HashResult { algo: string; value: string; }

export async function hashBytes(buffer: ArrayBuffer): Promise<HashResult[]> {
    return Promise.all(["SHA-1", "SHA-256", "SHA-512"].map(async algo => ({ algo, value: Array.from(new Uint8Array(await crypto.subtle.digest(algo, buffer))).map(n => n.toString(16).padStart(2, "0")).join("") })));
}
