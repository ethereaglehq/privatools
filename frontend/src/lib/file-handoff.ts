/** Previous releases stored one base64 file here. Only read it for migration. */
export const FILE_HANDOFF_KEY = "privatools.file-handoff";

const MAX_HANDOFF_AGE_MS = 10 * 60 * 1000;

type FileHandoff = {
  files: File[];
  targetSlug?: string;
  createdAt: number;
};

// Same-document navigation keeps File references intact. File bytes never go
// to storage, a server, or a base64 string, and the storage quota is irrelevant.
let pending: FileHandoff | null = null;
let expiryTimer: ReturnType<typeof setTimeout> | undefined;

function clearLegacyPayload(): void {
  try { sessionStorage.removeItem(FILE_HANDOFF_KEY); } catch { /* Storage may be disabled. */ }
}

export function clearFileHandoffs(): void {
  pending = null;
  if (expiryTimer !== undefined) clearTimeout(expiryTimer);
  expiryTimer = undefined;
  clearLegacyPayload();
}

/** Replace the entire pending selection, preserving order and distinct files. */
export async function storeFileHandoffs(files: readonly File[], targetSlug?: string): Promise<boolean> {
  clearFileHandoffs();
  if (!files.length) return false;
  pending = { files: [...files], targetSlug, createdAt: Date.now() };
  expiryTimer = setTimeout(clearFileHandoffs, MAX_HANDOFF_AGE_MS);
  return true;
}

/** Compatibility entry point for clipboard, samples, and result chaining. */
export async function storeFileHandoff(file: File, targetSlug?: string): Promise<boolean> {
  return storeFileHandoffs([file], targetSlug);
}

function isFresh(createdAt: number): boolean {
  const age = Date.now() - createdAt;
  return Number.isFinite(createdAt) && age >= 0 && age < MAX_HANDOFF_AGE_MS;
}

function matchesTarget(handoff: FileHandoff, targetSlug?: string): boolean {
  // A targeted selection can only be claimed by its destination. Older
  // unscoped single-file callers continue to work without a destination.
  return !handoff.targetSlug || handoff.targetSlug === targetSlug;
}

function readPending(): FileHandoff | null {
  if (pending) {
    if (!isFresh(pending.createdAt)) clearFileHandoffs();
    return pending;
  }

  try {
    const raw = sessionStorage.getItem(FILE_HANDOFF_KEY);
    if (!raw) return null;
    const payload = JSON.parse(raw);
    if (!payload || typeof payload.name !== "string" || !payload.name
      || typeof payload.data !== "string" || !payload.data.startsWith("data:")
      || typeof payload.createdAt !== "number" || !isFresh(payload.createdAt)
      || (payload.type !== undefined && typeof payload.type !== "string")
      || (payload.targetSlug !== undefined && typeof payload.targetSlug !== "string")) {
      clearLegacyPayload();
      return null;
    }
    return {
      files: [dataUrlToFile(payload.data, payload.name, payload.type)],
      targetSlug: payload.targetSlug,
      createdAt: payload.createdAt,
    };
  } catch {
    clearLegacyPayload();
    return null;
  }
}

/** Claim the complete selection once. A different tool leaves it untouched. */
export async function consumeFileHandoffs(targetSlug?: string): Promise<File[]> {
  const handoff = readPending();
  if (!handoff || !matchesTarget(handoff, targetSlug)) return [];
  clearFileHandoffs();
  return handoff.files;
}

/** Single-file tools must not take the first file and silently lose the rest. */
export async function consumeFileHandoff(targetSlug?: string): Promise<File | null> {
  const handoff = readPending();
  if (!handoff || handoff.files.length !== 1 || !matchesTarget(handoff, targetSlug)) return null;
  clearFileHandoffs();
  return handoff.files[0];
}

function dataUrlToFile(dataUrl: string, name: string, type?: string): File {
  const comma = dataUrl.indexOf(",");
  if (comma === -1) throw new Error("Malformed data URL");
  const header = dataUrl.slice(0, comma);
  const body = dataUrl.slice(comma + 1);
  const mime = type || header.match(/^data:([^;,]*)/)?.[1] || "application/octet-stream";

  // ArrayBuffer-backed, which Blob and File accept (TypeScript 5.9 lib.dom).
  let bytes: Uint8Array<ArrayBuffer>;
  if (/;base64/i.test(header)) {
    const bin = atob(body);
    bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  } else {
    bytes = new TextEncoder().encode(decodeURIComponent(body));
  }
  return new File([bytes], name, { type: mime, lastModified: Date.now() });
}
