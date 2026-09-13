/**
 * Consent-controlled Google tag. The tag owns browser sessions, first visits
 * and measured engagement; we send only canonical page views and existing
 * successful-tool signals. The old Measurement Protocol sender is not used.
 *
 * Enable the server switch only after checking the approved automatic-event
 * settings and disabling automatic user-provided data. Scroll, outbound clicks
 * and video measurement are retained. See deploy/analytics.md.
 */
import { ANALYTICS_CONSENT_KEY, ANALYTICS_OPT_OUT_KEY, GOOGLE_ANALYTICS_ID, googleAnalyticsAvailable, readAnalyticsPrivacyPreference, setAnalyticsRegionalDefault } from "./analyticsPrivacy";

type Gtag = (...args: unknown[]) => void;
type AnalyticsWindow = Window & { dataLayer?: unknown[]; gtag?: Gtag; ptSetAnalyticsDisabled?: (disabled: boolean) => void };
const SCRIPT_ID = "privatools-google-analytics";
const TOOL_SUCCESS_EVENT = "privatools:tool-success";
const PUBLIC_BASE = "https://privatools.me";
const PUBLIC_PAGES = new Set(["/", "/tools", "/pipeline", "/batch", "/ai", "/api", "/trust", "/security", "/status", "/support", "/about", "/privacy", "/terms", "/blog", "/compare"]);
let active = false;
let configured = false;
let lastPath = "";
let enabled = false;

function pathNow(): string {
    const hash = location.hash.replace(/^#/, "");
    const raw = hash.startsWith("/") ? hash : location.pathname;
    return raw.split("?")[0].split("#")[0].replace(/\/+$/, "") || "/";
}
export function isPublicAnalyticsPath(path: string): boolean {
    return PUBLIC_PAGES.has(path) || /^\/(?:tools?|blog|compare)\/[a-z0-9-]+$/.test(path);
}
function allowed(): boolean {
    return import.meta.env.PROD && googleAnalyticsAvailable() && !readAnalyticsPrivacyPreference().effectiveDisabled && isPublicAnalyticsPath(pathNow());
}
function disable(): void {
    enabled = false;
    (window as unknown as Record<string, unknown>)[`ga-disable-${GOOGLE_ANALYTICS_ID}`] = true;
}
function safeTitle(): string {
    // Route-derived titles cannot include filenames or text entered into tools.
    const path = pathNow();
    return path === "/" ? "PrivaTools" : `${path.split("/").filter(Boolean).join(" / ").replace(/-/g, " ")} — PrivaTools`;
}
function safeReferrer(): string {
    try {
        const ref = new URL(document.referrer);
        return ref.origin === PUBLIC_BASE && isPublicAnalyticsPath(ref.pathname) ? `${PUBLIC_BASE}${ref.pathname}` : "";
    } catch { return ""; }
}
function pageParameters(): Record<string, unknown> {
    return { page_location: `${PUBLIC_BASE}${pathNow()}`, page_title: safeTitle(), page_referrer: lastPath ? `${PUBLIC_BASE}${lastPath}` : safeReferrer() };
}
function bootTag(): Gtag | undefined {
    if (!allowed()) { disable(); return; }
    const win = window as AnalyticsWindow;
    win.dataLayer ||= [];
    // Google’s documented dataLayer queue uses IArguments, not an array message.
    // eslint-disable-next-line prefer-rest-params
    win.gtag ||= function () { win.dataLayer!.push(arguments); };
    const tag = win.gtag;
    if (!configured) {
        // Queue privacy settings before loading the script. Never grant ads.
        tag("consent", "default", { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
        tag("js", new Date());
        // Config-scoped page fields override later global `set` updates. Keep
        // route metadata global so retained automatic events follow SPA moves.
        // Queue clean fields before config, so initial SDK events are clean too.
        tag("set", pageParameters());
        tag("config", GOOGLE_ANALYTICS_ID, { send_page_view: false, allow_google_signals: false,
            allow_ad_personalization_signals: false, cookie_flags: "SameSite=Lax;Secure" });
        configured = true;
    }
    (window as unknown as Record<string, unknown>)[`ga-disable-${GOOGLE_ANALYTICS_ID}`] = false;
    enabled = true;
    if (!document.getElementById(SCRIPT_ID)) {
        const script = document.createElement("script");
        script.id = SCRIPT_ID; script.async = true; script.referrerPolicy = "no-referrer";
        script.src = `https://www.googletagmanager.com/gtag/js?id=${GOOGLE_ANALYTICS_ID}`;
        script.onerror = () => { disable(); script.remove(); };
        document.head.appendChild(script);
    }
    return tag;
}
export function sendPageview(): void {
    if (typeof window === "undefined") return;
    if (!allowed()) { disable(); return; }
    const path = pathNow();
    const tag = bootTag();
    if (!tag || path === lastPath) return;
    const params = pageParameters();
    // Update defaults as well so the tag's own lifecycle uses the same clean URL.
    tag("set", params);
    tag("event", "page_view", { ...params, send_to: GOOGLE_ANALYTICS_ID });
    lastPath = path;
}
export function startPageviewTracking(): () => void {
    if (typeof window === "undefined" || active) return () => {};
    active = true;
    const win = window as AnalyticsWindow;
    const previousPrivacyHandler = win.ptSetAnalyticsDisabled;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const sync = () => {
        if (!allowed()) {
            // ga-disable takes effect immediately, including the tag's own events.
            disable();
            if (configured) win.gtag?.("consent", "update", { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
            return;
        }
        if (configured && !enabled) win.gtag?.("consent", "update", { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
        sendPageview();
    };
    const onNav = () => {
        // Block private paths synchronously before awaiting React's route update.
        if (!allowed()) { disable(); if (!isPublicAnalyticsPath(pathNow())) lastPath = ""; }
        clearTimeout(timer); timer = setTimeout(sync, 0);
    };
    const onStorage = (event: StorageEvent) => {
        if (event.key === null || event.key === ANALYTICS_OPT_OUT_KEY || event.key === ANALYTICS_CONSENT_KEY) sync();
    };
    const onToolSuccess = () => {
        if (!allowed() || !/^\/tools?\//.test(pathNow())) return;
        sendPageview();
        // Never pass CustomEvent.detail (which could contain a label or filename).
        win.gtag?.("event", "tool_success", { page_location: `${PUBLIC_BASE}${pathNow()}`, page_title: safeTitle(), send_to: GOOGLE_ANALYTICS_ID });
    };
    win.ptSetAnalyticsDisabled = sync;
    sync();
    const policyAbort = new AbortController();
    let policyTimer: ReturnType<typeof setTimeout> | undefined;
    // Same-origin endpoint, independent of the optional processing API host.
    // No tag while an unknown region is pending. Failure keeps opt-in mode.
    if (import.meta.env.PROD && googleAnalyticsAvailable() && isPublicAnalyticsPath(pathNow())) {
        policyTimer = setTimeout(() => policyAbort.abort(), 3000);
        void fetch("/api/analytics/policy", { credentials: "omit", cache: "no-store", signal: policyAbort.signal })
            .then(response => response.ok ? response.json() : null)
            .then(policy => { if (!policyAbort.signal.aborted) { setAnalyticsRegionalDefault(policy?.mode === "default_on"); sync(); } })
            .catch(() => {})
            .finally(() => clearTimeout(policyTimer));
    }
    window.addEventListener("storage", onStorage);
    window.addEventListener("popstate", onNav);
    window.addEventListener("hashchange", onNav);
    window.addEventListener("pageshow", sync);
    window.addEventListener(TOOL_SUCCESS_EVENT, onToolSuccess);
    return () => {
        active = false; clearTimeout(timer); clearTimeout(policyTimer); policyAbort.abort(); disable();
        window.removeEventListener("storage", onStorage);
        window.removeEventListener("popstate", onNav);
        window.removeEventListener("hashchange", onNav);
        window.removeEventListener("pageshow", sync);
        window.removeEventListener(TOOL_SUCCESS_EVENT, onToolSuccess);
        if (win.ptSetAnalyticsDisabled === sync) win.ptSetAnalyticsDisabled = previousPrivacyHandler;
    };
}
