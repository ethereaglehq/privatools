/**
 * Light/dark preference for Daylight.
 *
 * Two copies of the resolution rule exist on purpose: index.html has to
 * resolve the same thing before first paint (an inline pre-paint script cannot
 * import), or a visitor who chose light watches the dark palette flash on
 * every load. `skinTheme.test.ts` holds the two together.
 *
 * Daylight paints from `data-theme` on <html>: its component CSS keys dark
 * styles on `[data-theme="dark"]` with a `prefers-color-scheme` fallback for
 * the moment before anything has set the attribute, and the generated token
 * palette in skins.css follows the same axis.
 */

import type { SkinId } from "./skins";

export type ThemeChoice = "system" | "light" | "dark" | "midnight";

/** Where the preference is kept. */
const KEYS: Record<SkinId, { key: string }> = {
    daylight: { key: "privatools.daylight.theme" },
};
const volatileChoices = new Map<SkinId, ThemeChoice>();

function systemPrefers(): "light" | "dark" {
    return typeof window !== "undefined"
        && window.matchMedia?.("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark";
}

export function readThemeChoice(skin: SkinId): ThemeChoice {
    const volatile = volatileChoices.get(skin);
    if (volatile) return volatile;
    try {
        const spec = KEYS[skin];
        if (!spec) return "system";
        const v = localStorage.getItem(spec.key);
        return v === "light" || v === "dark" || v === "midnight" || v === "system" ? v : "system";
    } catch {
        return "system";
    }
}

/** Resolve `system` against the OS; explicit choices (midnight included) pass through. */
export function resolveTheme(choice: ThemeChoice): "light" | "dark" | "midnight" {
    return choice === "system" ? systemPrefers() : choice;
}

/**
 * Persist the choice and paint it.
 *
 * Both halves matter for different reasons: the write is what survives a
 * reload (and what index.html reads before first paint), the attribute is
 * what makes the click do something now.
 */
export function setThemeChoice(skin: SkinId, choice: ThemeChoice): void {
    try {
        const spec = KEYS[skin];
        if (spec) localStorage.setItem(spec.key, choice);
        volatileChoices.delete(skin);
    } catch {
        // A blocked/quota-limited store still keeps this tab's manual choice.
        volatileChoices.set(skin, choice);
    }
    document.documentElement.setAttribute("data-theme", resolveTheme(choice));
    window.dispatchEvent(new CustomEvent("privatools:theme-change", { detail: { choice } }));
}

/** Follow OS changes only while the user has chosen the system appearance. */
export function watchThemeChoice(skin: SkinId, onChange: (choice: ThemeChoice) => void): () => void {
    const media = window.matchMedia("(prefers-color-scheme: light)");
    const update = () => {
        const choice = readThemeChoice(skin);
        document.documentElement.setAttribute("data-theme", resolveTheme(choice));
        onChange(choice);
    };
    const storage = (event: StorageEvent) => {
        if (event.key === KEYS[skin].key || event.key === null) {
            volatileChoices.delete(skin);
            update();
        }
    };
    media.addEventListener?.("change", update);
    window.addEventListener("storage", storage);
    const experience = (event: Event) => {
        const detail = (event as CustomEvent).detail;
        if (detail?.source !== "experience") return;
        volatileChoices.set(skin, detail.choice);
        onChange(detail.choice);
    };
    window.addEventListener("privatools:theme-change", experience);
    return () => {
        media.removeEventListener?.("change", update);
        window.removeEventListener("storage", storage);
        window.removeEventListener("privatools:theme-change", experience);
    };
}
