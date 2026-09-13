export const ANALYTICS_CONSENT_KEY = "pt-analytics-consent-v1";
export const ANALYTICS_OPT_OUT_KEY = "pt-analytics-opt-out";
export const GOOGLE_ANALYTICS_ID = "G-B3VWQ44MX1";

type PrivacyNavigator = Navigator & {
  globalPrivacyControl?: boolean;
  msDoNotTrack?: string | null;
};

type AnalyticsWindow = Window & typeof globalThis & {
  doNotTrack?: string | null;
  ptSetAnalyticsDisabled?: (disabled: boolean) => void;
};

let regionalDefault = false;
let documentOptOut = false;

export interface AnalyticsPrivacyPreference {
  regionalDefault: boolean;
  consented: boolean;
  localOptOut: boolean;
  browserPrivacySignal: boolean;
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

export function hasBrowserAnalyticsPrivacySignal(): boolean {
  if (typeof window === "undefined") return true;
  const nav = window.navigator as PrivacyNavigator;
  const win = window as AnalyticsWindow;
  const dnt = nav.doNotTrack ?? nav.msDoNotTrack ?? win.doNotTrack;

  return nav.globalPrivacyControl === true || dnt === "1" || dnt === "yes";
}

export function readAnalyticsPrivacyPreference(): AnalyticsPrivacyPreference {
  if (typeof window === "undefined") {
    return { regionalDefault: false, consented: false, localOptOut: false, browserPrivacySignal: true, effectiveDisabled: true };
  }

  let consented = false;
  try {
    const record = JSON.parse(localStorage.getItem(ANALYTICS_CONSENT_KEY) || "null");
    consented = record?.version === 1 && typeof record.grantedAt === "number" && record.grantedAt > 0;
  } catch { /* no affirmative consent */ }
  const localOptOut = readOptOutStorage();
  const browserPrivacySignal = hasBrowserAnalyticsPrivacySignal();

  return {
    regionalDefault,
    consented,
    localOptOut,
    browserPrivacySignal,
    effectiveDisabled: (!consented && !regionalDefault) || localOptOut || browserPrivacySignal,
  };
}

export function setAnalyticsOptOut(optOut: boolean): AnalyticsPrivacyPreference {
  if (typeof window === "undefined") {
    return { regionalDefault: false, consented: false, localOptOut: optOut, browserPrivacySignal: true, effectiveDisabled: true };
  }

  // Withdrawal must work immediately even if the browser denies storage.
  documentOptOut = optOut;
  try {
    if (optOut) {
      window.localStorage.setItem(ANALYTICS_OPT_OUT_KEY, "1");
      window.localStorage.removeItem(ANALYTICS_CONSENT_KEY);
    } else {
      window.localStorage.removeItem(ANALYTICS_OPT_OUT_KEY);
      window.localStorage.setItem(ANALYTICS_CONSENT_KEY, JSON.stringify({ version: 1, grantedAt: Date.now() }));
    }
  } catch {
    // localStorage can throw in private browsing or when storage is disabled.
  }

  const next = readAnalyticsPrivacyPreference();
  const win = window as AnalyticsWindow & Record<string, boolean>;
  win[`ga-disable-${GOOGLE_ANALYTICS_ID}`] = next.effectiveDisabled;
  win.ptSetAnalyticsDisabled?.(next.effectiveDisabled);

  return next;
}

/** Operator safety switch; off until the public tag configuration is verified. */
export function googleAnalyticsAvailable(): boolean {
  return typeof document !== "undefined" && document.querySelector('meta[name="privatools:google-analytics"]')?.getAttribute("content") === "enabled";
}

/** A server-reviewed regional default is not recorded as affirmative consent. */
export function setAnalyticsRegionalDefault(value: boolean): void {
  regionalDefault = value === true;
  if (typeof window !== "undefined") window.dispatchEvent(new Event("privatools:analytics-policy"));
}
