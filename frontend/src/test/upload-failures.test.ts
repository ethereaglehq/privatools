/**
 * What the page does when an upload cannot go through.
 *
 * The page on privatools.me calls api.privatools.me cross-origin. Production
 * nginx and the backend each refuse a request over 500 MB, counting the whole
 * multipart body, and nginx answers 502 while the app is down and 504 when it
 * says nothing for five minutes. Until those answers carried CORS headers the
 * page could not read them: each reached it as a network failure (status 0),
 * which it reported as "network" and sent again, the whole upload each time.
 *
 * The fake network has no CORS preflight: an answer it scripts is one the
 * browser let the page read. A real upload is preflighted, and nginx answers
 * the preflight too, so while the app is down its 502 (or a limit's 503)
 * reaches an upload only when the browser still holds a preflight for that
 * endpoint; otherwise the upload fails as the network error tested below.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
    MAX_RETRY_SIZE,
    postFormData,
    processFilesAndDownload,
    uploadFile,
    uploadFiles,
    uploadFilesWithProgress,
} from "@/lib/api";
import { toolErrorKind } from "@/lib/toolRun";
import { installNetwork, MB, MINUTE, SECOND, sizedFile } from "./fake-network";

beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "Date"] });
});
afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
});

/** Let settled requests run their callbacks: reading an answer's body is real I/O. */
async function drain() {
    for (let i = 0; i < 5; i++) await new Promise(resolve => setImmediate(resolve));
}

/** Move the clock a second at a time until the request fails, as it must. */
async function failure(promise: Promise<unknown>, ms = 2 * MINUTE): Promise<Error> {
    let caught: unknown;
    let settled = false;
    promise.then(() => { settled = true; }, err => { settled = true; caught = err; });
    for (let t = 0; t < ms && !settled; t += SECOND) {
        await vi.advanceTimersByTimeAsync(SECOND);
        await drain();
    }
    expect(caught).toBeInstanceOf(Error);
    return caught as Error;
}

const json = (detail: string) => ({ body: JSON.stringify({ detail }), headers: { "content-type": "application/json" } });
// nginx's own answers on the API host (deploy/oracle-vm/nginx-privatools.conf).
const NGINX_413 = json("This upload is too large: one request to the server can carry up to 500 MB.");
const NGINX_502 = json("The server is not available right now. Try again in a minute.");
const NGINX_504 = json("The server took too long to answer. Try a smaller file, or try again later.");

describe("a request that would pass the 500 MB one upload can carry", () => {
    const three = () => [sizedFile("a.pdf", 200 * MB), sizedFile("b.pdf", 200 * MB), sizedFile("c.pdf", 200 * MB)];
    const REFUSED = "These files are 600.0 MB in all, and one upload can carry 500 MB, counting the form they are sent in. Nothing was sent. Choose fewer or smaller files.";

    it.each([
        ["Merge, Bates, Page Counter (uploadFiles)", () => uploadFiles("/merge", three())],
        ["Audio and Video Merge, Batch Compress (uploadFilesWithProgress)", () => uploadFilesWithProgress("/video-merge", three(), undefined, vi.fn())],
        ["Unlock (processFilesAndDownload)", () => processFilesAndDownload("/unlock", three(), "unlocked.zip", { password: "x" })],
        ["Create ZIP, Collage, Compare and the other forms (postFormData)", () => postFormData("/create-zip", () => {
            const form = new FormData();
            for (const file of three()) form.append("files", file);
            return form;
        })],
    ])("%s is refused before anything is sent", async (_name, send) => {
        const net = installNetwork({ uploadMs: SECOND, answerAfterMs: SECOND });
        const err = await failure(send());
        expect(err.message).toBe(REFUSED);
        expect(toolErrorKind(err)).toBe("too_large");
        expect(net.requests).toEqual([]);
    });

    it("counts what the form adds to its files, so one file of exactly 500 MB does not fit either", async () => {
        const net = installNetwork({ uploadMs: SECOND, answerAfterMs: SECOND });
        const err = await failure(uploadFile("/compress", sizedFile("scan.pdf", 500 * MB)));
        expect(err.message).toBe("This file is 500.0 MB, and one upload can carry 500 MB, counting the form it is sent in. Nothing was sent. Choose a smaller file.");
        expect(toolErrorKind(err)).toBe("too_large");
        expect(net.requests).toEqual([]);
    });

    it("sends files that fit, however close to the limit", async () => {
        const net = installNetwork({ uploadMs: SECOND, answerAfterMs: SECOND });
        let result: unknown;
        uploadFiles("/merge", [sizedFile("a.pdf", 250 * MB), sizedFile("b.pdf", 250 * MB - 64 * 1024)]).then(res => { result = res; });
        await vi.advanceTimersByTimeAsync(3 * SECOND);
        await drain();
        expect((result as Response).ok).toBe(true);
        expect(net.requests).toHaveLength(1);
    });
});

describe("an answer nginx or the backend refused, when the page can read it", () => {
    it("shows a 413 for what it is, and never sends it again", async () => {
        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0, status: 413, ...NGINX_413 });
        const err = await failure(uploadFile("/split", sizedFile("scan.pdf", 2 * MB)));
        expect(err.message).toBe("This upload is too large: one request to the server can carry up to 500 MB.");
        expect(toolErrorKind(err)).toBe("too_large");
        expect(net.requests).toHaveLength(1);
    });

    // nginx's 504 reaches the page when the app answered the preflight and then
    // said nothing about the upload. Its 502 does only while the browser holds
    // a preflight for the endpoint (see the top).
    it("shows nginx's 502 and 504, classified as a server failure and a timeout", async () => {
        installNetwork({ uploadMs: 0, answerAfterMs: 0, status: 502, ...NGINX_502 });
        const down = await failure(uploadFile("/split", sizedFile("scan.pdf", 20 * MB)));
        expect(down.message).toBe("The server is not available right now. Try again in a minute.");
        expect(toolErrorKind(down)).toBe("server");

        const net = installNetwork({ uploadMs: 0, answerAfterMs: 0, status: 504, ...NGINX_504 });
        const late = await failure(uploadFile("/split", sizedFile("scan.pdf", 2 * MB)));
        expect(late.message).toBe("The server took too long to answer. Try a smaller file, or try again later.");
        expect(toolErrorKind(late)).toBe("timeout");
        expect(net.requests).toHaveLength(1);
    });

    it.each([
        [413, "That upload is too large. The maximum is 500 MB per upload.", "too_large"],
        [502, "The server isn't responding right now. Try again in a moment.", "server"],
        [503, "The server isn't responding right now. Try again in a moment.", "server"],
        [504, "Processing timed out. Try a smaller file or a lighter compression setting.", "timeout"],
    ])("words a %i without a JSON detail for its status", async (status, message, kind) => {
        installNetwork({ uploadMs: 0, answerAfterMs: 0, status, body: "<html><body>error</body></html>", headers: { "content-type": "text/html" } });
        const err = await failure(uploadFile("/split", sizedFile("scan.pdf", 20 * MB)));
        expect(err.message).toBe(message);
        expect(toolErrorKind(err)).toBe(kind);
    });
});

describe("sending an upload again", () => {
    it("tries a small upload three times after a network failure or a 5xx", async () => {
        const dropped = installNetwork({ uploadMs: 4 * SECOND, failAfterMs: 2 * SECOND });
        expect(toolErrorKind(await failure(uploadFile("/split", sizedFile("small.pdf", 5 * MB))))).toBe("network");
        expect(dropped.requests).toHaveLength(3);

        const down = installNetwork({ uploadMs: SECOND, answerAfterMs: 0, status: 502, ...NGINX_502 });
        expect(toolErrorKind(await failure(uploadFile("/split", sizedFile("small.pdf", 5 * MB))))).toBe("server");
        expect(down.requests).toHaveLength(3);
    });

    it("tries an upload over 10 MB once: another attempt would send all of it again", async () => {
        expect(MAX_RETRY_SIZE).toBe(10 * MB);
        const big = () => sizedFile("scan.pdf", 10 * MB + 1);

        const dropped = installNetwork({ uploadMs: MINUTE, failAfterMs: 30 * SECOND });
        expect(toolErrorKind(await failure(uploadFile("/split", big())))).toBe("network");
        expect(dropped.requests).toHaveLength(1);

        const down = installNetwork({ uploadMs: 20 * SECOND, answerAfterMs: 0, status: 502, ...NGINX_502 });
        expect(toolErrorKind(await failure(uploadFile("/split", big())))).toBe("server");
        expect(down.requests).toHaveLength(1);

        // Several files count together, whichever helper sends them.
        const merge = installNetwork({ uploadMs: MINUTE, failAfterMs: 30 * SECOND });
        await failure(uploadFiles("/merge", [sizedFile("a.pdf", 6 * MB), sizedFile("b.pdf", 6 * MB)]));
        expect(merge.requests).toHaveLength(1);
        const form = installNetwork({ uploadMs: MINUTE, failAfterMs: 30 * SECOND });
        await failure(postFormData("/watermark", () => {
            const fd = new FormData();
            fd.append("file", big());
            return fd;
        }));
        expect(form.requests).toHaveLength(1);
    });
});
