/**
 * Default-on Google tag with manual, sanitized events. The tag owns browser
 * sessions, first visits and measured engagement; we send canonical page
 * views, the existing successful-tool signal and one `tool_run` per tool use.
 * The saved opt-out on the Privacy page is the only visitor switch.
 *
 * Enable the server switch only after checking the approved automatic-event
 * settings and disabling automatic user-provided data. Scroll, outbound clicks
 * and video measurement are retained. See deploy/analytics.md.
 */
import { ANALYTICS_OPT_OUT_KEY, GOOGLE_ANALYTICS_ID, googleAnalyticsAvailable, readAnalyticsPrivacyPreference } from "./analyticsPrivacy";
import { TOOL_RUN_EVENT, type ToolRunDetail } from "./toolRun";
import { toolBySlug } from "@/data/tools";
import { nonPdfToolBySlug } from "@/data/non-pdf-tools";

type Gtag = (...args: unknown[]) => void;
type AnalyticsWindow = Window & { dataLayer?: unknown[]; gtag?: Gtag; ptSetAnalyticsDisabled?: (disabled: boolean) => void };
const SCRIPT_ID = "privatools-google-analytics";
const TOOL_SUCCESS_EVENT = "privatools:tool-success";
const PUBLIC_BASE = "https://privatools.me";
const PUBLIC_PAGES = new Set(["/", "/tools", "/pipeline", "/batch", "/ai", "/api", "/trust", "/security", "/status", "/support", "/about", "/privacy", "/terms", "/blog", "/compare"]);
const RUN_MODES = new Set(["single", "batch", "pipeline"]);
const RUN_OUTCOMES = new Set(["success", "partial", "error"]);
const MAX_FILE_COUNT = 10_000;
let active = false;
let configured = false;
let lastPath = "";
let enabled = false;
let navHandler: (() => void) | undefined;

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
/** Only registered tools are reportable; the registry category names the group. */
function toolCategory(slug: string): string | undefined {
    return toolBySlug[slug]?.category ?? nonPdfToolBySlug[slug]?.category;
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
/** React Router navigates with pushState, which fires no popstate; the app calls this on each location change. */
export function notifyNavigation(): void {
    navHandler?.();
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
        if (event.key === null || event.key === ANALYTICS_OPT_OUT_KEY) sync();
    };
    const onToolSuccess = () => {
        if (!allowed() || !/^\/tools?\//.test(pathNow())) return;
        sendPageview();
        // Never pass CustomEvent.detail (which could contain a label or filename).
        win.gtag?.("event", "tool_success", { page_location: `${PUBLIC_BASE}${pathNow()}`, page_title: safeTitle(), send_to: GOOGLE_ANALYTICS_ID });
    };
    const onToolRun = (event: Event) => {
        if (!allowed()) return;
        // Only the shape of the run is read from the detail. Anything else a
        // caller attaches (names, text, errors) is ignored by construction.
        const detail = ((event as CustomEvent<Partial<ToolRunDetail>>).detail ?? {}) as Partial<ToolRunDetail>;
        const path = pathNow();
        const slug = typeof detail.slug === "string" ? detail.slug : /^\/tools?\/([a-z0-9-]+)$/.exec(path)?.[1];
        const mode = detail.mode ?? "single";
        const outcome = detail.outcome;
        if (!slug || !/^[a-z0-9-]{1,64}$/.test(slug) || !RUN_MODES.has(mode) || typeof outcome !== "string" || !RUN_OUTCOMES.has(outcome)) return;
        if (detail.files !== undefined && !(Number.isInteger(detail.files) && (detail.files as number) >= 0)) return;
        const category = toolCategory(slug);
        if (!category) return;
        const tag = bootTag();
        if (!tag) return;
        const params: Record<string, unknown> = { tool_slug: slug, tool_category: category, run_mode: mode, outcome };
        if (detail.files !== undefined) params.file_count = Math.min(detail.files as number, MAX_FILE_COUNT);
        tag("event", "tool_run", { ...params, page_location: `${PUBLIC_BASE}${path}`, page_title: safeTitle(), send_to: GOOGLE_ANALYTICS_ID });
    };
    win.ptSetAnalyticsDisabled = sync;
    navHandler = onNav;
    sync();
    window.addEventListener("storage", onStorage);
    window.addEventListener("popstate", onNav);
    window.addEventListener("hashchange", onNav);
    window.addEventListener("pageshow", sync);
    window.addEventListener(TOOL_SUCCESS_EVENT, onToolSuccess);
    window.addEventListener(TOOL_RUN_EVENT, onToolRun);
    return () => {
        active = false; clearTimeout(timer); disable();
        if (navHandler === onNav) navHandler = undefined;
        window.removeEventListener("storage", onStorage);
        window.removeEventListener("popstate", onNav);
        window.removeEventListener("hashchange", onNav);
        window.removeEventListener("pageshow", sync);
        window.removeEventListener(TOOL_SUCCESS_EVENT, onToolSuccess);
        window.removeEventListener(TOOL_RUN_EVENT, onToolRun);
        if (win.ptSetAnalyticsDisabled === sync) win.ptSetAnalyticsDisabled = previousPrivacyHandler;
    };
}
