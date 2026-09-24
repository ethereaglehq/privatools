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
  // Own properties shadow jsdom's getters; deleting them restores the defaults.
  Reflect.deleteProperty(document, "referrer"); Reflect.deleteProperty(navigator, "webdriver"); Reflect.deleteProperty(navigator, "userAgent");
});
afterEach(() => { stop?.(); stop = undefined; vi.useRealTimers(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
function setReferrer(value: string) { Object.defineProperty(document, "referrer", { configurable: true, value }); }
function pageViews() { return events().filter(command => command[1] === "page_view").map(command => command[2] as Record<string, unknown>); }
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

describe("where visits come from", () => {
  it("sends only the external referrer's origin on the landing page view", async () => {
    setReferrer("https://www.google.com/search?q=private+medical+terms&client=firefox");
    await start();
    expect(pageViews()).toEqual([expect.objectContaining({ page_location: "https://privatools.me/", page_referrer: "https://www.google.com/" })]);
    const text = JSON.stringify(commands());
    for (const hidden of ["search", "private", "medical", "client=", "firefox"]) expect(text).not.toContain(hidden);
  });

  it("carries only the allowlisted campaign tags into the landing page location", async () => {
    history.replaceState(null, "", "/tools/image-compressor?utm_source=newsletter&utm_medium=email&utm_campaign=Spring+Sale&utm_term=pdf%20tools&utm_content=hero-1&gclid=secret-click&email=me%40example.com&utm_id=77&UTM_SOURCE=upper#secret-fragment");
    setReferrer("https://news.example.org/issue/42?reader=secret-reader");
    await start();
    expect(pageViews()).toEqual([expect.objectContaining({
      page_location: "https://privatools.me/tools/image-compressor?utm_source=newsletter&utm_medium=email&utm_campaign=Spring%20Sale&utm_term=pdf%20tools&utm_content=hero-1",
      page_referrer: "https://news.example.org/",
    })]);
    const text = JSON.stringify(commands());
    for (const hidden of ["secret", "gclid", "email=", "example.com", "utm_id", "upper", "issue"]) expect(text).not.toContain(hidden);
  });

  it("drops campaign values outside the safe character set or longer than 64 characters", async () => {
    const max = "b".repeat(64);
    history.replaceState(null, "", `/?utm_source=${max}&utm_medium=${"c".repeat(65)}&utm_campaign=%3Cscript%3Ealert(1)%3C%2Fscript%3E&utm_term=jane%40example.com&utm_content=caf%C3%A9-%E0%A4%B9%E0%A4%BF`);
    await start();
    expect(pageViews()[0].page_location).toBe(`https://privatools.me/?utm_source=${max}&utm_content=${encodeURIComponent("café-हि")}`);
    const text = JSON.stringify(commands());
    for (const hidden of ["ccc", "script", "jane", "example.com"]) expect(text).not.toContain(hidden);
  });

  /** The campaign query the landing page view carries for a fresh page load at this URL. */
  async function landingQuery(search: string): Promise<string> {
    stop?.(); stop = undefined; vi.resetModules(); delete win.dataLayer; delete win.gtag;
    document.head.innerHTML = '<meta name="privatools:google-analytics" content="enabled">';
    history.replaceState(null, "", `/${search}`);
    await start();
    const url = String(pageViews()[0]?.page_location ?? "");
    return url.includes("?") ? url.slice(url.indexOf("?") + 1) : "";
  }

  it.each([
    // A literal + in a query decodes to a space, so this arrives as digits only.
    ["a phone number with a plus sign", "utm_term=+15551234567"],
    ["a dashed phone number", "utm_term=555-123-4567"],
    ["nine digits in a campaign name", "utm_campaign=launch_202609241"],
    ["the SHA-256 of an email address", "utm_content=8c87b489ce35cf2e2f39f80e282cb2e804932a56a213983eeeb428407d43b52d"],
    ["a 43-character random token", "utm_content=kHs7JdGfAcEuTiOaWbXyVnMqKrSzLpQw-BtRyN2mFd9"],
    ["a JWT", "utm_content=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"],
    ["a JWT header on its own", "utm_content=eyJhbGciOiJIUzI1NiJ9"],
    ["16 letters and digits with no separator", "utm_campaign=abcdefghijklmno1"],
  ])("drops %s", async (_label, query) => {
    expect(await landingQuery(`?${query}`)).toBe("");
  });

  it("keeps ordinary campaign names under the same rules", async () => {
    expect(await landingQuery("?utm_source=spring-sale&utm_medium=newsletter%202026-09&utm_campaign=launch_20260924&utm_term=internationalization&utm_content=abcdefghijklmn1"))
      .toBe("utm_source=spring-sale&utm_medium=newsletter%202026-09&utm_campaign=launch_20260924&utm_term=internationalization&utm_content=abcdefghijklmn1");
  });

  it("uses the first value of a repeated tag and ignores empty ones", async () => {
    history.replaceState(null, "", "/?utm_source=first&utm_source=second&utm_medium=&utm_campaign=%20%20");
    await start();
    expect(pageViews()[0].page_location).toBe("https://privatools.me/?utm_source=first");
  });

  it("sends the landing attribution on the first page view only and never through the global set", async () => {
    history.replaceState(null, "", "/?utm_source=newsletter&utm_campaign=launch");
    setReferrer("https://www.google.com/");
    const module = await start();
    history.pushState(null, "", "/tools/image-compressor"); module.notifyNavigation(); await vi.advanceTimersByTimeAsync(0);
    toolRun({ outcome: "error", errorKind: "server" });
    window.dispatchEvent(new CustomEvent("privatools:tool-success"));
    const views = pageViews();
    expect(views).toHaveLength(2);
    expect(views[0]).toMatchObject({ page_location: "https://privatools.me/?utm_source=newsletter&utm_campaign=launch", page_referrer: "https://www.google.com/" });
    expect(views[1]).toMatchObject({ page_location: "https://privatools.me/tools/image-compressor", page_referrer: "https://privatools.me/" });
    // Everything after the landing hit, and every global default, is clean.
    const later = [...commands().filter(command => command[0] !== "event"), ...events().slice(1)];
    expect(later.length).toBeGreaterThan(3);
    for (const command of later) {
      expect(JSON.stringify(command)).not.toContain("utm_");
      expect(JSON.stringify(command)).not.toContain("google.com");
    }
  });

  it("keeps the landing attribution for the first page view a private landing page never sent", async () => {
    history.replaceState(null, "", "/account/sign-in?utm_source=newsletter&token=secret");
    setReferrer("https://mail.example.net/inbox/123");
    const module = await start();
    expect(commands()).toEqual([]);
    history.pushState(null, "", "/"); module.notifyNavigation(); await vi.advanceTimersByTimeAsync(0);
    history.pushState(null, "", "/tools"); module.notifyNavigation(); await vi.advanceTimersByTimeAsync(0);
    expect(pageViews()).toEqual([
      expect.objectContaining({ page_location: "https://privatools.me/?utm_source=newsletter", page_referrer: "https://mail.example.net/" }),
      expect.objectContaining({ page_location: "https://privatools.me/tools", page_referrer: "https://privatools.me/" }),
    ]);
    expect(JSON.stringify(commands())).not.toContain("secret");
    expect(JSON.stringify(commands())).not.toContain("inbox");
  });

  it("treats this site as internal and ignores referrers that are not web or app links", async () => {
    setReferrer("https://privatools.me/tool/merge-pdf?input=secret");
    await start();
    expect(pageViews()[0].page_referrer).toBe("https://privatools.me/tool/merge-pdf");
    expect(JSON.stringify(commands())).not.toContain("secret");
    for (const [referrer, expected] of [
      [`${location.origin}/tools`, "https://privatools.me/tools"],
      ["file:///home/me/secret.html", ""],
      ["android-app://com.google.android.googlequicksearchbox/https/www.google.com", "android-app://com.google.android.googlequicksearchbox/"],
      ["not a url", ""],
    ]) {
      stop?.(); vi.resetModules(); delete win.dataLayer; delete win.gtag; document.head.innerHTML = '<meta name="privatools:google-analytics" content="enabled">';
      setReferrer(referrer);
      await start();
      expect(pageViews()[0].page_referrer).toBe(expected);
    }
    expect(JSON.stringify(commands())).not.toContain("secret");
  });

  it.each([
    "http://192.168.1.20:8080/admin",
    "http://10.0.0.5/",
    "http://[fd00::1]/wiki",
    "http://localhost:5173/",
    "http://intranet/wiki/page",
    "http://dev.localhost/",
    "https://jenkins.internal/job/1",
    "http://printer.local/",
    "http://router.home.arpa/",
  ])("records no referrer that only reveals an internal host: %s", async referrer => {
    setReferrer(referrer);
    await start();
    expect(pageViews()[0].page_referrer).toBe("");
  });

  it("still records public referrers, short names included", async () => {
    setReferrer("https://t.co/abc123");
    await start();
    expect(pageViews()[0].page_referrer).toBe("https://t.co/");
  });
});

describe("automated browsers", () => {
  it("does not load the tag or send anything in a WebDriver-controlled browser", async () => {
    Object.defineProperty(navigator, "webdriver", { configurable: true, value: true });
    history.replaceState(null, "", "/tool/merge-pdf");
    await start();
    toolRun({ outcome: "success", files: 1 });
    window.dispatchEvent(new CustomEvent("privatools:tool-success"));
    const { setAnalyticsOptOut } = await import("./analyticsPrivacy"); setAnalyticsOptOut(false);
    await navigate("/tools");
    expect(commands()).toEqual([]);
    expect(document.querySelector("script")).toBeNull();
    expect(disabled()).toBe(true);
  });

  it.each([
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Unknown; Linux x86_64) AppleWebKit/538.1 (KHTML, like Gecko) PhantomJS/2.1.1 Safari/538.1",
  ])("does not load the tag for a headless user agent: %s", async userAgent => {
    Object.defineProperty(navigator, "userAgent", { configurable: true, value: userAgent });
    await start();
    toolRun({ slug: "merge-pdf", outcome: "success" });
    expect(commands()).toEqual([]);
    expect(document.querySelector("script")).toBeNull();
    expect(disabled()).toBe(true);
  });

  it("still measures an ordinary browser, whatever its screen or language", async () => {
    Object.defineProperty(navigator, "webdriver", { configurable: true, value: false });
    Object.defineProperty(navigator, "userAgent", { configurable: true, value: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
    await start();
    expect(pageViews()).toHaveLength(1);
  });
});

describe("why tool runs fail", () => {
  it("adds a validated failure category to error and partial runs only", async () => {
    history.replaceState(null, "", "/tool/merge-pdf"); await start();
    toolRun({ outcome: "error", files: 1, errorKind: "too_large" });
    toolRun({ outcome: "partial", files: 2, errorKind: "server" });
    toolRun({ outcome: "success", errorKind: "server" });
    toolRun({ outcome: "error", errorKind: "Could not read secret-contract.pdf" });
    toolRun({ outcome: "error", errorKind: "cancelled" });
    toolRun({ outcome: "error", errorKind: 413 });
    expect(runs().map(run => run.error_kind)).toEqual(["too_large", "server", undefined, undefined, undefined, undefined]);
    expect(runs()[2]).not.toHaveProperty("error_kind");
    expect(JSON.stringify(commands())).not.toContain("secret");
  });

  it("accepts every category in the fixed list", async () => {
    history.replaceState(null, "", "/tool/merge-pdf"); await start();
    const { TOOL_ERROR_KINDS } = await import("./toolRun");
    for (const errorKind of TOOL_ERROR_KINDS) toolRun({ outcome: "error", errorKind });
    expect(runs().map(run => run.error_kind)).toEqual([...TOOL_ERROR_KINDS]);
    expect([...TOOL_ERROR_KINDS].sort()).toEqual(["bad_input", "browser", "network", "provider", "rate_limited", "server", "timeout", "too_large"]);
  });

  it("classifies a failure centrally and never sends its message", async () => {
    history.replaceState(null, "", "/tool/merge-pdf"); await start();
    const { emitToolRun } = await import("./toolRun");
    emitToolRun({ outcome: "error", files: 1 }, Object.assign(new Error("secret-contract.pdf is too large"), { __status: 413 }));
    emitToolRun({ outcome: "error", files: 1 }, new TypeError("Failed to fetch"));
    emitToolRun({ outcome: "error", files: 1 }, new Error("Could not parse secret text on page 3"));
    emitToolRun({ outcome: "error", files: 1 }, new DOMException("Aborted", "AbortError"));
    expect(runs()).toEqual([
      expect.objectContaining({ outcome: "error", file_count: 1, error_kind: "too_large" }),
      expect.objectContaining({ outcome: "error", file_count: 1, error_kind: "network" }),
      expect.objectContaining({ outcome: "error", file_count: 1, error_kind: "browser" }),
    ]);
    const text = JSON.stringify(commands());
    for (const hidden of ["secret", "Failed to fetch", "parse", "Aborted"]) expect(text).not.toContain(hidden);
  });
});

it("honors withdrawal in the current document when persistence fails", async () => {
  await start(); const { setAnalyticsOptOut } = await import("./analyticsPrivacy");
  const failStorage = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
  const preference = setAnalyticsOptOut(true); expect(preference.effectiveDisabled).toBe(true);
  expect(disabled()).toBe(true);
  failStorage.mockRestore();
});
