import { beforeEach, describe, expect, it, vi } from "vitest";
import { withAccounts } from "./withAccounts";

const api = vi.hoisted(() => ({ login: vi.fn(), loginWithPasskey: vi.fn(), startPasswordReset: vi.fn(), finishPasswordReset: vi.fn(), verifySignIn: vi.fn(), verifyEmailCode: vi.fn(), register: vi.fn(), listKeys: vi.fn(), me: vi.fn() }));
vi.mock("./accountLogic", async original => ({ ...await original<object>(), EMAIL_RESET: true, accountApi: api }));
class Base {
  state: Record<string, any> = {};
  setState(update: any) { Object.assign(this.state, typeof update === "function" ? update(this.state) : update); }
  renderVals() { return {}; }
}
const user = { id: "synthetic", email: "person@example.test", created_at: "2026-09-13" };
const flush = () => new Promise(resolve => setTimeout(resolve, 0));
function page() { const Account = withAccounts(Base, { palette: {}, navItem: () => ({}), navKey: "nav" }); return new Account({}); }
beforeEach(() => { history.replaceState(null, "", "/account/sign-in"); sessionStorage.clear(); localStorage.clear(); Object.values(api).forEach(mock => mock.mockReset()); api.listKeys.mockResolvedValue({ keys: [] }); });

describe("Clerk verification lifecycle", () => {
  it("renders a live signed-in profile before its key request completes", async () => {
    const account = page(); account._isAccountActive = () => true;
    api.me.mockResolvedValue({ user }); api.listKeys.mockReturnValue(new Promise(() => {}));
    await account._syncClerkAccount({ loaded: true, user: { id: user.id } });
    expect(account.state.acct).toMatchObject({ user, busy: false, keysLoading: true, accountHint: true });
    expect(localStorage.getItem("privatools.account-present")).toBe("1");
    expect(localStorage.getItem("privatools.account-present")).not.toContain(user.email);
    account._loadKeys(user.id);
    expect(api.listKeys).toHaveBeenCalledOnce();
  });
  it("does not rerender or refetch keys for unchanged Clerk token-refresh events", async () => {
    const account = page(); account._isAccountActive = () => true; api.me.mockResolvedValue({ user });
    const clerk = { loaded: true, user: { id: user.id } };
    await account._syncClerkAccount(clerk); await flush();
    await account._syncClerkAccount(clerk);
    expect(api.me).toHaveBeenCalledOnce(); expect(api.listKeys).toHaveBeenCalledOnce();
  });
  it("updates navigation away from account pages without eagerly loading API keys", async () => {
    const account = page(); account._isAccountActive = () => false; api.me.mockResolvedValue({ user });
    await account._syncClerkAccount({ loaded: true, user: { id: user.id } });
    expect(account.state.acct.user).toEqual(user); expect(api.listKeys).not.toHaveBeenCalled();
  });
  it("clears identity and presentation hints on a verified external sign-out", async () => {
    localStorage.setItem("privatools.account-present", "1");
    const account = page(); account._setAcct({ user, freshKey: "synthetic-key" });
    await account._syncClerkAccount({ loaded: true, user: null, session: null });
    expect(account.state.acct).toMatchObject({ user: null, freshKey: "", accountHint: false });
    expect(localStorage.getItem("privatools.account-present")).toBeNull();
  });
  it("never treats a navigation hint as an authenticated user", () => {
    localStorage.setItem("privatools.account-present", "1");
    const account = page(); const values = account.renderVals();
    expect(values.acctNavigationSignedIn).toBe(true); expect(values.acctSignedIn).toBe(false); expect(account.state.acct.user).toBeNull();
  });
  it("does not carry a failed sign-in password into the new-password form", () => {
    const account = page(); account._setAcct({ password: "failed old password", recoveryInput: "old-code", resetEmailSent: true });
    account.renderVals().acctShowRecover();
    expect(account.state.acct).toMatchObject({ mode: "recover", password: "", recoveryInput: "", resetEmailSent: false });
  });
  it("carries reset MFA into the verification form, then signs in only after it completes", async () => {
    api.finishPasswordReset.mockResolvedValue({ ok: true, user: null, status: "needs_sign_in_code", verification: "totp", destination: "your authenticator app" });
    const account = page(); account._setAcct({ mode: "recover", email: user.email, password: "new synthetic password", recoveryInput: "123456", resetEmailSent: true });
    account._acctRecover(null); await flush();
    expect(account.state.acct).toMatchObject({ user: null, mode: "signin", resetEmailSent: false, password: "", recoveryInput: "", signInVerification: "totp", verificationDestination: "your authenticator app", error: "" });
    expect(api.listKeys).not.toHaveBeenCalled();
    api.verifySignIn.mockResolvedValue({ user });
    account._setAcct({ emailCode: "654321" }); account._acctVerifySignIn(null); await flush();
    expect(account.state.acct).toMatchObject({ user, signInVerification: "", emailCode: "", error: "" });
    expect(api.listKeys).toHaveBeenCalledOnce();
  });

  it("uses the completed reset session rather than a separate potentially stale me request", async () => {
    api.finishPasswordReset.mockResolvedValue({ ok: true, user });
    const account = page(); account._setAcct({ mode: "recover", resetEmailSent: true, password: "new synthetic password", recoveryInput: "123456" });
    account._acctRecover(null); await flush();
    expect(account.state.acct).toMatchObject({ user, password: "", recoveryInput: "", resetEmailSent: false });
  });

  it("does not start two reset emails while one is pending", () => {
    api.startPasswordReset.mockReturnValue(new Promise(() => {}));
    const account = page(); account._setAcct({ mode: "recover", email: user.email });
    account._acctRecover(null); account._acctRecover(null);
    expect(api.startPasswordReset).toHaveBeenCalledOnce();
  });

  it("clears the accepted signup password before requesting the email code", async () => {
    api.register.mockResolvedValue({ status: "needs_email_code", user: null, recovery_code: "" });
    const account = page(); account._setAcct({ mode: "signup", email: user.email, password: "synthetic signup password" });
    account._acctSubmit(null); await flush();
    expect(account.state.acct).toMatchObject({ needsEmailCode: true, password: "", user: null });
    expect(api.listKeys).not.toHaveBeenCalled();
  });

  it("does not resubmit signup verification while its request is pending", () => {
    api.verifyEmailCode.mockReturnValue(new Promise(() => {}));
    const account = page(); account._setAcct({ needsEmailCode: true, emailCode: "123456" });
    account._acctVerifyEmail(null); account._acctVerifyEmail(null);
    expect(api.verifyEmailCode).toHaveBeenCalledOnce();
  });
});


describe("verified account return navigation", () => {
  it.each(["password", "passkey", "email verification"])("returns to settings after %s sign-in", async method => {
    history.replaceState(null, "", "/account/sign-in?next=/account/settings");
    const account = page();
    if (method === "password") { api.login.mockResolvedValue({ user }); account._acctSubmit(null); }
    else if (method === "passkey") { api.loginWithPasskey.mockResolvedValue({ user }); account._acctPasskey(); }
    else { api.verifySignIn.mockResolvedValue({ user }); account._setAcct({ emailCode: "123456", signInVerification: "email_code" }); account._acctVerifySignIn(null); }
    await flush();
    expect(location.pathname).toBe("/account/settings");
    expect(account.state.acct.user).toEqual(user);
  });
  it("retains the destination through an incomplete new-device verification", async () => {
    history.replaceState(null, "", "/account/sign-in?next=/account/keys");
    const account = page(); api.login.mockResolvedValue({ user: null, status: "needs_sign_in_code", verification: "email_code", destination: "your email" });
    account._acctSubmit(null); await flush();
    expect(location.pathname).toBe("/account/sign-in");
    api.verifySignIn.mockResolvedValue({ user }); account._setAcct({ emailCode: "123456" }); account._acctVerifySignIn(null); await flush();
    expect(location.pathname).toBe("/account/keys");
  });
  it("returns after a verified OAuth session without trusting the URL alone", async () => {
    history.replaceState(null, "", "/account/sign-in?next=/account/settings"); page();
    history.replaceState(null, "", "/account?sso_return=1");
    const account = page(); await account._syncClerkAccount({ loaded: true, user: null, session: null });
    expect(location.pathname).toBe("/account"); expect(account.state.acct.resolved).toBe(true);
    api.me.mockResolvedValue({ user }); await account._syncClerkAccount({ loaded: true, user: { id: user.id } });
    expect(location.pathname).toBe("/account/settings");
  });
  it("does not leave a native signup recovery code before acknowledgment", async () => {
    history.replaceState(null, "", "/account/sign-up?next=/account/settings");
    const account = page(); account._setAcct({ mode: "signup" });
    api.register.mockResolvedValue({ user, recovery_code: "synthetic-recovery" }); account._acctSubmit(null); await flush();
    expect(location.pathname).toBe("/account/sign-up");
    account._acctAckRecovery(); expect(location.pathname).toBe("/account/settings");
  });
});
