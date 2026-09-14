import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clerkAccountApi } from "./accountApi";

const fixture = vi.hoisted(() => ({ clerk: {} as any, token: vi.fn() }));
vi.mock("./instance", () => ({ requireClerk: () => fixture.clerk, requireClerkClient: () => fixture.clerk, clerkToken: fixture.token }));
vi.mock("@/lib/api", () => ({ apiUrl: (path: string) => `https://api.privatools.example/api${path}` }));
beforeEach(() => {
  fixture.token.mockReset();
  fixture.clerk = { user: { id: "synthetic", primaryEmailAddress: { emailAddress: "synthetic@example.test" }, createdAt: new Date("2026-09-13"), updatePassword: vi.fn().mockResolvedValue({}) }, session: { getToken: fixture.token }, setActive: vi.fn().mockResolvedValue(undefined), client: { signIn: {}, signUp: {} } };
});
afterEach(() => vi.unstubAllGlobals());

describe("Clerk account contracts", () => {
  it("loads filtered API activity with the account session and supports cancellation", async () => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ keys: [], recent: [] }) }); vi.stubGlobal("fetch", fetch);
    const controller = new AbortController();
    await clerkAccountApi.apiActivity("key/one", controller.signal);
    expect(fetch).toHaveBeenCalledWith("https://api.privatools.example/api/account/api-activity?key_id=key%2Fone", expect.objectContaining({ signal: controller.signal, credentials: "omit", cache: "no-store", headers: expect.objectContaining({ Authorization: "Bearer synthetic-session-token" }) }));
  });

  it("uses the configured API origin and a fresh bearer token without cookies", async () => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ keys: [] }) }); vi.stubGlobal("fetch", fetch);
    await clerkAccountApi.listKeys();
    expect(fetch).toHaveBeenCalledWith("https://api.privatools.example/api/keys", expect.objectContaining({ credentials: "omit", cache: "no-store", headers: expect.objectContaining({ Authorization: "Bearer synthetic-session-token" }) }));
  });

  it("does not send an anonymous key request when no session token is available", async () => {
    fixture.token.mockResolvedValue(null); const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    await expect(clerkAccountApi.listKeys()).rejects.toThrow("Not signed in");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("reports the email-verification step without claiming sign-up completed", async () => {
    const prepare = vi.fn().mockResolvedValue({});
    fixture.clerk.client.signUp.create = vi.fn().mockResolvedValue({ status: "missing_requirements", prepareEmailAddressVerification: prepare });
    expect(await clerkAccountApi.register("synthetic@example.test", "synthetic-passphrase")).toEqual({ status: "needs_email_code", user: null, recovery_code: "" });
    expect(prepare).toHaveBeenCalledWith({ strategy: "email_code" });
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("activates a session only after the reset code completes verification", async () => {
    fixture.clerk.client.signIn.attemptFirstFactor = vi.fn().mockResolvedValue({ status: "complete", createdSessionId: "synthetic-session" });
    await clerkAccountApi.finishPasswordReset("123456", "synthetic-passphrase");
    expect(fixture.clerk.client.signIn.attemptFirstFactor).toHaveBeenCalledWith({ strategy: "reset_password_email_code", code: "123456", password: "synthetic-passphrase" });
    expect(fixture.clerk.setActive).toHaveBeenCalledWith({ session: "synthetic-session" });
  });

  it("ends other sessions on a password change, matching native auth", async () => {
    await clerkAccountApi.changePassword("synthetic-old", "synthetic-new");
    expect(fixture.clerk.user.updatePassword).toHaveBeenCalledWith({ currentPassword: "synthetic-old", newPassword: "synthetic-new", signOutOfOtherSessions: true });
  });

  it("omits currentPassword only when the SDK confirms the account has none", async () => {
    fixture.clerk.user.passwordEnabled = false;
    await clerkAccountApi.changePassword("ignored-form-value", "synthetic-new", "synthetic");
    expect(fixture.clerk.user.updatePassword).toHaveBeenCalledExactlyOnceWith({ newPassword: "synthetic-new", signOutOfOtherSessions: true });
  });

  it.each([true, undefined])("requires the existing password when SDK passwordEnabled is %s", async passwordEnabled => {
    fixture.clerk.user.passwordEnabled = passwordEnabled;
    await expect(clerkAccountApi.changePassword("", "synthetic-new", "synthetic")).rejects.toThrow("Enter your current password");
    expect(fixture.clerk.user.updatePassword).not.toHaveBeenCalled();
  });

  it("rejects credentials addressed to a different signed-in account", async () => {
    await expect(clerkAccountApi.changePassword("synthetic-old", "synthetic-new", "previous-account")).rejects.toThrow("Your sign-in has changed");
    expect(fixture.clerk.user.updatePassword).not.toHaveBeenCalled();
  });

  it("preserves Clerk’s structured security challenge for the verification hook", async () => {
    const challenge = { errors: [{ code: "session_reverification_required", message: "Verify first" }] };
    fixture.clerk.user.updatePassword.mockRejectedValue(challenge);
    await expect(clerkAccountApi.changePassword("synthetic-old", "synthetic-new", "synthetic")).rejects.toBe(challenge);
  });

  it("does not claim completion for an SDK account that changed during the update", async () => {
    fixture.clerk.user.updatePassword.mockImplementation(async () => { fixture.clerk.user.id = "another-account"; });
    await expect(clerkAccountApi.changePassword("synthetic-old", "synthetic-new", "synthetic")).rejects.toThrow("Your sign-in has changed");
  });
});


describe("username, passkeys and new-device verification", () => {
  it("recognizes Clerk device trust as an email verification step", async () => {
    const prepare = vi.fn().mockResolvedValue({});
    fixture.clerk.client.signIn.create = vi.fn().mockResolvedValue({ status: "needs_client_trust", supportedSecondFactors: [{ strategy: "email_code", emailAddressId: "email_1", safeIdentifier: "p***@example.test" }], prepareSecondFactor: prepare });
    expect(await clerkAccountApi.login("person_4", "four unrelated words")).toMatchObject({ status: "needs_sign_in_code", verification: "email_code" });
    expect(prepare).toHaveBeenCalledWith({ strategy: "email_code", emailAddressId: "email_1" });
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("continues a password reset into MFA without resending the reset code", async () => {
    fixture.clerk.client.signIn.attemptFirstFactor = vi.fn().mockResolvedValue({ status: "needs_second_factor", supportedSecondFactors: [{ strategy: "totp" }] });
    const result = await clerkAccountApi.finishPasswordReset(" 123456 ", "new password with spaces");
    expect(result).toMatchObject({ ok: true, user: null, status: "needs_sign_in_code", verification: "totp" });
    expect(fixture.clerk.client.signIn.attemptFirstFactor).toHaveBeenCalledWith({ strategy: "reset_password_email_code", code: "123456", password: "new password with spaces" });
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("does not send an email code while required signup fields are missing", async () => {
    const prepare = vi.fn();
    fixture.clerk.client.signUp.create = vi.fn().mockResolvedValue({ status: "missing_requirements", missingFields: ["username"], unverifiedFields: ["email_address"], prepareEmailAddressVerification: prepare });
    await expect(clerkAccountApi.register("person@example.test", "four unrelated words")).rejects.toThrow("Add a username");
    expect(prepare).not.toHaveBeenCalled();
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("reports remaining signup requirements after a verified email instead of blaming its code", async () => {
    fixture.clerk.client.signUp.attemptEmailAddressVerification = vi.fn().mockResolvedValue({ status: "missing_requirements", missingFields: ["username"], unverifiedFields: [] });
    await expect(clerkAccountApi.verifyEmailCode("123456")).rejects.toThrow("Add a username");
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("does not activate a missing signup session", async () => {
    fixture.clerk.client.signUp.create = vi.fn().mockResolvedValue({ status: "complete", createdSessionId: null });
    await expect(clerkAccountApi.register("person@example.test", "four unrelated words")).rejects.toThrow("did not create a session");
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });
  it("sends the optional username at signup and accepts a username identifier at sign-in", async () => {
    fixture.clerk.client.signUp.create = vi.fn().mockResolvedValue({ status: "complete", createdSessionId: "signup-session" });
    fixture.clerk.client.signIn.create = vi.fn().mockResolvedValue({ status: "complete", createdSessionId: "signin-session" });
    await clerkAccountApi.register(" person@example.test ", "four unrelated words", "person_4");
    expect(fixture.clerk.client.signUp.create).toHaveBeenCalledWith({ emailAddress: "person@example.test", password: "four unrelated words", username: "person_4" });
    await clerkAccountApi.login(" person_4 ", "four unrelated words");
    expect(fixture.clerk.client.signIn.create).toHaveBeenCalledWith({ identifier: "person_4", password: "four unrelated words" });
  });

  it("prepares a new-device email check without activating an incomplete session", async () => {
    const prepare = vi.fn().mockResolvedValue({});
    fixture.clerk.client.signIn.create = vi.fn().mockResolvedValue({ status: "needs_second_factor", supportedSecondFactors: [{ strategy: "email_code", emailAddressId: "email_1", safeIdentifier: "p***@example.test" }], prepareSecondFactor: prepare });
    expect(await clerkAccountApi.login("person_4", "four unrelated words")).toEqual({ user: null, status: "needs_sign_in_code", verification: "email_code", destination: "p***@example.test" });
    expect(prepare).toHaveBeenCalledWith({ strategy: "email_code", emailAddressId: "email_1" });
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
    fixture.clerk.client.signIn.supportedSecondFactors = [{ strategy: "email_code" }];
    fixture.clerk.client.signIn.attemptSecondFactor = vi.fn().mockResolvedValue({ status: "complete", createdSessionId: "verified-session" });
    await clerkAccountApi.verifySignIn("123456");
    expect(fixture.clerk.setActive).toHaveBeenCalledWith({ session: "verified-session" });
  });

  it("supports an existing authenticator without relying on recovery codes", async () => {
    fixture.clerk.client.signIn.create = vi.fn().mockResolvedValue({ status: "needs_second_factor", supportedSecondFactors: [{ strategy: "totp" }] });
    expect(await clerkAccountApi.login("person_4", "four unrelated words")).toMatchObject({ user: null, verification: "totp" });
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("starts a discoverable passkey flow and activates only its completed session", async () => {
    vi.stubGlobal("isSecureContext", true); vi.stubGlobal("PublicKeyCredential", class {});
    Object.defineProperty(navigator, "credentials", { configurable: true, value: {} });
    fixture.clerk.client.signIn.authenticateWithPasskey = vi.fn().mockResolvedValue({ status: "complete", createdSessionId: "passkey-session" });
    await clerkAccountApi.loginWithPasskey();
    expect(fixture.clerk.client.signIn.authenticateWithPasskey).toHaveBeenCalledWith({ flow: "discoverable" });
    expect(fixture.clerk.setActive).toHaveBeenCalledWith({ session: "passkey-session" });
  });

  it("leaves the session untouched when a passkey prompt is cancelled", async () => {
    vi.stubGlobal("isSecureContext", true); vi.stubGlobal("PublicKeyCredential", class {});
    Object.defineProperty(navigator, "credentials", { configurable: true, value: {} });
    fixture.clerk.client.signIn.authenticateWithPasskey = vi.fn().mockRejectedValue(new DOMException("Cancelled", "NotAllowedError"));
    await expect(clerkAccountApi.loginWithPasskey()).rejects.toThrow("cancelled");
    expect(fixture.clerk.setActive).not.toHaveBeenCalled();
  });

  it("does not invoke WebAuthn in an unsupported browser", async () => {
    vi.stubGlobal("isSecureContext", false);
    fixture.clerk.client.signIn.authenticateWithPasskey = vi.fn();
    await expect(clerkAccountApi.loginWithPasskey()).rejects.toThrow("cannot use passkeys");
    expect(fixture.clerk.client.signIn.authenticateWithPasskey).not.toHaveBeenCalled();
  });
});


describe("Clerk account deletion", () => {
  it("deletes the verified identity before cleaning local API data with the captured token", async () => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const calls: string[] = [];
    const fetch = vi.fn().mockImplementation(async () => { calls.push("local"); return { ok: true }; });
    vi.stubGlobal("fetch", fetch);
    fixture.clerk.user.delete = vi.fn().mockImplementation(async () => { calls.push("identity"); fixture.clerk.user = null; fixture.clerk.session = null; });
    await expect(clerkAccountApi.deleteAccount("synthetic")).resolves.toEqual({ ok: true, cleanupPending: false });
    expect(calls).toEqual(["identity", "local"]);
    expect(fixture.token).toHaveBeenCalledExactlyOnceWith({ skipCache: true });
    expect(fetch).toHaveBeenCalledWith("https://api.privatools.example/api/auth/me", expect.objectContaining({ method: "DELETE", credentials: "omit", cache: "no-store", headers: { Authorization: "Bearer synthetic-session-token" } }));
  });

  it.each(["session_reverification_required", "reverification_cancelled", "identity_failure"])("does not delete local data after %s", async code => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    const failure = { errors: [{ code, message: "private response" }] };
    fixture.clerk.user.delete = vi.fn().mockRejectedValue(failure);
    await expect(clerkAccountApi.deleteAccount("synthetic")).rejects.toBe(failure);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("retries identity verification before one successful deletion and one local cleanup", async () => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const fetch = vi.fn().mockResolvedValue({ ok: true }); vi.stubGlobal("fetch", fetch);
    const deleted = vi.fn().mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ id: "synthetic", deleted: true });
    fixture.clerk.user.delete = deleted;
    await expect(clerkAccountApi.deleteAccount("synthetic")).rejects.toMatchObject({ errors: [{ code: "session_reverification_required" }] });
    expect(fetch).not.toHaveBeenCalled();
    await expect(clerkAccountApi.deleteAccount("synthetic")).resolves.toMatchObject({ ok: true, cleanupPending: false });
    expect(deleted).toHaveBeenCalledTimes(2);
    expect(fixture.token).toHaveBeenCalledTimes(2);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it.each(["http", "network"])("reports pending local cleanup after %s failure without deleting the identity again", async failure => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const fetch = failure === "http" ? vi.fn().mockResolvedValue({ ok: false, status: 503 }) : vi.fn().mockRejectedValue(new Error("private response"));
    vi.stubGlobal("fetch", fetch);
    const deleted = vi.fn().mockImplementation(async () => { fixture.clerk.user = null; }); fixture.clerk.user.delete = deleted;
    await expect(clerkAccountApi.deleteAccount("synthetic")).resolves.toEqual({ ok: true, cleanupPending: true });
    expect(deleted).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("does not touch either account if identity changes while capturing the token", async () => {
    const deleted = vi.fn(); fixture.clerk.user.delete = deleted;
    fixture.token.mockImplementation(async () => { fixture.clerk.user = { id: "other-account", delete: vi.fn() }; return "synthetic-session-token"; });
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    await expect(clerkAccountApi.deleteAccount("synthetic")).rejects.toThrow("Your sign-in has changed");
    expect(deleted).not.toHaveBeenCalled();
    expect(fixture.clerk.user.delete).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("does not begin destruction without a usable original-account token", async () => {
    fixture.token.mockResolvedValue(null);
    fixture.clerk.user.delete = vi.fn();
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    await expect(clerkAccountApi.deleteAccount("synthetic")).rejects.toThrow("Not signed in");
    expect(fixture.clerk.user.delete).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });
});
