import { afterEach, describe, expect, it, vi } from "vitest";
import { accountApi } from "./accountLogic";

vi.mock("@/lib/clerk/instance", () => ({ isClerkEnabled: () => false }));
afterEach(() => vi.unstubAllGlobals());

describe("native account transport", () => {
  it("keeps HttpOnly session requests on the frontend origin with no caching", async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ user: { id: "synthetic" } }) });
    vi.stubGlobal("fetch", fetch);
    await accountApi.login("synthetic@example.test", "a-synthetic-passphrase");
    expect(fetch).toHaveBeenCalledWith("/api/auth/login", expect.objectContaining({
      method: "POST", credentials: "same-origin", cache: "no-store",
      body: JSON.stringify({ email: "synthetic@example.test", password: "a-synthetic-passphrase" }),
    }));
  });

  it("shows validation messages without serializing submitted inputs", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ msg: "String should have at most 1024 characters", input: "SYNTHETIC_SECRET" }] }) }));
    await expect(accountApi.login("synthetic@example.test", "SYNTHETIC_SECRET")).rejects.toThrow("String should have at most 1024 characters");
  });
});
