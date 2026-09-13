import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
function environment() {
    const worker = Object.assign(new EventTarget(), { state: "installing", postMessage: vi.fn() });
    const registration = Object.assign(new EventTarget(), { waiting: null as typeof worker | null, active: null as typeof worker | null, installing: worker, update: vi.fn().mockResolvedValue(undefined) });
    const serviceWorker = Object.assign(new EventTarget(), { register: vi.fn().mockResolvedValue(registration), controller: null as typeof worker | null });
    const win = Object.assign(new EventTarget(), { matchMedia: () => Object.assign(new EventTarget(), { matches: false }), location: { reload: vi.fn() }, setTimeout, clearTimeout });
    const doc = Object.assign(new EventTarget(), { readyState: "complete", visibilityState: "visible" });
    vi.stubGlobal("window", win); vi.stubGlobal("document", doc); vi.stubGlobal("navigator", { serviceWorker, onLine: true });
    return { win, worker, registration, serviceWorker };
}
beforeEach(() => { vi.resetModules(); vi.stubEnv("PROD", true); });
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.useRealTimers(); });
const settle = async () => { await Promise.resolve(); await Promise.resolve(); };
describe("PWA registration", () => {
    it("registers once and never reloads when another worker takes control", async () => {
        const h = environment(); const pwa = await import("@/lib/sw-register"); pwa.registerServiceWorker(); pwa.registerServiceWorker(); await settle();
        expect(h.serviceWorker.register).toHaveBeenCalledExactlyOnceWith("/sw.js", { updateViaCache: "none" });
        h.serviceWorker.dispatchEvent(new Event("controllerchange"));
        expect(h.win.location.reload).not.toHaveBeenCalled(); expect(pwa.getPwaState().offlineReady).toBe(true);
    });
    it("leaves a waiting update alone and reloads once only after explicit action", async () => {
        const h = environment(); h.registration.waiting = h.worker; h.serviceWorker.controller = h.worker;
        const pwa = await import("@/lib/sw-register"); pwa.registerServiceWorker(); await settle();
        expect(pwa.getPwaState().updateAvailable).toBe(true); expect(h.worker.postMessage).not.toHaveBeenCalled();
        pwa.applyPwaUpdate(); expect(h.worker.postMessage).toHaveBeenCalledExactlyOnceWith("SKIP_WAITING");
        h.serviceWorker.dispatchEvent(new Event("controllerchange")); h.serviceWorker.dispatchEvent(new Event("controllerchange"));
        expect(h.win.location.reload).toHaveBeenCalledOnce();
    });
    it("does not force a late reload if an update times out", async () => {
        vi.useFakeTimers(); const h = environment(); h.registration.waiting = h.worker;
        const pwa = await import("@/lib/sw-register"); pwa.registerServiceWorker(); await settle(); pwa.applyPwaUpdate(); vi.advanceTimersByTime(15000);
        expect(pwa.getPwaState().updating).toBe(false); expect(pwa.getPwaState().error).toContain("current work is still open");
        h.serviceWorker.dispatchEvent(new Event("controllerchange")); expect(h.win.location.reload).not.toHaveBeenCalled();
    });
    it("offers only the received native install prompt and consumes a dismissed prompt", async () => {
        const h = environment(); const pwa = await import("@/lib/sw-register"); pwa.registerServiceWorker(); await settle();
        const prompt = vi.fn().mockResolvedValue(undefined);
        const event = Object.assign(new Event("beforeinstallprompt", { cancelable: true }), { prompt, userChoice: Promise.resolve({ outcome: "dismissed" }) });
        h.win.dispatchEvent(event); expect(event.defaultPrevented).toBe(true); expect(pwa.getPwaState().canInstall).toBe(true);
        await pwa.installPwa(); await pwa.installPwa(); expect(prompt).toHaveBeenCalledOnce();
        expect(pwa.getPwaState().canInstall).toBe(false); expect(pwa.getPwaState().installed).toBe(false);
    });
    it("reports connectivity and setup failure without crashing", async () => {
        const h = environment(); h.serviceWorker.register.mockRejectedValueOnce(new Error("blocked"));
        const pwa = await import("@/lib/sw-register"); pwa.registerServiceWorker(); await settle();
        expect(pwa.getPwaState().error).toContain("continue using PrivaTools online");
        h.win.dispatchEvent(new Event("offline")); expect(pwa.getPwaState().online).toBe(false);
        h.win.dispatchEvent(new Event("online")); expect(pwa.getPwaState().online).toBe(true);
    });
    it("does not register a production worker in development", async () => {
        const h = environment(); vi.stubEnv("PROD", false);
        const pwa = await import("@/lib/sw-register"); pwa.registerServiceWorker(); await settle();
        expect(h.serviceWorker.register).not.toHaveBeenCalled(); expect(pwa.getPwaState().supported).toBe(false);
    });
});
