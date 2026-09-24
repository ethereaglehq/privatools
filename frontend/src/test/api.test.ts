import { afterEach, describe, expect, it, vi } from "vitest";
import {
    apiUrl,
    chooseDownloadFilename,
    getErrorDetail,
    getErrorStatus,
    getRequestId,
    postFormData,
    postForm,
    postJson,
    processAndDownload,
    readJson,
    resolveApiOrigin,
    uploadFile,
    uploadFileGetJson,
    uploadFiles,
    uploadFilesWithProgress,
    uploadFileWithProgress,
    withErrorKind,
} from "@/lib/api";
import { toolErrorKind } from "@/lib/toolRun";
import { installNetwork } from "./fake-network";

describe("resolveApiOrigin (api-subdomain split)", () => {
    afterEach(() => {
        document
            .querySelectorAll('meta[name="privatools:api-base"]')
            .forEach((m) => m.remove());
    });

    it("returns same-origin (empty) when no meta tag is present", () => {
        expect(resolveApiOrigin()).toBe("");
    });

    it("uses the injected api-base meta tag, stripping a trailing slash", () => {
        const meta = document.createElement("meta");
        meta.setAttribute("name", "privatools:api-base");
        meta.setAttribute("content", "https://api.privatools.me/");
        document.head.appendChild(meta);
        expect(resolveApiOrigin()).toBe("https://api.privatools.me");
    });

    it("apiUrl normalizes endpoints against the same-origin base by default", () => {
        // No meta tag (removed in afterEach) → API_BASE is "/api".
        expect(apiUrl("/health")).toBe("/api/health");
        expect(apiUrl("/api/compress")).toBe("/api/compress");
    });
});

const noRetry = { attempts: 0, backoffMs: 1 };
const originalCreateObjectURL = URL.createObjectURL;
const originalRevokeObjectURL = URL.revokeObjectURL;

describe("api form-data helpers", () => {
    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
        restoreBlobUrlMethod("createObjectURL", originalCreateObjectURL);
        restoreBlobUrlMethod("revokeObjectURL", originalRevokeObjectURL);
    });

    it("posts arbitrary FormData through the normalized API route", async () => {
        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0 });
        const buildBody = vi.fn(() => {
            const fd = new FormData();
            fd.append("file", new File(["hello"], "sample.pdf", { type: "application/pdf" }));
            fd.append("quality", "80");
            return fd;
        });

        const res = await postFormData("/api/compress", buildBody, { retry: noRetry });

        expect(await res.text()).toBe("ok");
        expect(buildBody).toHaveBeenCalledTimes(1);
        expect(net.requests).toHaveLength(1);
        expect(net.requests[0]?.url).toBe("/api/compress");
        expect(net.requests[0]?.body).toBeInstanceOf(FormData);
    });

    it("sends a form with a file by XMLHttpRequest, which reports upload progress, and one without by fetch", async () => {
        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0 });
        const withFile = new FormData();
        withFile.append("logo", new File(["png"], "logo.png", { type: "image/png" }));
        const withoutFile = new FormData();
        withoutFile.append("data", "https://example.com/");

        await postFormData("/qr-code", withFile, { retry: noRetry });
        await postFormData("/qr-code", withoutFile, { retry: noRetry });

        expect(net.requests.map(request => request.transport)).toEqual(["xhr", "fetch"]);
        expect(net.fetch.mock.calls[0]?.[1]).toMatchObject({ method: "POST", body: withoutFile });
    });

    it("preserves backend detail, status, and request id on errors", async () => {
        installNetwork({
            uploadMs: 0,
            answerAfterMs: 0,
            status: 415,
            body: JSON.stringify({ detail: "Unsupported output format" }),
            headers: {
                "content-type": "application/json",
                "x-request-id": "req-test-123",
            },
        });

        const fd = new FormData();
        fd.append("file", new File(["bad"], "sample.bin"));

        let caught: unknown;
        try {
            await postFormData("/convert", fd, { retry: noRetry });
        } catch (err) {
            caught = err;
        }

        expect(caught).toBeInstanceOf(Error);
        expect((caught as Error).message).toBe("Unsupported output format");
        expect(getErrorStatus(caught)).toBe(415);
        expect(getRequestId(caught)).toBe("req-test-123");
        expect(getErrorDetail(caught)).toBe("Unsupported output format");
    });

    it("tells the server's own words apart from a message written for a bare status", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("<html>413</html>", { status: 413 }));

        let caught: unknown;
        try {
            await postFormData("/convert", new FormData(), { retry: noRetry });
        } catch (err) {
            caught = err;
        }

        expect(getErrorStatus(caught)).toBe(413);
        expect(getErrorDetail(caught)).toBeUndefined();
    });

    it("rebuilds FormData bodies for retry attempts", async () => {
        const net = installNetwork(attempt => attempt === 0
            ? { uploadMs: 0, answerAfterMs: 0, status: 503, body: "temporary" }
            : { uploadMs: 0, answerAfterMs: 0 });
        const buildBody = vi.fn(() => {
            const fd = new FormData();
            fd.append("file", new File(["hello"], "sample.pdf", { type: "application/pdf" }));
            return fd;
        });

        const res = await postFormData("/compress", buildBody, {
            retry: { attempts: 1, backoffMs: 1 },
        });

        expect(await res.text()).toBe("ok");
        expect(buildBody).toHaveBeenCalledTimes(2);
        expect(net.requests).toHaveLength(2);
    });

    it("leaves the browser's whole-request timeout off, since it would count the upload", async () => {
        const xhr = stubSuccessfulXhr();

        await uploadFileWithProgress("/compress", new File(["x"], "sample.pdf"));
        await uploadFilesWithProgress("/merge", [new File(["x"], "sample.pdf")]);

        // The stub starts at -1 so that any value the helpers set would show.
        expect(xhr.instances.map(instance => instance.timeout)).toEqual([-1, -1]);
    });

    it("honors an explicit wait on the progress helpers, 0 meaning none", async () => {
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        installNetwork({ uploadMs: 60_000, stallAfterMs: 0 });
        const file = new File(["x"], "sample.pdf");
        const outcomes: string[] = [];
        const record = (name: string) => (err: unknown) => { outcomes.push(`${name}: ${toolErrorKind(err)}`); };

        uploadFileWithProgress("/compress", file, undefined, undefined, undefined, { timeoutMs: 12_345 }).catch(record("single"));
        uploadFilesWithProgress("/merge", [file], undefined, undefined, undefined, { timeoutMs: 0 }).catch(record("multi"));

        await vi.advanceTimersByTimeAsync(12_344);
        expect(outcomes).toEqual([]);
        await vi.advanceTimersByTimeAsync(1);
        expect(outcomes).toEqual(["single: timeout"]);
        await vi.advanceTimersByTimeAsync(24 * 60 * 60 * 1000);
        expect(outcomes).toEqual(["single: timeout"]);
    });

    it("forwards processAndDownload's wait into the progress path", async () => {
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        installNetwork({ uploadMs: 60_000, stallAfterMs: 0 });
        let caught: unknown;

        processAndDownload(
            "/compress",
            new File(["x"], "sample.pdf"),
            "sample-compressed.pdf",
            undefined,
            vi.fn(),
            undefined,
            { timeoutMs: 98_765 },
        ).catch(err => { caught = err; });

        await vi.advanceTimersByTimeAsync(98_764);
        expect(caught).toBeUndefined();
        await vi.advanceTimersByTimeAsync(1);
        expect(toolErrorKind(caught)).toBe("timeout");
    });

    it("downloads the answer of a progress upload and releases its anchor and blob URL", async () => {
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        stubSuccessfulXhr();
        Object.defineProperty(URL, "createObjectURL", {
            configurable: true,
            value: vi.fn(() => "blob:test"),
        });
        Object.defineProperty(URL, "revokeObjectURL", {
            configurable: true,
            value: vi.fn(),
        });
        vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

        await processAndDownload(
            "/compress",
            new File(["x"], "sample.pdf"),
            "sample-compressed.pdf",
            undefined,
            vi.fn(),
        );

        // Let the download release its anchor and blob URL before jsdom exits.
        await vi.advanceTimersByTimeAsync(100);
        expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:test");
        expect(document.querySelector('a[download="sample-compressed.pdf"]')).toBeNull();
    });

    it("keeps original-based filenames when backend returns generic names", async () => {
        expect(chooseDownloadFilename("contract_unlocked.pdf", "unlocked.pdf")).toBe("contract_unlocked.pdf");
        expect(chooseDownloadFilename("scan_compressed.pdf", "compressed.pdf")).toBe("scan_compressed.pdf");
        expect(chooseDownloadFilename("report_split.zip", "split_pages.zip")).toBe("report_split.zip");
        expect(chooseDownloadFilename("contract_unlocked.pdf", "contract_unlocked.pdf")).toBe("contract_unlocked.pdf");
        expect(chooseDownloadFilename("output.pdf", "server_named_report.pdf")).toBe("server_named_report.pdf");
    });
});

/** A request body's file parts, as [field, file] pairs in the order sent. */
function uploads(body: unknown): [string, File][] {
    expect(body).toBeInstanceOf(FormData);
    return [...(body as FormData).entries()].filter((entry): entry is [string, File] => entry[1] instanceof File);
}

describe("each single-file upload carries its file once", () => {
    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
        restoreBlobUrlMethod("createObjectURL", originalCreateObjectURL);
        restoreBlobUrlMethod("revokeObjectURL", originalRevokeObjectURL);
    });
    const pdf = () => new File(["%PDF-1.7 synthetic"], "report.pdf", { type: "application/pdf" });
    // `/grayscale` reads `file: UploadFile`; `/compress` and `/strip-metadata` read `files: list[UploadFile]`.
    const routes = [["/grayscale", "file"], ["/compress", "files"], ["/api/strip-metadata", "files"]] as const;

    it.each(routes)("uploadFile sends one part to %s, named %s", async (endpoint, field) => {
        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0 });
        const file = pdf();

        await uploadFile(endpoint, file, { level: "light" }, { retry: noRetry });

        const body = net.requests[0]?.body;
        expect(uploads(body)).toEqual([[field, file]]);
        expect((body as FormData).get("level")).toBe("light");
    });

    it.each(routes)("uploadFileWithProgress sends one part to %s, named %s", async (endpoint, field) => {
        const xhr = stubSuccessfulXhr();
        const file = pdf();

        await uploadFileWithProgress(endpoint, file, { level: "light" });

        const body = xhr.instances[0]?.send.mock.calls[0]?.[0];
        expect(uploads(body)).toEqual([[field, file]]);
        expect((body as FormData).get("level")).toBe("light");
    });

    it("keeps to one part when the helpers are reached through uploadFileGetJson and processAndDownload", async () => {
        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0, body: '{"fields": []}',
            headers: { "content-type": "application/json" } });
        Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:test") });
        Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
        vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
        const file = pdf();

        await uploadFileGetJson("/fill-form/fields", file, undefined, { retry: noRetry });
        await processAndDownload("/redact", file, "report_redacted.pdf", undefined, undefined, undefined, { retry: noRetry });
        await processAndDownload("/compress", file, "report_compressed.pdf", undefined, vi.fn());

        expect(net.requests.map(request => uploads(request.body))).toEqual([[["file", file]], [["file", file]], [["files", file]]]);
        // Let the downloads release their anchors before jsdom exits.
        await new Promise(resolve => setTimeout(resolve, 150));
    });

    it("rebuilds the same single part for a retry", async () => {
        const net = installNetwork(attempt => attempt === 0
            ? { uploadMs: 0, answerAfterMs: 0, status: 503, body: "temporary" }
            : { uploadMs: 0, answerAfterMs: 0 });
        const file = pdf();

        await uploadFile("/compress", file, undefined, { retry: { attempts: 1, backoffMs: 1 } });

        expect(net.requests).toHaveLength(2);
        for (const request of net.requests) expect(uploads(request.body)).toEqual([["files", file]]);
    });
});

describe("failure categories on api errors", () => {
    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
    });
    async function failure(run: () => Promise<unknown>): Promise<unknown> {
        try { await run(); } catch (err) { return err; }
        throw new Error("expected the request to fail");
    }
    const pdf = () => new File(["%PDF"], "secret.pdf", { type: "application/pdf" });

    it.each([
        [413, "too_large"],
        [429, "rate_limited"],
        [415, "bad_input"],
        [504, "timeout"],
        [500, "server"],
    ])("classifies an HTTP %i answer as %s", async (status, kind) => {
        installNetwork({ uploadMs: 0, answerAfterMs: 0, status, body: "nope" });
        expect(toolErrorKind(await failure(() => uploadFile("/compress", pdf(), undefined, { retry: noRetry })))).toBe(kind);
    });

    it("classifies a fetch that never completed as a network failure", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
        const err = await failure(() => postFormData("/compress", () => new FormData(), { retry: noRetry }));
        expect(toolErrorKind(err)).toBe("network");
    });

    it("tags a fetch failure the browser words differently", async () => {
        // WebKit's wording matches none of the known fetch-failure messages, so
        // only the tag api.ts adds can classify it. (A form without a file goes
        // by fetch; uploads go by XMLHttpRequest, whose failures are tagged too.)
        vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("The network connection was lost."));
        const err = await failure(() => postFormData("/qr-code", () => new FormData(), { retry: noRetry }));
        expect(toolErrorKind(err)).toBe("network");
        expect((err as { __kind?: string }).__kind).toBe("network");
    });

    it("classifies a response body the tool cannot parse as a server failure", async () => {
        installNetwork({ uploadMs: 0, answerAfterMs: 0, body: "<!doctype html><title>Bad gateway</title>", headers: { "content-type": "text/html" } });
        expect(toolErrorKind(await failure(() => uploadFileGetJson("/metadata", pdf(), undefined, { retry: noRetry })))).toBe("server");
        expect(toolErrorKind(await failure(() => postJson("/metadata", {}, { retry: noRetry })))).toBe("server");
        expect(toolErrorKind(await failure(() => postForm("/metadata", {}, { retry: noRetry })))).toBe("server");
        expect(toolErrorKind(await failure(() => readJson(new Response('{"truncated": '))))).toBe("server");
        await expect(readJson(new Response('{"pages": 3}'))).resolves.toEqual({ pages: 3 });
    });

    it("classifies the client deadline as a timeout and a user abort as a cancel", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((_url, init) => new Promise((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () => reject(init.signal!.reason));
        }));
        const late = await failure(() => postFormData("/compress", () => new FormData(), { retry: noRetry, timeoutMs: 5 }));
        expect(toolErrorKind(late)).toBe("timeout");
        const controller = new AbortController();
        const pending = failure(() => postFormData("/compress", () => new FormData(), { retry: noRetry, timeoutMs: 0, signal: controller.signal }));
        controller.abort();
        expect(toolErrorKind(await pending)).toBe("cancelled");
    });

    it("classifies XHR network errors, deadlines and HTTP answers", async () => {
        stubFailingXhr("error");
        const offline = await failure(() => uploadFileWithProgress("/compress", pdf()));
        expect(toolErrorKind(offline)).toBe("network");
        // Its message would also match the fetch wording; the tag is what api.ts owes.
        expect((offline as { __kind?: string }).__kind).toBe("network");
        stubFailingXhr("timeout");
        expect(toolErrorKind(await failure(() => uploadFilesWithProgress("/merge", [pdf()])))).toBe("timeout");
        stubFailingXhr(413);
        expect(toolErrorKind(await failure(() => uploadFileWithProgress("/compress", pdf())))).toBe("too_large");
    });

    it("classifies files the browser refuses before sending", async () => {
        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0 });
        const huge = pdf();
        Object.defineProperty(huge, "size", { value: 600 * 1024 * 1024 });
        expect(toolErrorKind(await failure(() => uploadFile("/compress", huge)))).toBe("too_large");
        expect(toolErrorKind(await failure(() => uploadFiles("/merge", [])))).toBe("bad_input");
        expect(net.requests).toEqual([]);
    });

    it("lets a caller tag its own failure", () => {
        const err = withErrorKind(new Error("The server returned an empty PDF."), "server");
        expect(toolErrorKind(err)).toBe("server");
        expect((err as Error).message).toBe("The server returned an empty PDF.");
    });
});

function stubFailingXhr(failure: "error" | "timeout" | number) {
    class MockXHR {
        upload: { onprogress?: (event: ProgressEvent) => void } = {};
        response = new Blob(["nope"], { type: "text/plain" });
        responseType = "";
        status = typeof failure === "number" ? failure : 0;
        timeout = -1;
        onabort: (() => void) | null = null;
        onerror: (() => void) | null = null;
        onload: (() => void) | null = null;
        onloadend: (() => void) | null = null;
        ontimeout: (() => void) | null = null;
        open = vi.fn();
        abort = vi.fn();
        send = vi.fn(() => {
            if (failure === "error") this.onerror?.();
            else if (failure === "timeout") this.ontimeout?.();
            else this.onload?.();
            this.onloadend?.();
        });
        getAllResponseHeaders = vi.fn(() => "content-type: text/plain\r\n");
    }
    vi.stubGlobal("XMLHttpRequest", MockXHR);
}

function stubSuccessfulXhr() {
    class MockXHR {
        static instances: MockXHR[] = [];
        upload: { onprogress?: (event: ProgressEvent) => void } = {};
        response = new Blob(["ok"], { type: "application/pdf" });
        responseType = "";
        status = 200;
        timeout = -1;
        onabort: (() => void) | null = null;
        onerror: (() => void) | null = null;
        onload: (() => void) | null = null;
        onloadend: (() => void) | null = null;
        ontimeout: (() => void) | null = null;

        constructor() {
            MockXHR.instances.push(this);
        }

        open = vi.fn();
        abort = vi.fn(() => {
            this.onabort?.();
            this.onloadend?.();
        });
        send = vi.fn((_body?: unknown) => {
            this.onload?.();
            this.onloadend?.();
        });
        getAllResponseHeaders = vi.fn(() => "content-type: application/pdf\r\nx-request-id: req-xhr\r\n");
    }

    vi.stubGlobal("XMLHttpRequest", MockXHR);
    return MockXHR;
}

function restoreBlobUrlMethod<T extends "createObjectURL" | "revokeObjectURL">(
    method: T,
    original: (typeof URL)[T] | undefined,
) {
    if (original) {
        Object.defineProperty(URL, method, { configurable: true, value: original });
    } else {
        delete (URL as typeof URL & Record<T, unknown>)[method];
    }
}
