import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import BatchPage from "./BatchPage";
import { postFormData } from "@/lib/api";

vi.mock("@/lib/api", async load => ({ ...await load<typeof import("@/lib/api")>(), postFormData: vi.fn() }));

beforeEach(() => {
    localStorage.clear(); vi.clearAllMocks();
    vi.mocked(postFormData).mockResolvedValue({ blob: async () => new Blob(["output"]), headers: new Headers() } as Response);
});
afterEach(cleanup);

function setup(tool: string, file: File) {
    const { container } = render(<BatchPage />);
    fireEvent.click(within(container.querySelector(".pt-batch-tool-picker") as HTMLElement).getByRole("button", { name: /Change tool/ }));
    fireEvent.change(screen.getByPlaceholderText(/Filter .* batchable tools/), { target: { value: tool } });
    fireEvent.click(screen.getByRole("button", { name: tool }));
    fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [file] } });
    return container;
}

function requestBody() {
    const body = vi.mocked(postFormData).mock.calls[0][1];
    return typeof body === "function" ? body() : body;
}

describe("batch processing contract", () => {
    it("sends PNG-to-WebP's selected format instead of the generic converter default", async () => {
        setup("PNG to WebP", new File(["synthetic image"], "weekend.png", { type: "image/png" }));
        fireEvent.click(screen.getByRole("button", { name: "Process 1" }));
        await screen.findByRole("link", { name: "Download" });
        expect(postFormData).toHaveBeenCalledOnce();
        expect(vi.mocked(postFormData).mock.calls[0][0]).toBe("/image-converter");
        expect(requestBody().get("target_format")).toBe("webp");
    });
    it("prevents Highlight from uploading until the required search text is provided", async () => {
        setup("Highlight PDF", new File(["synthetic PDF"], "weekend.pdf", { type: "application/pdf" }));
        expect(screen.getByRole("button", { name: "Process 1" })).toBeDisabled();
        expect(postFormData).not.toHaveBeenCalled();
        fireEvent.change(screen.getByLabelText("Text to highlight in every PDF"), { target: { value: " weekend " } });
        fireEvent.click(screen.getByRole("button", { name: "Process 1" }));
        await screen.findByRole("link", { name: "Download" });
        expect(vi.mocked(postFormData).mock.calls[0][0]).toBe("/highlight");
        expect(requestBody().get("query")).toBe("weekend");
    });
    it("converts subtitle batches locally without requesting a nonexistent backend endpoint", async () => {
        const file = new File(["1\n00:00:01,000 --> 00:00:02,000\nHello weekend\n"], "weekend.srt", { type: "text/plain" });
        Object.defineProperty(file, "text", { value: async () => "1\n00:00:01,000 --> 00:00:02,000\nHello weekend\n" });
        const captureBlob = vi.spyOn(URL, "createObjectURL");
        setup("Subtitle Converter", file);
        expect(screen.getByText(/Subtitle conversion runs on this device/)).toBeVisible();
        fireEvent.click(screen.getByRole("button", { name: "Process 1" }));
        const download = await screen.findByRole("link", { name: "Download" });
        expect(postFormData).not.toHaveBeenCalled();
        expect(download).toHaveAttribute("download", "weekend.vtt");
        expect(captureBlob.mock.calls.at(-1)?.[0]).toMatchObject({ type: "text/vtt" });
        captureBlob.mockRestore();
    });
    it("shows malformed subtitles as an actionable per-file error", async () => {
        const file = new File(["no cues"], "broken.srt", { type: "text/plain" });
        Object.defineProperty(file, "text", { value: async () => "no cues" });
        setup("Subtitle Converter", file);
        fireEvent.click(screen.getByRole("button", { name: "Process 1" }));
        await waitFor(() => expect(screen.getByText(/subtitle block has no valid timing line/)).toBeVisible());
        expect(postFormData).not.toHaveBeenCalled();
        expect(screen.queryByRole("link", { name: "Download" })).not.toBeInTheDocument();
    });
});
