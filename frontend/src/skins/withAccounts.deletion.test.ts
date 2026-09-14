import { beforeEach, describe, expect, it, vi } from "vitest";
import { withAccounts } from "./withAccounts";

const mocks = vi.hoisted(() => ({ remove: vi.fn(), warning: vi.fn(), success: vi.fn() }));
vi.mock("./accountLogic", async original => ({ ...await original<object>(), EMAIL_RESET: true, accountApi: { deleteAccount: mocks.remove } }));
vi.mock("sonner", () => ({ toast: { warning: mocks.warning, success: mocks.success } }));

class Base {
    state: Record<string, any> = {};
    setState(update: any) { Object.assign(this.state, typeof update === "function" ? update(this.state) : update); }
}
const user = { id: "original-account", email: "person@example.test", created_at: "2026-09-13" };
const flush = () => new Promise(resolve => setTimeout(resolve, 0));
function page() {
    const Account = withAccounts(Base, {});
    const account = new Account({});
    account._setAcct({ user });
    account._setAccountSecurityRunner((action: () => Promise<unknown>) => action());
    return account;
}
beforeEach(() => { vi.resetAllMocks(); localStorage.clear(); sessionStorage.clear(); });

describe("verified account deletion controller", () => {
    it("requires explicit confirmation and serializes the confirmed action", async () => {
        let complete!: () => void;
        mocks.remove.mockImplementation(() => new Promise(resolve => { complete = () => resolve({ ok: true, cleanupPending: false }); }));
        const account = page();
        account._acctDelete();
        expect(mocks.remove).not.toHaveBeenCalled();
        account._acctDelete(); account._acctDelete();
        expect(mocks.remove).toHaveBeenCalledExactlyOnceWith(user.id);
        complete(); await flush();
        expect(account.state.acct.user).toBeNull();
        expect(mocks.success).toHaveBeenCalledWith("Your account has been deleted.");
    });

    it("does not run deletion while the verification bridge is unavailable", async () => {
        const account = page(); account._setAccountSecurityRunner(null);
        account._acctDelete(true); await flush();
        expect(mocks.remove).not.toHaveBeenCalled();
        expect(account.state.acct.user).toEqual(user);
        expect(account.state.acct.error).toContain("could not be verified");
    });

    it("preserves the account after a cancelled security check and hides raw errors", async () => {
        mocks.remove.mockRejectedValue({ errors: [{ code: "session_reverification_required" }] });
        const account = page();
        account._setAccountSecurityRunner(async (action: () => Promise<unknown>) => { try { return await action(); } catch { throw { code: "reverification_cancelled", message: "private response" }; } });
        account._acctDelete(true); await flush();
        expect(mocks.remove).toHaveBeenCalledTimes(1);
        expect(account.state.acct).toMatchObject({ user, busy: false, confirmingDelete: false });
        expect(account.state.acct.error).toContain("Verification was cancelled");
        expect(account.state.acct.error).not.toContain("private response");
        expect(mocks.success).not.toHaveBeenCalled();
    });

    it("retries only the original account action after completed verification", async () => {
        mocks.remove.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ ok: true, cleanupPending: false });
        const account = page();
        account._setAccountSecurityRunner(async (action: () => Promise<unknown>) => { try { return await action(); } catch { return action(); } });
        account._acctDelete(true); await flush();
        expect(mocks.remove).toHaveBeenCalledTimes(2);
        expect(mocks.remove).toHaveBeenNthCalledWith(2, user.id);
        expect(account.state.acct.user).toBeNull();
    });

    it.each(["account change", "unmount"])("does not resume deletion after %s during verification", async reason => {
        mocks.remove.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ ok: true });
        let verify!: () => void;
        const gate = new Promise<void>(resolve => { verify = resolve; });
        const account = page();
        account._setAccountSecurityRunner(async (action: () => Promise<unknown>) => { try { return await action(); } catch { await gate; return action(); } });
        account._acctDelete(true); await flush();
        if (reason === "unmount") account._accountUnmounted = true;
        else account._setAcct({ user: { ...user, id: "another-account" }, busy: false });
        verify(); await flush();
        expect(mocks.remove).toHaveBeenCalledTimes(1);
        expect(mocks.success).not.toHaveBeenCalled();
        if (reason === "account change") expect(account.state.acct.user.id).toBe("another-account");
    });

    it("warns about unconfirmed cleanup after SDK sign-out without retrying identity deletion", async () => {
        const account = page();
        mocks.remove.mockImplementation(async () => { account._setAcct({ user: null, freshKey: "", keys: [] }); return { ok: true, cleanupPending: true }; });
        account._acctDelete(true); await flush();
        expect(account.state.acct).toMatchObject({ user: null, resolved: true, busy: false });
        expect(mocks.warning).toHaveBeenCalledWith(expect.stringContaining("API data cleanup could not be confirmed"), { duration: 15_000 });
        account._acctDelete(true); await flush();
        expect(mocks.remove).toHaveBeenCalledTimes(1);
        expect(mocks.success).not.toHaveBeenCalled();
    });
});
