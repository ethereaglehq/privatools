import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { ImageToPdfUI } from "./ImageToPdfUI";
import { HeicToPdfUI } from "./NamedImageToPdfVariants";
import { processFilesAndDownload } from "@/lib/api";

vi.mock("@/lib/file-handoff", () => ({ consumeFileHandoffs: vi.fn(async () => []) }));
vi.mock("@/lib/api", async importOriginal => ({
    ...await importOriginal<typeof import("@/lib/api")>(),
    processFilesAndDownload: vi.fn(async () => undefined),
}));
vi.mock("@/hooks/useFirstSuccess", () => ({ emitToolSuccess: vi.fn() }));
vi.mock("@/lib/toolRun", () => ({ emitToolRun: vi.fn() }));

const MB = 1024 * 1024;

function photos(count: number, { from = 1, bytes = MB, ext = "jpg" } = {}) {
    return Array.from({ length: count }, (_, index) => {
        const file = new File(["x"], `IMG_${from + index}.${ext}`, { type: ext === "jpg" ? "image/jpeg" : "image/heic" });
        Object.defineProperty(file, "size", { value: bytes });
        return file;
    });
}

function choose(files: File[]) {
    const input = document.querySelector<HTMLInputElement>('input[type="file"]');
    if (!input) throw new Error("file input missing");
    fireEvent.change(input, { target: { files } });
}

beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
});
afterEach(cleanup);

describe("Image to PDF limits", { timeout: 20_000 }, () => {
    it("states how many images and megabytes one PDF takes before anything is chosen", () => {
        render(<ImageToPdfUI />);
        expect(screen.getByText(/One PDF takes up to 100 images, 200 MB in total\./)).toBeVisible();
        expect(screen.getByText("0 of 100 images selected")).toBeVisible();
    });

    it("refuses 100 phone photos that add up to more than 200 MB, saying how much they are", () => {
        render(<ImageToPdfUI />);
        choose(photos(100, { bytes: 3.5 * MB }));

        expect(screen.getByRole("alert")).toHaveTextContent(
            "One PDF takes up to 200 MB of images and this selection is 350.0 MB, so it was not added.",
        );
        expect(screen.getByText("0 of 100 images selected")).toBeVisible();
    });

    it("keeps a running total against the 200 MB cap and refuses the selection that would pass it", () => {
        render(<ImageToPdfUI />);
        choose(photos(50, { bytes: 3.5 * MB }));
        expect(screen.getByText("175.0 MB of 200 MB")).toBeVisible();
        choose(photos(8, { from: 51, bytes: 3.5 * MB }));

        const alert = screen.getByRole("alert");
        expect(alert).toHaveTextContent(
            "One PDF takes up to 200 MB of images. Adding these 8 would make 203.0 MB, so they were not added.",
        );
        expect(screen.getByText("50 of 100 images selected")).toBeVisible();
        // Shown where the selection was made, not after 50 thumbnails.
        const pages = screen.getByRole("region", { name: "Page order" });
        expect(alert.compareDocumentPosition(pages) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });

    it("sends 100 images of exactly 200 MB in one request, without the 60-second client deadline", async () => {
        let finish!: () => void;
        vi.mocked(processFilesAndDownload).mockImplementationOnce(() => new Promise<void>(resolve => { finish = resolve; }));
        render(<ImageToPdfUI />);
        choose(photos(60, { bytes: 2 * MB }));
        choose(photos(40, { from: 61, bytes: 2 * MB }));
        expect(screen.getByText("100 of 100 images selected")).toBeVisible();
        expect(screen.getByText("200.0 MB of 200 MB")).toBeVisible();
        fireEvent.click(screen.getByRole("button", { name: "Convert 100 images → PDF" }));

        // Progress shows above the 100 thumbnails, and says a full batch takes a while.
        const progress = await screen.findByRole("status");
        expect(progress).toHaveTextContent("100 images, arranged in one PDF. Large batches can take a few minutes.");
        const pages = screen.getByRole("region", { name: "Page order" });
        expect(progress.compareDocumentPosition(pages) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

        expect(processFilesAndDownload).toHaveBeenCalledTimes(1);
        const [endpoint, files, , params, , , options] = vi.mocked(processFilesAndDownload).mock.calls[0];
        expect(endpoint).toBe("/image-to-pdf");
        expect(files.map(file => file.name)).toEqual(Array.from({ length: 100 }, (_, index) => `IMG_${index + 1}.jpg`));
        expect(params).toEqual({ page_size: "auto" });
        // The upload alone can take minutes; the server bounds the processing.
        expect(options?.timeoutMs).toBe(0);

        await act(async () => finish());
        expect(await screen.findByText("100 images, one PDF.")).toBeVisible();
    });

    it("refuses a selection that would make 101 images and keeps the images already chosen", () => {
        render(<ImageToPdfUI />);
        choose(photos(60));
        choose(photos(41, { from: 61 }));

        expect(screen.getByRole("alert")).toHaveTextContent(
            "One PDF takes up to 100 images. Adding these 41 would make 101, so they were not added.",
        );
        expect(screen.getByText("60 of 100 images selected")).toBeVisible();
        expect(screen.getByRole("button", { name: "Convert 60 images → PDF" })).toBeEnabled();
        expect(processFilesAndDownload).not.toHaveBeenCalled();
    });

    it("counts in the variant's own noun", () => {
        render(<HeicToPdfUI />);
        choose(photos(2, { ext: "heic" }));
        expect(screen.getByText("2 of 100 HEIC photos selected")).toBeVisible();
    });
});
