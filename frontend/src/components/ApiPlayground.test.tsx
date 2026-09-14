import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ApiPlayground from "./ApiPlayground";
import { samplePdf } from "./api-playground-samples";

const key = "pk_PLAYGROUND_TEST_SECRET";
const usage = (units = 10, bytes = 1000, resets_at = "2026-09-15T00:00:00Z") => ({ key_id: "key-123", resets_at, units: { used: units, remaining: 500 - units }, bytes: { used: bytes } });
const json = (body: unknown, status = 200, headers: Record<string, string> = {}) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
const pdf = (body = samplePdf(1)) => new Response(body, { headers: { "Content-Type": "application/pdf", "X-Request-ID": "request-sample-123" } });
function mount() {
    const rendered = render(<ApiPlayground />);
    fireEvent.change(screen.getByLabelText("Playground API key"), { target: { value: key } });
    return rendered;
}
function start() { fireEvent.click(screen.getByRole("button", { name: "Run sample" })); }
function deferred<T>() {
    let resolve!: (value: T) => void;
    const promise = new Promise<T>(finish => { resolve = finish; });
    return { promise, resolve };
}
function readBlob(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = reject;
        reader.readAsText(blob);
    });
}
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe("API sample playground", () => {
    it("runs one real merge with sample files and displays its downloadable result and measured usage", async () => {
        const createUrl = vi.spyOn(URL, "createObjectURL");
        const store = vi.spyOn(Storage.prototype, "setItem");
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(pdf()).mockResolvedValueOnce(json(usage(11, 3000)));
        vi.stubGlobal("fetch", fetchMock);
        mount();
        expect(screen.getByText(/Each run uses your normal allowance: 1 unit/)).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "sample-1.pdf" })).toHaveAttribute("download", "sample-1.pdf");
        start();
        const download = await screen.findByRole("link", { name: "Download merged.pdf" });
        expect(download).toHaveAttribute("href", expect.stringContaining("blob:"));
        expect(download).toHaveAttribute("download", "merged.pdf");
        expect(screen.getByText("HTTP 200")).toBeInTheDocument();
        expect(screen.getByText("request-sample-123")).toBeInTheDocument();
        expect(screen.getByText("1 unit · 2,000 request bytes")).toBeInTheDocument();
        expect(screen.getByText("489 units remaining today.")).toBeInTheDocument();
        expect(fetchMock).toHaveBeenCalledTimes(3);
        expect(fetchMock.mock.calls.map(([url]) => url)).toEqual(["/api/v1/usage", "/api/v1/merge", "/api/v1/usage"]);
        const form = fetchMock.mock.calls[1][1].body as FormData;
        expect(form.getAll("files")).toHaveLength(2);
        expect((form.get("files") as File).name).toBe("sample-1.pdf");
        expect(await readBlob(form.get("files") as File)).toContain("PrivaTools API sample 1");
        for (const [url, options] of fetchMock.mock.calls) {
            expect(url).not.toContain(key);
            expect(options.headers).toEqual({ "X-API-Key": key });
            expect(options.credentials).toBe("omit");
            expect(options.redirect).toBe("error");
            expect(options.cache).toBe("no-store");
            expect(options.referrerPolicy).toBe("no-referrer");
        }
        expect(createUrl).toHaveBeenCalledTimes(3);
        expect(document.body.textContent).not.toContain(key);
        expect(screen.getByLabelText("Sample curl request")).toHaveTextContent("$PRIVATOOLS_API_KEY");
        expect(store).not.toHaveBeenCalled();
    });

    it("matches the compress request fields and safe copyable command", async () => {
        const writeText = vi.fn().mockResolvedValue(undefined);
        vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(pdf()).mockResolvedValueOnce(json(usage(11, 2200)));
        vi.stubGlobal("fetch", fetchMock);
        mount();
        fireEvent.change(screen.getByLabelText("Sample operation"), { target: { value: "compress" } });
        expect(screen.queryByRole("link", { name: "sample-2.pdf" })).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Copy sample request" }));
        expect(await screen.findByText("Copied sample request.")).toBeInTheDocument();
        const copied = writeText.mock.calls[0][0];
        expect(copied).toContain("/api/v1/compress");
        expect(copied).toContain("files=@sample-1.pdf;type=application/pdf");
        expect(copied).toContain("level=recommended");
        expect(copied).not.toContain(key);
        start();
        await screen.findByRole("link", { name: "Download compressed.pdf" });
        const form = fetchMock.mock.calls[1][1].body as FormData;
        expect(form.getAll("files")).toHaveLength(1);
        expect(form.get("level")).toBe("recommended");
    });

    it("allowlists and redacts text in the preview and JSON download", async () => {
        const createUrl = vi.spyOn(URL, "createObjectURL");
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(json({
            text: `Sample text ${key} <script>unsafe()</script>`, pages: [{ page: 1, text: `Page ${key}`, unknown: "PRIVATE" }, null],
            characters: 999, secret: key, unknown: "DO NOT DISPLAY",
        })).mockResolvedValueOnce(json(usage(15, 1800))));
        mount();
        fireEvent.change(screen.getByLabelText("Sample operation"), { target: { value: "pdf-to-text" } });
        expect(screen.getByText(/normal allowance: 5 units/)).toBeInTheDocument();
        start();
        await screen.findByRole("link", { name: "Download extracted-text.json" });
        expect(screen.getByText("Sample text [redacted] <script>unsafe()</script>")).toBeInTheDocument();
        expect(document.querySelector(".pt-playground-preview script")).toBeNull();
        const artifact = JSON.parse(await readBlob(createUrl.mock.calls.at(-1)![0] as Blob));
        expect(Object.keys(artifact)).toEqual(["text", "pages", "characters"]);
        expect(artifact.pages).toEqual([{ page: 1, text: "Page [redacted]" }]);
        expect(artifact.characters).toBe(artifact.text.length);
        expect(JSON.stringify(artifact)).not.toContain(key);
        expect(document.body.textContent).not.toContain("DO NOT DISPLAY");
    });

    it("shows safe error details, request ID and retry hints without reflecting credentials", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(json({
            code: "quota_exceeded", message: `Wait before using ${key}`, ignored: "PRIVATE",
        }, 429, { "X-Request-ID": `request-${key}`, "Retry-After": "60" })).mockResolvedValueOnce(json(usage())));
        mount(); start();
        expect(await screen.findByRole("alert")).toHaveTextContent("Wait before using [redacted] (quota_exceeded)");
        expect(screen.getByText("HTTP 429")).toBeInTheDocument();
        expect(screen.getByText("request-[redacted]")).toBeInTheDocument();
        expect(screen.getByText(/wait 60 seconds/)).toBeInTheDocument();
        expect(screen.getByText("0 units · 0 request bytes")).toBeInTheDocument();
        expect(screen.queryByRole("link", { name: /Download merged/ })).not.toBeInTheDocument();
        expect(document.body.textContent).not.toContain(key);
        expect(document.body.textContent).not.toContain("PRIVATE");
    });

    it.each(["before", "after", "rollover", "malformed"])("does not invent an allowance change when %s readings cannot be compared", async reason => {
        const before = reason === "before" ? json({}, 503) : json(reason === "malformed" ? { ...usage(), units: { used: "10", remaining: 490 } } : usage());
        const after = reason === "after" ? json({}, 503) : json(usage(11, 2000, reason === "rollover" ? "2026-09-16T00:00:00Z" : undefined));
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(before).mockResolvedValueOnce(pdf()).mockResolvedValueOnce(after));
        mount(); start();
        await screen.findByRole("link", { name: "Download merged.pdf" });
        expect(screen.getByText(/Usage change unavailable/)).toBeInTheDocument();
        expect(screen.queryByText(/1 unit ·/)).not.toBeInTheDocument();
    });

    it("clearing the key aborts in-flight work and ignores its late response", async () => {
        const pending = deferred<Response>();
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockReturnValueOnce(pending.promise);
        vi.stubGlobal("fetch", fetchMock);
        mount(); start();
        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
        const signal = fetchMock.mock.calls[1][1].signal;
        fireEvent.click(screen.getByRole("button", { name: "Clear playground key" }));
        expect(signal.aborted).toBe(true);
        await act(async () => pending.resolve(pdf()));
        expect(screen.getByLabelText("Playground API key")).toHaveValue("");
        expect(screen.getByRole("button", { name: "Run sample" })).toBeDisabled();
        expect(screen.queryByText("Request result")).not.toBeInTheDocument();
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("changing credentials while the first usage read is pending never submits with the old key", async () => {
        const pending = deferred<Response>();
        const fetchMock = vi.fn().mockReturnValueOnce(pending.promise);
        vi.stubGlobal("fetch", fetchMock);
        mount(); start();
        fireEvent.change(screen.getByLabelText("Playground API key"), { target: { value: "pk_REPLACEMENT" } });
        expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true);
        await act(async () => pending.resolve(json(usage())));
        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(screen.queryByText("Request result")).not.toBeInTheDocument();
    });

    it("does not publish a finished conversion after clearing during the last usage read", async () => {
        const pending = deferred<Response>();
        const createUrl = vi.spyOn(URL, "createObjectURL");
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(pdf()).mockReturnValueOnce(pending.promise);
        vi.stubGlobal("fetch", fetchMock);
        mount(); start();
        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
        fireEvent.click(screen.getByRole("button", { name: "Clear playground key" }));
        await act(async () => pending.resolve(json(usage(11, 2000))));
        expect(screen.queryByText("Request result")).not.toBeInTheDocument();
        expect(createUrl).toHaveBeenCalledTimes(2);
    });

    it("keeps one conversion active and allows stopping without retrying it", async () => {
        const pending = deferred<Response>();
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockReturnValueOnce(pending.promise);
        vi.stubGlobal("fetch", fetchMock);
        mount(); start();
        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
        expect(screen.getByRole("button", { name: "Running sample…" })).toBeDisabled();
        expect(screen.getByLabelText("Sample operation")).toBeDisabled();
        fireEvent.submit(screen.getByRole("button", { name: "Running sample…" }).closest("form")!);
        expect(fetchMock).toHaveBeenCalledTimes(2);
        fireEvent.click(screen.getByRole("button", { name: "Stop waiting" }));
        expect(screen.getByText(/Stopped waiting. The server may still finish/)).toBeInTheDocument();
        await act(async () => pending.resolve(pdf()));
        expect(screen.queryByText("Request result")).not.toBeInTheDocument();
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("revokes the result when it is cleared and sample URLs on unmount", async () => {
        const revoke = vi.spyOn(URL, "revokeObjectURL");
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(pdf()).mockResolvedValueOnce(json(usage(11, 2000))));
        const { unmount } = mount(); start();
        const link = await screen.findByRole("link", { name: "Download merged.pdf" });
        const url = link.getAttribute("href");
        fireEvent.click(screen.getByRole("button", { name: "Clear playground key" }));
        expect(revoke).toHaveBeenCalledWith(url);
        expect(screen.queryByText("Request result")).not.toBeInTheDocument();
        unmount();
        expect(revoke).toHaveBeenCalledTimes(3);
    });

    it("aborts on unmount and never allocates a late result URL", async () => {
        const pending = deferred<Response>();
        const createUrl = vi.spyOn(URL, "createObjectURL");
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockReturnValueOnce(pending.promise);
        vi.stubGlobal("fetch", fetchMock);
        const { unmount } = mount(); start();
        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
        unmount();
        expect(fetchMock.mock.calls[1][1].signal.aborted).toBe(true);
        await act(async () => pending.resolve(pdf()));
        expect(createUrl).toHaveBeenCalledTimes(2);
    });

    it("bounds the wait and explains uncertain server completion after timeout", async () => {
        vi.useFakeTimers();
        const fetchMock = vi.fn().mockResolvedValueOnce(json(usage())).mockImplementationOnce((_url, { signal }) => new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")))));
        vi.stubGlobal("fetch", fetchMock);
        mount(); start();
        await act(async () => { await vi.advanceTimersByTimeAsync(10); });
        expect(fetchMock).toHaveBeenCalledTimes(2);
        await act(async () => { await vi.advanceTimersByTimeAsync(120_000); });
        expect(screen.getByRole("alert")).toHaveTextContent("Stopped waiting after two minutes");
        expect(screen.getByRole("button", { name: "Run sample" })).toBeEnabled();
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it.each(["html", "oversize", "credential"])("does not offer an unsafe %s response as a PDF download", async kind => {
        const output = kind === "html" ? new Response(`<html>${key}</html>`, { headers: { "Content-Type": "text/html" } })
            : kind === "oversize" ? new Response("%PDF-", { headers: { "Content-Type": "application/pdf", "Content-Length": "3000000" } }) : pdf(`${samplePdf(1)}${key}`);
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(output).mockResolvedValueOnce(json(usage(11, 2000))));
        mount(); start();
        await screen.findByRole("alert");
        expect(screen.queryByRole("link", { name: "Download merged.pdf" })).not.toBeInTheDocument();
        expect(document.body.textContent).not.toContain(key);
    });

    it("cancels an oversized streaming response even without a Content-Length header", async () => {
        const cancel = vi.fn();
        const stream = new ReadableStream({
            start(controller) { controller.enqueue(new Uint8Array(2 * 1024 * 1024 + 1)); },
            cancel,
        });
        vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json(usage())).mockResolvedValueOnce(new Response(stream, { headers: { "Content-Type": "application/pdf" } })).mockResolvedValueOnce(json(usage(11, 2000))));
        mount(); start();
        expect(await screen.findByRole("alert")).toHaveTextContent("larger than this sample playground");
        expect(cancel).toHaveBeenCalledOnce();
        expect(screen.queryByRole("link", { name: "Download merged.pdf" })).not.toBeInTheDocument();
    });
});
