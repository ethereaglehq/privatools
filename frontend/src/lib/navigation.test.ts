import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let dispose = () => {};
beforeEach(() => {
    vi.resetModules();
    window.history.replaceState({ idx: 0, preserved: true }, "", "/ai");
    vi.spyOn(window, "scrollTo").mockImplementation(() => {});
});
afterEach(() => { dispose(); dispose = () => {}; vi.restoreAllMocks(); });

async function navigation(url = "/ai") {
    window.history.replaceState({ idx: 0, preserved: true }, "", url);
    const nav = await import("./navigation");
    const initialized = nav.initializeNavigation();
    dispose = initialized.dispose;
    return nav;
}

it("opens all three reported pages without retaining /ai or a hash", async () => {
    const nav = await navigation();
    const length = window.history.length;
    for (const path of ["/tools", "/pipeline", "/batch"]) {
        nav.navigateTo(path);
        expect(nav.currentRoute()).toBe(path);
        expect(window.location.hash).toBe("");
    }
    expect(window.history.length).toBe(length + 3);
});

it("Back and Forward restore clean routes and notify subscribers", async () => {
    const nav = await navigation();
    nav.navigateTo("/tools");
    nav.navigateTo("/pipeline");
    const back = new Promise<void>(resolve => window.addEventListener("popstate", () => resolve(), { once: true }));
    window.history.back();
    await back;
    expect(nav.currentRoute()).toBe("/tools");
    const forward = new Promise<void>(resolve => window.addEventListener("popstate", () => resolve(), { once: true }));
    window.history.forward();
    await forward;
    expect(nav.currentRoute()).toBe("/pipeline");
    expect(window.location.hash).toBe("");
});

it.each([
    ["/ai#/tools", "/tools"],
    ["/ai#/pipeline", "/pipeline"],
    ["/ai#/batch", "/batch"],
    ["/ai#/tool/resize-crop-image", "/tools/resize-crop-image"],
    ["/tools?cat=image#/tools", "/tools?cat=image"],
    ["/ai#/tools?cat=image", "/tools?cat=image"],
    ["/pipeline?p=shared#/pipeline", "/pipeline?p=shared"],
    ["/ai?unrelated=old#/tools?cat=image", "/tools?cat=image"],
    ["/ai#/unknown", "/unknown"],
])("normalizes bookmark %s in place", async (url, target) => {
    const length = window.history.length;
    await navigation(url);
    expect(window.location.pathname + window.location.search).toBe(target);
    expect(window.location.hash).toBe("");
    expect(window.history.length).toBe(length);
    expect(window.history.state).toEqual({ idx: 0, preserved: true });
});

it("normalizes hashes received after startup without extra history entries", async () => {
    const nav = await navigation();
    const length = window.history.length;
    const changed = new Promise<void>(resolve => window.addEventListener("hashchange", () => resolve(), { once: true }));
    window.location.hash = "#/batch";
    await changed;
    expect(nav.currentRoute()).toBe("/batch");
    expect(window.location.hash).toBe("");
    expect(window.history.length).toBe(length + 1);
});

it("keeps clean direct links and ordinary section fragments unchanged", async () => {
    const nav = await navigation("/privacy?section=retention#retention");
    expect(nav.currentRoute()).toBe("/privacy?section=retention");
    expect(window.location.hash).toBe("#retention");
});

it("keeps loaded AI capabilities after navigating through ordinary pages", async () => {
    const nav = await navigation("/ai");
    nav.navigateTo("/tools");
    nav.navigateTo("/tools/remove-background");
    expect(window.location.pathname).toBe("/tools/remove-background");
});

it("preserves account recovery queries within an account document", async () => {
    const nav = await navigation("/account/sign-in");
    nav.navigateTo("/tools");
    nav.navigateTo("/account?mode=recover");
    expect(window.location.pathname + window.location.search).toBe("/account?mode=recover");
});

describe("canonical app links", () => {
    it("chooses the right public path for PDF and non-PDF tools", async () => {
        const { canonicalPath } = await import("./navigation");
        expect(canonicalPath("#/tool/merge-pdf")).toBe("/tool/merge-pdf");
        expect(canonicalPath("/tools/ocr-pdf")).toBe("/tool/ocr-pdf");
        expect(canonicalPath("#/tool/resize-crop-image")).toBe("/tools/resize-crop-image");
        expect(canonicalPath("/settings?section=appearance")).toBe("/account/settings?section=appearance");
    });
    it("leaves external links, downloads, API endpoints and ordinary anchors to the browser", async () => {
        const { canonicalPath } = await import("./navigation");
        for (const href of ["https://example.com/tools", "//example.com/tools", "/\\example.com/tools", "#main-content", "/api/v1/jobs", "/download/file.pdf"]) {
            expect(canonicalPath(href)).toBeNull();
        }
    });
});
