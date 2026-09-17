import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
let stop: (() => void) | undefined;
const win = window as Window & { dataLayer?: IArguments[]; gtag?: (...args: unknown[]) => void; ptSetAnalyticsDisabled?: (value: boolean) => void };
const OPT_OUT_KEY = "pt-analytics-opt-out";
const GA_DISABLE = "ga-disable-G-B3VWQ44MX1";
beforeEach(() => {
  vi.resetModules(); vi.useFakeTimers(); vi.stubEnv("PROD", true);
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => ({}) })));
  localStorage.clear(); sessionStorage.clear(); history.replaceState(null, "", "/");
  document.head.innerHTML = '<meta name="privatools:google-analytics" content="enabled">';
  delete win.dataLayer; delete win.gtag; delete win.ptSetAnalyticsDisabled;
  Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: false });
  Object.defineProperty(navigator, "doNotTrack", { configurable: true, value: null });
});
afterEach(() => { stop?.(); stop = undefined; vi.useRealTimers(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
async function start() { const module = await import("./analyticsBeacon"); stop = module.startPageviewTracking(); return module; }
function commands(): unknown[][] { return (win.dataLayer || []).map(item => Array.from(item)); }
function events() { return commands().filter(command => command[0] === "event"); }
function runs() { return events().filter(command => command[1] === "tool_run").map(command => command[2] as Record<string, unknown>); }
function disabled(): unknown { return (window as unknown as Record<string, unknown>)[GA_DISABLE]; }
async function navigate(path: string) { history.replaceState(null, "", path); window.dispatchEvent(new PopStateEvent("popstate")); window.dispatchEvent(new HashChangeEvent("hashchange")); await vi.advanceTimersByTimeAsync(0); }
function toolRun(detail: Record<string, unknown>) { window.dispatchEvent(new CustomEvent("privatools:tool-run", { detail })); }

describe("default-on Google tag with sanitized manual pageviews", () => {
  it("has one browser sender and no inline or proxy beacon", () => {
    const shell = readFileSync(resolve(process.cwd(), "index.html"), "utf8");
    const module = readFileSync(resolve(process.cwd(), "src/lib/analyticsBeacon.ts"), "utf8");
    expect(shell).not.toContain("navigator.sendBeacon"); expect(shell).not.toContain("function sendPageview");
    expect(module).not.toContain("/api/analytics/pageview");
  });
  it("loads the tag and counts the arrival with no stored choice", async () => {
    await start();
    expect(commands()[0]).toEqual(["consent", "default", { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" }]);
    expect(events().map(c => c[1])).toEqual(["page_view"]);
    expect(document.querySelectorAll("script")).toHaveLength(1);
    expect(document.querySelector("script")!.getAttribute("src")).toBe("https://www.googletagmanager.com/gtag/js?id=G-B3VWQ44MX1");
    expect(localStorage.length).toBe(0);
    expect(disabled()).toBe(false);
  });
  it("never asks the server for a regional policy", async () => {
    await start(); await vi.advanceTimersByTimeAsync(5000);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("requires the verified deployment switch and production build", async () => {
    document.querySelector("meta")!.remove(); await start(); expect(commands()).toEqual([]);
    stop?.(); vi.stubEnv("PROD", false); document.head.innerHTML = '<meta name="privatools:google-analytics" content="enabled">';
    await start(); expect(commands()).toEqual([]);
  });
  it("keeps ads denied, delegates lifecycle to the SDK and sends one canonical arrival/navigation", async () => {
    await start(); await navigate("/pipeline?recipe=private#/pipeline");
    const configs = commands().filter(c => c[0] === "config");
    expect(configs).toHaveLength(1);
    expect(configs[0][2]).toMatchObject({ send_page_view: false, allow_google_signals: false, allow_ad_personalization_signals: false });
    expect(events().map(c => (c[2] as Record<string, unknown>).page_location)).toEqual(["https://privatools.me/", "https://privatools.me/pipeline"]);
    expect(events().every(c => c[1] === "page_view")).toBe(true);
    expect(JSON.stringify(commands())).not.toContain("client_id"); expect(JSON.stringify(commands())).not.toContain("session_engaged");
    expect(document.querySelectorAll("script")).toHaveLength(1);
  });
  it("never boots on private documents and blocks private soft navigation synchronously", async () => {
    history.replaceState(null, "", "/account/sign-in?email=secret@example.com"); await start();
    expect(commands()).toEqual([]);
    await navigate("/"); expect(events()).toHaveLength(1);
    history.replaceState(null, "", "/my-stuff/vault"); window.dispatchEvent(new PopStateEvent("popstate"));
    expect(disabled()).toBe(true);
    await vi.advanceTimersByTimeAsync(0); expect(events()).toHaveLength(1);
    expect(JSON.stringify(commands())).not.toContain("secret@example.com");
    expect(JSON.stringify(commands())).not.toContain("/my-stuff");
  });
  it("counts router navigations reported through notifyNavigation", async () => {
    const module = await start();
    history.pushState(null, "", "/tools/image-compressor"); module.notifyNavigation(); await vi.advanceTimersByTimeAsync(0);
    expect(events().map(c => (c[2] as Record<string, unknown>).page_location)).toEqual(["https://privatools.me/", "https://privatools.me/tools/image-compressor"]);
    history.pushState(null, "", "/account/settings?token=secret"); module.notifyNavigation();
    expect(disabled()).toBe(true);
    await vi.advanceTimersByTimeAsync(0);
    expect(events()).toHaveLength(2);
    expect(JSON.stringify(commands())).not.toContain("secret");
  });
  it("keeps retained automatic-event page fields current under Google parameter precedence", async () => {
    history.replaceState(null, "", "/?input=private"); document.title = "private-file.txt";
    await start(); await navigate("/blog?input=private#private");
    const global: Record<string, unknown> = {};
    const config: Record<string, unknown> = {};
    const defaultsAtConfig: Record<string, unknown>[] = [];
    // Google's documented precedence is event > config > global set. Apply
    // that contract: automatic events have no explicit event page overrides.
    for (const command of commands()) {
      if (command[0] === "set") Object.assign(global, command[1] as Record<string, unknown>);
      if (command[0] === "config") {
        Object.assign(config, command[2] as Record<string, unknown>);
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
    history.replaceState(null, "", "/tools/json-xml-formatter?input=secret"); document.title = "private-file.json";
    await start(); window.dispatchEvent(new CustomEvent("privatools:tool-success", { detail: { tool: "private-file.json", text: "SECRET" } }));
    expect(events().map(c => c[1])).toEqual(["page_view", "tool_success"]);
    expect(JSON.stringify(commands())).not.toContain("private-file"); expect(JSON.stringify(commands())).not.toContain("SECRET");
    expect(JSON.stringify(commands())).not.toContain("engagement_time_msec");
  });
  it("ignores Do Not Track and Global Privacy Control", async () => {
    Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: true });
    Object.defineProperty(navigator, "doNotTrack", { configurable: true, value: "1" });
    await start();
    expect(events().map(c => c[1])).toEqual(["page_view"]);
    expect(disabled()).toBe(false);
  });
  it("opting out disables immediately and opting back in resumes", async () => {
    await start(); const { setAnalyticsOptOut, readAnalyticsPrivacyPreference } = await import("./analyticsPrivacy");
    expect(events()).toHaveLength(1);
    setAnalyticsOptOut(true);
    expect(localStorage.getItem(OPT_OUT_KEY)).toBe("1");
    expect(disabled()).toBe(true);
    expect(readAnalyticsPrivacyPreference()).toEqual({ localOptOut: true, effectiveDisabled: true });
    await navigate("/tools/image-compressor"); window.dispatchEvent(new CustomEvent("privatools:tool-success"));
    expect(events()).toHaveLength(1);
    setAnalyticsOptOut(false);
    expect(localStorage.getItem(OPT_OUT_KEY)).toBeNull();
    expect(readAnalyticsPrivacyPreference()).toEqual({ localOptOut: false, effectiveDisabled: false });
    expect(events()).toHaveLength(2);
    expect(disabled()).toBe(false);
  });
  it("starts disabled when a saved opt-out exists", async () => {
    localStorage.setItem(OPT_OUT_KEY, "1"); await start();
    expect(commands()).toEqual([]); expect(document.querySelector("script")).toBeNull();
    expect(disabled()).toBe(true);
  });
});

describe("tool_run usage events", () => {
  it("sends the run with slug, category, mode and outcome, and nothing from the detail payload", async () => {
    history.replaceState(null, "", "/tool/merge-pdf?input=secret"); document.title = "private-file.pdf";
    await start();
    toolRun({ outcome: "success", files: 3, filename: "private-file.pdf", text: "SECRET" });
    expect(runs()).toEqual([{ tool_slug: "merge-pdf", tool_category: "organize", run_mode: "single", outcome: "success", file_count: 3, page_location: "https://privatools.me/tool/merge-pdf", page_title: "tool / merge pdf — PrivaTools", send_to: "G-B3VWQ44MX1" }]);
    expect(JSON.stringify(commands())).not.toContain("private-file"); expect(JSON.stringify(commands())).not.toContain("SECRET");
  });
  it("uses the explicit slug and mode from batch and pipeline runs", async () => {
    history.replaceState(null, "", "/batch"); await start();
    toolRun({ slug: "image-compressor", mode: "batch", outcome: "partial", files: 25 });
    toolRun({ slug: "compress-pdf", mode: "pipeline", outcome: "error" });
    expect(runs()).toEqual([
      expect.objectContaining({ tool_slug: "image-compressor", tool_category: "image", run_mode: "batch", outcome: "partial", file_count: 25 }),
      expect.objectContaining({ tool_slug: "compress-pdf", tool_category: "optimize", run_mode: "pipeline", outcome: "error" }),
    ]);
    expect(runs()[1]).not.toHaveProperty("file_count");
  });
  it("drops runs with unknown slugs, modes or outcomes, and everything once opted out", async () => {
    history.replaceState(null, "", "/tool/merge-pdf"); await start();
    toolRun({ outcome: "done" }); toolRun({ slug: "../etc", outcome: "success" }); toolRun({ mode: "cron", outcome: "success" }); toolRun({ slug: "not-a-real-tool", outcome: "success" });
    toolRun({ outcome: "success", files: "three" });
    expect(runs()).toHaveLength(0);
    history.replaceState(null, "", "/about"); toolRun({ outcome: "success" });
    expect(runs()).toHaveLength(0);
    history.replaceState(null, "", "/tool/merge-pdf");
    const { setAnalyticsOptOut } = await import("./analyticsPrivacy"); setAnalyticsOptOut(true);
    toolRun({ outcome: "success" });
    expect(runs()).toHaveLength(0);
  });
});

it("honors withdrawal in the current document when persistence fails", async () => {
  await start(); const { setAnalyticsOptOut } = await import("./analyticsPrivacy");
  const failStorage = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
  const preference = setAnalyticsOptOut(true); expect(preference.effectiveDisabled).toBe(true);
  expect(disabled()).toBe(true);
  failStorage.mockRestore();
});
