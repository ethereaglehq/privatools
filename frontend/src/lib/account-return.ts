/** Optional navigation only: this never represents authentication or grants access. */
const KEY = "privatools.account-return";
const MAX_AGE_MS = 15 * 60 * 1000;
const DESTINATIONS = new Set(["/account/settings", "/account/keys"]);

export function safeAccountReturn(value: string | null | undefined): string | null {
  return value && DESTINATIONS.has(value) ? value : null;
}

export function captureAccountReturn(search: string): void {
  const query = new URLSearchParams(search);
  if (!query.has("next")) return;
  const path = safeAccountReturn(query.get("next"));
  try {
    if (path) sessionStorage.setItem(KEY, JSON.stringify({ path, savedAt: Date.now() }));
    else sessionStorage.removeItem(KEY);
  } catch { /* Navigation remains optional when storage is unavailable. */ }
}

export function consumeAccountReturn(): string | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    sessionStorage.removeItem(KEY);
    if (!raw) return null;
    const value = JSON.parse(raw);
    if (typeof value.savedAt !== "number" || Date.now() < value.savedAt || Date.now() - value.savedAt > MAX_AGE_MS) return null;
    return safeAccountReturn(value.path);
  } catch { return null; }
}

export function clearAccountReturn(): void {
  try { sessionStorage.removeItem(KEY); } catch { /* Optional state. */ }
}
