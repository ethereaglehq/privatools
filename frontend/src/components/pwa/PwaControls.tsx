import { useState, useSyncExternalStore } from "react";
import { Check, Download, HardDrive, Loader2, RefreshCw, Share2, Smartphone, Wifi, WifiOff, X } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { applyPwaUpdate, checkPwaUpdate, getPwaState, installPwa, subscribePwaState } from "@/lib/sw-register";
import "./pwa.css";

/** Mount once in the app shell. Browser install availability is capability driven. */
export function PwaControls() {
    const state = useSyncExternalStore(subscribePwaState, getPwaState, getPwaState);
    const [open, setOpen] = useState(false);
    const [confirmUpdate, setConfirmUpdate] = useState(false);
    const [dismissedUpdate, setDismissedUpdate] = useState(false);
    const [dismissedOffline, setDismissedOffline] = useState(false);
    const [checking, setChecking] = useState(false);
    const [checked, setChecked] = useState(false);
    const iOS = typeof navigator !== "undefined" && (/iPad|iPhone|iPod/.test(navigator.userAgent)
        || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1));
    const openUpdate = () => { setOpen(true); setConfirmUpdate(true); };
    const check = async () => {
        setChecking(true);
        await checkPwaUpdate();
        setChecking(false);
        setChecked(true);
    };
    return <>
        <Dialog open={open} onOpenChange={(value) => { setOpen(value); if (!value) setConfirmUpdate(false); }}>
            <DialogTrigger asChild>
                <button className="pwa-trigger" type="button" title="Install PrivaTools and offline availability">
                    {state.installed ? <Check size={16} /> : <Smartphone size={16} />}
                    <span>{state.canInstall ? "Install app" : "App & offline"}</span>
                    {state.updateAvailable && <i className="pwa-update-dot" aria-label="Update available" />}
                </button>
            </DialogTrigger>
            <DialogContent className="pwa-dialog">
                <div className="pwa-dialog-emblem"><Smartphone size={27} strokeWidth={1.7} /></div>
                <DialogTitle className="pwa-title">{confirmUpdate ? "A fresh version is ready" : state.installed ? "PrivaTools, at home on your device" : "Your tools, one tap away"}</DialogTitle>
                <DialogDescription className="pwa-description">
                    {confirmUpdate ? "Updating reloads this tab. Download your results and finish any active tasks first; files currently open in a tool will reset." : "Keep PrivaTools in your dock or home screen. Your choice of Air or Play comes with you."}
                </DialogDescription>
                {confirmUpdate ? <div className="pwa-confirm-actions">
                    <button type="button" className="pwa-action pwa-primary" disabled={state.updating || !state.updateAvailable} onClick={applyPwaUpdate}>
                        {state.updating ? <Loader2 size={17} className="pwa-spinner" /> : <RefreshCw size={17} />}
                        {state.updating ? "Updating…" : "Update and reload"}
                    </button>
                    <button type="button" className="pwa-action" disabled={state.updating} onClick={() => { setOpen(false); setConfirmUpdate(false); }}>Keep working</button>
                </div> : <>
                    <div className="pwa-install-section">
                        {state.installed ? <p className="pwa-installed"><Check size={18} /> Installed on this device</p>
                            : state.canInstall ? <button type="button" className="pwa-action pwa-primary" disabled={state.installing} onClick={() => void installPwa()}>
                                {state.installing ? <Loader2 className="pwa-spinner" size={18} /> : <Download size={18} />}
                                {state.installing ? "Opening install…" : "Install PrivaTools"}
                            </button>
                                : <div className="pwa-manual-install">
                                    <span>{iOS ? <Share2 size={20} /> : <Smartphone size={20} />}</span>
                                    <div><strong>{iOS ? "Add to your Home Screen" : "Install from your browser"}</strong>
                                        <p>{iOS ? "Open this site in Safari, tap Share, then Add to Home Screen. Enable Open as Web App if shown." : "Open your browser’s menu and look for Install app or Add to Home Screen. The option appears in browsers that support installation."}</p>
                                    </div>
                                </div>}
                    </div>
                    <div className="pwa-capabilities">
                        <div><span><HardDrive size={19} /></span><div><strong>{state.offlineReady ? "App shell saved on this device" : "Offline availability"}</strong><p>{state.offlineReady ? "Previously opened browser tools can be available offline. A tool’s additional resources may still need a connection." : state.supported ? "The app saves its interface after it loads. Open a browser tool while connected before relying on it offline." : "Offline setup runs on the published app in supported browsers. You can still use the current page while connected."}</p></div></div>
                        <div><span>{state.online ? <Wifi size={19} /> : <WifiOff size={19} />}</span><div><strong>{state.online ? "Connected" : "You’re offline"}</strong><p>Server processing, account access, remote AI providers, and model downloads require a connection. Installing the app does not change how a tool processes your files.</p></div></div>
                    </div>
                    {state.supported && <div className="pwa-update-row">
                        <div><strong>{state.updateAvailable ? "Update available" : "App updates"}</strong><p>{state.updateAvailable ? "Install when your work is finished." : checked ? "Update check requested. New versions appear here when ready." : "We’ll let you choose when to reload."}</p></div>
                        <button className="pwa-action" disabled={checking || !state.online} type="button" onClick={state.updateAvailable ? () => setConfirmUpdate(true) : () => void check()}>
                            {checking ? <Loader2 size={16} className="pwa-spinner" /> : <RefreshCw size={16} />}{state.updateAvailable ? "Review update" : checking ? "Checking…" : "Check"}
                        </button>
                    </div>}
                </>}
                {state.error && <p className="pwa-error" role="status">{state.error}</p>}
            </DialogContent>
        </Dialog>
        <div className="pwa-notice-stack" aria-live="polite">
            {!state.online && !dismissedOffline && <div className="pwa-notice">
                <WifiOff size={19} className="pwa-notice-icon" />
                <div><strong>You’re offline</strong><p>Previously opened browser tools may still work. Server tools need a connection.</p><button type="button" onClick={() => setOpen(true)}>View offline details</button></div>
                <button type="button" className="pwa-notice-close" aria-label="Dismiss offline message" onClick={() => setDismissedOffline(true)}><X size={16} /></button>
            </div>}
            {state.updateAvailable && !dismissedUpdate && <div className="pwa-notice">
                <RefreshCw size={19} className="pwa-notice-icon" />
                <div><strong>A new version is ready</strong><p>Your work can wait here until you’re ready to update.</p><button type="button" onClick={openUpdate}>Review update</button></div>
                <button type="button" className="pwa-notice-close" aria-label="Dismiss update message" onClick={() => setDismissedUpdate(true)}><X size={16} /></button>
            </div>}
        </div>
    </>;
}
