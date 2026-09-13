/* eslint-disable */
// @ts-nocheck
/**
 * Accounts, as a mixin over a generated skin component.
 *
 * The four skins render accounts in four idioms but drive one flow. This holds
 * the flow — state, requests, bindings — and each skin supplies only what is
 * genuinely theme-specific: where its nav items live, what shape they are, and
 * which CSS variables to paint with.
 *
 * It subclasses rather than edits: `src/skins/<id>/SkinApp.tsx` is regenerated
 * from the design source, so a subclass is the only thing that survives.
 * `renderVals()` is extended, never replaced.
 */
import { mergeNavItem } from "./navInject";
import {
    accountApi, describeKey, defaultKeyLabel, downloadRecoveryCode, initialAccountState,
    MIN_PASSWORD_LENGTH, ACCOUNT_COPY, EMAIL_RESET,
} from "./accountLogic";
import { CLERK_BLOCKED_MESSAGE, clerkInstance, clerkLoadFailed, subscribeClerkInstance, whenClerkReady } from "@/lib/clerk/instance";
import { captureAccountReturn, consumeAccountReturn, clearAccountReturn } from "@/lib/account-return";
import { SSO_RETURN } from "@/lib/clerk/accountApi";

const ACCOUNT_PATH = /^\/account(?:\/(?:keys|settings|sign-in|sign-up))?\/?$/;
const ACCOUNT_HINT_KEY = "privatools.account-present";
function accountHint() {
    try { return localStorage.getItem(ACCOUNT_HINT_KEY) === "1"; } catch { return false; }
}
function rememberAccountHint(present) {
    try { if (present) localStorage.setItem(ACCOUNT_HINT_KEY, "1"); else localStorage.removeItem(ACCOUNT_HINT_KEY); } catch { /* Presentation never gates account access. */ }
}
type AccountLocation = { pathname: string; hash?: string; search?: string };

/** Shared with the application shell; hashes still require a canonical path navigation. */
export function accountPathForLocation(current: AccountLocation | null = typeof location === "undefined" ? null : location) {
    if (!current) return null;
    const hashPath = (current.hash || "").replace(/^#/, "").split("?")[0];
    const path = ACCOUNT_PATH.test(hashPath) ? hashPath : current.pathname;
    return ACCOUNT_PATH.test(path || "") ? path.replace(/\/+$/, "") : null;
}

export function accountModeForLocation(current: AccountLocation | null = typeof location === "undefined" ? null : location) {
    const path = accountPathForLocation(current);
    if (path === "/account/sign-up") return "signup";
    if (path === "/account/sign-in") return "signin";
    if (path === "/account") {
        const mode = new URLSearchParams(current?.search || "").get("mode");
        if (mode === "signup" || mode === "recover") return mode;
    }
    return "signin";
}

/**
 * @param Base    the generated component
 * @param config  theme specifics:
 *   route        hash or path this surface answers on
 *   isActive()   whether that route is current
 *   navKey       binding name holding the nav list ("navSys", "navMain", …)
 *   navItem()    builds one nav item in this theme's shape
 *   injectNav()  optional — for themes whose nav is grouped rather than flat
 *   palette      CSS variables this theme paints accounts with
 */
export function withAccounts(Base, config) {
    return class WithAccounts extends Base {
        constructor(props) {
            super(props);
            this.state = { ...this.state, acct: { ...initialAccountState, mode: accountModeForLocation(), accountHint: accountHint(), resolved: false } };
            this._accountRouteIdentity = accountPathForLocation();
            if (this._accountRouteIdentity) captureAccountReturn(location.search);
            this._onAcctNav = () => {
                this._ensureAccountPath(); this._syncAccountMode(); this.forceUpdate();
                if (accountPathForLocation()) captureAccountReturn(location.search);
                const userId = this.state.acct.user?.id;
                if (userId && this._isAccountActive() && this._keysLoadedUser !== userId) this._loadKeys(userId);
            };
            this._onAccountHint = event => { if (event.key === ACCOUNT_HINT_KEY || event.key === null) this._setAcct({ accountHint: accountHint() }); };
        }

        componentDidMount() {
            this._accountUnmounted = false;
            if (super.componentDidMount) super.componentDidMount();
            window.addEventListener("hashchange", this._onAcctNav);
            window.addEventListener("popstate", this._onAcctNav);
            window.addEventListener("privatools:clerk-blocked", this._onClerkBlocked);
            window.addEventListener("storage", this._onAccountHint);
            if (EMAIL_RESET) this._unsubscribeClerk = subscribeClerkInstance(this._syncClerkAccount);
            this._ensureAccountPath();
            // The block usually happens before this route is even opened, so
            // check the flag as well as listening for the event.
            if (clerkLoadFailed()) this._onClerkBlocked();
            this._bootAccount();
        }

        componentWillUnmount() {
            this._accountUnmounted = true;
            this._clerkSyncId = (this._clerkSyncId || 0) + 1;
            this._keysRequestId = (this._keysRequestId || 0) + 1;
            if (super.componentWillUnmount) super.componentWillUnmount();
            window.removeEventListener("hashchange", this._onAcctNav);
            window.removeEventListener("popstate", this._onAcctNav);
            window.removeEventListener("privatools:clerk-blocked", this._onClerkBlocked);
            window.removeEventListener("storage", this._onAccountHint);
            this._unsubscribeClerk?.();
        }

        /**
         * Put the account view on the /account *path*, never a hash of some
         * other page.
         *
         * The CSP that lets clerk-js load is scoped per path, and a hash never
         * reaches the server — so `/#/account` and `/tool/x#/account` are served
         * the homepage's and the tool's policies, which do not name Clerk, and
         * sign-in dies with "Failed to load Clerk JS". Only a real navigation
         * gets the right headers, so any hash that lands here is turned into
         * one. `replace`, not `assign`: the broken URL should not sit in the
         * back button.
         */
        /**
         * Settle who is signed in, once Clerk can actually answer.
         *
         * Two things had to move here. Clerk is parked from an effect, so
         * calling `me()` straight out of componentDidMount could beat it and
         * report a signed-in visitor as signed out, permanently. And a visitor
         * coming back from GitHub arrives with the handshake half-finished:
         * it completes only if this page asks it to.
         */
        _bootAccount = async () => {
            if (EMAIL_RESET) {
                const clerk = await whenClerkReady();
                if (this._accountUnmounted) return;
                if (!clerk) {
                    if (clerkLoadFailed()) this._onClerkBlocked();
                    this._setAcct({ resolved: true });
                    return;
                }
                // Only on the leg back from the provider, which signInWithSocial
                // marks explicitly. Clerk's own resources cannot be used to
                // detect this: an untouched signIn already reads
                // "needs_identifier", so a truthiness check runs the callback
                // on every ordinary visit to the page.
                const returning = new URLSearchParams(location.search).has(SSO_RETURN);
                // `session` settles before `user` does, and running the
                // callback against a finished flow is what bounces the visitor
                // to the hosted portal. Check both.
                const alreadyIn = Boolean(clerk.user || clerk.session);
                // And the verification must still be live. A page that has seen
                // an earlier attempt keeps a spent one around — status
                // "expired", strategy still oauth_github — and handing that to
                // handleRedirectCallback fails, on which Clerk navigates to its
                // hosted portal. So a stale marker in a bookmarked URL was
                // enough to throw someone off the site entirely.
                const LIVE = ["transferable", "verified", "unverified"];
                const live = (v) => Boolean(v && LIVE.includes(v.status));
                const pending = live(clerk.client?.signIn?.firstFactorVerification)
                    || live(clerk.client?.signUp?.verifications?.externalAccount);
                if (returning && !alreadyIn && pending && !this._socialCompleting) {
                    this._socialCompleting = true;
                    try {
                        await accountApi.completeSocialRedirect();
                        // Clerk leaves its bookkeeping in the address bar.
                        history.replaceState(null, "", location.pathname + location.hash);
                    } catch (err) {
                        this._setAcct({ busy: false, error: err.message });
                    } finally { this._socialCompleting = false; }
                }
                return this._syncClerkAccount(clerkInstance() || clerk);
            }
            accountApi.me()
                .then(({ user }) => { this._setAcct({ user, resolved: true }); this._resumeAccountReturn(user); if (this._isAccountActive()) this._loadKeys(user.id); })
                .catch(() => { this._setAcct({ resolved: true }); });
        };

        _syncClerkAccount = async clerk => {
            if (this._accountUnmounted || !clerk?.loaded) return;
            if (!clerk.user) {
                if (clerk.session) return; // User can settle just after its session.
                this._clerkSignature = "";
                this._clerkSyncId = (this._clerkSyncId || 0) + 1;
                rememberAccountHint(false);
                if (this.state.acct.user) {
                    this._keysRequestId = (this._keysRequestId || 0) + 1;
                    this._keysLoadedUser = null;
                    this._setAcct({ ...initialAccountState, accountHint: false, resolved: true });
                } else this._setAcct({ accountHint: false, resolved: true });
                return;
            }
            const source = clerk.user;
            const signature = JSON.stringify([source.id, source.primaryEmailAddress?.emailAddress, source.username, source.passwordEnabled]);
            // Token refreshes emit too. Avoid rerendering the whole tool app or
            // refetching API keys when the account itself has not changed.
            if (signature === this._clerkSignature) return;
            this._clerkSignature = signature;
            const syncId = this._clerkSyncId = (this._clerkSyncId || 0) + 1;
            try {
                const { user } = await accountApi.me();
                if (this._accountUnmounted || syncId !== this._clerkSyncId) return;
                const changedUser = this.state.acct.user?.id !== user.id;
                rememberAccountHint(true);
                if (changedUser) {
                    this._keysRequestId = (this._keysRequestId || 0) + 1;
                    this._keysLoadedUser = null;
                }
                this._setAcct({ user, accountHint: true, blocked: false, resolved: true, ...(changedUser ? { keys: [], freshKey: "", freshKeyCopied: false } : {}) });
                this._resumeAccountReturn(user);
                if (changedUser && this._isAccountActive()) this._loadKeys(user.id);
            } catch { if (syncId === this._clerkSyncId) { this._clerkSignature = ""; this._setAcct({ resolved: true }); } }
        };

        _resumeAccountReturn = (user, recoveryCode = "") => {
            if (!user || recoveryCode || !this._isAccountActive()) return;
            const target = consumeAccountReturn();
            if (!target) return;
            // Both destinations are in the existing account document's CSP scope.
            history.replaceState(null, "", target);
            window.dispatchEvent(new PopStateEvent("popstate"));
        };

        _ensureAccountPath = () => {
            if (typeof location === "undefined") return;
            const hashPath = (location.hash || "").replace(/^#/, "").split("?")[0];
            if (!ACCOUNT_PATH.test(hashPath)) return;
            const target = hashPath.replace(/\/+$/, "");
            if (location.pathname.replace(/\/+$/, "") === target) return;
            location.replace(target);
        };

        _isAccountActive = () => Boolean(config.isActive?.() || accountPathForLocation());

        _syncAccountMode = () => {
            const path = accountPathForLocation();
            if (path === this._accountRouteIdentity) return;
            this._accountRouteIdentity = path;
            if (!path) return;
            this._setAcct({ mode: accountModeForLocation(), error: "", needsEmailCode: false, signInVerification: "", verificationDestination: "", emailCode: "", resetEmailSent: false, password: "", recoveryInput: "" });
        };

        _acctChooseMode = (mode) => {
            const target = mode === "signup" ? "/account/sign-up" : "/account/sign-in";
            this._setAcct({ mode, error: "", needsEmailCode: false, signInVerification: "", verificationDestination: "", emailCode: "", resetEmailSent: false, password: "", recoveryInput: "" });
            // All canonical account subpaths share the account CSP. A visitor
            // outside that family still needs a full navigation for its headers.
            if (!ACCOUNT_PATH.test(location.pathname || "")) { location.assign(target); return; }
            history.pushState(null, "", target);
            this._accountRouteIdentity = target;
            window.dispatchEvent(new PopStateEvent("popstate"));
        };

        _onClerkBlocked = () => {
            this._setAcct({ busy: false, blocked: true, resolved: true, error: CLERK_BLOCKED_MESSAGE });
        };

        _setAcct(patch) {
            if (this._accountUnmounted) return;
            this.setState((s) => ({ acct: { ...s.acct, ...(typeof patch === "function" ? patch(s.acct) : patch) } }));
        }

        _loadKeys(userId = this.state.acct.user?.id) {
            if (this._keysLoadPromise && this._keysLoadUser === userId && this._keysLoadId === this._keysRequestId) return this._keysLoadPromise;
            const requestId = this._keysRequestId = (this._keysRequestId || 0) + 1;
            this._keysLoadUser = userId; this._keysLoadId = requestId;
            this._setAcct({ keysLoading: true });
            const request = accountApi.listKeys()
                .then(({ keys }) => { if (requestId === this._keysRequestId) { this._keysLoadedUser = userId; this._setAcct({ keys, keysLoading: false, error: "" }); } })
                .catch(() => {
                    if (requestId === this._keysRequestId) this._setAcct({ keysLoading: false, error: "Your API keys could not be loaded. Check your connection and retry." });
                }).finally(() => { if (this._keysLoadPromise === request) this._keysLoadPromise = null; });
            this._keysLoadPromise = request;
            return request;
        }

        _acctSubmit = (event) => {
            if (event && event.preventDefault) event.preventDefault();
            const { mode, email, password, username } = this.state.acct;
            if (this.state.acct.busy) return;
            // One form, three modes. Recover takes a different endpoint and a
            // different field, so it branches here rather than duplicating the
            // whole form in each design's markup.
            if (mode === "recover") return this._acctRecover(null);
            this._setAcct({ busy: true, error: "" });
            const request = mode === "signup"
                ? accountApi.register(email, password, username || undefined)
                : accountApi.login(email, password);
            request
                .then((res) => {
                    if (res.status === "needs_sign_in_code") {
                        this._setAcct({ busy: false, password: "", signInVerification: res.verification, verificationDestination: res.destination, emailCode: "" });
                        return;
                    }
                    // Clerk can stop half way and email a code. Local auth never
                    // did, so `user` would be null here and the form would
                    // silently reappear as though nothing had happened.
                    if (res.status === "needs_email_code") {
                        // Verification now has its own form, so the password
                        // can leave application state as soon as Clerk accepts it.
                        this._setAcct({
                            busy: false, error: "", password: "",
                            needsEmailCode: true, emailCode: "",
                        });
                        return;
                    }
                    // Signup answers with the recovery code, and it is answered
                    // exactly once. There is no reset email, so dropping it here
                    // — which is what this used to do — left the account with no
                    // way back in at all. Clerk sends "" and the panel that
                    // renders it is already conditional, so it just does not show.
                    this._setAcct({
                        user: res.user, busy: false, password: "", error: "",
                        recoveryCode: res.recovery_code ?? "", recoverySaved: false,
                    });
                    this._resumeAccountReturn(res.user, res.recovery_code);
                    this._loadKeys(res.user.id);
                })
                .catch((err) => this._setAcct({ busy: false, error: err.message }));
        };

        _acctPasskey = () => {
            if (this.state.acct.busy) return;
            this._setAcct({ busy: true, error: "" });
            accountApi.loginWithPasskey().then(res => {
                if (res.status === "needs_sign_in_code") {
                    this._setAcct({ busy: false, password: "", signInVerification: res.verification, verificationDestination: res.destination, emailCode: "" });
                    return;
                }
                this._setAcct({ user: res.user, busy: false, password: "", error: "" });
                this._resumeAccountReturn(res.user, res.recovery_code);
                this._loadKeys(res.user.id);
            }).catch(err => this._setAcct({ busy: false, error: err.message }));
        };

        _acctVerifySignIn = event => {
            event?.preventDefault();
            const code = this.state.acct.emailCode.trim();
            if (!code || this.state.acct.busy) return;
            this._setAcct({ busy: true, error: "" });
            accountApi.verifySignIn(code).then(res => {
                if (!res.user) throw new Error("Verification is not complete. Try a new code.");
                this._setAcct({ user: res.user, busy: false, signInVerification: "", emailCode: "", password: "", error: "" });
                this._resumeAccountReturn(res.user, res.recovery_code);
                this._loadKeys(res.user.id);
            }).catch(err => this._setAcct({ busy: false, error: err.message }));
        };

        _acctResendCode = () => {
            if (this.state.acct.busy) return;
            this._setAcct({ busy: true, error: "" });
            const request = this.state.acct.signInVerification ? accountApi.resendSignInCode() : accountApi.resendSignUpCode();
            request.then(() => this._setAcct({ busy: false, emailCode: "" }))
                .catch(err => this._setAcct({ busy: false, error: err.message }));
        };

        /** Finish a Clerk sign-up with the code it emailed. */
        _acctVerifyEmail = (event) => {
            if (event && event.preventDefault) event.preventDefault();
            const code = (this.state.acct.emailCode || "").trim();
            if (!code || this.state.acct.busy) return;
            this._setAcct({ busy: true, error: "" });
            accountApi.verifyEmailCode(code)
                .then(({ user }) => {
                    this._setAcct({
                        user, busy: false, error: "", needsEmailCode: false,
                        emailCode: "", recoveryCode: "", recoverySaved: false,
                        password: "",
                    });
                    this._resumeAccountReturn(user);
                    this._loadKeys(user.id);
                })
                .catch((err) => this._setAcct({ busy: false, error: err.message }));
        };

        /**
         * Reset a password. Two very different flows behind one submit:
         *
         * - Local auth: one call with the recovery code issued at signup.
         * - Clerk: stage one emails a code, stage two redeems it. Clerk has no
         *   `recover` — calling it would throw — so the branch is not cosmetic.
         *   `finishPasswordReset` activates the session, so success here IS a
         *   sign-in, not a return to the form.
         */
        _acctRecover = (event) => {
            if (event && event.preventDefault) event.preventDefault();
            const { email, recoveryInput, password, resetEmailSent } = this.state.acct;
            if (this.state.acct.busy) return;
            this._setAcct({ busy: true, error: "" });
            if (EMAIL_RESET && !resetEmailSent) {
                accountApi.startPasswordReset(email)
                    .then(() => this._setAcct({ busy: false, resetEmailSent: true, error: "" }))
                    .catch((err) => this._setAcct({ busy: false, error: err.message }));
                return;
            }
            if (EMAIL_RESET) {
                accountApi.finishPasswordReset(recoveryInput, password)
                    .then((res) => {
                        if (res.status === "needs_sign_in_code") {
                            this._setAcct({
                                busy: false, password: "", recoveryInput: "", error: "",
                                mode: "signin", resetEmailSent: false, emailCode: "",
                                signInVerification: res.verification, verificationDestination: res.destination,
                            });
                            return;
                        }
                        this._setAcct({
                            busy: false, password: "", recoveryInput: "", error: "",
                            mode: "signin", resetEmailSent: false, user: res.user,
                        });
                        this._resumeAccountReturn(res.user, res.recovery_code);
                        this._loadKeys(res.user.id);
                    })
                    .catch((err) => this._setAcct({ busy: false, error: err.message }));
                return;
            }
            accountApi.recover(email, recoveryInput, password)
                .then(({ recovery_code }) => this._setAcct({
                    busy: false, password: "", recoveryInput: "", error: "",
                    mode: "signin", recoveryCode: recovery_code, recoverySaved: false,
                    user: null, keys: [], freshKey: "", freshKeyCopied: false,
                }))
                .catch((err) => this._setAcct({ busy: false, error: err.message }));
        };

        _acctCopyRecovery = () => {
            const code = this.state.acct.recoveryCode;
            if (!code || !navigator.clipboard) return;
            navigator.clipboard.writeText(code)
                .then(() => this._setAcct({ recoverySaved: true }))
                .catch(() => { /* the code is on screen either way */ });
        };

        /** Dismiss the panel. Only reachable once the code has been shown. */
        _acctAckRecovery = () => { this._setAcct({ recoveryCode: "", recoverySaved: true }); this._resumeAccountReturn(this.state.acct.user); };

        _acctDownloadRecovery = () => {
            const { recoveryCode, user } = this.state.acct;
            if (!recoveryCode) return;
            downloadRecoveryCode(recoveryCode, user ? user.email : "");
            this._setAcct({ recoverySaved: true });
        };

        /** Open and close the "replace my code" form. */
        _acctToggleRotate = () => this._setAcct({
            rotating: !this.state.acct.rotating, rotatePassword: "", error: "",
        });
        _acctSetRotatePassword = (e) => this._setAcct({ rotatePassword: e.target.value, error: "" });

        /** Mint a fresh code for someone already signed in. */
        _acctRotate = (event) => {
            if (event && event.preventDefault) event.preventDefault();
            const { rotatePassword } = this.state.acct;
            this._setAcct({ busy: true, error: "" });
            accountApi.rotateRecovery(rotatePassword)
                .then(({ recovery_code }) => this._setAcct({
                    busy: false, rotating: false, rotatePassword: "", error: "",
                    recoveryCode: recovery_code, recoverySaved: false,
                }))
                .catch((err) => this._setAcct({ busy: false, error: err.message }));
        };

        _acctNewKey = () => {
            if (this._keyRequest || this.state.acct.busy || this.state.acct.freshKey) return;
            this._keyRequest = true;
            this._keysRequestId = (this._keysRequestId || 0) + 1;
            this._setAcct({ busy: true, keysLoading: false, error: "" });
            accountApi.createKey(defaultKeyLabel(this.state.acct.keys))
                .then(({ key, record }) => this._setAcct(a => ({ freshKey: key, freshKeyCopied: false, keys: [record, ...a.keys] })))
                .catch((err) => this._setAcct({ error: err.message }))
                .finally(() => { this._keyRequest = false; this._setAcct({ busy: false }); });
        };

        _acctCopyKey = () => {
            const key = this.state.acct.freshKey;
            if (!key) return;
            if (!navigator.clipboard) { this._setAcct({ error: "Copy is unavailable. Select the key and copy it manually." }); return; }
            navigator.clipboard.writeText(key)
                .then(() => this._setAcct({ freshKeyCopied: true, error: "" }))
                .catch(() => this._setAcct({ error: "Copy is unavailable. Select the key and copy it manually." }));
        };

        _acctAckKey = () => this._setAcct({ freshKey: "", freshKeyCopied: false });

        _acctRevoke = (keyId) => {
            if (this._keyRequest || this.state.acct.busy || this.state.acct.keys.find(k => k.key_id === keyId)?.revoked) return;
            this._keyRequest = true;
            this._keysRequestId = (this._keysRequestId || 0) + 1;
            this._setAcct({ busy: true, keysLoading: false, error: "" });
            accountApi.revokeKey(keyId)
                .then(() => this._setAcct(a => ({ keys: a.keys.map(k => k.key_id === keyId ? { ...k, revoked: true } : k) })))
                .catch((err) => this._setAcct({ error: err.message }))
                .finally(() => { this._keyRequest = false; this._setAcct({ busy: false }); });
        };

        // Social sign-in. accountApi.signInWithSocial redirects the tab to the
        // provider when Clerk is configured, and rejects with a plain message
        // on the local-auth build — where SOCIAL_SIGN_IN is empty and no skin
        // renders the buttons in the first place.
        _acctSocial = (provider) => {
            this._setAcct({ busy: true, error: "" });
            accountApi.signInWithSocial(provider)
                .catch((err) => this._setAcct({ busy: false, error: err.message }));
        };

        _acctSignOut = () => {
            if (this.state.acct.busy) return;
            this._setAcct({ busy: true, error: "" });
            accountApi.logout()
                .then(() => {
                    rememberAccountHint(false);
                    clearAccountReturn();
                    this._keysRequestId = (this._keysRequestId || 0) + 1;
                    this._setAcct({ ...initialAccountState, accountHint: false, resolved: true });
                })
                .catch(() => this._setAcct({ busy: false, error: "You could not be signed out. Check your connection and try again." }));
        };

        _acctDelete = () => {
            if (this.state.acct.busy) return;
            if (!this.state.acct.confirmingDelete) {
                this._setAcct({ confirmingDelete: true });
                return;
            }
            this._setAcct({ busy: true, error: "" });
            accountApi.deleteAccount()
                .then(() => {
                    rememberAccountHint(false);
                    clearAccountReturn();
                    this._keysRequestId = (this._keysRequestId || 0) + 1;
                    this._setAcct({ ...initialAccountState, accountHint: false, resolved: true });
                })
                .catch((err) => this._setAcct({ busy: false, error: err.message, confirmingDelete: false }));
        };

        _acctGo = (e) => {
            if (e && e.preventDefault) e.preventDefault();
            config.navigate();
        };

        /**
         * The design's router does not know this route and would title it 404.
         *
         * The three designs name this differently — Aurora and Structured have
         * `titleFor(route, param)` returning a string, Carbon has
         * `setTitle(route, sub)` writing document.title itself — so both are
         * covered rather than assuming one shape.
         */
        _acctTitle() {
            const path = accountPathForLocation();
            const title = path === "/account/settings" ? "Account settings" : path === "/account/keys" && this.state.acct.user ? "API keys" : this.state.acct.user ? "Account" : this.state.acct.mode === "signup" ? "Create an account" : this.state.acct.mode === "recover" ? "Reset your password" : "Sign in";
            return title + " — PrivaTools";
        }

        titleFor(route, param) {
            if (this._isAccountActive()) return this._acctTitle();
            return super.titleFor ? super.titleFor(route, param) : document.title;
        }

        setTitle(route, sub) {
            if (this._isAccountActive()) {
                try { document.title = this._acctTitle(); } catch (e) { /* SSR */ }
                return;
            }
            if (super.setTitle) super.setTitle(route, sub);
        }

        renderVals() {
            const v = super.renderVals();
            const a = this.state.acct;
            const active = this._isAccountActive();
            const signedIn = Boolean(a.user);
            const p = config.palette;

            const item = config.navItem({
                label: signedIn || a.accountHint ? "Account" : "Sign in",
                icon: signedIn ? "account_circle" : "login",
                onClick: this._acctGo,
                active,
            });

            const nav = config.injectNav
                ? config.injectNav(v, item)
                : { [config.navKey]: mergeNavItem(v[config.navKey] ?? [], item) };

            return {
                ...v,
                ...nav,
                // Whatever the theme's own router resolved for this unknown
                // path has to be switched off, or its page renders underneath
                // ours. Usually that is the 404 — but Structured's route table
                // treats "/" as a prefix pattern, so every unmatched path
                // resolves to `home` instead.
                ...(active
                    ? Object.fromEntries((config.suppressFlags ?? ["is404"]).map((f) => [f, false]))
                    : {}),

                isAccount: active,
                isAccountSettings: active && accountPathForLocation() === "/account/settings",
                isAccountKeys: active && accountPathForLocation() === "/account/keys",
                acctUser: a.user,
                acctNavigationSignedIn: signedIn || a.accountHint,
                acctSettingsHref: "/account/settings",
                acctKeysHref: "/account/keys",
                acctTitle: signedIn ? "Account" : (
                    a.mode === "signup" ? "Create an account"
                        : a.mode === "recover" ? "Reset your password" : "Sign in"),
                acctLede: signedIn
                    ? "Manage the API keys issued to this account."
                    : "Only needed for the developer API. Every tool works without one.",

                acctSignedOut: !signedIn,
                acctSignedIn: signedIn,

                acctEmail: a.email,
                acctPassword: a.password,
                acctSetEmail: (e) => this._setAcct({ email: e.target.value, error: "" }),
                acctSetPassword: (e) => this._setAcct({ password: e.target.value, error: "" }),
                acctSubmit: a.needsEmailCode ? this._acctVerifyEmail : this._acctSubmit,
                acctBusy: a.busy,
                acctBusyOpacity: a.busy ? ".6" : "1",
                acctSubmitLabel: a.busy ? "Working…" : (
                    a.needsEmailCode ? "Verify email"
                        : a.mode === "signup" ? "Create account"
                            : a.mode === "recover" ? "Reset password" : "Sign in"),
                acctPasswordLabel: a.mode === "recover" ? "New password" : "Password",
                acctPwAutocomplete: a.mode === "signin" ? "current-password" : "new-password",
                acctHintD: (a.mode === "signup" && !a.needsEmailCode) ? "block" : "none",
                acctPasswordHint: `At least ${MIN_PASSWORD_LENGTH} characters. Length is what makes a password strong.`,
                acctCopyStorage: ACCOUNT_COPY.storage,
                acctError: a.error,
                acctErrD: a.error ? "block" : "none",

                acctShowSignIn: () => this._acctChooseMode("signin"),
                acctShowSignUp: () => this._acctChooseMode("signup"),
                acctSignInBd: a.mode === "signin" ? p.accent : p.line,
                acctSignInBg: a.mode === "signin" ? p.accentSoft : "transparent",
                acctSignInFg: a.mode === "signin" ? p.accent : p.dim,
                acctSignUpBd: a.mode === "signup" ? p.accent : p.line,
                acctSignUpBg: a.mode === "signup" ? p.accentSoft : "transparent",
                acctSignUpFg: a.mode === "signup" ? p.accent : p.dim,

                acctEmailShown: a.user ? a.user.email : "",
                acctSignOut: this._acctSignOut,
                acctDelete: this._acctDelete,
                acctDeleteLabel: a.confirmingDelete ? "Press again to delete for good" : "Delete account",

                // The code is shown once, and the panel deliberately stands in
                // front of everything else until it is acknowledged — a code
                // scrolled past is an account that will eventually be lost.
                acctRecoveryCode: a.recoveryCode,
                acctRecoveryD: a.recoveryCode ? "block" : "none",
                acctBodyD: a.recoveryCode ? "none" : "block",
                acctCopyRecovery: this._acctCopyRecovery,
                acctCopyLabel: a.recoverySaved ? "Copied" : "Copy",
                acctAckRecovery: this._acctAckRecovery,
                acctDownloadRecovery: this._acctDownloadRecovery,

                // Replacing a mislaid code, from inside a signed-in session.
                acctRotating: a.rotating,
                acctRotateFormD: a.rotating ? "block" : "none",
                acctRotateOpenD: a.rotating ? "none" : "block",
                acctToggleRotate: this._acctToggleRotate,
                acctRotatePassword: a.rotatePassword,
                acctSetRotatePassword: this._acctSetRotatePassword,
                acctRotateSubmit: this._acctRotate,
                acctRotateLabel: a.busy ? "Working…" : "Generate",
                acctRecoveryNudgeD: a.recoverySaved ? "none" : "block",

                // The email-code step reuses the recovery-code input rather than
                // adding a field. The skins' markup comes from their design
                // sources and cannot grow one, but this input is already the
                // right shape — a short code, one-time-code autocomplete, in
                // the same form — so it is retargeted instead of duplicated.
                acctRecoverD: (a.mode === "recover" || a.needsEmailCode) ? "block" : "none",
                acctCredsD: a.mode === "recover" ? "none" : "block",
                acctCodeLabel: a.needsEmailCode ? "Emailed code" : "Recovery code",
                acctRecoveryInput: a.needsEmailCode ? a.emailCode : a.recoveryInput,
                acctSetRecoveryInput: (e) => this._setAcct(
                    a.needsEmailCode
                        ? { emailCode: e.target.value, error: "" }
                        : { recoveryInput: e.target.value, error: "" },
                ),
                acctRecoverSubmit: this._acctRecover,
                acctShowRecover: () => this._setAcct({ mode: "recover", error: "", password: "", recoveryInput: "", emailCode: "", resetEmailSent: false }),
                acctRecoverLabel: a.busy ? "Working…" : "Reset password",
                acctVerifyEmail: this._acctVerifyEmail,

                acctNewKey: this._acctNewKey,
                acctNewKeyValue: a.freshKey,
                acctNewKeyD: a.freshKey ? "block" : "none",
                acctNoKeysD: a.keys.length === 0 ? "block" : "none",
                acctKeys: a.keys.map((k) => ({
                    label: k.label,
                    labelColor: k.revoked ? p.faint : p.text,
                    meta: describeKey(k),
                    revoked: k.revoked,
                    revokeD: k.revoked ? "none" : "inline-flex",
                    revoke: () => this._acctRevoke(k.key_id),
                })),
            };
        }
    };
}
