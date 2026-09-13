import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SummarizePdfUI } from "./SummarizePdfUI";
const mocks = vi.hoisted(() => ({ content: vi.fn(), pipeline: vi.fn() }));
vi.mock("pdfjs-dist", () => ({ GlobalWorkerOptions: {}, getDocument: () => ({ promise: Promise.resolve({ numPages: 1, getPage: async () => ({ getTextContent: mocks.content }) }) }) }));
vi.mock("pdfjs-dist/build/pdf.worker.mjs?url", () => ({ default: "worker.js" }));
vi.mock("@huggingface/transformers", () => ({ env: {}, pipeline: mocks.pipeline }));
vi.mock("@/hooks/useByok", () => ({ useByok: () => ({ ready: false, provider: null }) }));
beforeEach(() => { localStorage.clear(); mocks.content.mockReset(); mocks.pipeline.mockReset(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
function pick() { const { container } = render(<SummarizePdfUI />); const file = new File(["sample"], "sample.pdf", { type: "application/pdf" }); Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(1) }); fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [file] } }); fireEvent.click(screen.getByRole("button", { name: "Summarize this PDF" })); }
describe("summary run boundaries", () => {
 it("does not start a model after cancelling PDF extraction", async () => { let resolve!: (value: unknown) => void; mocks.content.mockImplementation(() => new Promise(r => { resolve = r; })); pick(); await waitFor(() => expect(mocks.content).toHaveBeenCalled()); fireEvent.click(screen.getByRole("button", { name: "Cancel" })); await act(async () => resolve({ items: [{ str: "A useful document with enough text to summarize." }] })); expect(mocks.pipeline).not.toHaveBeenCalled(); expect(screen.getByRole("button", { name: "Summarize this PDF" })).toBeEnabled(); });
 it("retries a model download after a loading failure", async () => { vi.spyOn(console, "error").mockImplementation(() => {}); mocks.content.mockResolvedValue({ items: [{ str: "A useful document to summarize." }] }); const summarize = vi.fn().mockResolvedValue([{ summary_text: "A useful summary." }]); mocks.pipeline.mockRejectedValueOnce(new Error("Model download interrupted")).mockResolvedValueOnce(summarize); pick(); expect(await screen.findByRole("alert")).toHaveTextContent("Model download interrupted"); fireEvent.click(screen.getByRole("button", { name: "Summarize this PDF" })); await screen.findByText("A useful summary."); expect(mocks.pipeline).toHaveBeenCalledTimes(2); expect(summarize).toHaveBeenCalled(); });
});
