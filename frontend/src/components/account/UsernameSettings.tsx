import { useEffect, useRef, useState, type FormEvent } from "react";
import { AtSign, CheckCircle2, Loader2 } from "lucide-react";
import { usernameAccountsEnabled } from "@/lib/auth-mode";
import { isClerkEnabled, requireClerk, whenClerkReady } from "@/lib/clerk/instance";
import "./username-settings.css";

function readableError(error: unknown): string {
    const value = error as { errors?: Array<{ longMessage?: string; message?: string }>; message?: string };
    return value?.errors?.[0]?.longMessage || value?.errors?.[0]?.message || value?.message || "Your username could not be saved. Try again.";
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

    function currentUser() {
        const user = requireClerk().user;
        if (!user || user.id !== accountId) throw new Error("Your sign-in has changed. Reload this page before changing your username.");
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
            } catch (err) { if (!cancelled) { setError(readableError(err)); setReady(false); } }
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
            const user = currentUser();
            // An empty field only clears the username after this explicit form submission.
            const updated = await user.update({ username: next || null });
            if (!alive.current) return;
            currentUser();
            const confirmed = updated.username || "";
            setSaved(confirmed); setUsername(confirmed);
            setNotice(confirmed ? "Your username has been saved." : "Your username has been removed. You can still sign in with your other account methods.");
        } catch (err) { if (alive.current) setError(readableError(err)); }
        finally { submitting.current = false; if (alive.current) setBusy(false); }
    }

    return <section className="pt-username-settings" aria-labelledby="username-title">
        <div className="pt-username-intro"><span className="pt-connection-symbol"><AtSign size={25} strokeWidth={1.5} /></span><div><p className="pt-workspace-caption">A name to remember</p><h2 id="username-title">Your username</h2><p>An optional way to sign in. Pick a name that’s easy for you to remember.</p></div></div>
        <div className="pt-username-editor">
            {checking ? <p role="status" className="pt-inline-actions"><Loader2 size={16} className="animate-spin" /> Loading your username…</p> : ready ? <form onSubmit={event => void save(event)}><label className="pt-input-label">Username <span className="pt-username-optional">optional</span><input className="pt-input" autoComplete="username" autoCapitalize="none" spellCheck={false} value={username} onChange={event => { setUsername(event.target.value); setNotice(""); setError(""); }} minLength={4} maxLength={64} disabled={busy} aria-describedby="username-help" placeholder="Choose your username" /></label><p id="username-help" className="pt-account-hint">Use 4–64 characters. Your name must be unique; it is checked when you save. To remove it, clear this field and choose Save username.</p><button type="submit" className="pt-studio-button" disabled={busy || username.trim() === saved}>{busy && <Loader2 size={16} className="animate-spin" />}{busy ? "Saving…" : "Save username"}</button></form> : <button type="button" className="pt-studio-button is-secondary" onClick={() => setRevision(value => value + 1)}>Try loading again</button>}
            {error && <p role="alert" className="pt-form-error">{error}</p>}
            {notice && <p role="status" className="pt-username-notice"><CheckCircle2 size={17} />{notice}</p>}
        </div>
    </section>;
}
