import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ArrowUpRight, CheckCircle2, KeyRound, Loader2, Palette, Shield } from "lucide-react";
import { AccountSecurityError, securityErrorMessage } from "@/lib/clerk/securityActions";
import { runAccountAction, useAccountReverification, type AccountSecurityRunner } from "@/lib/clerk/useAccountReverification";
import { accountApi, MIN_PASSWORD_LENGTH, type AccountUser } from "@/skins/accountLogic";
import { isClerkEnabled, whenClerkReady } from "@/lib/clerk/instance";
import { StudioPage, StudioHeader } from "@/skins/experience/Studio";
import PasskeySettings from "@/components/account/PasskeySettings";
import UsernameSettings from "@/components/account/UsernameSettings";
import AccountWorkspaceHeader from "@/components/account/AccountWorkspaceHeader";
import "@/skins/experience/secondary-pages.css";

export interface AccountSettingsPageProps {
    /** Shared Air / Play and light / dark controls supplied by the application shell. */
    appearanceArea?: ReactNode;
    /** Pass the shell's account user to keep inline sign-in and this page in sync. */
    accountUser?: AccountUser | null;
    accountChecking?: boolean;
}

export default function AccountSettingsPage(props: AccountSettingsPageProps) {
    return isClerkEnabled() ? <HostedAccountSettings {...props} /> : <SettingsBody {...props} runSecurity={runAccountAction} />;
}

function HostedAccountSettings(props: AccountSettingsPageProps) {
    const runSecurity = useAccountReverification();
    return <SettingsBody {...props} runSecurity={runSecurity} />;
}

function SettingsBody({ appearanceArea, accountUser, accountChecking = false, runSecurity }: AccountSettingsPageProps & { runSecurity: AccountSecurityRunner }) {
    const [loadedUser, setUser] = useState<AccountUser | null>(accountUser ?? null);
    const user = accountUser === undefined ? loadedUser : accountUser;
    const [checking, setChecking] = useState(accountUser === undefined);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [createdFor, setCreatedFor] = useState("");
    const [identityChanged, setIdentityChanged] = useState(false);
    const activeRequest = useRef<object | null>(null);
    const currentAccount = useRef(user?.id);
    currentAccount.current = user?.id;
    const alive = useRef(false);
    const submitting = useRef(false);
    const form = useRef<HTMLFormElement>(null);
    const passwordless = isClerkEnabled() && user?.password_enabled === false && createdFor !== user.id;

    useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
    useEffect(() => { activeRequest.current = null; submitting.current = false; setBusy(false); form.current?.reset(); setError(""); setSuccess(""); setCreatedFor(""); setIdentityChanged(false); }, [user?.id]);
    useEffect(() => { if (user?.password_enabled) setCreatedFor(""); }, [user?.password_enabled]);
    useEffect(() => {
        if (accountUser !== undefined) { setUser(accountUser); setChecking(false); return; }
        let current = true;
        const load = async () => {
            try {
                if (isClerkEnabled()) await whenClerkReady();
                const result = await accountApi.me();
                if (current) setUser(result.user);
            } catch { if (current) setUser(null); }
            finally { if (current) setChecking(false); }
        };
        void load();
        window.addEventListener("focus", load);
        return () => { current = false; window.removeEventListener("focus", load); };
    }, [accountUser]);

    async function changePassword(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (submitting.current || !user || identityChanged) return;
        const values = new FormData(event.currentTarget);
        const currentPassword = String(values.get("current-password") ?? "");
        const nextPassword = String(values.get("new-password") ?? "");
        const confirmation = String(values.get("confirm-password") ?? "");
        setError(""); setSuccess("");
        if (nextPassword !== confirmation) { setError("The new passwords do not match. Check both fields."); return; }
        if (nextPassword.length < MIN_PASSWORD_LENGTH) { setError(`Use at least ${MIN_PASSWORD_LENGTH} characters for your new password.`); return; }
        if (!passwordless && !currentPassword) { setError("Enter your current password before choosing a new one."); return; }
        if (!passwordless && nextPassword === currentPassword) { setError("Choose a different password from your current one."); return; }
        const accountId = user.id;
        const request = {}; activeRequest.current = request;
        const isCurrent = () => alive.current && activeRequest.current === request && currentAccount.current === accountId;
        submitting.current = true; setBusy(true);
        try {
            await runSecurity(() => {
                if (!isCurrent()) throw new AccountSecurityError("account_changed");
                return isClerkEnabled() ? accountApi.changePassword(currentPassword, nextPassword, accountId)
                    : accountApi.changePassword(currentPassword, nextPassword);
            });
            if (!isCurrent()) return;
            form.current?.reset(); setSuccess(passwordless ? "created" : "updated");
            if (passwordless) setCreatedFor(accountId);
        } catch (cause) {
            if (isCurrent()) {
                setError(securityErrorMessage(cause, passwordless
                    ? "Your password could not be created. Complete the identity check, check your connection, and try again."
                    : "Your password could not be changed. Check your current password and connection, then try again."));
                if (cause instanceof AccountSecurityError && cause.code === "account_changed") { form.current?.reset(); setIdentityChanged(true); }
            }
        } finally {
            if (activeRequest.current === request) { activeRequest.current = null; submitting.current = false; if (alive.current) setBusy(false); }
        }
    }

    if (accountChecking || checking) return <StudioPage className="pt-settings-page pt-settings-gate"><p role="status" className="pt-inline-actions"><Loader2 size={18} className="animate-spin" /> Checking your account…</p></StudioPage>;
    if (!user) return <StudioPage className="pt-settings-page pt-settings-gate">
        <StudioHeader kicker={<><KeyRound size={16} /> Account settings</>} title={<>Sign in to manage<br />your account.</>} description="Your profile, passkeys, password and account controls are available after you sign in." />
        <div className="pt-inline-actions"><a href="/account/sign-in?next=/account/settings" className="pt-studio-button">Sign in <ArrowUpRight size={16} /></a><a href="/tools" className="pt-studio-link">Continue using tools <ArrowUpRight size={16} /></a></div>
        <p className="pt-settings-save-note">You can still change Air / Play and light / dark in the header.</p>
    </StudioPage>;

    return <StudioPage className="pt-settings-page pt-account-workspace">
        <AccountWorkspaceHeader active="settings" email={user.email} title="Account settings" description="Manage how you sign in, secure your account, and make this space yours." />
        <div className="pt-settings-security">
            <UsernameSettings accountId={user.id} />
            <section className="pt-settings-password" aria-labelledby="password-title">
                <div className="pt-settings-password-intro">
                    <div className="pt-settings-section-heading"><span className="pt-connection-symbol"><KeyRound size={24} strokeWidth={1.5} /></span><div><p className="pt-workspace-caption">Account security</p><h2 id="password-title">{passwordless ? "Create your password" : "Change your password"}</h2></div></div>
                    <p className="pt-account-hint">{passwordless ? "You currently sign in without a password. Add one here to give yourself another way in." : "Use a strong, unique password that you don’t use for another account."}</p>
                    <p className="pt-account-hint">{isClerkEnabled() ? "You may be asked to verify your identity first. Saving a password signs out your other sessions." : "Saving a password signs out your other sessions."}</p>
                </div>
                <form className="pt-settings-password-editor" ref={form} onSubmit={event => void changePassword(event)} onChange={() => { setError(""); setSuccess(""); }}>
                    <fieldset disabled={busy || identityChanged}>
                        {!passwordless && <label className="pt-input-label">Current password<input name="current-password" type="password" autoComplete="current-password" required className="pt-input" /></label>}
                        <label className="pt-input-label">New password<input name="new-password" type="password" autoComplete="new-password" required minLength={MIN_PASSWORD_LENGTH} className="pt-input" aria-describedby="password-help" /></label>
                        <p id="password-help" className="pt-account-hint">At least {MIN_PASSWORD_LENGTH} characters. A few unrelated words make a memorable passphrase.</p>
                        <label className="pt-input-label">Confirm new password<input name="confirm-password" type="password" autoComplete="new-password" required minLength={MIN_PASSWORD_LENGTH} className="pt-input" /></label>
                        <button type="submit" className="pt-studio-button">{busy && <Loader2 size={16} className="animate-spin" />}{busy ? "Saving password…" : passwordless ? "Create password" : "Update password"}</button>
                    </fieldset>
                    {error && <p role="alert" className="pt-form-error">{error}</p>}
                    {success && <p role="status" className="pt-form-success"><CheckCircle2 size={17} /> Your password has been {success}.</p>}
                </form>
            </section>
            <PasskeySettings accountId={user.id} />
        </div>
        <div className="pt-settings-preferences">
            {appearanceArea && <section className="pt-settings-appearance" aria-labelledby="appearance-title"><div className="pt-settings-section-heading"><span className="pt-connection-symbol"><Palette size={25} strokeWidth={1.5} /></span><div><p className="pt-workspace-caption">Browser preferences</p><h2 id="appearance-title">Make it yours</h2></div></div><p>Choose Air or Play, then set your light or dark theme.</p>{appearanceArea}<p className="pt-settings-save-note">Your choices are remembered in this browser.</p></section>}
            <aside className="pt-settings-housekeeping"><Shield size={27} strokeWidth={1.4} /><div><p className="pt-workspace-caption">Local data</p><h2>What this browser remembers</h2><p>Saved passwords, signatures and tool defaults belong to this browser. View, export or erase them from My Stuff.</p></div><a href="/my-stuff" className="pt-studio-link">Manage local data <ArrowUpRight size={16} /></a></aside>
            <div className="pt-settings-shortcuts"><a href="/privacy"><Shield size={22} /><span><strong>Your privacy choices</strong><small>Understand where your data goes.</small></span><ArrowUpRight size={18} /></a></div>
        </div>
    </StudioPage>;
}
