import { useEffect, useRef, useState, type FormEvent } from "react";
import { AtSign, CheckCircle2, Loader2 } from "lucide-react";
import { usernameAccountsEnabled } from "@/lib/auth-mode";
import { isClerkEnabled, requireClerk, whenClerkReady } from "@/lib/clerk/instance";
import { AccountSecurityError, securityErrorMessage } from "@/lib/clerk/securityActions";
import { useAccountReverification } from "@/lib/clerk/useAccountReverification";
import "./username-settings.css";

function readableError(error: unknown): string {
    const value = error as { errors?: Array<{ code?: string }> };
    if (value?.errors?.some(item => item.code === "form_identifier_exists")) return "That username is already taken. Choose another.";
    if (value?.errors?.some(item => item.code === "form_param_format_invalid" || item.code === "form_username_invalid_character")) return "Choose a username with letters, numbers, hyphens or underscores.";
    return securityErrorMessage(error, "Your username could not be saved. Check your connection and try again.");
}

export default function UsernameSettings({ accountId }: { accountId: string }) {
    return isClerkEnabled() && usernameAccountsEnabled() ? <EnabledUsernameSettings key={accountId} accountId={accountId} /> : null;
}

function EnabledUsernameSettings({ accountId }: { accountId: string }) {
    const [username, setUsername] = useState("");
    const [saved, setSaved] = useState("");
    const [checking, setChecking] = useState(true);
    const [ready, setReady] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [revision, setRevision] = useState(0);
    const alive = useRef(false);
    const submitting = useRef(false);
    const runSecurity = useAccountReverification();

    function currentUser() {
        const user = requireClerk().user;
        if (!alive.current || !user || user.id !== accountId) throw new AccountSecurityError("account_changed");
        return user;
    }

    useEffect(() => {
        alive.current = true;
        let cancelled = false;
        setChecking(true); setError("");
        void (async () => {
            try {
                if (!await whenClerkReady()) throw new Error("Your account could not load. Check your connection and try again.");
                const user = currentUser();
                if (!cancelled) { setUsername(user.username || ""); setSaved(user.username || ""); setReady(true); }
            } catch (err) { if (!cancelled) { setError(securityErrorMessage(err, "Your account could not load. Check your connection and try again.")); setReady(false); } }
            finally { if (!cancelled) setChecking(false); }
        })();
        return () => { cancelled = true; alive.current = false; };
        // The keyed component keeps each signed-in account's form separate.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [accountId, revision]);

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (submitting.current || checking || !ready) return;
        const next = username.trim();
        setError(""); setNotice("");
        if (next && (next.length < 4 || next.length > 64)) { setError("Choose a username between 4 and 64 characters, or leave it blank to remove it."); return; }
        if (next === saved) return;
        submitting.current = true; setBusy(true);
        try {
            // An empty field only clears the username after this explicit form submission.
            const updated = await runSecurity(() => currentUser().update({ username: next || null }));
            if (!alive.current) return;
            currentUser();
            const confirmed = updated.username || "";
            setSaved(confirmed); setUsername(confirmed);
            setNotice(confirmed ? "Your username has been saved." : "Your username has been removed. You can still sign in with your other account methods.");
        } catch (err) {
            if (alive.current) {
                setError(readableError(err));
                if (err instanceof AccountSecurityError && err.code === "account_changed") { setUsername(""); setSaved(""); setReady(false); }
            }
        }
        finally { submitting.current = false; if (alive.current) setBusy(false); }
    }

    return <section className="pt-username-settings" aria-labelledby="username-title">
        <div className="pt-username-intro"><span className="pt-connection-symbol"><AtSign size={25} strokeWidth={1.5} /></span><div><p className="pt-workspace-caption">Profile</p><h2 id="username-title">Your username</h2><p>An optional way to sign in. Pick a name that’s easy for you to remember.</p></div></div>
        <div className="pt-username-editor">
            {checking ? <p role="status" className="pt-inline-actions"><Loader2 size={16} className="animate-spin" /> Loading your username…</p> : ready ? <form onSubmit={event => void save(event)}><label className="pt-input-label">Username <span className="pt-username-optional">optional</span><input className="pt-input" autoComplete="username" autoCapitalize="none" spellCheck={false} value={username} onChange={event => { setUsername(event.target.value); setNotice(""); setError(""); }} minLength={4} maxLength={64} disabled={busy} aria-describedby="username-help" placeholder="Choose your username" /></label><p id="username-help" className="pt-account-hint">Use 4–64 characters. Your name must be unique; it is checked when you save. To remove it, clear this field and choose Save username.</p><button type="submit" className="pt-studio-button" disabled={busy || username.trim() === saved}>{busy && <Loader2 size={16} className="animate-spin" />}{busy ? "Saving…" : "Save username"}</button></form> : <button type="button" className="pt-studio-button is-secondary" onClick={() => setRevision(value => value + 1)}>Try loading again</button>}
            {error && <p role="alert" className="pt-form-error">{error}</p>}
            {notice && <p role="status" className="pt-username-notice"><CheckCircle2 size={17} />{notice}</p>}
        </div>
    </section>;
}
