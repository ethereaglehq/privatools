import { Suspense, lazy, useEffect, useState } from "react";
import DaylightApp from "./extensions/daylight";
import { canonicalPath, currentRoute, navigateTo } from "@/lib/navigation";

/**
 * Mounts Daylight — the site's design.
 *
 * Daylight is a complete application: its own navigation, its own routing, its
 * own page compositions. It began as one of four selectable skins and is now
 * the only one, so it is imported eagerly — it *is* the first paint, and a
 * lazy chunk here would put a blank frame in front of every visitor.
 */

// The workspace banners the house shell used to carry. Backend-down and
// unfinished-batch are product states, not house-design states, so they live
// on whatever design owns the screen.
const BackendStatusBanner = lazy(() =>
    import("@/components/BackendStatusBanner").then((m) => ({ default: m.BackendStatusBanner })));
const BatchResumeBanner = lazy(() =>
    import("@/components/BatchResumeBanner").then((m) => ({ default: m.BatchResumeBanner })));

/** Whether Daylight is currently showing the batch surface. */
function useOnBatch(): boolean {
    const [on, setOn] = useState(() => /^\/batch(\/|\?|$)/.test(currentRoute()));
    useEffect(() => {
        const read = () => setOn(/^\/batch(\/|\?|$)/.test(currentRoute()));
        window.addEventListener("popstate", read);
        return () => window.removeEventListener("popstate", read);
    }, []);
    return on;
}

export function SkinAppHost() {
    const onBatch = useOnBatch();

    // Retire the pre-hydration brand painted by index.html — Daylight renders
    // its own header, and leaving both shows a second, offset logo.
    useEffect(() => { document.documentElement.classList.add("app-ready"); }, []);

    // The skip link in index.html has to point at Daylight's main element.
    // It targets `#main-content` (a default that predates Daylight), so
    // retarget it once the design has mounted. Poll on a timer rather than
    // rAF: a tab opened in the background gets no animation frames at all,
    // and the link has to be correct by the time that tab is fronted.
    useEffect(() => {
        let tries = 0;
        let timer = 0;
        let skipLink: HTMLElement | null = null;
        const skip = (event: MouseEvent) => {
            const main = document.querySelector<HTMLElement>("main[id]");
            if (!main) return;
            // A fragment is a page route in this app. Move focus directly so
            // the accessibility link cannot navigate to a nonexistent page.
            event.preventDefault();
            main.focus({ preventScroll: true });
            main.scrollIntoView({ block: "start", behavior: "instant" });
        };
        const settle = () => {
            const prepaint = document.getElementById("prepaint-skip");
            if (!prepaint) return;
            const main = document.querySelector("main[id]");
            if (main) {
                prepaint.setAttribute("href", `#${main.id}`);
                skipLink = prepaint;
                prepaint.addEventListener("click", skip);
                return;
            }
            if (++tries < 40) timer = window.setTimeout(settle, 50);
        };
        settle();
        return () => {
            window.clearTimeout(timer);
            skipLink?.removeEventListener("click", skip);
        };
    }, []);

    // Keep app links in the mounted workspace. Capture-phase also handles
    // React Router links before their own history handler runs.
    const onClickCapture = (e: React.MouseEvent) => {
        if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        const a = (e.target as HTMLElement).closest?.("a");
        if (!a) return;
        const target = a.getAttribute("target");
        if (target && target !== "_self") return;
        if (a.hasAttribute("download")) return;
        const href = a.getAttribute("href") || "";
        if (!canonicalPath(href)) return;
        e.preventDefault();
        navigateTo(href);
    };

    return (
        <div onClickCapture={onClickCapture}>
            <Suspense fallback={null}>
                <BackendStatusBanner />
                {!onBatch && <BatchResumeBanner />}
            </Suspense>
            <DaylightApp />
        </div>
    );
}
