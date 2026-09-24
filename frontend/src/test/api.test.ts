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
        const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
            new Response("ok", { status: 200 }),
        );
        const buildBody = vi.fn(() => {
            const fd = new FormData();
            fd.append("file", new File(["hello"], "sample.pdf", { type: "application/pdf" }));
            fd.append("quality", "80");
            return fd;
        });

        const res = await postFormData("/api/compress", buildBody, { retry: noRetry });

        expect(await res.text()).toBe("ok");
        expect(buildBody).toHaveBeenCalledTimes(1);
        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/compress");
        expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ method: "POST" });
        expect(fetchMock.mock.calls[0]?.[1]?.body).toBeInstanceOf(FormData);
    });

    it("preserves backend detail, status, and request id on errors", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue(
            new Response(JSON.stringify({ detail: "Unsupported output format" }), {
                status: 415,
                headers: {
                    "content-type": "application/json",
                    "x-request-id": "req-test-123",
                },
            }),
        );

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
        const fetchMock = vi.spyOn(globalThis, "fetch")
            .mockResolvedValueOnce(new Response("temporary", { status: 503 }))
            .mockResolvedValueOnce(new Response("ok", { status: 200 }));
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
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("keeps the historical XHR progress timeout by default", async () => {
        const xhr = stubSuccessfulXhr();

        await uploadFileWithProgress("/compress", new File(["x"], "sample.pdf"));

        expect(xhr.instances[0]?.timeout).toBe(300_000);
    });

    it("honors explicit XHR progress timeout values for single and multi-file uploads", async () => {
        const xhr = stubSuccessfulXhr();
        const file = new File(["x"], "sample.pdf");

        await uploadFileWithProgress("/compress", file, undefined, undefined, undefined, { timeoutMs: 12_345 });
        await uploadFilesWithProgress("/merge", [file], undefined, undefined, undefined, { timeoutMs: 0 });

        expect(xhr.instances[0]?.timeout).toBe(12_345);
        expect(xhr.instances[1]?.timeout).toBe(0);
    });

    it("forwards processAndDownload timeouts into the XHR progress path", async () => {
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        const xhr = stubSuccessfulXhr();
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
            undefined,
            { timeoutMs: 98_765 },
        );

        expect(xhr.instances[0]?.timeout).toBe(98_765);
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
        const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("ok"));
        const file = pdf();

        await uploadFile(endpoint, file, { level: "light" }, { retry: noRetry });

        const body = fetchMock.mock.calls[0]?.[1]?.body;
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
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response('{"fields": []}', {
            headers: { "content-type": "application/json" },
        }));
        const xhr = stubSuccessfulXhr();
        Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:test") });
        Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
        vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
        const file = pdf();

        await uploadFileGetJson("/fill-form/fields", file, undefined, { retry: noRetry });
        await processAndDownload("/redact", file, "report_redacted.pdf", undefined, undefined, undefined, { retry: noRetry });
        await processAndDownload("/compress", file, "report_compressed.pdf", undefined, vi.fn());

        expect(fetchMock.mock.calls.map(([, init]) => uploads(init?.body))).toEqual([[["file", file]], [["file", file]]]);
        expect(uploads(xhr.instances[0]?.send.mock.calls[0]?.[0])).toEqual([["files", file]]);
        await vi.advanceTimersByTimeAsync(100);
    });

    it("rebuilds the same single part for a retry", async () => {
        const fetchMock = vi.spyOn(globalThis, "fetch")
            .mockResolvedValueOnce(new Response("temporary", { status: 503 }))
            .mockResolvedValueOnce(new Response("ok"));
        const file = pdf();

        await uploadFile("/compress", file, undefined, { retry: { attempts: 1, backoffMs: 1 } });

        expect(fetchMock).toHaveBeenCalledTimes(2);
        for (const [, init] of fetchMock.mock.calls) expect(uploads(init?.body)).toEqual([["files", file]]);
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
        vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("nope", { status }));
        expect(toolErrorKind(await failure(() => uploadFile("/compress", pdf(), undefined, { retry: noRetry })))).toBe(kind);
    });

    it("classifies a fetch that never completed as a network failure", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
        const err = await failure(() => postFormData("/compress", () => new FormData(), { retry: noRetry }));
        expect(toolErrorKind(err)).toBe("network");
    });

    it("tags a fetch failure the browser words differently", async () => {
        // WebKit's wording matches none of the known fetch-failure messages, so
        // only the tag api.ts adds can classify it.
        vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("The network connection was lost."));
        const err = await failure(() => uploadFile("/compress", pdf(), undefined, { retry: noRetry }));
        expect(toolErrorKind(err)).toBe("network");
        expect((err as { __kind?: string }).__kind).toBe("network");
    });

    it("classifies a response body the tool cannot parse as a server failure", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response("<!doctype html><title>Bad gateway</title>", { status: 200, headers: { "content-type": "text/html" } }));
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
        const fetchMock = vi.spyOn(globalThis, "fetch");
        const huge = pdf();
        Object.defineProperty(huge, "size", { value: 600 * 1024 * 1024 });
        expect(toolErrorKind(await failure(() => uploadFile("/compress", huge)))).toBe("too_large");
        expect(toolErrorKind(await failure(() => uploadFiles("/merge", [])))).toBe("bad_input");
        expect(fetchMock).not.toHaveBeenCalled();
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
