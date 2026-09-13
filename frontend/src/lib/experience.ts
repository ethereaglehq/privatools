import { useSyncExternalStore } from "react";

export type Experience = "air" | "play";
export type Appearance = "system" | "light" | "dark";
export type ResolvedAppearance = "light" | "dark";

export const EXPERIENCE_STORAGE_KEY = "privatools.experience";
export const APPEARANCE_STORAGE_KEY = "privatools.appearance";
export const LEGACY_THEME_STORAGE_KEY = "privatools.daylight.theme";
export const EXPERIENCE_THEME_EVENT = "privatools:theme-change";

interface ExperienceSnapshot {
  experience: Experience;
  appearance: Appearance;
  resolved: ResolvedAppearance;
}

const SERVER_SNAPSHOT: ExperienceSnapshot = {
  experience: "air", appearance: "system", resolved: "light",
};

function appearanceOf(value: unknown): Appearance | null {
  // Midnight belonged to the previous design. The selected Graphite and
  // Charcoal palettes are now the deliberate dark appearance of each style.
  if (value === "midnight") return "dark";
  return value === "system" || value === "light" || value === "dark" ? value : null;
}

function stored(key: string): string | null {
  try { return window.localStorage.getItem(key); } catch { return null; }
}

function resolved(appearance: Appearance): ResolvedAppearance {
  if (appearance !== "system") return appearance;
  if (typeof window === "undefined" || !window.matchMedia) return "light";
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function readSnapshot(): ExperienceSnapshot {
  if (typeof window === "undefined") return SERVER_SNAPSHOT;
  const experience = stored(EXPERIENCE_STORAGE_KEY) === "play" ? "play" : "air";
  const appearance = appearanceOf(stored(APPEARANCE_STORAGE_KEY))
    ?? appearanceOf(stored(LEGACY_THEME_STORAGE_KEY)) ?? "system";
  return { experience, appearance, resolved: resolved(appearance) };
}

const CHROME_COLORS = {
  air: { light: "#edf3f9", dark: "#151619" },
  play: { light: "#fae7eb", dark: "#181818" },
} as const;

function paint(snapshot: ExperienceSnapshot) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.dataset.experience = snapshot.experience;
  root.dataset.appearance = snapshot.appearance;
  root.dataset.theme = snapshot.resolved;
  root.style.colorScheme = snapshot.resolved;
  const color = CHROME_COLORS[snapshot.experience][snapshot.resolved];
  // A stored manual choice outranks the OS even in standalone browser chrome.
  document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')
    .forEach(meta => { meta.content = color; });
}

/** One store keeps every selector in agreement without replacing the app tree. */
export function createExperienceStore() {
  let current = readSnapshot();
  const listeners = new Set<() => void>();
  let stop: (() => void) | undefined;

  function update(next: ExperienceSnapshot, persist = false, announce = false) {
    const changed = current.experience !== next.experience
      || current.appearance !== next.appearance || current.resolved !== next.resolved;
    current = changed ? next : current;
    if (persist && typeof window !== "undefined") {
      // Each write is independent: a blocked/quota-limited store never resets
      // this tab's current choice or prevents the page from repainting.
      for (const [key, value] of [
        [EXPERIENCE_STORAGE_KEY, current.experience],
        [APPEARANCE_STORAGE_KEY, current.appearance],
        [LEGACY_THEME_STORAGE_KEY, current.appearance],
      ]) {
        try { window.localStorage.setItem(key, value); } catch { /* keep in memory */ }
      }
    }
    paint(current);
    if (changed) listeners.forEach(listener => listener());
    if (announce && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(EXPERIENCE_THEME_EVENT, {
        detail: { choice: current.appearance, source: "experience" },
      }));
    }
  }

  function setExperience(experience: Experience) {
    if (experience !== "air" && experience !== "play") return;
    update({ ...current, experience }, true);
  }

  function setAppearance(appearance: Appearance) {
    if (appearance !== "system" && appearance !== "light" && appearance !== "dark") return;
    update({ ...current, appearance, resolved: resolved(appearance) }, true, true);
  }

  function start() {
    if (typeof window === "undefined") return () => {};
    const media = window.matchMedia?.("(prefers-color-scheme: light)");
    const onSystem = () => {
      if (current.appearance === "system") {
        update({ ...current, resolved: resolved("system") });
      }
    };
    const onStorage = (event: StorageEvent) => {
      try { if (event.storageArea && event.storageArea !== window.localStorage) return; } catch { /* blocked store */ }
      if (event.key === null) update(readSnapshot());
      else if (event.key === EXPERIENCE_STORAGE_KEY) {
        update({ ...current, experience: event.newValue === "play" ? "play" : "air" });
      } else if (event.key === APPEARANCE_STORAGE_KEY || event.key === LEGACY_THEME_STORAGE_KEY) {
        const appearance = appearanceOf(event.newValue) ?? "system";
        update({ ...current, appearance, resolved: resolved(appearance) });
      }
    };
    const onTheme = (event: Event) => {
      const detail = (event as CustomEvent<{ choice?: unknown; source?: string }>).detail;
      if (detail?.source === "experience") return;
      const appearance = appearanceOf(detail?.choice);
      if (appearance) update({ ...current, appearance, resolved: resolved(appearance) }, true);
    };
    // Older controls can still paint data-theme directly. Reconcile those
    // changes while preserving system mode when the resolved color is correct.
    const observer = typeof MutationObserver === "undefined" ? null : new MutationObserver(() => {
      const theme = appearanceOf(document.documentElement.dataset.theme);
      if (!theme || theme === "system" || theme === current.resolved) return;
      const legacy = appearanceOf(stored(LEGACY_THEME_STORAGE_KEY));
      const appearance = legacy && resolved(legacy) === theme ? legacy : theme;
      update({ ...current, appearance, resolved: resolved(appearance) }, true);
    });
    media?.addEventListener?.("change", onSystem);
    window.addEventListener("storage", onStorage);
    window.addEventListener(EXPERIENCE_THEME_EVENT, onTheme);
    observer?.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    update({ ...current, resolved: resolved(current.appearance) }, true);
    return () => {
      media?.removeEventListener?.("change", onSystem);
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(EXPERIENCE_THEME_EVENT, onTheme);
      observer?.disconnect();
    };
  }

  return {
    getSnapshot: () => current,
    subscribe(listener: () => void) {
      listeners.add(listener);
      if (listeners.size === 1) stop = start();
      return () => {
        listeners.delete(listener);
        if (listeners.size === 0) { stop?.(); stop = undefined; }
      };
    },
    setExperience,
    setAppearance,
  };
}

const store = createExperienceStore();
export const setExperience = store.setExperience;
export const setAppearance = store.setAppearance;

export function useExperience() {
  const snapshot = useSyncExternalStore(store.subscribe, store.getSnapshot, () => SERVER_SNAPSHOT);
  return { ...snapshot, setExperience, setAppearance };
}
