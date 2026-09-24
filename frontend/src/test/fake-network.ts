/**
 * A scripted network for tests of how long pages wait on the server.
 *
 * `installNetwork` stubs both `fetch` and `XMLHttpRequest` with the same
 * timeline, so a test states what the connection does (how long the upload
 * takes, when the answer comes, whether it stalls) and holds whichever
 * transport lib/api.ts uses. Drive it with Vitest's fake timers.
 *
 * The XMLHttpRequest stand-in follows the parts of the standard lib/api.ts
 * relies on: upload `progress` events while the body is sent, upload `load`
 * once it has gone, `readystatechange` as the answer arrives, the `timeout`
 * attribute (a limit on the whole request, counted from `send`), and `abort`.
 */
import { Blob as NodeBlob } from "node:buffer";
import { vi } from "vitest";

export interface Script {
    /** How long the body takes to send. Progress is reported every second. */
    uploadMs: number;
    /** The connection dies this far into the upload: nothing more is sent or answered. */
    stallAfterMs?: number;
    /** The request fails this far into the upload with a network error (status 0),
     *  as a dropped connection does, or an answer the page may not read. */
    failAfterMs?: number;
    /** From the last byte sent to the answer's headers. Leave out to never answer. */
    answerAfterMs?: number;
    /** How long the answer's body takes to arrive, reported every second. */
    downloadMs?: number;
    /** The answer's body stops arriving this far into the download. */
    downloadStallAfterMs?: number;
    status?: number;
    body?: string;
    headers?: Record<string, string>;
}

export interface SentRequest {
    transport: "fetch" | "xhr";
    url: string;
    body: unknown;
    /** Set once the page has aborted it: abort(), or the fetch signal. */
    aborted?: boolean;
}

type Handler = ((event: ProgressLike) => void) | null;
interface ProgressLike { lengthComputable: boolean; loaded: number; total: number }

/** How many bytes a request body would send: its files plus its text fields. */
function bodySize(body: unknown): number {
    if (typeof body === "string") return body.length;
    if (!(body instanceof FormData)) return 0;
    let size = 0;
    for (const value of body.values()) size += typeof value === "string" ? value.length : value.size;
    return size;
}

export function installNetwork(script: Script | ((index: number) => Script)) {
    const requests: SentRequest[] = [];
    const scriptFor = (index: number) => typeof script === "function" ? script(index) : script;

    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const index = requests.length;
        const request: SentRequest = { transport: "fetch", url: String(input), body: init?.body };
        requests.push(request);
        const s = scriptFor(index);
        return new Promise<Response>((resolve, reject) => {
            const signal = init?.signal ?? undefined;
            let timer: ReturnType<typeof setTimeout> | undefined;
            const onAbort = () => {
                clearTimeout(timer);
                request.aborted = true;
                reject(signal?.reason ?? new DOMException("Aborted", "AbortError"));
            };
            if (signal?.aborted) { onAbort(); return; }
            signal?.addEventListener("abort", onAbort, { once: true });
            if (s.failAfterMs !== undefined) {
                timer = setTimeout(() => {
                    signal?.removeEventListener("abort", onAbort);
                    reject(new TypeError("Failed to fetch"));
                }, s.failAfterMs);
                return;
            }
            // fetch() resolves once the headers are in; a dead connection never answers.
            if (s.stallAfterMs === undefined && s.answerAfterMs !== undefined) {
                timer = setTimeout(() => {
                    signal?.removeEventListener("abort", onAbort);
                    resolve(new Response(s.body ?? "ok", { status: s.status ?? 200, headers: s.headers }));
                }, s.uploadMs + s.answerAfterMs);
            }
        });
    });

    class FakeUpload {
        onprogress: Handler = null;
        onload: Handler = null;
        onloadend: Handler = null;
        onabort: Handler = null;
        onerror: Handler = null;
    }

    class FakeXhr {
        readonly upload = new FakeUpload();
        readyState = 0;
        status = 0;
        response: Blob | null = null;
        responseType = "";
        timeout = 0;
        onreadystatechange: Handler = null;
        onprogress: Handler = null;
        onload: Handler = null;
        onerror: Handler = null;
        onabort: Handler = null;
        ontimeout: Handler = null;
        onloadend: Handler = null;
        private url = "";
        private request: SentRequest | null = null;
        private headerText = "";
        private uploadDone = false;
        private done = false;
        private timers: ReturnType<typeof setTimeout>[] = [];

        open(_method: string, url: string) { this.url = url; this.readyState = 1; }
        setRequestHeader() { /* not used by the helpers */ }
        getAllResponseHeaders() { return this.headerText; }

        send(body?: unknown) {
            const index = requests.length;
            this.request = { transport: "xhr", url: this.url, body };
            requests.push(this.request);
            const s = scriptFor(index);
            const total = bodySize(body);
            // A request's own `timeout` attribute limits the whole request, upload included.
            if (this.timeout > 0) this.later(this.timeout, () => this.end("timeout"));
            const sending = s.failAfterMs ?? s.stallAfterMs ?? s.uploadMs;
            for (let t = 1000; t <= sending; t += 1000) {
                this.later(t, () => this.progress(this.upload.onprogress, Math.min(total, Math.round((total * t) / s.uploadMs)), total));
            }
            if (s.failAfterMs !== undefined) {
                this.later(s.failAfterMs, () => this.end("error"));
                return;
            }
            if (s.stallAfterMs !== undefined) return;
            this.later(s.uploadMs, () => {
                this.progress(this.upload.onprogress, total, total);
                this.uploadDone = true;
                this.upload.onload?.(this.event(total, total));
                this.upload.onloadend?.(this.event(total, total));
            });
            if (s.answerAfterMs === undefined) return;
            const answeredAt = s.uploadMs + s.answerAfterMs;
            const body_ = s.body ?? "ok";
            this.later(answeredAt, () => {
                this.status = s.status ?? 200;
                this.headerText = Object.entries({ "content-type": "text/plain", ...s.headers })
                    .map(([name, value]) => `${name}: ${value}\r\n`).join("");
                this.state(2);
                this.state(3);
            });
            const downloading = s.downloadStallAfterMs ?? s.downloadMs ?? 0;
            for (let t = 1000; t <= downloading; t += 1000) {
                this.later(answeredAt + t, () => this.progress(this.onprogress, Math.min(body_.length, Math.round((body_.length * t) / (s.downloadMs ?? t))), body_.length));
            }
            if (s.downloadStallAfterMs !== undefined) return;
            this.later(answeredAt + (s.downloadMs ?? 0), () => {
                this.progress(this.onprogress, body_.length, body_.length);
                // A browser's XMLHttpRequest hands back a Blob its own Response
                // accepts. Here Response is Node's, which reads only Node's Blob:
                // given jsdom's it would read the text "[object Blob]".
                this.response = new NodeBlob([body_], { type: s.headers?.["content-type"] ?? "text/plain" }) as unknown as Blob;
                this.end("load");
            });
        }

        abort() {
            if (this.done) return;
            if (this.request) this.request.aborted = true;
            this.end("abort");
        }

        private end(kind: "load" | "abort" | "timeout" | "error") {
            if (this.done) return;
            this.done = true;
            for (const timer of this.timers) clearTimeout(timer);
            if (kind !== "load") this.status = 0;
            this.state(4);
            if (kind !== "load" && !this.uploadDone) {
                const handler = kind === "abort" ? this.upload.onabort : kind === "error" ? this.upload.onerror : null;
                handler?.(this.event(0, 0));
                this.upload.onloadend?.(this.event(0, 0));
            }
            const handler = { load: this.onload, abort: this.onabort, timeout: this.ontimeout, error: this.onerror }[kind];
            handler?.(this.event(0, 0));
            this.onloadend?.(this.event(0, 0));
        }

        private state(readyState: number) {
            this.readyState = readyState;
            this.onreadystatechange?.(this.event(0, 0));
        }

        private progress(handler: Handler, loaded: number, total: number) {
            handler?.(this.event(loaded, total));
        }

        private event(loaded: number, total: number): ProgressLike {
            return { lengthComputable: total > 0, loaded, total };
        }

        private later(ms: number, run: () => void) {
            this.timers.push(setTimeout(() => { if (!this.done) run(); }, ms));
        }
    }

    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("XMLHttpRequest", FakeXhr);
    return { requests, fetch: fetchMock };
}

/** A file of `bytes` without allocating them: only `size` is read on the way out. */
export function sizedFile(name: string, bytes: number, type = "application/pdf"): File {
    const file = new File(["%PDF-1.7 synthetic"], name, { type });
    Object.defineProperty(file, "size", { value: bytes });
    return file;
}

export const SECOND = 1000;
export const MINUTE = 60 * SECOND;
export const MB = 1024 * 1024;
