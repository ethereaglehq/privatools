export const ANALYTICS_OPT_OUT_KEY = "pt-analytics-opt-out";
export const GOOGLE_ANALYTICS_ID = "G-B3VWQ44MX1";

type AnalyticsWindow = Window & typeof globalThis & {
  ptSetAnalyticsDisabled?: (disabled: boolean) => void;
};

let documentOptOut = false;

/** Analytics runs by default; the saved opt-out is the visitor's only switch. */
export interface AnalyticsPrivacyPreference {
  localOptOut: boolean;
  effectiveDisabled: boolean;
}

function readOptOutStorage(): boolean {
  if (documentOptOut) return true;
  try {
    return window.localStorage.getItem(ANALYTICS_OPT_OUT_KEY) === "1";
  } catch {
    return false;
  }
}

export function readAnalyticsPrivacyPreference(): AnalyticsPrivacyPreference {
  if (typeof window === "undefined") return { localOptOut: false, effectiveDisabled: true };
  const localOptOut = readOptOutStorage();
  return { localOptOut, effectiveDisabled: localOptOut };
}

export function setAnalyticsOptOut(optOut: boolean): AnalyticsPrivacyPreference {
  if (typeof window === "undefined") return { localOptOut: optOut, effectiveDisabled: true };

  // Withdrawal must work immediately even if the browser denies storage.
  documentOptOut = optOut;
  try {
    if (optOut) window.localStorage.setItem(ANALYTICS_OPT_OUT_KEY, "1");
    else window.localStorage.removeItem(ANALYTICS_OPT_OUT_KEY);
  } catch {
    // localStorage can throw in private browsing or when storage is disabled.
  }

  const next = readAnalyticsPrivacyPreference();
  const win = window as AnalyticsWindow & Record<string, unknown>;
  win[`ga-disable-${GOOGLE_ANALYTICS_ID}`] = next.effectiveDisabled;
  win.ptSetAnalyticsDisabled?.(next.effectiveDisabled);

  return next;
}

/** Operator safety switch; the server sets it only after the public tag configuration is verified. */
export function googleAnalyticsAvailable(): boolean {
  return typeof document !== "undefined" && document.querySelector('meta[name="privatools:google-analytics"]')?.getAttribute("content") === "enabled";
}
