import { useEffect, useRef, useState, type FormEvent } from "react";
import { CheckCircle2, Fingerprint, KeyRound, Loader2, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { passkeyAccountsEnabled } from "@/lib/auth-mode";
import { passkeysSupported } from "@/lib/clerk/accountApi";
import { requireClerk, whenClerkReady } from "@/lib/clerk/instance";
import { AccountSecurityError, securityErrorMessage } from "@/lib/clerk/securityActions";
import { useAccountReverification } from "@/lib/clerk/useAccountReverification";
import "./passkey-settings.css";

type ClerkUser = NonNullable<ReturnType<typeof requireClerk>["user"]>;
type Passkey = ClerkUser["passkeys"][number];

function dateLabel(date: Date | null): string {
    return date && Number.isFinite(new Date(date).getTime())
        ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(date))
        : "Not used yet";
}

function errorMessage(error: unknown, fallback = "Passkeys could not be updated. Check your connection and try again."): string {
    const value = error as { name?: string; errors?: Array<{ code?: string }> };
    if (value?.name === "NotAllowedError" || value?.name === "AbortError" || value?.errors?.some(item => /passkey.*(cancel|not_allowed)/.test(item.code ?? ""))) {
        return "The passkey request was cancelled or timed out. You can try again when you’re ready.";
    }
    return securityErrorMessage(error, fallback);
}

/** Local accounts never load the hosted passkey controls. Account changes reset sensitive UI state. */
export default function PasskeySettings({ accountId }: { accountId: string }) {
    return passkeyAccountsEnabled() ? <EnabledPasskeySettings key={accountId} accountId={accountId} /> : null;
}

function EnabledPasskeySettings({ accountId }: { accountId: string }) {
    const [passkeys, setPasskeys] = useState<Passkey[]>([]);
    const [checking, setChecking] = useState(true);
    const [ready, setReady] = useState(false);
    const [pending, setPending] = useState("");
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [editing, setEditing] = useState("");
    const [name, setName] = useState("");
    const [removing, setRemoving] = useState("");
    const [revision, setRevision] = useState(0);
    const alive = useRef(false);
    const working = useRef(false);
    const supported = passkeysSupported();
    const runSecurity = useAccountReverification();

    function currentUser(): ClerkUser {
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
                if (!await whenClerkReady()) throw new Error("Account security could not load. Check your connection and try again.");
                const user = currentUser();
                const refreshed = await user.reload();
                if (!cancelled) { currentUser(); setPasskeys([...refreshed.passkeys]); setReady(true); }
            } catch (err) {
                if (!cancelled) { setError(errorMessage(err, "Account security could not load. Check your connection and try again.")); setReady(false); setPasskeys([]); }
            } finally { if (!cancelled) setChecking(false); }
        })();
        return () => { cancelled = true; alive.current = false; };
        // The keyed component fixes accountId for this instance.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [accountId, revision]);

    async function mutate(action: string, operation: (user: ClerkUser) => Promise<Passkey[]>, message: string) {
        if (working.current || checking || !ready) return;
        working.current = true; setPending(action); setError(""); setNotice("");
        let attempts = 0;
        try {
            const updated = await runSecurity(() => {
                const user = currentUser();
                // Reverification resumes asynchronously. Enrollment needs a fresh click
                // for browsers that require transient activation for WebAuthn.
                if (action === "create" && attempts > 0) throw new AccountSecurityError("enrollment_ready");
                attempts += 1;
                return operation(user);
            });
            if (!alive.current) return;
            const user = currentUser();
            setPasskeys(updated); setEditing(""); setRemoving(""); setNotice(message);
            try {
                const refreshed = await user.reload();
                if (alive.current) { currentUser(); setPasskeys([...refreshed.passkeys]); }
            } catch {
                if (alive.current) { currentUser(); setNotice(`${message} The list could not refresh; refresh it when your connection is back.`); }
            }
        } catch (err) {
            if (alive.current) {
                if (err instanceof AccountSecurityError && err.code === "enrollment_ready") setNotice(err.message);
                else {
                    setError(errorMessage(err));
                    if (err instanceof AccountSecurityError && err.code === "account_changed") { setPasskeys([]); setReady(false); setEditing(""); setRemoving(""); setName(""); setNotice(""); }
                }
            }
        } finally {
            working.current = false;
            if (alive.current) setPending("");
        }
    }

    function enroll() {
        if (!supported) return;
        void mutate("create", async user => {
            const passkey = await user.createPasskey();
            return [...user.passkeys.filter(item => item.id !== passkey.id), passkey];
        }, "Your passkey is ready. You can use it the next time you sign in.");
    }

    function rename(event: FormEvent<HTMLFormElement>, id: string) {
        event.preventDefault();
        const nextName = name.trim();
        if (!nextName) { setError("Give your passkey a name so you can recognise it later."); return; }
        void mutate(id, async user => {
            const passkey = user.passkeys.find(item => item.id === id);
            if (!passkey) throw new AccountSecurityError("passkey_missing");
            const updated = await passkey.update({ name: nextName });
            return user.passkeys.map(item => item.id === id ? updated : item);
        }, "Passkey name updated.");
    }

    function remove(id: string) {
        void mutate(id, async user => {
            const passkey = user.passkeys.find(item => item.id === id);
            if (!passkey) throw new AccountSecurityError("passkey_missing");
            await passkey.delete();
            return user.passkeys.filter(item => item.id !== id);
        }, "Passkey removed from your account. You can also remove its saved copy from your device or password manager.");
    }

    const disabled = checking || Boolean(pending) || !ready;
    return <section className="pt-passkeys" aria-labelledby="passkeys-title">
        <div className="pt-passkeys-intro">
            <span className="pt-passkeys-symbol"><Fingerprint size={30} strokeWidth={1.4} /></span>
            <p className="pt-workspace-caption">Account security</p>
            <h2 id="passkeys-title">Passkeys</h2>
            <p>Sign in with a passkey saved on your device or in your password manager. Your browser will ask you to confirm with your screen lock, security key, or biometrics.</p>
            <p className="pt-passkeys-privacy">PrivaTools never receives your fingerprint, face scan, or device PIN.</p>
            <button type="button" className="pt-studio-button" onClick={enroll} disabled={disabled || !supported} aria-describedby={!supported ? "passkey-device-help" : undefined}>
                {pending === "create" ? <Loader2 size={17} className="animate-spin" /> : <Plus size={17} />}
                {pending === "create" ? "Follow your browser’s prompt…" : "Add a passkey"}
            </button>
            {!supported && <p id="passkey-device-help" className="pt-passkeys-support">This browser cannot create passkeys here. Use a current browser on the secure HTTPS website. You can still manage saved passkeys below.</p>}
        </div>
        <div className="pt-passkeys-manager">
            <div className="pt-passkeys-heading"><h3>Saved passkeys <span>{checking ? "" : passkeys.length}</span></h3><button type="button" className="pt-passkeys-text-button" disabled={checking || Boolean(pending)} onClick={() => { setNotice(""); setRevision(value => value + 1); }}><RefreshCw size={14} />Refresh</button></div>
            {checking ? <p role="status" className="pt-passkeys-empty"><Loader2 size={18} className="animate-spin" /> Checking your account…</p> : ready && !passkeys.length ? <div className="pt-passkeys-empty"><KeyRound size={25} strokeWidth={1.4} /><div><strong>A simpler sign-in starts here.</strong><p>Add your first passkey when you’re ready. Your existing sign-in methods stay available.</p></div></div> : <ul className="pt-passkeys-list">
                {passkeys.map((passkey, index) => <li key={passkey.id} className="pt-passkeys-row">
                    <span className="pt-passkeys-key"><KeyRound size={19} /></span>
                    <div className="pt-passkeys-details"><strong>{passkey.name || `Passkey ${index + 1}`}</strong><p>Added {dateLabel(passkey.createdAt)} <span>·</span> {passkey.lastUsedAt ? `Last used ${dateLabel(passkey.lastUsedAt)}` : "Not used yet"}</p></div>
                    <div className="pt-passkeys-actions"><button type="button" className="pt-passkeys-text-button" disabled={disabled} aria-label={`Rename ${passkey.name || `passkey ${index + 1}`}`} onClick={() => { setEditing(passkey.id); setName(passkey.name || ""); setRemoving(""); setError(""); }}><Pencil size={14} />Rename</button><button type="button" className="pt-passkeys-text-button" disabled={disabled} aria-label={`Remove ${passkey.name || `passkey ${index + 1}`}`} onClick={() => { setRemoving(passkey.id); setEditing(""); setError(""); }}><Trash2 size={14} />Remove</button></div>
                    {editing === passkey.id && <form className="pt-passkeys-edit" onSubmit={event => rename(event, passkey.id)}><label className="pt-input-label">Passkey name<input className="pt-input" value={name} onChange={event => setName(event.target.value)} autoFocus maxLength={64} required disabled={Boolean(pending)} placeholder="For example, personal laptop" /></label><div className="pt-passkeys-actions"><button className="pt-studio-button" type="submit" disabled={Boolean(pending)}>{pending === passkey.id ? "Saving…" : "Save name"}</button><button type="button" className="pt-passkeys-text-button" disabled={Boolean(pending)} onClick={() => setEditing("")}>Cancel</button></div></form>}
                    {removing === passkey.id && <div className="pt-passkeys-confirm"><p>Remove <strong>{passkey.name || "this passkey"}</strong> from your account? You won’t be able to use it to sign in again. Make sure another sign-in method is available.</p><div className="pt-passkeys-actions"><button type="button" className="pt-studio-button is-secondary" disabled={Boolean(pending)} onClick={() => remove(passkey.id)}>{pending === passkey.id ? "Removing…" : "Confirm removal"}</button><button type="button" className="pt-passkeys-text-button" disabled={Boolean(pending)} onClick={() => setRemoving("")}>Keep passkey</button></div></div>}
                </li>)}
            </ul>}
            {error && <p role="alert" className="pt-form-error">{error}</p>}
            {notice && <p role="status" className="pt-passkeys-notice"><CheckCircle2 size={17} />{notice}</p>}
        </div>
    </section>;
}
