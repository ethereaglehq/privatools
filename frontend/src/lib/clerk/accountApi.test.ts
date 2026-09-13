import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clerkAccountApi } from "./accountApi";

const fixture = vi.hoisted(() => ({ clerk: {} as any, token: vi.fn() }));
vi.mock("./instance", () => ({ requireClerk: () => fixture.clerk, requireClerkClient: () => fixture.clerk, clerkToken: fixture.token }));
vi.mock("@/lib/api", () => ({ apiUrl: (path: string) => `https://api.privatools.example/api${path}` }));
beforeEach(() => {
  fixture.token.mockReset();
  fixture.clerk = { user: { id: "synthetic", primaryEmailAddress: { emailAddress: "synthetic@example.test" }, createdAt: new Date("2026-09-13"), updatePassword: vi.fn().mockResolvedValue({}) }, setActive: vi.fn().mockResolvedValue(undefined), client: { signIn: {}, signUp: {} } };
});
afterEach(() => vi.unstubAllGlobals());

describe("Clerk account contracts", () => {
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
  it("cleans local API access before deleting the Clerk identity", async () => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    const calls: string[] = [];
    const fetch = vi.fn().mockImplementation(async () => { calls.push("local"); return { ok: true, json: async () => ({ ok: true }) }; });
    vi.stubGlobal("fetch", fetch);
    fixture.clerk.user.delete = vi.fn().mockImplementation(async () => { calls.push("identity"); });
    await clerkAccountApi.deleteAccount();
    expect(calls).toEqual(["local", "identity"]);
    expect(fetch).toHaveBeenCalledWith("https://api.privatools.example/api/auth/me", expect.objectContaining({ method: "DELETE" }));
  });
  it("retains the identity if local key cleanup could not finish", async () => {
    fixture.token.mockResolvedValue("synthetic-session-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: "Unavailable" }) }));
    fixture.clerk.user.delete = vi.fn();
    await expect(clerkAccountApi.deleteAccount()).rejects.toThrow("Unavailable");
    expect(fixture.clerk.user.delete).not.toHaveBeenCalled();
  });
});
