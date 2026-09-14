/**
 * `accountApi`, backed by Clerk.
 *
 * Same shape as the local-auth version in skins/accountLogic.ts, so the four
 * skins and AccountPage keep working without knowing which one they got. That
 * matters more than usual here: three of those skins are generated from design
 * sources and are extended by subclassing, so a change to the call shape is a
 * change to four UIs and a generator.
 *
 * Two places the shapes genuinely cannot match, and are handled rather than
 * papered over:
 *
 * - There is no recovery code. Clerk's way back in is an email, which is the
 *   whole reason for moving. `register` returns `recovery_code: ""`, and every
 *   caller already renders the recovery panel only when that string is
 *   non-empty, so the panel simply does not appear.
 *
 * - Signing up may not finish in one step. Clerk can require an emailed code,
 *   which local auth never did. `register` reports that as
 *   `status: "needs_email_code"` instead of pretending to be done, and the
 *   caller finishes with `verifyEmailCode`.
 */

import type { AccountUser, ApiKey } from "@/skins/accountLogic";
import type { ApiActivityData } from "@/lib/api-activity";
import { apiUrl } from "@/lib/api";
import { clerkToken, requireClerk, requireClerkClient } from "./instance";

/** Query flag we add to the OAuth return URL; see signInWithSocial. */
export const SSO_RETURN = "__pt_sso";

/** Clerk errors carry the useful text in `errors[0]`, not in `message`. */
function readable(err: unknown): Error {
    const e = err as { errors?: Array<{ longMessage?: string; message?: string }>; message?: string };
    const first = e?.errors?.[0];
    const msg = first?.longMessage || first?.message || e?.message || "Something went wrong.";
    // clerk-js failing to arrive is almost always an ad blocker eating the
    // script (or, once, a certificate mid-issue). Its own message names
    // internals; say something a visitor can act on instead.
    if (/failed to load/i.test(msg) && /clerk|script/i.test(msg)) {
        return new Error(
            "The sign-in service couldn\u2019t load. If you use an ad blocker or "
            + "privacy extension, allow clerk.privatools.me and reload the page.",
        );
    }
    return new Error(msg);
}

function toAccountUser(user: {
    id: string;
    primaryEmailAddress?: { emailAddress?: string } | null;
    createdAt?: Date | null;
    username?: string | null;
    passwordEnabled?: boolean;
}): AccountUser {
    return {
        id: user.id,
        username: user.username ?? undefined,
        password_enabled: user.passwordEnabled,
        email: user.primaryEmailAddress?.emailAddress ?? "",
        created_at: (user.createdAt ?? new Date()).toISOString(),
    };
}

/**
 * A call to our own API, carrying the Clerk session token.
 *
 * The cookie the local flow relied on does not exist here, so the token is the
 * only thing identifying the caller. A missing token is reported as a plain
 * "not signed in" rather than being sent as an anonymous request that comes
 * back 401 from the far end.
 */
async function callWithToken<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await clerkToken();
    if (!token) throw new Error("Not signed in.");

    const res = await fetch(apiUrl(path), {
        ...init,
        credentials: "omit",
        cache: "no-store",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            ...(init?.headers ?? {}),
        },
    });
    let body: unknown = null;
    try {
        body = await res.json();
    } catch {
        /* empty or non-JSON */
    }
    if (!res.ok) {
        const detail = (body as { detail?: string } | null)?.detail;
        throw new Error(detail || `Request failed (${res.status})`);
    }
    return body as T;
}

/** The social providers this deployment offers, in the order they are shown. */
export type SocialProvider = "google" | "github" | "apple";

export const SOCIAL_PROVIDERS: ReadonlyArray<{ id: SocialProvider; label: string }> = [
    { id: "google", label: "Google" },
    { id: "github", label: "GitHub" },
    { id: "apple", label: "Apple" },
];

export type RegisterResult =
    | { status: "complete"; user: AccountUser; recovery_code: string }
    | { status: "needs_email_code"; user: null; recovery_code: string };

export type SignInResult =
    | { user: AccountUser; status?: "complete" }
    | { user: null; status: "needs_sign_in_code"; verification: "email_code" | "totp"; destination: string };

export type PasswordResetResult = { ok: true } & SignInResult;

type SignInAttempt = Awaited<ReturnType<ReturnType<typeof requireClerkClient>["client"]["signIn"]["create"]>>;

async function finishSignIn(attempt: SignInAttempt): Promise<SignInResult> {
    const clerk = requireClerkClient();
    if (attempt.status === "complete" && attempt.createdSessionId) {
        await clerk.setActive({ session: attempt.createdSessionId });
        if (!clerk.user) throw new Error("Your session is ready. Reload this page to finish signing in.");
        return { user: toAccountUser(clerk.user) };
    }
    if (attempt.status === "needs_second_factor" || attempt.status === "needs_client_trust") {
        const email = attempt.supportedSecondFactors?.find(f => f.strategy === "email_code");
        if (email?.strategy === "email_code") {
            await attempt.prepareSecondFactor({ strategy: "email_code", emailAddressId: email.emailAddressId });
            return { user: null, status: "needs_sign_in_code", verification: "email_code", destination: email.safeIdentifier };
        }
        if (attempt.supportedSecondFactors?.some(f => f.strategy === "totp")) {
            return { user: null, status: "needs_sign_in_code", verification: "totp", destination: "your authenticator app" };
        }
    }
    if (attempt.status === "needs_new_password") throw new Error("Your password needs updating. Choose Forgot your password to reset it by email.");
    throw new Error("This sign-in needs another verification method. Try Google or use the account’s email recovery.");
}

function remainingSignUpRequirements(attempt: { missingFields?: string[] }): void {
    const missing = attempt.missingFields ?? [];
    if (!missing.length) return;
    if (missing.length === 1 && missing[0] === "username") {
        throw new Error("Add a username, then create your account again.");
    }
    throw new Error(`Sign-up still needs ${missing.map(field => field.replace(/_/g, " ")).join(", ")}. Complete those details before verifying your email.`);
}

async function activateSignUp(attempt: { createdSessionId: string | null }): Promise<AccountUser> {
    const clerk = requireClerkClient();
    if (!attempt.createdSessionId) throw new Error("Sign-up did not create a session. Start again to finish your account.");
    await clerk.setActive({ session: attempt.createdSessionId });
    if (!clerk.user) throw new Error("Your session is ready. Reload this page to finish signing in.");
    return toAccountUser(clerk.user);
}

export function passkeysSupported(): boolean {
    return typeof window !== "undefined" && window.isSecureContext && typeof window.PublicKeyCredential !== "undefined" && Boolean(navigator.credentials);
}

export function readablePasskeyError(err: unknown): Error {
    const e = err as { name?: string; errors?: Array<{ code?: string }> };
    if (e?.name === "NotAllowedError" || e?.name === "AbortError" || e?.errors?.some(x => /passkey.*(cancel|not_found)|passkey_not_allowed/.test(x.code ?? ""))) {
        return new Error("The passkey request was cancelled or no matching passkey was found. Try again, or use Google or your password.");
    }
    return readable(err);
}

export const clerkAccountApi = {
    me: async (): Promise<{ user: AccountUser }> => {
        const clerk = requireClerkClient();
        if (!clerk.user) throw new Error("Not signed in.");
        return { user: toAccountUser(clerk.user) };
    },

    register: async (email: string, password: string, username?: string): Promise<RegisterResult> => {
        const clerk = requireClerkClient();
        try {
            const attempt = await clerk.client.signUp.create({
                emailAddress: email.trim(),
                password,
                ...(username?.trim() ? { username: username.trim() } : {}),
            });
            if (attempt.status === "complete") {
                return {
                    status: "complete",
                    user: await activateSignUp(attempt),
                    recovery_code: "",
                };
            }
            remainingSignUpRequirements(attempt);
            if (attempt.status !== "missing_requirements" || (attempt.unverifiedFields && !attempt.unverifiedFields.includes("email_address"))) {
                throw new Error("Sign-up could not be completed with email verification. Start again to review your details.");
            }
            await attempt.prepareEmailAddressVerification({ strategy: "email_code" });
            return { status: "needs_email_code", user: null, recovery_code: "" };
        } catch (err) {
            throw readable(err);
        }
    },

    /** Second half of `register` when Clerk asked for an emailed code. */
    verifyEmailCode: async (code: string): Promise<{ user: AccountUser }> => {
        const clerk = requireClerkClient();
        try {
            const attempt = await clerk.client.signUp.attemptEmailAddressVerification({ code: code.trim() });
            if (attempt.status !== "complete") {
                remainingSignUpRequirements(attempt);
                throw new Error("Email verification did not complete sign-up. Start again to review your account details.");
            }
            return { user: await activateSignUp(attempt) };
        } catch (err) {
            throw readable(err);
        }
    },

    login: async (identifier: string, password: string): Promise<SignInResult> => {
        try {
            return await finishSignIn(await requireClerkClient().client.signIn.create({ identifier: identifier.trim(), password }));
        } catch (err) { throw readable(err); }
    },

    loginWithPasskey: async (): Promise<SignInResult> => {
        if (!passkeysSupported()) throw new Error("This browser cannot use passkeys. Continue with Google or your email and password.");
        try {
            const attempt = await requireClerkClient().client.signIn.authenticateWithPasskey({ flow: "discoverable" });
            return await finishSignIn(attempt);
        } catch (err) { throw readablePasskeyError(err); }
    },

    verifySignIn: async (code: string): Promise<SignInResult> => {
        const signIn = requireClerkClient().client.signIn;
        try {
            const strategy = signIn.supportedSecondFactors?.some(f => f.strategy === "email_code") ? "email_code" : "totp";
            return await finishSignIn(await signIn.attemptSecondFactor({ strategy, code: code.trim() }));
        } catch (err) { throw readable(err); }
    },

    resendSignInCode: async (): Promise<void> => {
        const signIn = requireClerkClient().client.signIn;
        const factor = signIn.supportedSecondFactors?.find(f => f.strategy === "email_code");
        if (!factor || factor.strategy !== "email_code") throw new Error("Use the current code from your authenticator app.");
        try { await signIn.prepareSecondFactor({ strategy: "email_code", emailAddressId: factor.emailAddressId }); }
        catch (err) { throw readable(err); }
    },

    resendSignUpCode: async (): Promise<void> => {
        try { await requireClerkClient().client.signUp.prepareEmailAddressVerification({ strategy: "email_code" }); }
        catch (err) { throw readable(err); }
    },

    /**
     * Hand off to a social provider.
     *
     * This is the door most people will actually use, and the reason moving to
     * Clerk was worth it: it removes the password entirely, and with it the
     * scrypt hashing, the per-account lockout, and the recovery code that was
     * previously the only way back into an account.
     *
     * `authenticateWithRedirect` leaves the page, so nothing after it runs on
     * success. The redirect comes back to /account, where Clerk completes the
     * handshake from the URL before the app renders.
     */
    signInWithSocial: async (provider: SocialProvider): Promise<void> => {
        const clerk = requireClerkClient();
        try {
            await clerk.client.signIn.authenticateWithRedirect({
                strategy: `oauth_${provider}` as `oauth_${SocialProvider}`,
                // The marker is what tells the landing page to finish the
                // handshake. Inferring it from signIn.status does not work:
                // a freshly loaded page already reports "needs_identifier",
                // so any truthiness check fires on every visit.
                redirectUrl: `${window.location.origin}/account?${SSO_RETURN}=1`,
                redirectUrlComplete: `${window.location.origin}/account`,
            });
        } catch (err) {
            throw readable(err);
        }
    },

    /**
     * Finish an OAuth round trip.
     *
     * `authenticateWithRedirect` sends the visitor to GitHub and GitHub back to
     * us; the handshake is only completed by calling this on the page they land
     * on. Nothing did, so signing in with GitHub always ended silently back at
     * a signed-out form.
     *
     * The fallback URLs are what turn a first-time GitHub user into a sign-up:
     * the attempt starts as a sign-in, finds no account, and Clerk transfers it
     * only if it has somewhere to send the result.
     */
    completeSocialRedirect: async (): Promise<void> => {
        const clerk = requireClerkClient();
        const here = `${window.location.origin}/account`;
        try {
            await clerk.handleRedirectCallback({
                signInFallbackRedirectUrl: here,
                signUpFallbackRedirectUrl: here,
                continueSignUpUrl: here,
            });
        } catch (err) {
            // The flow can already be finished by the time this runs — Clerk
            // answers a second callback with "identifier_already_signed_in"
            // and then sends the browser to its hosted Account Portal, which
            // to the visitor looks exactly like sign-in failing and dumping
            // them on a stranger's page. Their session is fine; say nothing.
            const e = err as { errors?: Array<{ code?: string }> };
            if (e?.errors?.some((x) => x.code === "identifier_already_signed_in")) return;
            throw readable(err);
        }
    },

    logout: async (): Promise<{ ok: true }> => {
        await requireClerk().signOut();
        return { ok: true };
    },

    changePassword: async (
        currentPassword: string,
        newPassword: string,
    ): Promise<{ ok: true }> => {
        const clerk = requireClerk();
        if (!clerk.user) throw new Error("Not signed in.");
        try {
            await clerk.user.updatePassword({
                currentPassword,
                newPassword,
                // Match native auth: retain this session and end the others.
                signOutOfOtherSessions: true,
            });
            return { ok: true };
        } catch (err) {
            throw readable(err);
        }
    },

    deleteAccount: async (): Promise<{ ok: true }> => {
        const clerk = requireClerk();
        if (!clerk.user) throw new Error("Not signed in.");
        try {
            // Remove local API access while a valid Clerk session still exists.
            // The webhook covers deletion initiated outside this application.
            await callWithToken<{ ok: true }>("/auth/me", { method: "DELETE" });
            await clerk.user.delete();
            return { ok: true };
        } catch (err) {
            throw readable(err);
        }
    },

    /**
     * Start a password reset. Clerk emails a code.
     *
     * The local flow took a recovery code the user already held; this one has
     * to send something first, so it is two calls rather than one.
     */
    startPasswordReset: async (email: string): Promise<{ ok: true }> => {
        const clerk = requireClerkClient();
        try {
            await clerk.client.signIn.create({
                strategy: "reset_password_email_code",
                identifier: email.trim(),
            });
            return { ok: true };
        } catch (err) {
            throw readable(err);
        }
    },

    finishPasswordReset: async (
        code: string,
        newPassword: string,
    ): Promise<PasswordResetResult> => {
        const clerk = requireClerkClient();
        try {
            const attempt = await clerk.client.signIn.attemptFirstFactor({
                strategy: "reset_password_email_code",
                code: code.trim(),
                password: newPassword,
            });
            // Resetting the password can still require device trust or MFA.
            // Preserve that live attempt instead of resending a spent reset code.
            return { ok: true, ...await finishSignIn(attempt) };
        } catch (err) {
            throw readable(err);
        }
    },

    // --- API keys stay ours -------------------------------------------------
    // Clerk holds the identity; the keys, their labels and their quota live in
    // our own database and are unchanged. Only the credential differs: a bearer
    // token instead of the session cookie.
    listKeys: () => callWithToken<{ keys: ApiKey[] }>("/keys"),
    apiActivity: (keyId?: string, signal?: AbortSignal) => callWithToken<ApiActivityData>(`/account/api-activity${keyId ? `?key_id=${encodeURIComponent(keyId)}` : ""}`, { signal }),
    createKey: (label: string) =>
        callWithToken<{ key: string; record: ApiKey }>("/keys", {
            method: "POST",
            body: JSON.stringify({ label }),
        }),
    revokeKey: (keyId: string) =>
        callWithToken<{ ok: true }>(`/keys/${encodeURIComponent(keyId)}`, {
            method: "DELETE",
        }),
};
