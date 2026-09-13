import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  APPEARANCE_STORAGE_KEY, EXPERIENCE_STORAGE_KEY, EXPERIENCE_THEME_EVENT,
  LEGACY_THEME_STORAGE_KEY, createExperienceStore,
} from "./experience";

let media: EventTarget & { matches: boolean };
const cleanups: Array<() => void> = [];

beforeEach(() => {
  localStorage.clear();
  for (const name of ["data-theme", "data-experience", "data-appearance", "style"]) {
    document.documentElement.removeAttribute(name);
  }
  media = Object.assign(new EventTarget(), { matches: true });
  vi.spyOn(window, "matchMedia").mockReturnValue(media as MediaQueryList);
});

afterEach(() => {
  cleanups.splice(0).forEach(cleanup => cleanup());
  vi.restoreAllMocks();
  document.querySelectorAll('meta[data-experience-test]').forEach(node => node.remove());
});

function mountedStore() {
  const store = createExperienceStore();
  const changed = vi.fn();
  cleanups.push(store.subscribe(changed));
  return { store, changed };
}

describe("independent design and appearance preferences", () => {
  it("defaults to Air and follows the device setting", () => {
    const { store } = mountedStore();
    expect(store.getSnapshot()).toEqual({ experience: "air", appearance: "system", resolved: "light" });
    expect(document.documentElement.dataset).toMatchObject({ experience: "air", appearance: "system", theme: "light" });
  });

  it("keeps appearance unchanged when switching the experience", () => {
    const { store, changed } = mountedStore();
    store.setAppearance("dark");
    store.setExperience("play");
    expect(store.getSnapshot()).toEqual({ experience: "play", appearance: "dark", resolved: "dark" });
    expect(localStorage.getItem(EXPERIENCE_STORAGE_KEY)).toBe("play");
    expect(localStorage.getItem(APPEARANCE_STORAGE_KEY)).toBe("dark");
    expect(localStorage.getItem(LEGACY_THEME_STORAGE_KEY)).toBe("dark");
    expect(changed).toHaveBeenCalledTimes(2);
    expect(createExperienceStore().getSnapshot()).toEqual(store.getSnapshot());
  });

  it("returns a stable snapshot for unchanged state", () => {
    const { store, changed } = mountedStore();
    const snapshot = store.getSnapshot();
    store.setExperience("air");
    store.setAppearance("system");
    expect(store.getSnapshot()).toBe(snapshot);
    expect(changed).not.toHaveBeenCalled();
  });

  it.each(["light", "dark", "system", "midnight"])("migrates the previous %s appearance", previous => {
    localStorage.setItem(LEGACY_THEME_STORAGE_KEY, previous);
    const { store } = mountedStore();
    expect(store.getSnapshot().appearance).toBe(previous === "midnight" ? "dark" : previous);
    expect(localStorage.getItem(APPEARANCE_STORAGE_KEY)).toBe(previous === "midnight" ? "dark" : previous);
  });

  it("prefers a valid new setting and recovers from invalid stored choices", () => {
    localStorage.setItem(APPEARANCE_STORAGE_KEY, "light");
    localStorage.setItem(LEGACY_THEME_STORAGE_KEY, "dark");
    localStorage.setItem(EXPERIENCE_STORAGE_KEY, "unknown");
    expect(createExperienceStore().getSnapshot()).toEqual({ experience: "air", appearance: "light", resolved: "light" });
    localStorage.setItem(APPEARANCE_STORAGE_KEY, "unknown");
    expect(createExperienceStore().getSnapshot().appearance).toBe("dark");
  });

  it("follows OS changes only in system mode", () => {
    const { store } = mountedStore();
    media.matches = false;
    media.dispatchEvent(new Event("change"));
    expect(store.getSnapshot().resolved).toBe("dark");
    expect(store.getSnapshot().appearance).toBe("system");
    store.setAppearance("light");
    media.dispatchEvent(new Event("change"));
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("keeps both manual choices usable when persistence is blocked", () => {
    const { store } = mountedStore();
    vi.spyOn(window.localStorage, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    store.setAppearance("dark");
    store.setExperience("play");
    media.dispatchEvent(new Event("change"));
    expect(store.getSnapshot()).toEqual({ experience: "play", appearance: "dark", resolved: "dark" });
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("synchronizes choices from another tab and handles a storage clear", () => {
    const { store } = mountedStore();
    window.dispatchEvent(new StorageEvent("storage", { key: EXPERIENCE_STORAGE_KEY, newValue: "play" }));
    window.dispatchEvent(new StorageEvent("storage", { key: APPEARANCE_STORAGE_KEY, newValue: "dark" }));
    expect(store.getSnapshot()).toEqual({ experience: "play", appearance: "dark", resolved: "dark" });
    localStorage.clear();
    window.dispatchEvent(new StorageEvent("storage", { key: null }));
    expect(store.getSnapshot()).toEqual({ experience: "air", appearance: "system", resolved: "light" });
  });

  it("coordinates legacy controls without recursively announcing changes", () => {
    const { store, changed } = mountedStore();
    const event = vi.fn();
    window.addEventListener(EXPERIENCE_THEME_EVENT, event);
    cleanups.push(() => window.removeEventListener(EXPERIENCE_THEME_EVENT, event));
    window.dispatchEvent(new CustomEvent(EXPERIENCE_THEME_EVENT, { detail: { choice: "midnight" } }));
    expect(store.getSnapshot().appearance).toBe("dark");
    expect(event).toHaveBeenCalledTimes(1);
    store.setAppearance("light");
    expect(event).toHaveBeenCalledTimes(2);
    expect(changed).toHaveBeenCalledTimes(2);
  });

  it("reconciles direct legacy DOM paints", async () => {
    const { store } = mountedStore();
    localStorage.setItem(LEGACY_THEME_STORAGE_KEY, "dark");
    document.documentElement.dataset.theme = "dark";
    await Promise.resolve();
    expect(store.getSnapshot().appearance).toBe("dark");
  });

  it("detaches event listeners when the final subscriber leaves", () => {
    const store = createExperienceStore();
    const stop = store.subscribe(() => {});
    stop();
    media.matches = false;
    media.dispatchEvent(new Event("change"));
    expect(store.getSnapshot().resolved).toBe("light");
  });
});

describe("prepaint and installed browser chrome", () => {
  const html = readFileSync(resolve(__dirname, "../../index.html"), "utf8");
  const script = html.match(/<script id="experience-prepaint">([\s\S]*?)<\/script>/)?.[1];

  it.each([
    ["air", "light", "#edf3f9"], ["air", "dark", "#151619"],
    ["play", "light", "#fae7eb"], ["play", "dark", "#181818"],
  ] as const)("prepaints %s %s identically to the mounted store", (experience, appearance, color) => {
    const meta = document.createElement("meta");
    meta.name = "theme-color";
    meta.setAttribute("data-experience-test", "");
    document.head.appendChild(meta);
    localStorage.setItem(EXPERIENCE_STORAGE_KEY, experience);
    localStorage.setItem(APPEARANCE_STORAGE_KEY, appearance);
    expect(script).toBeTruthy();
    new Function("window", "document", script!)(window, document);
    expect(document.documentElement.dataset).toMatchObject({ experience, appearance, theme: appearance });
    expect(meta.content).toBe(color);
    const { store } = mountedStore();
    expect(store.getSnapshot()).toEqual({ experience, appearance, resolved: appearance });
    expect(meta.content).toBe(color);
  });

  it("prepaint resolves legacy midnight and an explicit choice above OS preference", () => {
    localStorage.setItem(LEGACY_THEME_STORAGE_KEY, "midnight");
    new Function("window", "document", script!)(window, document);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(document.documentElement.dataset.appearance).toBe("dark");
    localStorage.setItem(APPEARANCE_STORAGE_KEY, "system");
    new Function("window", "document", script!)(window, document);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(document.documentElement.dataset.appearance).toBe("system");
  });
});
