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
    it("shows detected signature fields without inventing a validity or tampering verdict", async () => {
        vi.mocked(uploadFile).mockResolvedValue(new Response(JSON.stringify({ has_signatures: true, signatures: [{ signer: "Example signer", date: "", status: "detected" }], note: "Cryptographic verification is not supported." })));
        const { container } = render(<VerifySignatureUI />);
        fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [new File(["%PDF"], "signed.pdf")] } });
        fireEvent.click(screen.getByRole("button", { name: "Verify signatures" }));
        await screen.findByText("Signature fields found");
        expect(screen.getByText("Detected")).toBeInTheDocument();
        expect(screen.queryByText("Invalid")).not.toBeInTheDocument();
        expect(screen.queryByText(/broken or tampered/i)).not.toBeInTheDocument();
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
