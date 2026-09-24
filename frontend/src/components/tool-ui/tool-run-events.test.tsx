import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { GenericUI } from "./GenericUI";
import { SimpleConvertUI } from "./SimpleConvertUI";
import { VerifySignatureUI } from "./VerifySignatureUI";
import { uploadFileWithProgress } from "@/lib/api";
import { consumeFileHandoffs } from "@/lib/file-handoff";

vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), uploadFileWithProgress: vi.fn(), downloadBlob: vi.fn() }));
vi.mock("@/lib/file-handoff", () => ({ consumeFileHandoffs: vi.fn(async () => []) }));

const RUN_EVENT = "privatools:tool-run";
type Detail = Record<string, unknown>;
function listen(): Detail[] {
    const seen: Detail[] = [];
    window.addEventListener(RUN_EVENT, event => seen.push((event as CustomEvent<Detail>).detail));
    return seen;
}
function pdf(name: string) { return new File(["%PDF synthetic"], name, { type: "application/pdf" }); }
function ok() { return { blob: async () => new Blob(["out"], { type: "application/pdf" }), headers: new Headers() } as Response; }
/** The shape api.ts gives an HTTP error: a message the UI shows, plus the status. */
function httpError(status: number) { return Object.assign(new Error("boom secret"), { __status: status }); }

beforeEach(() => {
    vi.clearAllMocks(); vi.mocked(consumeFileHandoffs).mockResolvedValue([]);
    URL.createObjectURL = vi.fn(() => "blob:synthetic"); URL.revokeObjectURL = vi.fn();
});
afterEach(() => { cleanup(); });

describe("GenericUI usage events", () => {
    it("emits one successful single run with the file count after processing", async () => {
        const seen = listen();
        vi.mocked(uploadFileWithProgress).mockResolvedValue(ok());
        const { container } = render(<GenericUI slug="rotate-pdf" toolName="Rotate PDF" actionLabel="Rotate now" outputLabel="rotated.pdf" accepts=".pdf" />);
        fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [pdf("secret-a.pdf"), pdf("secret-b.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: /^Rotate now/ }));
        await waitFor(() => expect(uploadFileWithProgress).toHaveBeenCalledTimes(2));
        await waitFor(() => expect(seen).toHaveLength(1));
        expect(seen).toEqual([{ mode: "single", outcome: "success", files: 2 }]);
        expect(JSON.stringify(seen)).not.toContain("secret");
    });
    it("reports a failed single-file run as an error with its category, without the message", async () => {
        const seen = listen();
        vi.mocked(uploadFileWithProgress).mockRejectedValue(httpError(413));
        const { container } = render(<GenericUI slug="rotate-pdf" toolName="Rotate PDF" actionLabel="Rotate now" outputLabel="rotated.pdf" accepts=".pdf" />);
        fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [pdf("secret.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: /^Rotate now/ }));
        await waitFor(() => expect(seen).toHaveLength(1));
        expect(seen).toEqual([{ mode: "single", outcome: "error", files: 1, errorKind: "too_large" }]);
        expect(JSON.stringify(seen)).not.toContain("secret");
    });
    it("reports nothing when the visitor cancels the run", async () => {
        const seen = listen();
        vi.mocked(uploadFileWithProgress).mockImplementation((_endpoint, _file, _params, _onProgress, signal) => new Promise<Response>((_resolve, reject) => {
            signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        }));
        const { container } = render(<GenericUI slug="rotate-pdf" toolName="Rotate PDF" actionLabel="Rotate now" outputLabel="rotated.pdf" accepts=".pdf" />);
        fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [pdf("secret.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: /^Rotate now/ }));
        fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));
        await waitFor(() => expect(screen.getByRole("button", { name: /^Rotate now/ })).toBeEnabled());
        expect(seen).toEqual([]);
    });
});

describe("direct call site usage events", () => {
    // VerifySignatureUI calls the real uploadFile, so these go through lib/api.ts.
    async function verify(response: Response) {
        const seen = listen();
        vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
        const { container } = render(<VerifySignatureUI />);
        fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [pdf("secret-contract.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: "Verify signatures" }));
        await waitFor(() => expect(seen).toHaveLength(1));
        vi.mocked(globalThis.fetch).mockRestore();
        return seen;
    }
    it("passes the server's refusal to the usage signal", async () => {
        const seen = await verify(new Response(JSON.stringify({ detail: "secret-contract.pdf is too large" }), { status: 413, headers: { "content-type": "application/json" } }));
        expect(seen).toEqual([{ outcome: "error", files: 1, errorKind: "too_large" }]);
        expect(JSON.stringify(seen)).not.toContain("secret");
    });
    it("calls a response the tool cannot parse a server failure", async () => {
        const seen = await verify(new Response("<!doctype html><title>Bad gateway</title>", { status: 200, headers: { "content-type": "text/html" } }));
        expect(seen).toEqual([{ outcome: "error", files: 1, errorKind: "server" }]);
    });
});

describe("SimpleConvertUI usage events", () => {
    it("emits a partial run when one of two conversions fails", async () => {
        const seen = listen();
        vi.mocked(uploadFileWithProgress).mockResolvedValueOnce(ok()).mockRejectedValueOnce(httpError(503));
        const { container } = render(<SimpleConvertUI slug="bmp-to-pdf" label="Convert to PDF" outputExt="pdf" outputFilename="converted.pdf" acceptFileTypes=".bmp" description="Convert BMP images to PDF" />);
        fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [new File(["x"], "secret-a.bmp", { type: "image/bmp" }), new File(["x"], "secret-b.bmp", { type: "image/bmp" })] } });
        fireEvent.click(screen.getByRole("button", { name: /Convert to PDF/ }));
        await waitFor(() => expect(seen).toHaveLength(1));
        expect(seen).toEqual([{ mode: "single", outcome: "partial", files: 2, errorKind: "server" }]);
        expect(JSON.stringify(seen)).not.toContain("secret");
    });
});
