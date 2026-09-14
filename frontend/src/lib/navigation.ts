import { nonPdfTools } from "@/data/non-pdf-tools";
import { tools } from "@/data/tools";
import { documentNavigationFor } from "@/skins/cspRoutes";
import { EXACT_ROUTES, PARAM_ROUTE_PREFIXES } from "@/skins/pathRoutes";
import { documentPath } from "./documentLocation";

const nonPdfSlugs = new Set(nonPdfTools.map(tool => tool.slug));
const pdfSlugs = new Set(tools.map(tool => tool.slug));
const accountPath = /^\/account(?:\/|$)/;

/** Resolve app links and old route fragments to their public URL. */
export function canonicalPath(href: string): string | null {
    const raw = href.startsWith("#/") ? href.slice(1) : href;
    if (!raw.startsWith("/") || raw.startsWith("//")) return null;
    const url = new URL(raw, "https://privatools.me");
    // URL parsing also rejects backslash spellings of foreign origins.
    if (url.origin !== "https://privatools.me") return null;
    let path = url.pathname.replace(/\/+$/, "") || "/";
    if (path === "/settings") path = "/account/settings";
    const tool = /^\/tools?\/([^/]+)$/.exec(path);
    if (tool && nonPdfSlugs.has(tool[1])) path = "/tools/" + tool[1];
    else if (tool && pdfSlugs.has(tool[1])) path = "/tool/" + tool[1];
    if (path !== "/" && !EXACT_ROUTES.includes(path)
        && !PARAM_ROUTE_PREFIXES.some(prefix => path === prefix || path.startsWith(prefix + "/"))
        && !/^\/(?:account|my-stuff)\//.test(path)) return null;
    return path + url.search + url.hash;
}

/** The displayed route comes from the path; ordinary section fragments are separate. */
export function currentRoute(): string {
    return typeof window === "undefined" ? "/" : window.location.pathname + window.location.search;
}

function requiresDocument(target: string): boolean {
    const path = target.split(/[?#]/)[0];
    return (accountPath.test(path) && !accountPath.test(documentPath))
        || Boolean(documentNavigationFor(documentPath, target));
}

function announceNavigation() {
    window.dispatchEvent(new PopStateEvent("popstate", { state: window.history.state }));
}

/** Preserve the mounted workspace unless the destination requires new response headers. */
export function navigateTo(href: string, { replace = false }: { replace?: boolean } = {}): void {
    const target = canonicalPath(href);
    if (!target || requiresDocument(target)) {
        window.location[replace ? "replace" : "assign"](target || href);
        return;
    }
    if (target === currentRoute() + window.location.hash) {
        window.scrollTo(0, 0);
        return;
    }
    const previous = window.history.state;
    const state = replace ? previous : {
        usr: null, key: crypto.randomUUID(), idx: (previous?.idx ?? 0) + 1,
    };
    window.history[replace ? "replaceState" : "pushState"](state, "", target);
    announceNavigation();
}

/** Replace old bookmarks in place, keeping Back free of duplicate route entries. */
function normalizeLocation(): boolean {
    const { pathname, search, hash } = window.location;
    const legacy = hash.startsWith("#/");
    const raw = legacy ? hash : pathname + search + hash;
    let target = canonicalPath(raw);
    // Unknown legacy routes should still reach the app's 404 at a clean URL.
    if (!target && legacy && hash.startsWith("#/") && !hash.startsWith("#//")) {
        const url = new URL(hash.slice(1), window.location.origin);
        if (url.origin === window.location.origin) target = url.pathname + url.search + url.hash;
    }
    if (!target) return true;
    if (legacy && !hash.includes("?") && canonicalPath(pathname) === target.split("#")[0]) {
        target += search;
    }
    if (requiresDocument(target)) {
        window.location.replace(target);
        return false;
    }
    if (target !== pathname + search + hash) window.history.replaceState(window.history.state, "", target);
    return true;
}

/** Run before mounting React so bookmarked hashes never become application state. */
export function initializeNavigation(): { ready: boolean; dispose: () => void } {
    const ready = normalizeLocation();
    const onPopState = (event: PopStateEvent) => {
        if (!normalizeLocation()) event.stopImmediatePropagation();
    };
    const onHashChange = () => {
        if (window.location.hash.startsWith("#/") && normalizeLocation()) announceNavigation();
    };
    window.addEventListener("popstate", onPopState);
    window.addEventListener("hashchange", onHashChange);
    return { ready, dispose: () => {
        window.removeEventListener("popstate", onPopState);
        window.removeEventListener("hashchange", onHashChange);
    } };
}
