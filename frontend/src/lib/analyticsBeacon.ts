/**
 * Send the first-party pageview beacon.
 *
 * `/api/analytics/pageview` has existed on the backend, and the privacy page
 * has described it in the present tense, for a long time — but nothing in the
 * browser ever called it. GA4 was empty because no pageview was ever sent, not
 * because a key was missing.
 *
 * Everything here is deliberately small: a path, a title, a same-origin
 * referrer and an anonymous id. No file names, no query strings, no uploads.
 * The backend re-sanitises all of it before forwarding, so this is the polite
 * version of a contract it already enforces.
 */

import { readAnalyticsPrivacyPreference } from "./analyticsPrivacy";

const CLIENT_ID_KEY = "pt-analytics-cid";
const SESSION_KEY = "pt-analytics-session";
const ENDPOINT = "/api/analytics/pageview";
/** GA4's own definition of a session: 30 minutes of inactivity ends it. */
const SESSION_IDLE_MS = 30 * 60 * 1000;
/** GA4 rejects a single event claiming more than an hour of engagement. */
const MAX_ENGAGEMENT_MS = 3_600_000;
/**
 * Don't spend a request on a sub-second sliver.
 *
 * Time under the threshold is *kept*, not dropped — it stays in the
 * accumulator and rides along with the next flush — so a visitor who flicks
 * between tabs a dozen times still has every millisecond counted once.
 */
const MIN_FLUSH_MS = 1000;

/**
 * A random id, kept in localStorage so repeat visits count as one browser.
 *
 * Not derived from anything about the visitor: no fingerprint, no IP, no
 * account. Clearing site data ends it, which is the intended escape hatch.
 * Private mode throws on storage, and a per-session id is the right fallback.
 */
function clientId(): string {
    const fresh = () =>
        `${Date.now().toString(36)}.${Math.random().toString(36).slice(2, 12)}`;
    try {
        const held = localStorage.getItem(CLIENT_ID_KEY);
        if (held) return held;
        const made = fresh();
        localStorage.setItem(CLIENT_ID_KEY, made);
        return made;
    } catch {
        return fresh();
    }
}

/**
 * Whether this visitor has asked, by any means, not to be counted.
 *
 * `effectiveDisabled` already folds together the local toggle and the
 * browser's DNT/GPC signal, so this defers to it rather than re-deriving the
 * rule and risking the two drifting apart.
 */
function optedOut(): boolean {
    try {
        return readAnalyticsPrivacyPreference().effectiveDisabled;
    } catch {
        // A preference we cannot read is not consent.
        return true;
    }
}

/**
 * One canonical path per view.
 *
 * The skin routes on the hash, and it sets that hash from the URL path on
 * mount — so a single arrival produces "/" and then "/#/", which look like two
 * different pages and were counted as two. Reading the hash when there is one,
 * and trimming the trailing slash, collapses them to the same "/". Query
 * strings are dropped here as well as server-side: a shared link can carry
 * things a page-view report has no business holding.
 */
function normalise(raw: string): string {
    const noQuery = raw.split("?")[0].split("#")[0];
    return noQuery.replace(/\/+$/, "") || "/";
}

function currentPath(): string {
    const hash = window.location.hash.replace(/^#/, "");
    return normalise(hash.startsWith("/") ? hash : window.location.pathname);
}

/**
 * A GA4 session id, rolled after 30 minutes of inactivity.
 *
 * Without one, and without engagement_time_msec below, GA4 accepts the event
 * and shows it in Realtime but never counts it towards users, sessions or
 * engagement — so every standard report stays empty while the data appears to
 * be arriving. It is the most expensive silent failure in Measurement
 * Protocol, because everything looks like it is working.
 */
function sessionId(): string {
    const now = Date.now();
    const fresh = () => String(Math.floor(now / 1000));
    try {
        const raw = sessionStorage.getItem(SESSION_KEY);
        if (raw) {
            const [id, last] = raw.split(":");
            if (id && Number(last) && now - Number(last) < SESSION_IDLE_MS) {
                sessionStorage.setItem(SESSION_KEY, `${id}:${now}`);
                return id;
            }
        }
        const made = fresh();
        sessionStorage.setItem(SESSION_KEY, `${made}:${now}`);
        return made;
    } catch {
        return fresh();
    }
}

/**
 * Foreground milliseconds spent on the current page and not yet reported.
 *
 * GA4 calls a session engaged when it lasts over ten seconds, reaches a second
 * page, or fires a key event — and bounce rate is simply the inverse. So a
 * visit that reports no engagement time and never navigates is *defined* as a
 * bounce no matter how long the visitor actually stayed.
 *
 * The first version of this file measured the wrong interval: it sent the time
 * between module load and the pageview firing, which is a few milliseconds,
 * and then sent nothing else for the rest of the visit. Every single-page
 * visit therefore reported ~0ms and scored as a bounce, which is how a real
 * site produced a 100% bounce rate. Accumulating foreground time and flushing
 * it when the page is hidden is what gtag.js does, and it is the only way the
 * number means anything.
 */
let unreported = 0;
/** When the current foreground stretch began; 0 while the page is hidden. */
let foregroundSince = Date.now();

/** Fold the open foreground stretch into the accumulator. */
function accrue(): void {
    if (!foregroundSince) return;
    const now = Date.now();
    unreported += now - foregroundSince;
    foregroundSince = now;
}

/** Take everything accumulated so far, leaving the accumulator empty. */
function takeEngagement(): number {
    accrue();
    const ms = Math.min(unreported, MAX_ENGAGEMENT_MS);
    unreported = 0;
    return ms;
}

function post(body: Record<string, unknown>): void {
    const json = JSON.stringify(body);
    try {
        // sendBeacon survives the page being closed mid-navigation, which is
        // exactly when the last pageview of a visit would otherwise be lost.
        if (navigator.sendBeacon) {
            navigator.sendBeacon(ENDPOINT, new Blob([json], { type: "application/json" }));
            return;
        }
        void fetch(ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: json,
            keepalive: true,
        }).catch(() => {});
    } catch {
        // Analytics must never be the reason a page misbehaves.
    }
}

/** The last path sent, so a re-render does not count twice. */
let lastPath = "";

export function sendPageview(path?: string): void {
    if (typeof window === "undefined") return;
    if (optedOut()) return;

    const clean = path ? normalise(path) : currentPath();
    if (clean === lastPath) return;
    lastPath = clean;

    post({
        event: "page_view",
        path: clean,
        title: document.title.slice(0, 160) || null,
        referrer: document.referrer || null,
        client_id: clientId(),
        session_id: sessionId(),
        // Whatever the visitor spent on the page they are leaving. On the very
        // first view of a visit this is legitimately ~0.
        engagement_time_msec: takeEngagement(),
    });
}

/**
 * Report time spent, without counting another page view.
 *
 * `user_engagement` is GA4's own event for this: it adds to engagement time
 * and can tip a session over the ten-second line, but it does not inflate the
 * page-view count the way a second `page_view` would.
 */
export function flushEngagement(): void {
    if (typeof window === "undefined") return;
    if (optedOut()) return;

    accrue();
    if (unreported < MIN_FLUSH_MS) return;
    const ms = Math.min(unreported, MAX_ENGAGEMENT_MS);
    unreported = 0;

    post({
        event: "user_engagement",
        path: currentPath(),
        title: document.title.slice(0, 160) || null,
        client_id: clientId(),
        session_id: sessionId(),
        engagement_time_msec: ms,
    });
}

/**
 * Count the first view, every hash navigation after it, and time on page.
 *
 * Returns a teardown so a test — or a second mount — cannot leave a listener
 * behind.
 */
export function startPageviewTracking(): () => void {
    if (typeof window === "undefined") return () => {};

    // The skin sets document.title from its own hashchange handler, which runs
    // after this one — so sending immediately records every tool page under
    // the *previous* page's title. One macrotask is enough to let the router
    // and React's effects settle, and a visitor who leaves inside that tick
    // was never going to register as a page view anyway.
    let navTimer: ReturnType<typeof setTimeout> | undefined;
    const onNav = () => {
        clearTimeout(navTimer);
        navTimer = setTimeout(() => sendPageview(), 0);
    };
    const onVisibility = () => {
        if (document.visibilityState === "hidden") {
            // Report before the tab is frozen, and stop the clock: minutes
            // spent in a background tab are not engagement.
            flushEngagement();
            foregroundSince = 0;
        } else if (!foregroundSince) {
            foregroundSince = Date.now();
        }
    };
    // pagehide, not beforeunload: beforeunload is unreliable on mobile Safari
    // and disqualifies the page from the back/forward cache.
    const onHide = () => flushEngagement();

    foregroundSince = document.visibilityState === "hidden" ? 0 : Date.now();
    sendPageview();

    window.addEventListener("hashchange", onNav);
    window.addEventListener("popstate", onNav);
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("pagehide", onHide);

    return () => {
        clearTimeout(navTimer);
        window.removeEventListener("hashchange", onNav);
        window.removeEventListener("popstate", onNav);
        document.removeEventListener("visibilitychange", onVisibility);
        window.removeEventListener("pagehide", onHide);
    };
}
