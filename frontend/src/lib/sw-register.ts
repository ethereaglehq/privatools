/** Production PWA lifecycle. Updates are explicit so files survive deploys. */
export type PwaState = {
    supported: boolean;
    online: boolean;
    installed: boolean;
    canInstall: boolean;
    offlineReady: boolean;
    updateAvailable: boolean;
    updating: boolean;
    installing: boolean;
    error: string | null;
};
type InstallEvent = Event & {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};
let state: PwaState = {
    supported: false, online: true, installed: false, canInstall: false,
    offlineReady: false, updateAvailable: false, updating: false, installing: false, error: null,
};
const listeners = new Set<() => void>();
let registration: ServiceWorkerRegistration | null = null;
let deferredInstall: InstallEvent | null = null;
let initialized = false;
let requestedReload = false;
let refreshed = false;
let updateTimeout: number | undefined;

const publish = (next: Partial<PwaState>) => {
    state = { ...state, ...next };
    listeners.forEach((listener) => listener());
};
export const getPwaState = () => state;
export const subscribePwaState = (listener: () => void) => {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
};

export async function installPwa(): Promise<void> {
    if (!deferredInstall || state.installing) return;
    const prompt = deferredInstall;
    deferredInstall = null;
    publish({ installing: true, canInstall: false, error: null });
    try {
        await prompt.prompt();
        const choice = await prompt.userChoice;
        if (choice.outcome === "accepted") publish({ installed: true });
    } catch { publish({ error: "The install prompt could not open. Try your browser’s install menu." }); }
    finally { publish({ installing: false }); }
}

/** The caller shows an explicit confirmation before invoking this. */
export function applyPwaUpdate(): void {
    if (!registration?.waiting || state.updating) return;
    requestedReload = true;
    publish({ updating: true, error: null });
    registration.waiting.postMessage("SKIP_WAITING");
    updateTimeout = window.setTimeout(() => {
        requestedReload = false;
        publish({ updating: false, error: "The update is taking longer than expected. Your current work is still open. Try again when you are ready." });
    }, 15000);
}

export async function checkPwaUpdate(): Promise<void> {
    if (!registration || !navigator.onLine) return;
    publish({ error: null });
    try { await registration.update(); }
    catch { publish({ error: "Could not check for updates. Please try again when your connection is stable." }); }
}

export function registerServiceWorker(): void {
    if (typeof window === "undefined" || initialized) return;
    initialized = true;
    const standalone = window.matchMedia("(display-mode: standalone)");
    const installed = () => standalone.matches || !!(navigator as Navigator & { standalone?: boolean }).standalone;
    publish({ supported: "serviceWorker" in navigator && import.meta.env.PROD, online: navigator.onLine, installed: installed() });
    window.addEventListener("online", () => { publish({ online: true }); void checkPwaUpdate(); });
    window.addEventListener("offline", () => publish({ online: false }));
    standalone.addEventListener?.("change", () => publish({ installed: installed() }));
    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredInstall = event as InstallEvent;
        publish({ canInstall: true });
    });
    window.addEventListener("appinstalled", () => {
        deferredInstall = null;
        publish({ installed: true, canInstall: false });
    });
    if (!state.supported) return;

    navigator.serviceWorker.addEventListener("controllerchange", () => {
        publish({ offlineReady: true });
        if (!requestedReload || refreshed) return;
        refreshed = true;
        window.clearTimeout(updateTimeout);
        window.location.reload();
    });
    const register = async () => {
        try {
            registration = await navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" });
            const ready = () => publish({ offlineReady: !!registration?.active, updateAvailable: !!registration?.waiting });
            ready();
            const observeInstalling = () => {
                const worker = registration?.installing;
                if (!worker) return;
                worker.addEventListener("statechange", () => {
                    if (worker.state === "installed") {
                        // The first worker activates normally; replacements wait.
                        publish({ offlineReady: true, updateAvailable: !!navigator.serviceWorker.controller });
                    } else if (worker.state === "activated") ready();
                });
            };
            registration.addEventListener("updatefound", observeInstalling);
            observeInstalling();
            document.addEventListener("visibilitychange", () => {
                if (document.visibilityState === "visible") void checkPwaUpdate();
            });
        } catch {
            publish({ error: "Offline setup is unavailable in this browser session. You can continue using PrivaTools online." });
        }
    };
    if (document.readyState === "complete") void register();
    else window.addEventListener("load", () => { void register(); }, { once: true });
}
