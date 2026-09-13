import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowUpRight, Cloud, CloudOff, Download, Loader2, Radio, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { useOnline } from "@/hooks/useOnline";
import { apiUrl } from "@/lib/api";
import { StudioPage, StudioHeader } from "@/skins/experience/Studio";
import "@/skins/experience/secondary-pages.css";

type Probe = "checking" | "up" | "down";

export default function StatusPage() {
    const online = useOnline();
    const [server, setServer] = useState<Probe>("checking");
    const [latency, setLatency] = useState<number | null>(null);
    const [swReady, setSwReady] = useState(false);
    const [checkedAt, setCheckedAt] = useState<Date | null>(null);
    const request = useRef<AbortController | null>(null);
    const probe = useCallback(() => {
        request.current?.abort();
        const ctl = new AbortController(); request.current = ctl;
        setServer("checking");
        const started = performance.now();
        const timer = window.setTimeout(() => ctl.abort(), 8000);
        void fetch(apiUrl("/health"), { signal: ctl.signal, cache: "no-store" })
            .then(res => { if (request.current !== ctl) return; setServer(res.ok ? "up" : "down"); setLatency(res.ok ? Math.round(performance.now() - started) : null); })
            .catch(() => { if (request.current === ctl) { setServer("down"); setLatency(null); } })
            .finally(() => { window.clearTimeout(timer); if (request.current === ctl) setCheckedAt(new Date()); });
    }, []);
    useEffect(() => { probe(); return () => { const current = request.current; request.current = null; current?.abort(); }; }, [probe, online]);
    useEffect(() => {
        if (!("serviceWorker" in navigator)) return;
        let alive = true;
        void navigator.serviceWorker.getRegistration().then(r => { if (alive) setSwReady(Boolean(r?.active)); }).catch(() => {});
        return () => { alive = false; };
    }, []);
    const rows = [
        { icon: online ? Wifi : WifiOff, label: "Your connection", value: online ? "Online" : "Offline", detail: online ? "This browser reports a network connection." : "Your browser reports no network. Previously cached browser tools may still work.", tone: online ? "ok" : "bad" },
        { icon: server === "up" ? Cloud : server === "down" ? CloudOff : Loader2, label: "Server tools", value: server === "up" ? "Reachable" : server === "down" ? "Unreachable" : "Checking…", detail: server === "up" ? `The health endpoint responded${latency !== null ? ` in ${latency} ms` : ""}. Individual tools may have additional dependencies.` : server === "down" ? "We couldn’t reach the server. Tools that send files there may be unavailable." : "Asking the server whether it is available.", tone: server === "up" ? "ok" : server === "down" ? "bad" : "idle" },
        { icon: Download, label: "Offline worker", value: swReady ? "Active" : "Not active", detail: swReady ? "A service worker is active. Offline availability depends on which app and tool assets have been cached." : "No active service worker was found. Revisit online or install the app to enable supported offline features.", tone: swReady ? "ok" : "idle" },
    ] as const;
    return <StudioPage className="pt-status-page">
        <StudioHeader kicker={<><Radio size={16} /> Service status</>} title={<>How’s everything <br />running?</>} description="A look at what this browser can reach, right now. These are live checks, not a stored uptime history." visual={<div className={`pt-status-route-art is-${server}`}><Radio size={44} strokeWidth={1.3} /><span>Checking in <br />on your workspace.</span></div>} />
        <section className={`pt-status-observatory is-${server}`} aria-labelledby="status-overview-title"><div className="pt-status-signal" aria-hidden="true"><span /><Radio size={38} strokeWidth={1.3} /></div><div><p className="pt-workspace-caption">From your browser</p><h2 id="status-overview-title">{server === "checking" ? "Taking a quick look…" : server === "up" && online ? "You’re connected." : "Something needs a moment."}</h2><p>{server === "checking" ? "Checking the PrivaTools health endpoint." : server === "up" ? "The server is responding. Your workspace is ready to explore." : "Try checking again, or visit Support if the problem continues."}</p></div><button className="pt-studio-button is-secondary" onClick={probe} disabled={server === "checking"}><RefreshCw size={16} className={server === "checking" ? "animate-spin" : ""} />Check again</button></section>
        <div className="pt-status-checks">{rows.map(row => <section key={row.label} className={`pt-status-check is-${row.tone}`}><div className="pt-status-check-top"><row.icon size={27} strokeWidth={1.5} className={row.value === "Checking…" ? "animate-spin" : ""} aria-hidden="true" /><span><i />{row.value}</span></div><h2>{row.label}</h2><p>{row.detail}</p></section>)}</div>
        <div className="pt-status-footer"><p role="status">{checkedAt ? `Last checked ${checkedAt.toLocaleTimeString()}. Results are specific to this device and connection.` : "Waiting for the first server check."}</p><a className="pt-studio-link" href="/support">Get a hand <ArrowUpRight size={16} /></a></div>
    </StudioPage>;
}
