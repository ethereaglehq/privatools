import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { withAccounts } from "./withAccounts";

const api = vi.hoisted(() => ({ listKeys: vi.fn(), createKey: vi.fn(), revokeKey: vi.fn(), logout: vi.fn(), recover: vi.fn() }));
vi.mock("./accountLogic", async importOriginal => ({ ...(await importOriginal<object>()), accountApi: api }));

class Base {
  state: Record<string, any> = {};
  setState(update: any) { Object.assign(this.state, typeof update === "function" ? update(this.state) : update); }
}
const record = { key_id: "test_id", label: "Key 1", created_at: "2026-09-13", last_used_at: null, revoked: false };
const flush = () => new Promise(resolve => setTimeout(resolve, 0));
function account() {
  const Account = withAccounts(Base, {});
  const result = new Account({});
  result._setAcct({ user: { id: "synthetic", email: "test@example.test", created_at: "2026-09-13" } });
  return result;
}
beforeEach(() => { Object.values(api).forEach(mock => mock.mockReset()); });
afterEach(() => vi.unstubAllGlobals());

describe("account API lifecycle", () => {
  it("serializes key creation and keeps the one-time secret until acknowledged", async () => {
    let finish!: (value: unknown) => void;
    api.createKey.mockReturnValue(new Promise(resolve => { finish = resolve; }));
    const page = account();
    page._acctNewKey(); page._acctNewKey();
    expect(api.createKey).toHaveBeenCalledTimes(1);
    finish({ key: "pk_SYNTHETIC", record }); await flush();
    page._acctNewKey();
    expect(api.createKey).toHaveBeenCalledTimes(1);
    expect(page.state.acct.freshKey).toBe("pk_SYNTHETIC");
    expect(page.state.acct.keys).toEqual([record]);
    page._acctAckKey(); page._acctNewKey();
    expect(api.createKey).toHaveBeenCalledTimes(2);
  });

  it("does not overwrite a newly created key with an older list response", async () => {
    let finish!: (value: unknown) => void;
    api.listKeys.mockReturnValue(new Promise(resolve => { finish = resolve; }));
    api.createKey.mockResolvedValue({ key: "pk_SYNTHETIC", record });
    const page = account(); page._loadKeys(); page._acctNewKey(); await flush();
    finish({ keys: [] }); await flush();
    expect(page.state.acct.keys).toEqual([record]);
  });

  it("retains the replacement recovery code while clearing the expired session", async () => {
    api.recover.mockResolvedValue({ ok: true, recovery_code: "SYNTHETIC-NEW-CODE" });
    const page = account();
    page._setAcct({ mode: "recover", email: "test@example.test", password: "a-new-synthetic-passphrase", recoveryInput: "SYNTHETIC-OLD-CODE", keys: [record], freshKey: "pk_OLD" });
    page._acctRecover(null); await flush();
    expect(page.state.acct.recoveryCode).toBe("SYNTHETIC-NEW-CODE");
    expect(page.state.acct.user).toBeNull();
    expect(page.state.acct.password).toBe("");
    expect(page.state.acct.recoveryInput).toBe("");
    expect(page.state.acct.freshKey).toBe("");
    page._acctAckRecovery();
    expect(page.state.acct.mode).toBe("signin");
    expect(page.state.acct.recoveryCode).toBe("");
  });

  it("keeps the signed-in state when logout fails", async () => {
    api.logout.mockRejectedValue(new Error("offline"));
    const page = account(); page._acctSignOut(); await flush();
    expect(page.state.acct.user.id).toBe("synthetic");
    expect(page.state.acct.error).toContain("could not be signed out");
    expect(page.state.acct.busy).toBe(false);
  });

  it("drops secrets and ignores stale key loads after successful logout", async () => {
    let finish!: (value: unknown) => void;
    api.listKeys.mockReturnValue(new Promise(resolve => { finish = resolve; }));
    api.logout.mockResolvedValue({ ok: true });
    const page = account(); page._loadKeys(); page._setAcct({ freshKey: "pk_SYNTHETIC" });
    page._acctSignOut(); await flush(); finish({ keys: [record] }); await flush();
    expect(page.state.acct.user).toBeNull();
    expect(page.state.acct.freshKey).toBe("");
    expect(page.state.acct.keys).toEqual([]);
  });

  it("marks a confirmed revocation and does not send it again", async () => {
    api.revokeKey.mockResolvedValue({ ok: true });
    const page = account(); page._setAcct({ keys: [record] });
    page._acctRevoke(record.key_id); page._acctRevoke(record.key_id); await flush();
    page._acctRevoke(record.key_id);
    expect(api.revokeKey).toHaveBeenCalledTimes(1);
    expect(page.state.acct.keys[0].revoked).toBe(true);
  });

  it("makes a key-list failure visible and keeps a key after clipboard failure", async () => {
    api.listKeys.mockRejectedValue(new Error("offline"));
    const page = account(); await page._loadKeys();
    expect(page.state.acct.keysLoading).toBe(false);
    expect(page.state.acct.error).toContain("could not be loaded");
    api.listKeys.mockResolvedValue({ keys: [record] }); await page._loadKeys();
    expect(page.state.acct.error).toBe("");
    expect(page.state.acct.keys).toEqual([record]);
    vi.stubGlobal("navigator", { clipboard: { writeText: vi.fn().mockRejectedValue(new Error("blocked")) } });
    page._setAcct({ freshKey: "pk_SYNTHETIC" }); page._acctCopyKey(); await flush();
    expect(page.state.acct.freshKey).toBe("pk_SYNTHETIC");
    expect(page.state.acct.freshKeyCopied).toBe(false);
    expect(page.state.acct.error).toContain("copy it manually");
  });
});
