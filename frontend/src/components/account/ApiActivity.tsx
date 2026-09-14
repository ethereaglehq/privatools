import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { accountApi } from "@/skins/accountLogic";
import { apiActivitySchema, type ApiActivityData, type ActivityKey } from "@/lib/api-activity";
import "./api-activity.css";

export default function ApiActivity({ accountId, keyVersion = "" }: { accountId: string; keyVersion?: string }) {
    // Remounting on account changes prevents even a single render of the previous owner's metadata.
    return <ActivityContent key={accountId} keyVersion={keyVersion} />;
}

function ActivityContent({ keyVersion }: { keyVersion: string }) {
    const [filter, setFilter] = useState("");
    const [refresh, setRefresh] = useState(0);
    const [data, setData] = useState<ApiActivityData | null>(null);
    const [keys, setKeys] = useState<ActivityKey[]>([]);
    const [busy, setBusy] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => { setFilter(""); }, [keyVersion]);

    useEffect(() => {
        const controller = new AbortController();
        let timedOut = false;
        setBusy(true); setError(false); setData(null);
        const timer = window.setTimeout(() => { timedOut = true; controller.abort(); setError(true); setBusy(false); }, 15000);
        accountApi.apiActivity(filter || undefined, controller.signal).then(value => {
            if (controller.signal.aborted) return;
            const parsed = apiActivitySchema.parse(value);
            setData(parsed);
            if (!filter) setKeys(parsed.keys);
        }).catch(() => {
            if (!controller.signal.aborted || timedOut) setError(true);
        }).finally(() => {
            window.clearTimeout(timer);
            if (!controller.signal.aborted) setBusy(false);
        });
        return () => { window.clearTimeout(timer); controller.abort(); };
    }, [filter, refresh, keyVersion]);

    const requests = data?.days.reduce((total, day) => total + day.requests, 0) ?? 0;
    const failures = data?.days.reduce((total, day) => total + day.failed, 0) ?? 0;
    const average = requests ? data!.days.reduce((total, day) => total + day.avg_duration_ms * day.requests, 0) / requests : 0;

    return <section className="pt-api-activity" aria-labelledby="api-activity-title">
        <header className="pt-activity-heading">
            <div><p className="pt-workspace-caption">Your integrations</p><h2 id="api-activity-title">API usage & activity</h2><p>Current allowance and seven days of processing requests.</p></div>
            <button type="button" className="pt-studio-link" disabled={busy} onClick={() => setRefresh(value => value + 1)}><RefreshCw size={15} aria-hidden="true" />Refresh activity</button>
        </header>
        <label className="pt-activity-filter">Activity for<select value={filter} onChange={event => setFilter(event.target.value)}>
            <option value="">All your keys</option>
            {keys.map(key => <option key={key.key_id} value={key.key_id}>{key.label || key.key_id}{key.revoked ? " (revoked)" : ""}</option>)}
        </select></label>
        {busy && <p role="status">Loading API activity…</p>}
        {error && <p role="alert">Your API activity could not be loaded. Refresh to try again.</p>}
        {data && <>
            {data.keys.length === 0 ? <p>Create a key to start tracking API usage.</p> : <>
                <div className="pt-activity-allowances" aria-label="Today's allowance by key">{data.keys.map(key => <article key={key.key_id}>
                    <h3>{key.label || "API key"}{key.revoked && <small>Revoked</small>}</h3><code>{key.key_id}</code>
                    <p><strong>{key.units.used} / {key.units.limit} units</strong><span>{key.units.remaining} remaining</span></p>
                    <progress aria-label={`${key.label || key.key_id} daily units`} max={Math.max(1, key.units.limit)} value={Math.min(key.units.used, Math.max(1, key.units.limit))} />
                    <p><span>{mib(key.bytes.used)} / {mib(key.bytes.limit)} uploaded</span></p>
                </article>)}</div>
                <p className="pt-activity-note">Daily allowances reset {new Date(data.resets_at).toLocaleString()}. Upload usage includes multipart fields and boundaries.</p>
            </>}
            <dl className="pt-activity-totals"><div><dt>Requests · 7 days</dt><dd>{requests.toLocaleString()}</dd></div><div><dt>HTTP errors</dt><dd>{failures.toLocaleString()}</dd></div><div><dt>Average request time</dt><dd>{requests ? formatDuration(average) : "—"}</dd></div></dl>
            <p className="pt-activity-note">Counts describe HTTP requests, not completed conversions. A 202 means a background job was accepted; check its status for the final result. Key checks, job polling, downloads, and deletion are excluded.</p>
            <details className="pt-activity-daily"><summary>Daily breakdown · UTC</summary><div className="pt-activity-scroll" role="region" aria-label="Daily request breakdown" tabIndex={0}>
                <table aria-label="Daily API requests in UTC"><thead><tr><th scope="col">Date</th><th scope="col">Requests</th><th scope="col">HTTP successes</th><th scope="col">Errors</th><th scope="col">Average time</th></tr></thead><tbody>{data.days.map(day => <tr key={day.date}><th scope="row">{day.date}</th><td>{day.requests}</td><td>{day.succeeded}</td><td>{day.failed}</td><td>{day.requests ? formatDuration(day.avg_duration_ms) : "—"}</td></tr>)}</tbody></table>
            </div></details>
            <h3 className="pt-activity-recent-title">Recent requests</h3>
            {data.recent.length === 0 ? <p>No processing requests recorded yet. <a href="/api">Run a sample conversion</a> to get started.</p> : <div className="pt-activity-scroll" role="region" aria-label="Recent API requests" tabIndex={0}>
                <table aria-label="Recent API requests"><thead><tr><th scope="col">Operation & request ID</th><th scope="col">Key</th><th scope="col">Response</th><th scope="col">Time</th><th scope="col">When</th></tr></thead><tbody>{data.recent.map((item, index) => <tr key={`${item.request_id}-${index}`}>
                    <td><strong>{operationName(item.operation)}</strong><code>{item.request_id || "Unavailable"}</code></td><td>{keys.find(key => key.key_id === item.key_id)?.label || item.key_id}</td>
                    <td><span className={item.status_code >= 400 ? "pt-activity-error" : ""}>{item.status_code} · {responseLabel(item.status_code)}</span>{item.error_code && <code>{item.error_code}</code>}</td>
                    <td>{formatDuration(item.duration_ms)}</td><td><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></td>
                </tr>)}</tbody></table>
            </div>}
        </>}
        <p className="pt-activity-note">History stores request metadata for up to seven days, with at most 1,000 recent records per key and 100,000 across the service. This page shows the latest 50. File contents, filenames, API secrets, and raw error messages are never included. Recording is best effort and starts when this feature is enabled.</p>
    </section>;
}

function mib(value: number) { return `${(value / 1048576).toFixed(2)} MiB`; }
function formatDuration(value: number) { return value < 1000 ? `${Math.round(value)} ms` : `${(value / 1000).toFixed(2)} s`; }
function operationName(value: string) { return value.replace(/^v1_(get|post|put|patch|delete)_/, "").replace(/_/g, " "); }
function responseLabel(status: number) { return status === 202 ? "Accepted" : status < 300 ? "Success" : status < 400 ? "Redirect" : status === 429 ? "Limited" : "Error"; }
