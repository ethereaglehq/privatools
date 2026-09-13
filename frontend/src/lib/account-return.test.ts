import { beforeEach, describe, expect, it, vi } from "vitest";
import { captureAccountReturn, consumeAccountReturn, safeAccountReturn } from "./account-return";
beforeEach(() => { sessionStorage.clear(); vi.useRealTimers(); });
describe("account sign-in return intent", () => {
  it.each(["https://evil.test", "//evil.test", "/account/settings?redirect=https://evil.test", "/account/keys#anything", "/account/settings/", "/tools", "/account/../settings"])("rejects non-allowlisted target %s", target => expect(safeAccountReturn(target)).toBeNull());
  it.each(["/account/settings", "/account/keys"])("preserves %s across OAuth URL changes and consumes once", target => {
    captureAccountReturn(`?next=${encodeURIComponent(target)}`);
    captureAccountReturn("?sso_return=1");
    expect(consumeAccountReturn()).toBe(target); expect(consumeAccountReturn()).toBeNull();
  });
  it("clears a prior intent when the next URL explicitly supplies an invalid target", () => {
    captureAccountReturn("?next=/account/settings"); captureAccountReturn("?next=//evil.test");
    expect(consumeAccountReturn()).toBeNull();
  });
  it("does not redirect to stale intent from an earlier attempt", () => {
    vi.useFakeTimers(); captureAccountReturn("?next=/account/keys"); vi.advanceTimersByTime(16 * 60_000);
    expect(consumeAccountReturn()).toBeNull(); vi.useRealTimers();
  });
});
