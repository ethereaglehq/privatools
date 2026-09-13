import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ArrowUpRight, CheckCircle2, KeyRound, Loader2, Palette, Shield, SlidersHorizontal } from "lucide-react";
import { accountApi, MIN_PASSWORD_LENGTH, type AccountUser } from "@/skins/accountLogic";
import { isClerkEnabled, whenClerkReady } from "@/lib/clerk/instance";
import { StudioPage, StudioHeader } from "@/skins/experience/Studio";
import PasskeySettings from "@/components/account/PasskeySettings";
import UsernameSettings from "@/components/account/UsernameSettings";
import "@/skins/experience/secondary-pages.css";

export interface AccountSettingsPageProps {
    /** Shared Air / Play and light / dark controls supplied by the application shell. */
    appearanceArea?: ReactNode;
    /** Pass the shell's account user to keep inline sign-in and this page in sync. */
    accountUser?: AccountUser | null;
    accountChecking?: boolean;
}

export default function AccountSettingsPage({ appearanceArea, accountUser, accountChecking = false }: AccountSettingsPageProps) {
    const [loadedUser, setUser] = useState<AccountUser | null>(accountUser ?? null);
    const user = accountUser === undefined ? loadedUser : accountUser;
    const [checking, setChecking] = useState(accountUser === undefined);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const alive = useRef(false);
    const submitting = useRef(false);
    const form = useRef<HTMLFormElement>(null);
    const passwordless = isClerkEnabled() && user?.password_enabled === false;

    useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
    useEffect(() => { form.current?.reset(); setError(""); setSuccess(false); }, [user?.id]);
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
        if (submitting.current || !user) return;
        const values = new FormData(event.currentTarget);
        const currentPassword = String(values.get("current-password") ?? "");
        const nextPassword = String(values.get("new-password") ?? "");
        const confirmation = String(values.get("confirm-password") ?? "");
        setError(""); setSuccess(false);
        if (nextPassword !== confirmation) { setError("The new passwords do not match. Check both fields."); return; }
        if (nextPassword.length < MIN_PASSWORD_LENGTH) { setError(`Use at least ${MIN_PASSWORD_LENGTH} characters for your new password.`); return; }
        if (nextPassword === currentPassword) { setError("Choose a different password from your current one."); return; }
        submitting.current = true; setBusy(true);
        try {
            await accountApi.changePassword(currentPassword, nextPassword);
            if (!alive.current) return;
            form.current?.reset(); setSuccess(true);
        } catch {
            // Do not reflect a server error that might contain submitted credential material.
            if (alive.current) setError("Your password could not be changed. Check your current password and connection, then try again. If you use social sign-in, use the account’s password reset flow first.");
        } finally {
            submitting.current = false;
            if (alive.current) setBusy(false);
        }
    }

    if (accountChecking || checking) return <StudioPage className="pt-settings-page pt-settings-gate"><p role="status" className="pt-inline-actions"><Loader2 size={18} className="animate-spin" /> Checking your account…</p></StudioPage>;
    if (!user) return <StudioPage className="pt-settings-page pt-settings-gate">
        <StudioHeader kicker={<><KeyRound size={16} /> Account settings</>} title={<>Sign in to manage<br />your account.</>} description="Your profile, passkeys, password and account controls are available after you sign in." />
        <div className="pt-inline-actions"><a href="/account/sign-in?next=/account/settings" className="pt-studio-button">Sign in <ArrowUpRight size={16} /></a><a href="/tools" className="pt-studio-link">Continue using tools <ArrowUpRight size={16} /></a></div>
        <p className="pt-settings-save-note">You can still change Air / Play and light / dark in the header.</p>
    </StudioPage>;

    return <StudioPage className="pt-settings-page">
        <StudioHeader kicker={<><SlidersHorizontal size={16} /> Make yourself at home</>} title={<>A space that <br />feels like you.</>} description="Set the mood, look after your account, and decide what this browser remembers." visual={<div className="pt-settings-route-art"><Palette size={38} strokeWidth={1.3} /><span>Your space. <br />Your pace.</span><i /><i /><i /></div>} />
        <div className="pt-settings-desk">
            {appearanceArea && <section className="pt-settings-appearance" aria-labelledby="appearance-title"><div className="pt-settings-section-heading"><span className="pt-connection-symbol"><Palette size={25} strokeWidth={1.5} /></span><div><p className="pt-workspace-caption">The look & feel</p><h2 id="appearance-title">Make it yours.</h2></div></div><p>Air gives you room to breathe. Play brings a little personality. Your work stays right where you left it.</p>{appearanceArea}<p className="pt-settings-save-note">Your choices are remembered in this browser.</p></section>}
            <section className="pt-settings-password" aria-labelledby="password-title"><div className="pt-settings-section-heading"><span className="pt-connection-symbol"><KeyRound size={24} strokeWidth={1.5} /></span><div><p className="pt-workspace-caption">A little peace of mind</p><h2 id="password-title">{passwordless ? "Your sign-in" : "Change your password"}</h2></div></div>
                {checking ? <p role="status" className="pt-inline-actions"><Loader2 size={15} className="animate-spin" /> Checking sign-in…</p> : !user ? <div className="pt-settings-sign-in"><p>Sign in to change your account password. Every file tool remains available without an account.</p><a href="/account/sign-in" className="pt-studio-button">Sign in <ArrowUpRight size={15} /></a></div> : passwordless ? <div className="pt-settings-passwordless"><h3>You sign in without a password</h3><p>You currently use a provider or passkey to sign in. If you’d like to add a password, start the email recovery flow for your account. There’s no current password to enter.</p><a href="/account?mode=recover" className="pt-studio-button">Set up a password by email <ArrowUpRight size={15} /></a></div> : <><p className="pt-settings-identity">Signed in as <b>{user.email}</b></p><form ref={form} onSubmit={event => void changePassword(event)} onChange={() => { setError(""); setSuccess(false); }}><fieldset disabled={busy}><label className="pt-input-label">Current password<input name="current-password" type="password" autoComplete="current-password" required className="pt-input" /></label><label className="pt-input-label">New password<input name="new-password" type="password" autoComplete="new-password" required minLength={MIN_PASSWORD_LENGTH} className="pt-input" aria-describedby="password-help" /></label><p id="password-help" className="pt-account-hint">At least {MIN_PASSWORD_LENGTH} characters. A few unrelated words make a memorable passphrase.</p><label className="pt-input-label">Confirm new password<input name="confirm-password" type="password" autoComplete="new-password" required minLength={MIN_PASSWORD_LENGTH} className="pt-input" /></label><button type="submit" className="pt-studio-button">{busy && <Loader2 size={16} className="animate-spin" />}{busy ? "Updating…" : "Update password"}</button></fieldset>{error && <p role="alert" className="pt-form-error">{error}</p>}{success && <p role="status" className="pt-form-success"><CheckCircle2 size={17} /> Your password has been updated.</p>}</form></>}
            </section>
            <aside className="pt-settings-housekeeping"><Shield size={27} strokeWidth={1.4} /><div><p className="pt-workspace-caption">A tidy digital home</p><h2>A little housekeeping.</h2><p>Saved passwords, signatures and tool defaults belong to this browser. See what is stored, export your setup, or erase it from My Stuff.</p></div><a href="/my-stuff" className="pt-studio-link">Manage local data <ArrowUpRight size={16} /></a></aside>
            <div className="pt-settings-shortcuts"><a href="/account/keys"><KeyRound size={22} /><span><strong>Your API access</strong><small>Create and revoke keys for your scripts.</small></span><ArrowUpRight size={18} /></a><a href="/privacy"><Shield size={22} /><span><strong>Your privacy choices</strong><small>Understand where your data goes.</small></span><ArrowUpRight size={18} /></a></div>
        </div>
        {user && <UsernameSettings accountId={user.id} />}
        {user && <PasskeySettings accountId={user.id} />}
    </StudioPage>;
}
