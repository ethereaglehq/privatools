import { StrictMode, useEffect, useRef } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeletePagesUI } from "../DeletePagesUI";
import { PdfToTextUI } from "../PdfToTextUI";
import { VerifySignatureUI } from "../VerifySignatureUI";
import { BookmarksUI } from "../BookmarksUI";
import { ESignUI } from "../ESignUI";
import { MarkdownToPdfUI } from "../MarkdownToPdfUI";
import { LongImageUI } from "../LongImageUI";
import { uploadFile, downloadBlob } from "@/lib/api";
import { clearFileHandoffs, storeFileHandoff } from "@/lib/file-handoff";

vi.mock("./PdfPageStage", () => ({ PdfPageStage: ({ onPageChange, onDimensions }: {onPageChange?: (page: number) => void; onDimensions?: (info: { width: number; height: number; pages: number }) => void}) => { const dimensions = useRef(onDimensions); useEffect(() => { dimensions.current = onDimensions; }, [onDimensions]); useEffect(() => { let cancelled = false; queueMicrotask(() => { if (!cancelled) dimensions.current?.({ width: 595, height: 842, pages: 3 }); }); return () => { cancelled = true; }; }, []); return <button onClick={() => onPageChange?.(2)}>Preview page two</button>; } }));
vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), uploadFile: vi.fn(), downloadBlob: vi.fn() }));
vi.mock("@/lib/signatureStore", () => ({ loadSignature: vi.fn(async () => null), saveSignature: vi.fn(), forgetSignature: vi.fn() }));

beforeEach(() => {
    localStorage.clear(); clearFileHandoffs(); vi.clearAllMocks();
    vi.mocked(uploadFile).mockImplementation(async () => new Response(new Blob(["synthetic PDF"], { type: "application/pdf" })));
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({ setTransform: vi.fn(), clearRect: vi.fn(), save: vi.fn(), restore: vi.fn(), fillText: vi.fn() } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, "toDataURL").mockReturnValue("data:image/png;base64,aW5r");
    URL.createObjectURL = vi.fn(() => "blob:synthetic"); URL.revokeObjectURL = vi.fn();
});
afterEach(() => { cleanup(); clearFileHandoffs(); vi.restoreAllMocks(); });

describe("PDF editor backend and file handoff contracts", () => {
    it("sends an e-signature to the selected page using the actual backend field names", async () => {
        const { container } = render(<ESignUI />);
        const file = new File(["%PDF synthetic"], "contract.pdf", { type: "application/pdf" });
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [file] } });
        expect(screen.getByRole("button", { name: "Apply e-signature" })).toBeDisabled();
        fireEvent.click(screen.getByRole("tab", { name: "Type" }));
        fireEvent.change(screen.getByPlaceholderText("Type your name…"), { target: { value: "Alex Example" } });
        fireEvent.click(screen.getByRole("button", { name: "Preview page two" }));
        fireEvent.click(screen.getByRole("button", { name: "Apply e-signature" }));
        await waitFor(() => expect(uploadFile).toHaveBeenCalledTimes(1));
        expect(uploadFile).toHaveBeenCalledWith("/esign-pdf", file, expect.objectContaining({ signature: "data:image/png;base64,aW5r", page: 2 }));
        const params = vi.mocked(uploadFile).mock.calls[0][2];
        expect(params).not.toHaveProperty("signature_data"); expect(params).not.toHaveProperty("page_number");
        await waitFor(() => expect(downloadBlob).toHaveBeenCalledTimes(1));
    });
    it("receives Markdown in StrictMode once, waits for conversion, and sends the original file", async () => {
        const source = new File(["# A fresh page\n\nKept as Markdown."], "readme.markdown", { type: "text/markdown" });
        await storeFileHandoff(source, "markdown-to-pdf");
        const { container } = render(<StrictMode><MarkdownToPdfUI /></StrictMode>);
        await screen.findByText("readme.markdown");
        expect(container.querySelector('input[type=file]')).toHaveAttribute("accept", ".md,.markdown,.txt");
        expect(uploadFile).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: "Convert to PDF" }));
        await waitFor(() => expect(uploadFile).toHaveBeenCalledTimes(1));
        expect(vi.mocked(uploadFile).mock.calls[0][0]).toBe("/markdown-to-pdf");
        expect(vi.mocked(uploadFile).mock.calls[0][1]).toBe(source);
        await waitFor(() => expect(downloadBlob).toHaveBeenCalledTimes(1));
    });
    it("honors long-image resolution and format and downloads the existing result again", async () => {
        const { container } = render(<LongImageUI />);
        const file = new File(["%PDF"], "pages.pdf", { type: "application/pdf" });
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [file] } });
        fireEvent.change(screen.getByLabelText("Image format"), { target: { value: "jpg" } });
        fireEvent.change(screen.getByLabelText("Resolution"), { target: { value: "150" } });
        fireEvent.click(screen.getByRole("button", { name: "Create long image" }));
        await waitFor(() => expect(uploadFile).toHaveBeenCalledWith("/pdf-to-long-image", file, { format: "jpg", dpi: 150 }));
        fireEvent.click(await screen.findByRole("button", { name: "Download again" }));
        expect(uploadFile).toHaveBeenCalledTimes(1); expect(downloadBlob).toHaveBeenCalledTimes(2);
    });
    const certificate = { subject: "Common Name: Alice Example", issuer: "Common Name: Example CA", valid_from: "2026-01-01T00:00:00+00:00", valid_until: "2027-01-01T00:00:00+00:00", self_signed: false };
    const signature = (overrides: Record<string, unknown>) => ({ field: "Signature1", signed: true, kind: "signature", signer: "Alice Example", date: "2026-09-18T16:05:56+00:00", status: "valid", modification: "none", certificate, reason: "", ...overrides });
    const verify = async (signatures: unknown[]) => {
        vi.mocked(uploadFile).mockResolvedValue(new Response(JSON.stringify({ has_signatures: signatures.some(s => (s as { signed: boolean }).signed), signatures, note: "Certificates are not checked against a trust list." })));
        const { container } = render(<VerifySignatureUI />);
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [new File(["%PDF"], "signed.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: "Verify signatures" }));
        // The upload zone has a status region too; the verdict is the one under this label.
        return (await screen.findByText("Verification result")).closest<HTMLElement>('[role="status"]')!;
    };
    it("reports a matching signature without claiming the signer's identity", async () => {
        const verdict = await verify([signature({})]);
        expect(verdict).toHaveTextContent("Signature matches the document");
        expect(verdict).toHaveTextContent(/not checked against a trust list/i);
        expect(screen.getByText("Alice Example")).toBeInTheDocument();
        expect(screen.getByText("Valid")).toBeInTheDocument();
        expect(screen.getByText(/Common Name: Alice Example/)).toHaveTextContent("Common Name: Example CA");
        expect(screen.queryByText(/verified signer|trusted/i)).not.toBeInTheDocument();
    });
    it("marks a signature invalid and says why", async () => {
        const verdict = await verify([signature({ status: "invalid", modification: null, reason: "The signed content has changed since it was signed." })]);
        expect(verdict).toHaveTextContent("A signature does not match the document");
        expect(screen.getByText("Invalid")).toBeInTheDocument();
        expect(screen.getByText("The signed content has changed since it was signed.")).toBeInTheDocument();
    });
    it("separates changes saved after signing by what kind they are", async () => {
        const verdict = await verify([signature({ field: "First", status: "modified", modification: "form_filling" }), signature({ field: "Second", status: "modified", modification: "other" })]);
        expect(verdict).toHaveTextContent("Changed after signing");
        expect(screen.getByText(/form fields were filled in or signed/i)).toBeInTheDocument();
        expect(screen.getByText(/can change what the document shows/i)).toBeInTheDocument();
    });
    it("lists empty and unchecked signature fields without a verdict on them", async () => {
        const verdict = await verify([signature({ field: "Empty", signed: false, signer: "", date: "", status: "unsigned", modification: null, certificate: null }), signature({ status: "unchecked", modification: null, certificate: null, reason: "This signature uses the adbe.x509.rsa_sha1 format, which cannot be checked here." })]);
        expect(verdict).toHaveTextContent("A signature could not be checked");
        expect(screen.getByText("Not signed")).toBeInTheDocument();
        expect(screen.getByText("Not checked")).toBeInTheDocument();
        expect(screen.getByText(/adbe.x509.rsa_sha1/)).toBeInTheDocument();
        expect(screen.queryByText("Valid")).not.toBeInTheDocument();
    });
    it("says when a PDF has no signature fields", async () => {
        const verdict = await verify([]);
        expect(verdict).toHaveTextContent("No signature fields found");
    });
    it("keeps invalid bookmark JSON editable and prevents submission without crashing the row editor", async () => {
        const { container } = render(<BookmarksUI />);
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [new File(["%PDF"], "book.pdf")] } });
        await waitFor(() => expect(screen.getByLabelText("Bookmark 1 page")).toHaveAttribute("max", "3"));
        fireEvent.click(screen.getByRole("button", { name: "JSON" }));
        fireEvent.change(screen.getByLabelText("Bookmarks JSON"), { target: { value: "[null]" } });
        expect(screen.getByRole("button", { name: "Add bookmarks" })).toBeDisabled();
        fireEvent.click(screen.getByRole("button", { name: "Rows" }));
        expect(screen.getByLabelText("Bookmark 1 title")).toHaveValue("Chapter 1");
    });

    it("requires a valid page selection, keeps one page, and reprocesses adjusted selections", async () => {
        const { container } = render(<DeletePagesUI />);
        const source = new File(["%PDF"], "pages.pdf");
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [source] } });
        expect(screen.getByRole("button", { name: "Delete pages" })).toBeDisabled();
        fireEvent.change(screen.getByLabelText("Page range"), { target: { value: "1-3" } });
        expect(await screen.findByRole("alert")).toHaveTextContent("Keep at least one page");
        expect(screen.getByRole("button", { name: "Delete pages" })).toBeDisabled();
        fireEvent.change(screen.getByLabelText("Page range"), { target: { value: "1" } });
        fireEvent.click(screen.getByRole("button", { name: "Delete pages" }));
        fireEvent.click(await screen.findByRole("button", { name: "Adjust selection" }));
        fireEvent.change(screen.getByLabelText("Page range"), { target: { value: "2" } });
        fireEvent.click(screen.getByRole("button", { name: "Delete pages" }));
        await waitFor(() => expect(uploadFile).toHaveBeenCalledTimes(2));
        expect(vi.mocked(uploadFile).mock.calls.map(call => call[2])).toEqual([{ pages: "1" }, { pages: "2" }]);
    });
    it("uses the server's page array as a count in extracted-text results", async () => {
        const payload = JSON.stringify({ text: "A readable document with useful words.", pages: [{ page: 1, text: "A" }, { page: 2, text: "B" }, { page: 3, text: "C" }] });
        vi.mocked(uploadFile).mockResolvedValue({ headers: new Headers(), blob: async () => Object.assign(new Blob([payload]), { text: async () => payload }) } as Response);
        const { container } = render(<PdfToTextUI />);
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [new File(["%PDF"], "source.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: "Extract text" }));
        const label = await screen.findByText("Pages");
        expect(label.parentElement).toHaveTextContent("3");
        expect(container).not.toHaveTextContent("[object Object]");
    });

});
