import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ClerkInstance } from "./instance";

beforeEach(() => { vi.resetModules(); vi.useFakeTimers(); vi.stubEnv("VITE_CLERK_PUBLISHABLE_KEY", "synthetic-public-key"); vi.stubGlobal("location", { pathname: "/account/sign-in" }); });
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
const clerk = (loaded: boolean) => ({ loaded } as ClerkInstance);

describe("Clerk readiness without polling", () => {
  it("does not wait for a provider on a document whose CSP excludes it", async () => {
    vi.stubGlobal("location", { pathname: "/", hash: "#/account" });
    const state = await import("./instance");
    expect(await state.whenClerkReady()).toBeNull(); expect(vi.getTimerCount()).toBe(0);
    expect(state.isClerkDocument("/account")).toBe(true);
    expect(state.isClerkDocument("/account/settings")).toBe(true);
    expect(state.isClerkDocument("/accounting")).toBe(false);
    expect(state.isClerkDocument("/tools/markdown-html")).toBe(false);
  });
  it("retains account document readiness after the visible path changes", async () => {
    const state = await import("./instance");
    vi.stubGlobal("location", { pathname: "/tools" });
    expect(state.isClerkDocument()).toBe(true);
    const pending = state.whenClerkReady();
    const ready = clerk(true); state.setClerkInstance(ready);
    expect(await pending).toBe(ready);
    expect(vi.getTimerCount()).toBe(0);
  });
  it("settles immediately when a newly ready instance replaces its loading instance", async () => {
    const state = await import("./instance");
    state.setClerkInstance(clerk(false));
    const pending = state.whenClerkReady();
    const ready = clerk(true); state.setClerkInstance(ready);
    expect(await pending).toBe(ready);
    expect(vi.getTimerCount()).toBe(0);
  });
  it("does not consider a parked but unloaded instance ready", async () => {
    const state = await import("./instance");
    const settled = vi.fn(); const pending = state.whenClerkReady().then(settled);
    state.setClerkInstance(clerk(false)); await Promise.resolve();
    expect(settled).not.toHaveBeenCalled();
    state.markClerkLoadFailed(); await pending;
    expect(settled).toHaveBeenCalledWith(null);
    expect(vi.getTimerCount()).toBe(0);
  });
  it("releases a blocked-script wait immediately rather than waiting fifteen seconds", async () => {
    const state = await import("./instance");
    const pending = state.whenClerkReady(); state.markClerkLoadFailed();
    expect(await pending).toBeNull(); expect(vi.getTimerCount()).toBe(0);
  });
  it("supports late readiness and live session changes after the initial timeout", async () => {
    const state = await import("./instance"); const listener = vi.fn();
    const unsubscribe = state.subscribeClerkInstance(listener);
    const pending = state.whenClerkReady(100); await vi.advanceTimersByTimeAsync(100);
    expect(await pending).toBeNull();
    const ready = clerk(true); state.setClerkInstance(ready);
    expect(listener).toHaveBeenLastCalledWith(ready);
    expect(await state.whenClerkReady()).toBe(ready);
    unsubscribe(); state.setClerkInstance(null);
    expect(listener).toHaveBeenCalledOnce(); expect(vi.getTimerCount()).toBe(0);
  });
});
