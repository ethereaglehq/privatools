import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
let stop: (() => void) | undefined;
const win = window as Window & { dataLayer?: IArguments[]; gtag?: (...args: unknown[]) => void; ptSetAnalyticsDisabled?: (value: boolean) => void };
const CONSENT_KEY = "pt-analytics-consent-v1";
beforeEach(() => {
  vi.resetModules(); vi.useFakeTimers(); vi.stubEnv("PROD", true);
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => ({ mode: "opt_in" }) })));
  localStorage.clear(); sessionStorage.clear(); history.replaceState(null, "", "/");
  document.head.innerHTML = '<meta name="privatools:google-analytics" content="enabled">';
  delete win.dataLayer; delete win.gtag; delete win.ptSetAnalyticsDisabled;
  Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: false });
  Object.defineProperty(navigator, "doNotTrack", { configurable: true, value: null });
});
afterEach(() => { stop?.(); stop = undefined; vi.useRealTimers(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
function consent() { localStorage.setItem(CONSENT_KEY, JSON.stringify({ version: 1, grantedAt: Date.now() })); }
async function start() { const module = await import("./analyticsBeacon"); stop = module.startPageviewTracking(); return module; }
function commands(): unknown[][] { return (win.dataLayer || []).map(item => Array.from(item)); }
function events() { return commands().filter(command => command[0] === "event"); }
async function navigate(path: string) { history.replaceState(null, "", path); window.dispatchEvent(new PopStateEvent("popstate")); window.dispatchEvent(new HashChangeEvent("hashchange")); await vi.advanceTimersByTimeAsync(0); }

describe("consented Google tag with sanitized manual pageviews", () => {
  it("has one browser sender and no inline or proxy beacon", () => {
    const shell = readFileSync(resolve(process.cwd(), "index.html"), "utf8");
    const module = readFileSync(resolve(process.cwd(), "src/lib/analyticsBeacon.ts"), "utf8");
    expect(shell).not.toContain("navigator.sendBeacon"); expect(shell).not.toContain("function sendPageview");
    expect(module).not.toContain("/api/analytics/pageview");
  });
  it("does not load Google or create analytics identifiers without affirmative consent", async () => {
    await start(); expect(commands()).toEqual([]); expect(document.querySelector("script")).toBeNull();
    expect(localStorage.length).toBe(0);
  });
  it("requires the verified deployment switch and production build even with consent", async () => {
    consent(); document.querySelector("meta")!.remove(); await start(); expect(commands()).toEqual([]);
    stop?.(); vi.stubEnv("PROD", false); document.head.innerHTML = '<meta name="privatools:google-analytics" content="enabled">';
    await start(); expect(commands()).toEqual([]);
  });
  it("keeps ads denied, delegates lifecycle to the SDK and sends one canonical arrival/navigation", async () => {
    consent(); await start(); await navigate("/pipeline?recipe=private#/pipeline");
    const configs = commands().filter(c => c[0] === "config");
    expect(configs).toHaveLength(1);
    expect(configs[0][2]).toMatchObject({ send_page_view: false, allow_google_signals: false, allow_ad_personalization_signals: false });
    expect(commands()[0]).toEqual(["consent", "default", { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" }]);
    expect(events().map(c => (c[2] as any).page_location)).toEqual(["https://privatools.me/", "https://privatools.me/pipeline"]);
    expect(events().every(c => c[1] === "page_view")).toBe(true);
    expect(JSON.stringify(commands())).not.toContain("client_id"); expect(JSON.stringify(commands())).not.toContain("session_engaged");
    expect(document.querySelectorAll("script")).toHaveLength(1);
  });
  it("never boots on private documents and blocks private soft navigation synchronously", async () => {
    consent(); history.replaceState(null, "", "/account/sign-in?email=secret@example.com"); await start();
    expect(commands()).toEqual([]);
    await navigate("/"); expect(events()).toHaveLength(1);
    history.replaceState(null, "", "/my-stuff/vault"); window.dispatchEvent(new PopStateEvent("popstate"));
    expect((window as any)["ga-disable-G-B3VWQ44MX1"]).toBe(true);
    await vi.advanceTimersByTimeAsync(0); expect(events()).toHaveLength(1);
    expect(JSON.stringify(commands())).not.toContain("secret@example.com");
    expect(JSON.stringify(commands())).not.toContain("/my-stuff");
  });
  it("keeps retained automatic-event page fields current under Google parameter precedence", async () => {
    consent(); history.replaceState(null, "", "/?input=private"); document.title = "private-file.txt";
    await start(); await navigate("/blog?input=private#private");
    const global: Record<string, unknown> = {};
    const config: Record<string, unknown> = {};
    const defaultsAtConfig: Record<string, unknown>[] = [];
    // Google's documented precedence is event > config > global set. Apply
    // that contract: automatic events have no explicit event page overrides.
    for (const command of commands()) {
      if (command[0] === "set") Object.assign(global, command[1]);
      if (command[0] === "config") {
        Object.assign(config, command[2]);
        defaultsAtConfig.push({ ...global, ...config });
      }
    }
    expect(defaultsAtConfig).toHaveLength(1);
    expect(defaultsAtConfig[0]).toMatchObject({ page_location: "https://privatools.me/", page_title: "PrivaTools", send_page_view: false });
    expect({ ...global, ...config }).toMatchObject({ page_location: "https://privatools.me/blog", page_title: "blog — PrivaTools", page_referrer: "https://privatools.me/" });
    expect(events().filter(command => command[1] === "page_view")).toHaveLength(2);
    expect(JSON.stringify(commands())).not.toContain("private");
  });
  it("records existing tool success without labels, filenames, input, or fake timing", async () => {
    consent(); history.replaceState(null, "", "/tools/json-xml-formatter?input=secret"); document.title = "private-file.json";
    await start(); window.dispatchEvent(new CustomEvent("privatools:tool-success", { detail: { tool: "private-file.json", text: "SECRET" } }));
    expect(events().map(c => c[1])).toEqual(["page_view", "tool_success"]);
    expect(JSON.stringify(commands())).not.toContain("private-file"); expect(JSON.stringify(commands())).not.toContain("SECRET");
    expect(JSON.stringify(commands())).not.toContain("engagement_time_msec");
  });
  it("respects GPC and DNT over a previous opt-in", async () => {
    consent(); Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: true });
    await start(); expect(commands()).toEqual([]);
    Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: false });
    Object.defineProperty(navigator, "doNotTrack", { configurable: true, value: "1" });
    win.ptSetAnalyticsDisabled?.(false); expect(commands()).toEqual([]);
  });
  it("enables on explicit opt-in, and immediately disables after withdrawal", async () => {
    await start(); const { setAnalyticsOptOut } = await import("./analyticsPrivacy");
    setAnalyticsOptOut(false); expect(events()).toHaveLength(1); expect(localStorage.getItem(CONSENT_KEY)).toBeTruthy();
    setAnalyticsOptOut(false); expect(events()).toHaveLength(1);
    setAnalyticsOptOut(true); expect(localStorage.getItem(CONSENT_KEY)).toBeNull();
    expect((window as any)["ga-disable-G-B3VWQ44MX1"]).toBe(true);
    await navigate("/tools/image-compressor"); window.dispatchEvent(new CustomEvent("privatools:tool-success"));
    expect(events()).toHaveLength(1);
  });
});


describe("verified regional analytics defaults", () => {
  it("stays off while policy is pending, then honors a reviewed default without storing consent", async () => {
    let resolvePolicy!: (value: unknown) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise(resolve => { resolvePolicy = resolve; })));
    await start(); expect(commands()).toEqual([]);
    resolvePolicy({ ok: true, json: async () => ({ mode: "default_on" }) });
    await vi.advanceTimersByTimeAsync(0);
    expect(events()).toHaveLength(1); expect(localStorage.getItem(CONSENT_KEY)).toBeNull();
    expect(fetch).toHaveBeenCalledWith("/api/analytics/policy", expect.objectContaining({ credentials: "omit", cache: "no-store" }));
  });
  it("keeps unknown, failed and malformed policies in opt-in mode", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => ({ mode: "anything-else", country: "US" }) })));
    await start(); await vi.advanceTimersByTimeAsync(0); expect(commands()).toEqual([]);
  });
  it.each(["gpc", "optout"])("a regional default never overrides %s", async (mode) => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => ({ mode: "default_on" }) })));
    if (mode === "gpc") Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: true });
    else localStorage.setItem("pt-analytics-opt-out", "1");
    await start(); await vi.advanceTimersByTimeAsync(0); expect(commands()).toEqual([]);
  });
});


it("honors withdrawal in the current document when persistence fails", async () => {
  consent(); await start(); const { setAnalyticsOptOut } = await import("./analyticsPrivacy");
  const failStorage = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
  const preference = setAnalyticsOptOut(true); expect(preference.effectiveDisabled).toBe(true);
  expect((window as any)["ga-disable-G-B3VWQ44MX1"]).toBe(true);
  failStorage.mockRestore();
});
